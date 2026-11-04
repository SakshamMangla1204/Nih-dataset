# NIH Project Current State Audit

**Audit scope:** inspection only. The notebooks were not run. No project data or existing outputs were changed during this audit. This report was added as requested.

## Executive summary

The project contains a 10,000-image archive and derived image inventory/prepared copies, but the official NIH labels and official test list are absent. The file `nih_chestxray14/metadata/image_labels.csv` does **not** contain genuine NIH metadata-derived labels: all 10,000 `original_findings` and `binary_label` fields are empty, each row has `class_name=EXCLUDED`, and `official_test_split=unknown`. The existing test predictions therefore do not establish classification performance against official ground truth.

The search of all project files found no `Data_Entry_2017_v2020.csv` and no `test_list.txt`.

## Per-file audit

| File | Purpose and input data | Cleaning / processing | Outputs and execution evidence | Original data / split behavior |
|---|---|---|---|---|
| `NIH_DATA_CLEANING_AND_EDA.ipynb` | Reads `nih_chestxray14/images/images_004.tar.gz` (10,000 PNGs). | Fully decodes images; hashes original bytes; parses patient ID from filename; applies EXIF orientation, converts to RGB, resizes to 224×224; records failed images; summarizes dimensions, modes, brightness, patient counts. | **Saved outputs show successful execution:** cells 1–9 have execution counts and output showing 10,000 prepared, 0 rejected, and a patient overlap check passing. Writes `cleaned/cleaned_manifest.csv`, `cleaned/rejected_manifest.csv`, `cleaned/split_manifest.csv`, EDA summaries/plots and sample contact sheet. | Source archive is read-only; writes transformed copies. Creates a **provisional random patient-level 70/15/15 split** with seed 42; it is not the official NIH split. No labels are loaded. |
| `NIH_BASIC_EDA_AND_LABEL_CLEANING.ipynb` | Reads `eda/image_inventory.csv`; optionally reads metadata CSV and official test list, but both configuration values are `None`. | Trims metadata fields if present; checks missing/duplicate metadata, patient counts, dimensions, blanks, low variance, duplicate flags and pixel distributions; applies exact single-label Pneumonia/No Finding eligibility rules. | **Saved outputs show execution:** all code cells have execution counts 1–8 and output. Writes `metadata/image_labels.csv`, `eda/images_per_patient.csv`, `eda/basic_pixel_distributions.png`, `eda/basic_eda_summary.json`. Saved output says 0 eligible positives, 0 negatives, 10,000 excluded. | Does not modify the original image archive or source metadata. It overwrites derived outputs when run. It does **not** create a split; official membership is unknown. |
| `nih_chestxray14/clean_dataset.ipynb` | Reads the image archive. | Repeats full decode, source SHA-256 duplicate detection, EXIF orientation, RGB conversion and 224×224 resize; builds accepted/rejected manifests. | **No saved execution evidence:** all code-cell execution counts are `null`, outputs are empty. If run, writes `cleaned/cleaned_manifest.csv`, `cleaned/rejected_manifest.csv`, `cleaned/cleaning_report.json`, and prepared images under `cleaned/images/`. | Leaves source archive unchanged and makes derived copies. Does not assign labels or splits. Its core image-preparation work overlaps the first notebook. |
| `nih_chestxray14/run_basic_eda.py` | Reads `eda/image_inventory.csv`; accepts optional `--metadata` and `--test-list` inputs. | Reconciles metadata filenames and labels when supplied; trims labels; applies exact Pneumonia/No Finding rules; computes inventory, patient, image-quality and split audit summaries. | Script itself has no notebook execution record. Existing `basic_eda_summary.json` and `image_labels.csv` show the same broad task ran, but the saved JSON's structure and label output correspond to the notebook, so this does not prove the current script generated them. If run, it overwrites `metadata/image_labels.csv` and `eda/basic_eda_summary.json`. | Reads source files without editing them; writes derived outputs. It only checks official test membership if provided; does not create a split. |
| `test_model.ipynb` | Reads `baseline_model.keras`, cleaned image manifest/images, split manifest, and optionally labels or class-folder data. | Loads/resizes/converts images, batches model predictions, optionally calculates binary metrics when labels are present. `get_manifest` creates a random patient split if the split file is missing. | **No saved notebook execution evidence:** all execution counts are `null`, outputs empty. Existing prediction CSVs are separate artifacts, but do not prove this notebook was executed. If run, it can write predictions, metrics JSON, confusion matrix and ROC plot; its fallback can also write a split manifest. | Does not change source images/metadata, but writes derived prediction/evaluation results. Uses a provisional split when no split manifest exists; it does not load or enforce the official test list. |

### Output filename caveat

