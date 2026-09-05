from __future__ import annotations

import csv
import gc
import hashlib
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.model_selection import ParameterGrid, StratifiedGroupKFold
from torch.utils.data import DataLoader, WeightedRandomSampler

from .data import SequenceDataset
from .evaluation import metrics, select_threshold
from .models import MODELS
from .training import collate, logits


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def _loader(records, cfg, train=False):
    sampler = None
    shuffle = train
    if train and cfg.get("balanced_sampler", False):
        labels = np.asarray([r.label for r in records])
        counts = np.bincount(labels, minlength=2)
        weights = torch.as_tensor([1.0 / max(counts[r.label], 1) for r in records], dtype=torch.double)
        sampler, shuffle = WeightedRandomSampler(weights, len(weights), replacement=True), False
    return DataLoader(
        SequenceDataset(records), batch_size=int(cfg["batch_size"]), shuffle=shuffle,
        sampler=sampler, num_workers=int(cfg.get("workers", 2)), collate_fn=collate,
        pin_memory=torch.cuda.is_available(), persistent_workers=int(cfg.get("workers", 2)) > 0,
    )


def _to_device(batch, device):
    return {k: (v.to(device, non_blocking=True) if torch.is_tensor(v) else v) for k, v in batch.items()}


@torch.inference_mode()
def predict_gpu(model, records, cfg, device):
    model.eval(); ids, ys, ps = [], [], []
    for batch in _loader(records, cfg):
        ids.extend(batch["id"]); batch = _to_device(batch, device)
        with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=bool(cfg.get("amp", True) and device.type == "cuda")):
            output = model(batch["x"], batch["position_mask"], length=batch["length"], domain=batch["domain"])
        ys.extend(batch["label"].cpu().tolist()); ps.extend(torch.sigmoid(logits(output)).float().cpu().tolist())
    return ids, ys, ps


def fit_fold(train_records, valid_records, params, cfg, device, seed):
    seed_everything(seed)
    model = MODELS[params["model_name"]](**params).to(device)
    if cfg.get("compile", False) and hasattr(torch, "compile"):
        model = torch.compile(model)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(params["learning_rate"]), weight_decay=float(params["weight_decay"]))
    labels = np.asarray([r.label for r in train_records])
    pw = torch.tensor([(labels == 0).sum() / max((labels == 1).sum(), 1)], device=device, dtype=torch.float32)
    criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pw if cfg.get("weighted_bce", True) else None)
    scaler = torch.amp.GradScaler("cuda", enabled=bool(cfg.get("amp", True) and device.type == "cuda"))
    best_state, best_score, best_epoch, stale = None, -2.0, -1, 0
    for epoch in range(int(cfg["epochs"])):
        model.train()
        for batch in _loader(train_records, cfg, train=True):
            batch = _to_device(batch, device); optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=scaler.is_enabled()):
                output = model(batch["x"], batch["position_mask"], length=batch["length"], domain=batch["domain"])
                if torch.is_tensor(output):
                    loss = criterion(output, batch["label"].float())
                else:
                    loss = criterion(output["shared"], batch["label"].float()) + criterion(output["specialist"], batch["label"].float()) + float(cfg.get("domain_loss_weight",.1))*torch.nn.functional.cross_entropy(output["domain"],batch["domain"])
            scaler.scale(loss).backward(); scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), float(cfg.get("gradient_clip", 1.0)))
            scaler.step(optimizer); scaler.update()
        _, y, p = predict_gpu(model, valid_records, cfg, device)
        score = metrics(y, p, select_threshold(y, p))[cfg.get("primary_metric", "mcc")]
        if score > best_score:
            best_score, best_epoch, stale = score, epoch, 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            stale += 1
        if stale >= int(cfg["patience"]): break
    model.load_state_dict(best_state)
    ids, y, p = predict_gpu(model, valid_records, cfg, device)
    del model, optimizer, scaler; gc.collect()
    if device.type == "cuda": torch.cuda.empty_cache()
    return ids, y, p, best_epoch + 1


def _expand_spaces(spaces):
    return [p for space in spaces for p in ParameterGrid(space)]


