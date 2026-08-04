from __future__ import annotations
import csv, hashlib, json, os, random, time
from pathlib import Path
import numpy as np, torch
from torch.utils.data import DataLoader, WeightedRandomSampler
from .data import SequenceDataset
from .evaluation import metrics, select_threshold
from .models import MODELS

def seed_all(seed): random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.use_deterministic_algorithms(True,warn_only=True)
def collate(batch):
    out={}
    for key in ("x","valid_mask","position_mask","length","label","domain"):
        vals=[b[key] for b in batch]; out[key]=torch.stack(vals) if torch.is_tensor(vals[0]) else torch.tensor(vals)
    out["id"]=[b["id"] for b in batch]; return out
def logits(output,alpha=.5): return output if torch.is_tensor(output) else alpha*output["shared"]+(1-alpha)*output["specialist"]

def predict(model,records,batch_size=128):
    model.eval(); ids=[]; ys=[]; ps=[]
    with torch.no_grad():
        for b in DataLoader(SequenceDataset(records),batch_size=batch_size,collate_fn=collate):
            out=model(b["x"],b["position_mask"],length=b["length"],domain=b["domain"]); ps.extend(torch.sigmoid(logits(out)).tolist()); ys.extend(b["label"].tolist()); ids.extend(b["id"])
    return ids,ys,ps

def train(records,model_name,output_dir,config,resume=True):
    seed=int(config.get("seed",2025)); seed_all(seed); torch.set_num_threads(int(config.get("threads",4)))
    subsets={p:[r for r in records if r.partition==p] for p in ("train","validation","test")}; model=MODELS[model_name](**config); outdir=Path(output_dir); outdir.mkdir(parents=True,exist_ok=True); latest=outdir/"latest.pt"
    optimizer=torch.optim.AdamW(model.parameters(),lr=float(config.get("learning_rate",3e-4)),weight_decay=float(config.get("weight_decay",1e-4))); scheduler=torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer,mode="max",patience=3,factor=.5)
    selection_config={k:v for k,v in config.items() if k != "evaluate_test"}
    config_hash=hashlib.sha256(json.dumps(selection_config,sort_keys=True).encode()).hexdigest()
    complete=outdir/"validation_complete.json"
    if resume and complete.exists():
        done=json.loads(complete.read_text())
        if done.get("config_hash")==config_hash and (not config.get("evaluate_test",False) or (outdir/"test_metrics.json").exists()): return outdir
    start=0; best=-2.; history=[]; stale=0
    if resume and latest.exists():
        ck=torch.load(latest,map_location="cpu",weights_only=False); model.load_state_dict(ck["model"]); optimizer.load_state_dict(ck["optimizer"]); scheduler.load_state_dict(ck["scheduler"]); start=ck["epoch"]+1; best=ck["best_mcc"]; history=ck["history"]; stale=ck.get("stale",0)
    labels=np.array([r.label for r in subsets["train"]]); pos_weight=torch.tensor([(labels==0).sum()/max((labels==1).sum(),1)],dtype=torch.float32); loss_fn=torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight if config.get("weighted_bce",True) else None); began=time.time(); patience=int(config.get("patience",8))
    for epoch in range(start,int(config.get("epochs",25))):
        if stale>=patience: break
        model.train(); losses=[]
        train_rows=subsets["train"]
        if config.get("balanced_sampler",True):
            from collections import Counter
            strata=Counter((r.domain,r.organism,r.label) for r in train_rows)
            weights=torch.tensor([1.0/strata[(r.domain,r.organism,r.label)] for r in train_rows],dtype=torch.double)
            sampler=WeightedRandomSampler(weights,len(weights),replacement=True); shuffle=False
        else: sampler=None; shuffle=True
        loader=DataLoader(SequenceDataset(train_rows),batch_size=int(config.get("batch_size",64)),shuffle=shuffle,sampler=sampler,num_workers=int(config.get("workers",0)),collate_fn=collate)
        for b in loader:
            optimizer.zero_grad(); output=model(b["x"],b["position_mask"],length=b["length"],domain=b["domain"])
            if torch.is_tensor(output): loss=loss_fn(output,b["label"].float())
            else: loss=loss_fn(output["shared"],b["label"].float())+loss_fn(output["specialist"],b["label"].float())+float(config.get("domain_loss_weight",.1))*torch.nn.functional.cross_entropy(output["domain"],b["domain"])
            loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),float(config.get("gradient_clip",1.0))); optimizer.step(); losses.append(loss.item())
        ids,y,p=predict(model,subsets["validation"],int(config.get("batch_size",64))*2); threshold=select_threshold(y,p); val=metrics(y,p,threshold); scheduler.step(val["mcc"]); history.append({"epoch":epoch,"train_loss":float(np.mean(losses)),"validation_mcc":val["mcc"],"validation_pr_auc":val["pr_auc"],"threshold":threshold})
        improved=val["mcc"]>best
        if improved: best=val["mcc"]; stale=0
        else: stale+=1
        state={"epoch":epoch,"model":model.state_dict(),"optimizer":optimizer.state_dict(),"scheduler":scheduler.state_dict(),"best_mcc":best,"stale":stale,"history":history,"config":config,"config_hash":config_hash,"model_name":model_name}; torch.save(state,latest)
        if improved: torch.save(state,outdir/"best_mcc.pt")
        if val["pr_auc"]>=max(h["validation_pr_auc"] for h in history): torch.save(state,outdir/"best_pr_auc.pt")
        (outdir/"history.json").write_text(json.dumps(history,indent=2))
        if stale>=patience: break
    ck=torch.load(outdir/"best_mcc.pt",map_location="cpu",weights_only=False); model.load_state_dict(ck["model"]); _,yv,pv=predict(model,subsets["validation"]); threshold=select_threshold(yv,pv)
    parts=["validation"]+(["test"] if config.get("evaluate_test",False) else [])
    for part in parts:
        ids,y,p=predict(model,subsets[part]); rows=[]
        lookup={r.internal_id:r for r in subsets[part]}
        for i,t,prob in zip(ids,y,p):
            r=lookup[i]; rows.append({"internal_id":i,"original_header":r.original_header,"source_file":r.source_file,"domain":r.domain,"organism":r.organism,"true_label":t,"predicted_label":int(prob>=threshold),"promoter_probability":prob,"threshold":threshold,"partition":part,"model_name":model_name,"seed":seed,"fold":""})
        with (outdir/f"{part}_predictions.csv").open("w",newline="") as f: w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
        (outdir/f"{part}_metrics.json").write_text(json.dumps(metrics(y,p,threshold),indent=2))
    (outdir/"run.json").write_text(json.dumps({"duration_seconds":time.time()-began,"parameter_count":sum(p.numel() for p in model.parameters()),"threshold":threshold,"seed":seed,"config_hash":config_hash},indent=2))
    complete.write_text(json.dumps({"config_hash":config_hash,"epochs_completed":len(history),"best_epoch":ck["epoch"],"best_validation_mcc":best},indent=2)); return outdir
