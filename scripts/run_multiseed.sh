#!/usr/bin/env bash
set -euo pipefail

mkdir -p results/logs
exec >> results/logs/multiseed_driver.log 2>&1

run_domain() {
  local domain="$1"
  local model="$2"
  local config="$3"
  local epochs="$4"
  for seed in 2025 2026 2027; do
    echo "[$(date -Is)] validation ${domain} ${model} seed=${seed}"
    python main.py train --domain "$domain" --model "$model" --config "$config" --epochs "$epochs" --seed "$seed"
    echo "[$(date -Is)] frozen test ${domain} ${model} seed=${seed}"
    python main.py train --domain "$domain" --model "$model" --config "$config" --epochs "$epochs" --seed "$seed" --evaluate-test
  done
}

run_domain bacteria multiscale_cnn configs/screening.yaml 20
run_domain archaea multiscale_cnn configs/screening.yaml 20
run_domain eukaryota residual_cnn configs/eukaryota_multiscale.yaml 20

python -m scripts.ensemble_results