`test_model.ipynb` configures `LABEL_COLUMN = 'label'`. The current `image_labels.csv` has `binary_label`, not `label`. Also, the label file contains empty labels, so the notebook's labeled evaluation path cannot calculate trustworthy metrics from it. A run may stop with a missing-column or missing-label error depending on which path it selects.

## Metadata and image-label status

`image_labels.csv` has 10,000 rows and columns:

`image, patient_id, original_findings, binary_label, class_name, eligible, exclusion_reason, official_test_split`

All 10,000 findings and binary labels are empty. All rows are marked `EXCLUDED`, `eligible=False`, and official split `unknown`. Patient IDs are filename-derived. These are generated placeholders/status values, **not NIH label records**.

`cleaned_metadata.csv` is a one-row status file (`status=not_created`) saying original metadata is absent. `cleaning_exclusions.csv` is also only one row and must not be read as a complete exclusion ledger for the 10,000-image inventory.

## CSV inventory: `nih_chestxray14/metadata/`

Missing counts below count empty cells in CSV fields. For CSVs with 0 rows, only the header/schema exists.

| File | Rows; columns | Missing values | Sample / interpretation |
|---|---:|---|---|
| `cleaned_metadata.csv` | 1; `status, source_file, reason` | `source_file`: 1 | `not_created`; notes NIH source metadata is absent. |
| `image_labels.csv` | 10,000; `image, patient_id, original_findings, binary_label, class_name, eligible, exclusion_reason, official_test_split` | `original_findings`: 10,000; `binary_label`: 10,000 | First example `00008468_031.png`, patient `00008468`, findings/label empty, `EXCLUDED`, split `unknown`. |
| `cleaning_exclusions.csv` | 1; `image, patient_id, exclusion_reason` | None | One example image, reason says source metadata and official test list unavailable. Not a full inventory. |
| `duplicate_images.csv` | 0; `duplicate_group, image, duplicate_type, distance` | n/a | Header only; no duplicate records. |
| `image_integrity_report.csv` | 1; 20 columns (`image, archive_member, exists_in_archive, open_ok, error, format, width, height, mode, source_bytes, pixel_min_gray, pixel_max_gray, mean_gray, std_gray, zero_sized, unusually_small_lt32, blank_constant, low_variance_std_lt1, sha256, phash64`) | `error`: 1 | One sample image reports PNG, openable, 1024×1024, mode L. This is a one-image report, not a full 10,000-image check. |
| `cleaned_test_manifest.csv` | 1,454; 12 columns (`image, patient_id_from_filename, split, raw_model_score, exists_in_archive, sha256, width, height, format, official_test_split, eligible_for_official_test_evaluation, status_reason`) | `exists_in_archive, sha256, width, height, format`: 1,454 each | Example marked `split=test`, `official_test_split=unknown`, ineligible for official test evaluation; score is a model output. Not official NIH test membership. |

## CSV inventory: `nih_chestxray14/eda/`

| File | Rows; columns | Missing values | Sample / interpretation |
|---|---:|---|---|
| `filename_patient_groups.csv` | 10,000; `image, patient_id_from_filename` | None | Example maps `00008468_031.png` to filename-derived patient `00008468`. |
| `image_format_counts.csv` | 2; `source_width, source_height, source_mode, image_count` | None | 9,931 images are 1024×1024 L; 69 are 1024×1024 RGBA. |
| `image_inventory.csv` | 10,000; `image, bytes, width, height, mode, mean_intensity, std_intensity, min_intensity, max_intensity, sha256, duplicate_of` | `duplicate_of`: 10,000 (empty means no duplicate match recorded) | First row is 00008468_031.png, 1024×1024 L. All images have unique filenames/hashes per inventory. |
| `images_per_patient.csv` | 2,648; `patient_id, image_count` | None | Largest shown patient group has 83 images; next sample has 70. |
| `images_per_patient_summary.csv` | 8; index field ``, plus `image_count` | None | Summary count 2,648; mean 3.776; median is 1 according to EDA JSON/description. |
| `numeric_summary.csv` | 3; index field ``, plus `count, mean, std, min, 25%, 50%, 75%, max` | None | `source_bytes`: n=10,000, mean 383,726.74, min 135,295, max 789,842. Includes mean and SD grayscale intensity rows. |
| `read_failures.csv` | 0; `image, error` | n/a | Header only; no decode failures recorded. |

## JSON outputs

