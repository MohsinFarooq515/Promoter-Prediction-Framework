from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from src.data import assign_splits, build_records
from src.evaluation import metrics, select_threshold
from src.features import feature_matrix
from src.groups import DOMAIN_GROUPS, MODEL_GROUPS, records_for_group

RUNS = {
    "ecoli": ("multiscale_cnn", "screening"),
    "bsubtilis": ("multiscale_cnn", "screening"),
    "archaea": ("multiscale_cnn", "screening"),
    "human": ("residual_cnn", "eukaryota_multiscale"),
    "mouse": ("residual_cnn", "eukaryota_multiscale"),
    "arabidopsis": ("residual_cnn", "eukaryota_multiscale"),
}
SEEDS = (2025, 2026, 2027)


def cnn_probabilities(group: str, partition: str, ids: list[str]) -> np.ndarray:
    model, config = RUNS[group]
    root = Path("results/checkpoints") / group / model / config
    seed_predictions = []
    for seed in SEEDS:
        path = root / f"seed_{seed}" / f"{partition}_predictions.csv"
        rows = {row["internal_id"]: float(row["promoter_probability"]) for row in csv.DictReader(path.open())}
        seed_predictions.append([rows[sequence_id] for sequence_id in ids])
    return np.asarray(seed_predictions).mean(axis=0)


def train_group(group: str, records, trees: int, threads: int) -> dict:
    group_records = records_for_group(records, group)
    subsets = {part: [record for record in group_records if record.partition == part]
               for part in ("train", "validation", "test")}
    maximum_length = max(record.model_input_length for record in subsets["train"])
    ablation_path=Path("results/main_tables/feature_ablation_oof.json")
    if not ablation_path.exists(): ablation_path=Path("results/main_tables/feature_ablation.json")
    ablations=json.loads(ablation_path.read_text()) if ablation_path.exists() else {}
    feature_blocks=ablations.get(group,{}).get("selected_blocks",["canonical_kmers","position_specific","stability"])
    domain=MODEL_GROUPS[group]["domain"]
    x_train = feature_matrix([record.sequence for record in subsets["train"]], maximum_length, domain, feature_blocks)
    y_train = np.asarray([record.label for record in subsets["train"]])
    forest = RandomForestClassifier(
        n_estimators=trees,
        class_weight="balanced_subsample",
        max_features="sqrt",
        min_samples_leaf=2,
        n_jobs=threads,
        random_state=2025,
    )
    forest.fit(x_train, y_train)

    probabilities = {}
    labels = {}
    for part in ("validation", "test"):
        subset = subsets[part]
        x = feature_matrix([record.sequence for record in subset], maximum_length, domain, feature_blocks)
        labels[part] = np.asarray([record.label for record in subset])
        rf = forest.predict_proba(x)[:, 1]
        cnn = cnn_probabilities(group, part, [record.internal_id for record in subset])
        probabilities[part] = (cnn, rf)

    best = None
    for cnn_weight in np.linspace(0, 1, 21):
        cnn, rf = probabilities["validation"]
        blended = cnn_weight * cnn + (1 - cnn_weight) * rf
        threshold = select_threshold(labels["validation"], blended)
        score = metrics(labels["validation"], blended, threshold)
        candidate = (score["mcc"], score["pr_auc"], float(cnn_weight), float(threshold), score)
        if best is None or candidate[:2] > best[:2]:
            best = candidate

    _, _, cnn_weight, threshold, validation_metrics = best
    cnn, rf = probabilities["test"]
    test_blended = cnn_weight * cnn + (1 - cnn_weight) * rf
    test_metrics = metrics(labels["test"], test_blended, threshold)
    cnn_test_metrics = metrics(labels["test"], cnn, select_threshold(labels["validation"], probabilities["validation"][0]))

    output = Path("results/hybrid_models") / group
    output.mkdir(parents=True, exist_ok=True)
    joblib.dump(forest, output / "random_forest.joblib", compress=3)
    metadata = {
        "model_group": group,
        "domain": MODEL_GROUPS[group]["domain"],
        "organism": MODEL_GROUPS[group]["organism"],
        "feature_version": 2,
        "feature_blocks": feature_blocks,
        "maximum_length": maximum_length,
        "trees": trees,
        "cnn_weight": cnn_weight,
        "random_forest_weight": 1 - cnn_weight,
        "threshold": threshold,
        "validation_metrics": validation_metrics,
        "test_metrics": test_metrics,
        "cnn_only_test_metrics": cnn_test_metrics,
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2))
    return metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=[*RUNS, "all"], default="all")
    parser.add_argument("--trees", type=int, default=500)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--data-dir", default="data/3) finalized")
    args = parser.parse_args()
    records, _, _ = build_records(args.data_dir)
    records, _ = assign_splits(records)
    groups = RUNS if args.group == "all" else (args.group,)
    summary = {}
    for group in groups:
        print(f"Training hybrid model for {group}...", flush=True)
        summary[group] = train_group(group, records, args.trees, args.threads)
        print(json.dumps({group: summary[group]["test_metrics"]}, indent=2), flush=True)
    weighted={}
    for domain, domain_groups in DOMAIN_GROUPS.items():
        available=[summary[group] for group in domain_groups if group in summary]
        if not available: continue
        counts={group:sum(1 for record in records_for_group(records,group) if record.partition=="test") for group in domain_groups if group in summary}
        total=sum(counts.values()); names=[name for name,value in available[0]["test_metrics"].items() if isinstance(value,(int,float))]
        weighted[domain]={"groups":[row["model_group"] for row in available],"test_count":total,"test_metrics":{
            name:sum(row["test_metrics"][name]*counts[row["model_group"]] for row in available)/total for name in names}}
    target = Path("results/main_tables/hybrid_ensemble.json")
    target.write_text(json.dumps({"organism_models":summary,"domain_weighted_average":weighted}, indent=2))
    print(target)


if __name__ == "__main__":
    main()
