# Experiment summary

Data audit and deterministic leakage-aware splitting are complete. Neural screening, optimization, multi-seed confirmation, untouched-test confirmation, controls, interpretation, ablations, and statistical comparisons require CPU execution and are not represented as completed results until their artifacts exist.

Resume any interrupted experiment by repeating its exact `python main.py train ...` command. The latest optimizer, scheduler, model, epoch, and history states are loaded automatically.

The `seed_997` bacterial residual-CNN run is a one-epoch engineering smoke test only. It is excluded from model selection.

## Trained domain specialists (seed 2025)

| Domain | Selected suitable architecture | Best epoch | Threshold | Test MCC | Test PR-AUC | Test ROC-AUC | Test balanced accuracy |
|---|---|---:|---:|---:|---:|---:|---:|
| Bacteria | Multi-scale CNN | 3 | 0.7081 | 0.5611 | 0.8441 | 0.8612 | 0.7784 |
| Archaea | Multi-scale CNN | 18 | 0.8510 | 0.8104 | 0.9469 | 0.9660 | 0.8977 |
| Eukaryota | Residual CNN | 10 | 0.7882 | 0.6957 | 0.9272 | 0.9050 | 0.8446 |

Bootstrap 95% test confidence intervals (1,000 resamples): Bacteria MCC 0.5132-0.6066, PR-AUC 0.8156-0.8708, ROC-AUC 0.8397-0.8804; Archaea MCC 0.7778-0.8391, PR-AUC 0.9336-0.9589, ROC-AUC 0.9571-0.9738; Eukaryota MCC 0.6838-0.7076, PR-AUC 0.9223-0.9320, ROC-AUC 0.8995-0.9102.

These are real untouched-test results from one seed. They are suitable trained specialists, but they do not establish superiority over every implemented architecture; a five-model, multi-seed comparison is still required for that claim. Execute remaining screening sequentially with `bash scripts/run_screening.sh`.
