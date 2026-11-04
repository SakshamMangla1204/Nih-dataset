# NIH Preliminary Cross-Domain Baseline — Provisional Predictions

## Status

**Provisional inference was run at the user's request, using the existing inference notebook's `rgb255` option.** This option is not verified against the model's original training pipeline, so the scores and class predictions must be treated as exploratory. The runner printed provisional accuracy **7/570 = 1.2281%** with the assumed sigmoid mapping and 0.5 threshold. No model weights, source images, metadata, or previous predictions were modified.

This folder contains prediction CSVs, a terminal runner, and this report. Diagnostic plots and extended metrics were not generated because the preprocessing, output-class semantics, and threshold provenance are unverified.

## Official NIH test cohort available locally

The official `metadata/official_test_list.txt` contains 25,596 unique filenames. Filename matching against the current local image inventory and `cleaned/images/` found 1,537 available files; 24,059 official test images are not present locally.

All 1,537 available files were opened and fully decoded with Pillow. No corrupted files were found. Source image SHA-256 values were unique for all 1,537 files. Official metadata has unique filenames and valid patient IDs, and the verified label CSV maps by filename. Exact-label cohort counts among locally available official test images:

| Cohort status | Count |
|---|---:|
| Exact Pneumonia, eligible | 7 |
| Exact No Finding, eligible | 563 |
| Other or multi-label findings, excluded | 967 |
| Missing local images from the full official test list | 24,059 |
| Corrupted among locally available official test files | 0 |
| Duplicate/ambiguous eligible image records found | 0 |

The local evaluation slice contains 570 eligible images (7 Pneumonia and 563 No Finding). No files outside the official test list were included.

## Preprocessing provenance check

The existing `test_model.ipynb` is inference code, not a record of model training. It has configuration choices `PREPROCESSING = 'rgb255'` or `'grayscale01'`, with the notebook currently defaulting to `rgb255`. The `grayscale01` branch converts to grayscale, pads to model shape, scales values to 0–1, then repeats channels. The `rgb255` branch converts to RGB, resizes directly to the model dimensions, and leaves values in 0–255. These choices disagree on grayscale conversion, padding, normalization, and potentially spatial distortion. No training script, notebook, configuration, or validation artifact in the project establishes which behavior was used to train this model.

Static inspection of the `.keras` archive config indicates an input declaration of `(None, 224, 224, 3)` and a final one-unit sigmoid layer. This is not a runtime model load and does not establish training-time pixel scaling, image conversion, resizing/padding, positive-class meaning, or the validation-selected decision threshold.

The inference notebook sets `THRESHOLD = 0.5`, but there is no evidence this threshold was established using the original Kaggle validation set. It is not validated for NIH, and it was not applied to the NIH labels.

The inference below used the existing `rgb255` option as an explicit assumption to produce the requested prediction file. It is not established as training-consistent. The model was loaded without compilation or weight changes; its runtime input shape was `(None, 224, 224, 3)` and output shape was `(None, 1)`.

## Provisional predictions

`nih_predictions.csv` has one filename-matched row for each of the 570 eligible, locally available official-test images. It records patient ID, original finding, verified binary label, raw sigmoid score, assumed predicted class at threshold 0.5, and flags that preprocessing and positive-class mapping remain unverified.

All **570/570** scores were at least 0.5 under the assumed mapping, so all rows are marked `PNEUMONIA` in the predicted-class field. This is a property of these provisional scores, not a validated NIH model result. The threshold of 0.5 was retained from the current inference notebook; its selection on Kaggle validation data is not documented.

## Existing prediction-score saturation

The prior file `nih_chestxray14/model_test_predictions.csv` contains 1,454 predictions from the generated project test split. Its `raw_model_score` mean is **0.997744**; the median is 0.999966, the minimum is 0.477662, and only 1 score is below 0.5. Across `model_predictions_all.csv` (10,000 rows), the mean is 0.997784 and only 3 scores are below 0.5.

These values show that the saved sigmoid scores are strongly concentrated near 1. They do not identify the cause. The unresolved preprocessing, output-class mapping, model calibration, training data balance, and model behavior are possible factors, but the available artifacts cannot distinguish among them. The existing files are not official-test predictions: only 206 of the 1,454 filenames occur in the official test list.

## Metrics and artifacts

No accuracy, precision, recall, specificity, F1, ROC-AUC, PR-AUC, confusion matrix, classification report, false-positive/false-negative lists, or prediction distribution plots were generated. These require verified preprocessing and output-class meaning; threshold-dependent metrics also require a validated threshold. The older predictions are from a generated split and are not substituted for this run.

Generated files:

- `results/nih_baseline_partial/nih_predictions.csv` — initial provisional inference output.
- `results/nih_baseline_partial/nih_predictions_terminal.csv` — rerun with terminal batch progress and provisional accuracy output.
- `results/nih_baseline_partial/run_nih_baseline_partial.py` — runner; it prints progress and accuracy and selects a fresh output filename rather than overwriting earlier predictions.

Requested plots and extended metrics are intentionally absent.

## Required before resuming inference

Provide or locate the original model training notebook/script and validation configuration/results that establish:

1. Image decoding, grayscale/RGB conversion, resizing or padding, channel order, and normalization used during training.
2. What the single sigmoid output represents (confirm Pneumonia as the positive class).
3. The decision threshold selected on the original Kaggle validation set, or explicitly authorize reporting threshold-independent ranking metrics only after the preprocessing and class meaning are verified.

After the training pipeline and class mapping are verified, the provisional scores can be confirmed or replaced. The current results cover only the 570 locally available eligible filenames, not the entire official test cohort.
