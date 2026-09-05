#!/usr/bin/env bash
set -euo pipefail

mkdir -p results/logs
exec >> results/logs/multiseed_driver.log 2>&1

run_group() {
  local group="$1"
  local model="$2"
  local config="$3"
  local epochs="$4"
  for seed in 2025 2026 2027; do
    echo "[$(date -Is)] validation ${group} ${model} seed=${seed}"
    python main.py train --group "$group" --model "$model" --config "$config" --epochs "$epochs" --seed "$seed"
    echo "[$(date -Is)] frozen test ${group} ${model} seed=${seed}"
    python main.py train --group "$group" --model "$model" --config "$config" --epochs "$epochs" --seed "$seed" --evaluate-test
  done
}

run_group ecoli multiscale_cnn configs/screening.yaml 20
run_group bsubtilis multiscale_cnn configs/screening.yaml 20
run_group archaea multiscale_cnn configs/screening.yaml 20
run_group human residual_cnn configs/eukaryota_multiscale.yaml 20
run_group mouse residual_cnn configs/eukaryota_multiscale.yaml 20
run_group arabidopsis residual_cnn configs/eukaryota_multiscale.yaml 20

python -m scripts.ensemble_results
