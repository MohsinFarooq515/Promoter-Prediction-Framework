from __future__ import annotations
import argparse, csv, json, platform, shutil, sys
from pathlib import Path
import yaml
from src.data import build_records, assign_splits, write_manifest, read_fasta, one_hot
from src.groups import DOMAIN_IDS, MODEL_GROUPS, records_for_group

DEFAULT_DATA="data/3) finalized"
def load_config(path): return yaml.safe_load(Path(path).read_text()) if path else {}
def records_and_splits(data,manifest="data/splits/split_manifest.csv"):
    records,audits,lengths=build_records(data); records,conflicts=assign_splits(records); write_manifest(records,manifest); return records,audits,lengths,conflicts
def audit(args):
    records,audits,lengths,conflicts=records_and_splits(args.data_dir)
    Path("results/main_tables").mkdir(parents=True,exist_ok=True); Path("reports").mkdir(exist_ok=True)
    Path("results/main_tables/dataset_audit.json").write_text(json.dumps(audits,indent=2))
    lines=["# Dataset audit","",f"Finalized source: `{args.data_dir}`. Original FASTA files were read only.","", "| File | Domain | Organism | Class | Sequence Count | Minimum Length | Maximum Length | Length Distribution | Equal Length |","|---|---|---|---|---:|---:|---:|---|---|"]
    for a in audits:
        dist="; ".join(f"{k} nt: {v} sequences" for k,v in a["length_distribution"].items()); lines.append(f"| {a['file']} | {a['domain']} | {a['organism']} | {a['class']} | {a['sequence_count']} | {a['minimum_length']} | {a['maximum_length']} | {dist} | {a['equal_length']} |")
    lines += ["","## Decisions",f"- Domain input lengths: {lengths}.",f"- Reverse-complement cross-label conflict groups quarantined: {len(conflicts)} ({sum(r.partition.startswith('quarantine') for r in records)} records).","- Exact duplicates and reverse complements share a deterministic group ID and cannot cross partitions.","- `N` is encoded as zeros with a separate validity mask; padding uses zeros with a position mask.","- Full statistics and SHA-256 hashes are in `results/main_tables/dataset_audit.json`."]
    Path("reports/dataset_audit.md").write_text("\n".join(lines)+"\n"); print("\n".join(lines[:18]))
def split(args): records,a,l,c=records_and_splits(args.data_dir,args.output); print(f"Wrote {args.output}: {len(records)} records, {len(c)} quarantined groups")
def train_cmd(args):
    from src.training import train
    records,_,_,_=records_and_splits(args.data_dir); cfg=load_config(args.config); cfg.update({"seed":args.seed,"epochs":args.epochs,"evaluate_test":args.evaluate_test})
    subset=[r for r in records_for_group(records,args.group) if not r.partition.startswith("quarantine")]
    config_tag=Path(args.config).stem
    output=Path("results/checkpoints")/args.group/args.model/config_tag/f"seed_{args.seed}"
    train(subset,args.model,output,cfg,not args.no_resume); print(output)
def compare(args):
    from src.evaluation import metrics
    roots=list((Path("results/checkpoints")/args.group).glob("*/*/seed_*/validation_metrics.json")); rows=[]
    for p in roots: rows.append({"model":p.parents[2].name,"config":p.parents[1].name,"seed":p.parent.name,**json.loads(p.read_text())})
    Path("results/main_tables").mkdir(parents=True,exist_ok=True); out=Path("results/main_tables")/f"{args.group}_comparison.json"; out.write_text(json.dumps(rows,indent=2)); print(out)
def predict_cmd(args):
    import torch
    from src.models import MODELS
    root=Path("results/final_models")/args.group; meta=json.loads((root/"metadata.json").read_text()); threshold=json.loads((root/"threshold.json").read_text())["threshold"]; cfg=yaml.safe_load((root/"config.yaml").read_text()); model=MODELS[meta["model_name"]](**cfg); state=torch.load(root/"model.pt",map_location="cpu",weights_only=False); model.load_state_dict(state["model"] if "model" in state else state); model.eval()
    did=DOMAIN_IDS[MODEL_GROUPS[args.group]["domain"]]
    for header,seq in read_fasta(args.fasta):
        x,valid,pos=one_hot(seq,meta["input_length"])
        with torch.no_grad(): out=model(x.unsqueeze(0),pos.unsqueeze(0),length=torch.tensor([len(seq)]),domain=torch.tensor([did])); logit=out if torch.is_tensor(out) else meta.get("shared_weight",.5)*out["shared"]+(1-meta.get("shared_weight",.5))*out["specialist"]; prob=torch.sigmoid(logit).item()
        print(json.dumps({"sequence_id":header,"promoter_probability":prob,"predicted_class":"promoter" if prob>=threshold else "non-promoter","threshold":threshold,"input_length_warning":None if len(seq)==meta["input_length"] else f"padded from {len(seq)} to {meta['input_length']}"}))
def repro(args):
    import torch, sklearn, numpy
    report={"python":sys.version,"platform":platform.platform(),"torch":torch.__version__,"numpy":numpy.__version__,"sklearn":sklearn.__version__,"cpu_threads":torch.get_num_threads()}; Path("reports").mkdir(exist_ok=True); Path("reports/reproducibility_report.md").write_text("# Reproducibility report\n\n```json\n"+json.dumps(report,indent=2)+"\n```\n"); print(json.dumps(report,indent=2))
def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(required=True,dest="command")
    a=sub.add_parser("audit"); a.add_argument("--data-dir",default=DEFAULT_DATA); a.set_defaults(func=audit)
    s=sub.add_parser("split"); s.add_argument("--data-dir",default=DEFAULT_DATA); s.add_argument("--output",default="data/splits/split_manifest.csv"); s.set_defaults(func=split)
    t=sub.add_parser("train"); t.add_argument("--data-dir",default=DEFAULT_DATA); t.add_argument("--group",choices=list(MODEL_GROUPS),required=True); t.add_argument("--model",choices=["residual_cnn","multiscale_cnn","cnn_bilstm","cnn_transformer","domain_aware"],required=True); t.add_argument("--config",default="configs/screening.yaml"); t.add_argument("--seed",type=int,default=2025); t.add_argument("--epochs",type=int,default=25); t.add_argument("--no-resume",action="store_true"); t.add_argument("--evaluate-test",action="store_true",help="Use only once after validation-only model selection is frozen"); t.set_defaults(func=train_cmd)
    c=sub.add_parser("compare"); c.add_argument("--group",choices=list(MODEL_GROUPS),required=True); c.set_defaults(func=compare)
    q=sub.add_parser("predict"); q.add_argument("--group",choices=list(MODEL_GROUPS),required=True); q.add_argument("--fasta",required=True); q.set_defaults(func=predict_cmd)
    r=sub.add_parser("reproducibility"); r.set_defaults(func=repro)
    args=p.parse_args(); args.func(args)
if __name__=="__main__": main()
