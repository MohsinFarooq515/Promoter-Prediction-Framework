#!/usr/bin/env bash
set -euo pipefail

mkdir -p results/logs
exec >> results/logs/screening_driver.log 2>&1
models=(residual_cnn multiscale_cnn cnn_bilstm cnn_transformer domain_aware)
domains=(bacteria archaea eukaryota)

for domain in "${domains[@]}"; do
  for model in "${models[@]}"; do
    log="results/logs/screening_${domain}_${model}.log"
    echo "[$(date -Is)] ${domain} ${model}" | tee -a "$log"
    python main.py train --domain "$domain" --model "$model" --epochs 25 2>&1 | tee -a "$log"
  done
done