- `eda/eda_summary.json`: reports 10,000 images listed/decoded, zero failures, all 1024×1024, 9,931 L and 69 RGBA, zero exact duplicates, 2,648 filename-derived patients (1–83 images per patient). It explicitly says label coverage is unavailable and split leakage cannot be assessed.
- `eda/basic_eda_summary.json`: reports the same 10,000 inventory, 2,648 patients, all 1024×1024; zero blank, invalid-dimension, low-variance, or duplicate flags; 10,000 `EXCLUDED`; metadata and official test list are null/unavailable. Its `inventory_columns` includes added in-memory analysis fields (`patient_id`, flags), although the on-disk inventory CSV has only 11 columns.
- `cleaned/cleaning_report.json` (outside the two requested output folders, but relevant): describes 10,000 prepared images, zero rejected/duplicate files, conversion to RGB and 224×224, and no inferred labels or splits.

## Execution and provenance notes

- `NIH_DATA_CLEANING_AND_EDA.ipynb` has execution counts and saved output consistent with a successful complete pass over all 10,000 archive images.
- `NIH_BASIC_EDA_AND_LABEL_CLEANING.ipynb` has execution counts and saved output through its summary cell. It reports warnings about filling missing numeric-dtype series with strings; its no-metadata branch still completes and writes excluded/unknown rows.
- `clean_dataset.ipynb` and `test_model.ipynb` are unexecuted in their saved notebook state (no execution counts/outputs).
- `run_basic_eda.py` has no embedded execution record. Since the notebook writes files of the same names, current generated outputs do not establish that the script ran.
- Existing `cleaned_manifest.csv`, `split_manifest.csv`, prediction CSVs, and image files are artifacts, but there is no reliable run provenance tying every artifact to a specific notebook or script from inspection alone.

## Duplicated and overlapping work

1. `NIH_DATA_CLEANING_AND_EDA.ipynb` and `clean_dataset.ipynb` both read the image archive and repeat full image decoding, hashing, patient-ID parsing, EXIF orientation, RGB conversion, 224×224 Lanczos resizing, and cleaned/rejected manifest creation. Use one image-preparation workflow, not both.
2. `NIH_DATA_CLEANING_AND_EDA.ipynb` and `NIH_BASIC_EDA_AND_LABEL_CLEANING.ipynb` both report patient counts and basic image quality/dimension information. The first computes quality while preparing images; the second audits the precomputed inventory and adds explicit label/test-list checks.
3. `NIH_BASIC_EDA_AND_LABEL_CLEANING.ipynb` and `run_basic_eda.py` implement substantially the same inventory checks, patient grouping, exact label rules, and summary outputs. They overwrite the same `image_labels.csv` and `basic_eda_summary.json` paths, with somewhat different output fields/schema.
4. `test_model.ipynb` can independently create the same kind of random patient split as the first notebook when its split manifest is absent. This duplicates split logic and risks treating a generated split as official.

## Recommendation

1. **Use `clean_dataset.ipynb` first for image preparation** only if you choose it as the single preparation notebook; otherwise retain the already executed preparation in `NIH_DATA_CLEANING_AND_EDA.ipynb`. Avoid rerunning both. For a clean, auditable workflow, `clean_dataset.ipynb` is the focused image-cleaning notebook, but its current saved state is unexecuted.
2. **Redundant notebooks:** `NIH_DATA_CLEANING_AND_EDA.ipynb` and `clean_dataset.ipynb` duplicate image preparation. `NIH_BASIC_EDA_AND_LABEL_CLEANING.ipynb` and `run_basic_eda.py` duplicate label/EDA reporting. `test_model.ipynb` duplicates fallback split generation and must not be used to claim official evaluation with current inputs.
3. **Already complete for the available archive:** full decoding/inventory for 10,000 images (zero read failures); dimensions/modes recorded; filename-derived patient IDs and counts; byte hashes and no exact duplicates recorded; blank/near-constant/dimension flags recorded; 224×224 RGB prepared copies and manifests exist. These results concern the available archive slice, not necessarily the entire NIH ChestX-ray14 release.
4. **Incomplete:** genuine label reconciliation, metadata missing/duplicate/name audit, authoritative patient ID reconciliation, official test membership, leakage audit against official partitions, and trustworthy labeled model evaluation. `image_integrity_report.csv` and `cleaning_exclusions.csv` are only one-row samples, not full reports. Current generated labels are placeholders, not trainable ground truth.
5. **Required before trustworthy NIH model evaluation:** the official `Data_Entry_2017_v2020.csv` (or authoritative NIH metadata CSV matching the images) and official `test_list.txt`; the corresponding image files for those metadata rows and official test entries; a verified patient-disjoint training/validation/test manifest that preserves the official test set; and a label mapping derived from complete annotations (exact Pneumonia positives, exact No Finding negatives, other/multi-label cases excluded under the stated experiment rule). Confirm the model’s training preprocessing and class mapping before scoring. Then evaluate once on the untouched official test set and report metrics with its actual label counts.
