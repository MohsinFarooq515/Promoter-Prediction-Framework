#!/usr/bin/env bash
set -euo pipefail

mkdir -p results/logs
exec >> results/logs/screening_driver.log 2>&1
models=(residual_cnn multiscale_cnn cnn_bilstm cnn_transformer domain_aware)
groups=(ecoli bsubtilis archaea human mouse arabidopsis)

for group in "${groups[@]}"; do
  for model in "${models[@]}"; do
    log="results/logs/screening_${group}_${model}.log"
    echo "[$(date -Is)] ${group} ${model}" | tee -a "$log"
    python main.py train --group "$group" --model "$model" --epochs 25 2>&1 | tee -a "$log"
  done
done
