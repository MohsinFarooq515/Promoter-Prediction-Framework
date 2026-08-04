from __future__ import annotations

import csv, json
from pathlib import Path
import numpy as np

from src.evaluation import bootstrap_ci, metrics, select_threshold

RUNS = {
    "bacteria": ("multiscale_cnn", "screening"),
    "archaea": ("multiscale_cnn", "screening"),
    "eukaryota": ("residual_cnn", "eukaryota_multiscale"),
}
SEEDS = (2025, 2026, 2027)

def read_predictions(path):
    rows=list(csv.DictReader(path.open()))
    return rows,{r["internal_id"]:float(r["promoter_probability"]) for r in rows}

def main():
    output=Path("results/main_tables/multiseed_ensemble.json"); output.parent.mkdir(parents=True,exist_ok=True); summary={}
    for domain,(model,config) in RUNS.items():
        root=Path("results/checkpoints")/domain/model/config
        validation=[]; tests=[]; validation_rows=None; test_rows=None
        for seed in SEEDS:
            validation_rows,pv=read_predictions(root/f"seed_{seed}/validation_predictions.csv")
            test_rows,pt=read_predictions(root/f"seed_{seed}/test_predictions.csv")
            validation.append(pv); tests.append(pt)
        validation_ids=[r["internal_id"] for r in validation_rows]; test_ids=[r["internal_id"] for r in test_rows]
        if any(set(x)!=set(validation_ids) for x in validation) or any(set(x)!=set(test_ids) for x in tests): raise RuntimeError(f"prediction ID mismatch for {domain}")
        yv=np.array([int(r["true_label"]) for r in validation_rows]); yt=np.array([int(r["true_label"]) for r in test_rows])
        pv=np.mean([[x[i] for i in validation_ids] for x in validation],axis=0); pt=np.mean([[x[i] for i in test_ids] for x in tests],axis=0)
        threshold=select_threshold(yv,pv); result={"model":model,"seeds":list(SEEDS),"threshold":threshold,"validation":metrics(yv,pv,threshold),"test":metrics(yt,pt,threshold),"test_bootstrap_95_ci":bootstrap_ci(yt,pt,threshold,n=1000)}; summary[domain]=result
        rows=[]
        for original,prob in zip(test_rows,pt): rows.append({**original,"promoter_probability":float(prob),"predicted_label":int(prob>=threshold),"threshold":threshold,"model_name":f"{model}_mean_seed_ensemble","seed":"2025;2026;2027"})
        target=Path("results/predictions")/f"{domain}_multiseed_ensemble_test.csv"; target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("w",newline="") as f: writer=csv.DictWriter(f,fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
    output.write_text(json.dumps(summary,indent=2)); print(output)

if __name__=="__main__": main()