def run_grid_search(records, output_dir, cfg):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda": raise RuntimeError("CUDA GPU not found. In Colab select Runtime > Change runtime type > T4 GPU.")
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    dev = [r for r in records if r.partition in {"train", "validation"}]
    test = [r for r in records if r.partition == "test"]
    y = np.asarray([r.label for r in dev]); groups = np.asarray([r.group_id for r in dev])
    strata = np.asarray([f"{r.organism}|{r.label}" for r in dev])
    splitter = StratifiedGroupKFold(n_splits=int(cfg["folds"]), shuffle=True, random_state=int(cfg["seed"]))
    splits = list(splitter.split(np.zeros(len(dev)), strata, groups))
    results_file = out / "grid_results.json"
    trials = json.loads(results_file.read_text()) if results_file.exists() else []
    completed = {row["key"] for row in trials}
    params_list = _expand_spaces(cfg["search_spaces"])
    search_settings = {k: v for k, v in cfg.items() if k != "search_spaces"}
    valid_keys = {
        hashlib.sha256(json.dumps({"params": p, "search_settings": search_settings}, sort_keys=True).encode()).hexdigest()[:12]
        for p in params_list
    }
    for trial, params in enumerate(params_list):
        key = hashlib.sha256(json.dumps({"params": params, "search_settings": search_settings}, sort_keys=True).encode()).hexdigest()[:12]
        if key in completed:
            print(f"trial {trial + 1}/{len(params_list)} already complete ({key})", flush=True)
            continue
        oof_y, oof_p, fold_epochs = [], [], []
        started = time.time()
        for fold, (ti, vi) in enumerate(splits):
            _, fy, fp, epochs = fit_fold([dev[i] for i in ti], [dev[i] for i in vi], params, cfg, device, int(cfg["seed"]) + fold)
            oof_y.extend(fy); oof_p.extend(fp); fold_epochs.append(epochs)
        threshold = select_threshold(oof_y, oof_p); result = metrics(oof_y, oof_p, threshold)
        row = {"trial": trial, "key": key, "params": params, "threshold": threshold, "fold_epochs": fold_epochs,
               "duration_seconds": time.time() - started, **result}
        trials.append(row)
        results_file.write_text(json.dumps(trials, indent=2))
        print(f"trial {trial + 1}/{len(params_list)} {params['model_name']} MCC={result['mcc']:.4f} PR-AUC={result['pr_auc']:.4f}", flush=True)
    primary = cfg.get("primary_metric", "mcc")
    current_trials = [row for row in trials if row["key"] in valid_keys]
    best = max(current_trials, key=lambda r: (r[primary], r["pr_auc"]))
    final_cfg = {**cfg, **best["params"], "epochs": max(1, int(round(np.median(best["fold_epochs"])))), "patience": 10**9}
    # Fixed CV-derived epoch count; an empty validation list is avoided by training one final fold-like pass manually.
    seed_everything(int(cfg["seed"])); model = MODELS[best["params"]["model_name"]](**best["params"]).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(best["params"]["learning_rate"]), weight_decay=float(best["params"]["weight_decay"]))
    labels = np.asarray([r.label for r in dev]); pw = torch.tensor([(labels == 0).sum()/max((labels == 1).sum(), 1)], device=device, dtype=torch.float32)
    criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pw if cfg.get("weighted_bce", True) else None)
    scaler = torch.amp.GradScaler("cuda", enabled=bool(cfg.get("amp", True)))
    for _ in range(final_cfg["epochs"]):
        model.train()
        for batch in _loader(dev, final_cfg, train=True):
            batch = _to_device(batch, device); optimizer.zero_grad(set_to_none=True)
            with torch.autocast("cuda", dtype=torch.float16, enabled=scaler.is_enabled()):
                output = model(batch["x"], batch["position_mask"], length=batch["length"], domain=batch["domain"])
                loss = criterion(logits(output), batch["label"].float())
            scaler.scale(loss).backward(); scaler.unscale_(optimizer); torch.nn.utils.clip_grad_norm_(model.parameters(), float(cfg.get("gradient_clip", 1.0))); scaler.step(optimizer); scaler.update()
    torch.save({"model": model.state_dict(), "model_name": best["params"]["model_name"], "params": best["params"]}, out / "best_model.pt")
    ids, test_y, test_p = predict_gpu(model, test, final_cfg, device); threshold = best["threshold"]
    test_metrics = metrics(test_y, test_p, threshold)
    (out / "best_params.json").write_text(json.dumps(best, indent=2)); (out / "test_metrics.json").write_text(json.dumps(test_metrics, indent=2))
    with (out / "test_predictions.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["internal_id", "true_label", "promoter_probability", "predicted_label"]); writer.writeheader()
        writer.writerows({"internal_id": i, "true_label": yy, "promoter_probability": pp, "predicted_label": int(pp >= threshold)} for i, yy, pp in zip(ids, test_y, test_p))
    summary = {"device": str(device), "gpu": torch.cuda.get_device_name(0), "trials": len(current_trials), "development_records": len(dev), "test_records": len(test), "best": best, "test_metrics": test_metrics}
    (out / "summary.json").write_text(json.dumps(summary, indent=2)); return summary
