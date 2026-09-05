from __future__ import annotations
import argparse, json
from pathlib import Path
import yaml
from src.data import assign_splits, build_records
from src.gpu_tuning import run_grid_search
from src.groups import MODEL_GROUPS, records_for_group

def main():
    parser = argparse.ArgumentParser(description="T4 GPU grouped-CV grid search")
    parser.add_argument("--group", choices=list(MODEL_GROUPS), required=True)
    parser.add_argument("--data-dir", default="data/3) finalized")
    parser.add_argument("--config", default="configs/colab_grid.yaml")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text())
    records, _, _ = build_records(args.data_dir); records, _ = assign_splits(records, seed=int(cfg["seed"]))
    records = [r for r in records_for_group(records, args.group) if not r.partition.startswith("quarantine")]
    output = args.output_dir or f"results/colab_grid/{args.group}"
    print(json.dumps(run_grid_search(records, output, cfg), indent=2))

if __name__ == "__main__": main()
