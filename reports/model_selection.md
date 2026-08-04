# Model selection protocol

Select independently within each domain using mean validation MCC, followed by PR-AUC, balanced accuracy, sensitivity/specificity balance, seed stability, and simplicity. Never select using test metrics. Freeze architecture, hyperparameters, seed ensemble, probability-combination weight, and validation-selected threshold before the single final test evaluation.
