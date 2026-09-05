from __future__ import annotations

import csv, json
from pathlib import Path
import numpy as np

from src.evaluation import bootstrap_ci, metrics, select_threshold
from src.groups import DOMAIN_GROUPS, MODEL_GROUPS

RUNS = {
    "ecoli": ("multiscale_cnn", "screening"),
    "bsubtilis": ("multiscale_cnn", "screening"),
    "archaea": ("multiscale_cnn", "screening"),
    "human": ("residual_cnn", "eukaryota_multiscale"),
    "mouse": ("residual_cnn", "eukaryota_multiscale"),
    "arabidopsis": ("residual_cnn", "eukaryota_multiscale"),
}
SEEDS = (2025, 2026, 2027)

def read_predictions(path):
    rows=list(csv.DictReader(path.open()))
    return rows,{r["internal_id"]:float(r["promoter_probability"]) for r in rows}

def main():
    output=Path("results/main_tables/multiseed_ensemble.json"); output.parent.mkdir(parents=True,exist_ok=True); summary={}
    for group,(model,config) in RUNS.items():
        root=Path("results/checkpoints")/group/model/config
        validation=[]; tests=[]; validation_rows=None; test_rows=None
        for seed in SEEDS:
            validation_rows,pv=read_predictions(root/f"seed_{seed}/validation_predictions.csv")
            test_rows,pt=read_predictions(root/f"seed_{seed}/test_predictions.csv")
            validation.append(pv); tests.append(pt)
        validation_ids=[r["internal_id"] for r in validation_rows]; test_ids=[r["internal_id"] for r in test_rows]
        if any(set(x)!=set(validation_ids) for x in validation) or any(set(x)!=set(test_ids) for x in tests): raise RuntimeError(f"prediction ID mismatch for {group}")
        yv=np.array([int(r["true_label"]) for r in validation_rows]); yt=np.array([int(r["true_label"]) for r in test_rows])
        pv=np.mean([[x[i] for i in validation_ids] for x in validation],axis=0); pt=np.mean([[x[i] for i in test_ids] for x in tests],axis=0)
        threshold=select_threshold(yv,pv); result={"model_group":group,"domain":MODEL_GROUPS[group]["domain"],"organism":MODEL_GROUPS[group]["organism"],"model":model,"seeds":list(SEEDS),"threshold":threshold,"validation":metrics(yv,pv,threshold),"test":metrics(yt,pt,threshold),"test_count":len(yt),"test_bootstrap_95_ci":bootstrap_ci(yt,pt,threshold,n=1000)}; summary[group]=result
        rows=[]
        for original,prob in zip(test_rows,pt): rows.append({**original,"promoter_probability":float(prob),"predicted_label":int(prob>=threshold),"threshold":threshold,"model_name":f"{model}_mean_seed_ensemble","seed":"2025;2026;2027"})
        target=Path("results/predictions")/f"{group}_multiseed_ensemble_test.csv"; target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("w",newline="") as f: writer=csv.DictWriter(f,fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
    metric_names = [name for name,value in next(iter(summary.values()))["test"].items() if isinstance(value,(int,float))]
    weighted = {}
    for domain, groups in DOMAIN_GROUPS.items():
        available = [summary[group] for group in groups if group in summary]
        total = sum(row["test_count"] for row in available)
        weighted[domain] = {"groups": [row["model_group"] for row in available], "test_count": total,
            "test": {name: sum(row["test"][name] * row["test_count"] for row in available) / total for name in metric_names}}
    payload={"organism_models":summary,"domain_weighted_average":weighted}
    output.write_text(json.dumps(payload,indent=2)); print(output)

if __name__=="__main__": main()
