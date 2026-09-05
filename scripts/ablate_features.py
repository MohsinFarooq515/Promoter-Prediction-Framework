from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold

from src.data import assign_splits, build_records
from src.evaluation import metrics, select_threshold
from src.features import feature_matrix, position_windows
from src.groups import MODEL_GROUPS, records_for_group

KMER_CANDIDATES=(
    ("directional_1_4",("legacy_kmers",)),
    ("directional_1_6",("directional_kmers_1_6",)),
    ("directional_3_6",("directional_kmers_3_6",)),
    ("canonical_1_6",("canonical_kmers",)),
)


def oof_score(records,domain,maximum_length,blocks,trees,threads,folds):
    labels=np.asarray([r.label for r in records]); groups=np.asarray([r.group_id for r in records])
    matrix=feature_matrix([r.sequence for r in records],maximum_length,domain,blocks)
    splitter=StratifiedGroupKFold(n_splits=folds,shuffle=True,random_state=2025)
    probability=np.empty(len(records),dtype=float); fold_mcc=[]
    for fold,(train_index,valid_index) in enumerate(splitter.split(matrix,labels,groups)):
        forest=RandomForestClassifier(n_estimators=trees,class_weight="balanced_subsample",max_features="sqrt",
            min_samples_leaf=2,n_jobs=threads,random_state=2025+fold)
        forest.fit(matrix[train_index],labels[train_index]); fold_probability=forest.predict_proba(matrix[valid_index])[:,1]
        probability[valid_index]=fold_probability
        fold_threshold=select_threshold(labels[valid_index],fold_probability)
        fold_mcc.append(float(metrics(labels[valid_index],fold_probability,fold_threshold)["mcc"]))
    threshold=select_threshold(labels,probability); score=metrics(labels,probability,threshold)
    return {"feature_count":int(matrix.shape[1]),"threshold":float(threshold),"mcc":float(score["mcc"]),
        "accuracy":float(score["accuracy"]),"pr_auc":float(score["pr_auc"]),"roc_auc":float(score["roc_auc"]),
        "fold_mcc":fold_mcc,"mean_fold_mcc":float(np.mean(fold_mcc)),"std_fold_mcc":float(np.std(fold_mcc))}


def ablate_group(group,records,trees,threads,minimum_delta,folds):
    details=MODEL_GROUPS[group]
    development=[r for r in records_for_group(records,group) if r.partition in {"train","validation"}]
    maximum_length=max(r.model_input_length for r in development); stages=[]
    for name,blocks in KMER_CANDIDATES:
        score=oof_score(development,details["domain"],maximum_length,blocks,trees,threads,folds)
        stages.append({"stage":name,"candidate_blocks":list(blocks),**score})
    baseline=stages[0]; best=max(stages,key=lambda row:(row["mcc"],row["pr_auc"]))
    if best is not baseline and best["mcc"]-baseline["mcc"]<minimum_delta: best=baseline
    selected=list(best["candidate_blocks"]); current=best
    for name in ("position_specific","stability"):
        if name=="position_specific" and not position_windows(details["domain"],maximum_length):
            stages.append({"stage":name,"candidate_blocks":selected.copy(),"accepted":False,"not_applicable":True,"delta_mcc":0.0}); continue
        candidate=selected+[name]
        score=oof_score(development,details["domain"],maximum_length,candidate,trees,threads,folds)
        delta=score["mcc"]-current["mcc"]; accepted=delta>=minimum_delta
        stages.append({"stage":name,"candidate_blocks":candidate,"accepted":accepted,"delta_mcc":float(delta),**score})
        if accepted: selected=candidate; current=stages[-1]
    for row in stages[:len(KMER_CANDIDATES)]:
        row["accepted"]=row["stage"]==best["stage"]
        row["delta_mcc"]=float(row["mcc"]-baseline["mcc"])
    return {"model_group":group,"domain":details["domain"],"organism":details["organism"],
        "protocol":"3-fold grouped out-of-fold development predictions; test untouched","development_count":len(development),
        "trees":trees,"folds":folds,"minimum_mcc_delta":minimum_delta,"selected_blocks":selected,
        "validation_oof":{key:current[key] for key in ("feature_count","threshold","mcc","accuracy","pr_auc","roc_auc","fold_mcc","mean_fold_mcc","std_fold_mcc")},"stages":stages}


def main():
    parser=argparse.ArgumentParser(description="Grouped OOF sequential feature ablation")
    parser.add_argument("--group",choices=[*MODEL_GROUPS,"all"],default="all")
    parser.add_argument("--trees",type=int,default=50); parser.add_argument("--threads",type=int,default=4)
    parser.add_argument("--folds",type=int,default=3); parser.add_argument("--minimum-mcc-delta",type=float,default=0.002)
    parser.add_argument("--data-dir",default="data/3) finalized")
    args=parser.parse_args(); records,_,_=build_records(args.data_dir); records,_=assign_splits(records)
    groups=MODEL_GROUPS if args.group=="all" else (args.group,); output={}
    for group in groups:
        print(f"OOF feature ablation: {group}",flush=True)
        output[group]=ablate_group(group,records,args.trees,args.threads,args.minimum_mcc_delta,args.folds)
        print(json.dumps({group:{"selected_blocks":output[group]["selected_blocks"],"validation_oof":output[group]["validation_oof"]}},indent=2),flush=True)
    target=Path("results/main_tables/feature_ablation_oof.json"); target.parent.mkdir(parents=True,exist_ok=True)
    existing=json.loads(target.read_text()) if target.exists() and args.group!="all" else {}; existing.update(output)
    target.write_text(json.dumps(existing,indent=2)); print(target)


if __name__=="__main__": main()
