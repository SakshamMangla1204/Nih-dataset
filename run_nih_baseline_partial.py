#!/usr/bin/env python3
"""Run the existing Keras model on the locally available eligible NIH test slice.

This reproduces the current notebook's rgb255 path. Training-time preprocessing,
positive-class semantics, and the 0.5 threshold have not been verified, so the
printed accuracy is explicitly provisional.
"""
from pathlib import Path
import csv
import sys

import numpy as np
import tensorflow as tf
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_ROOT = PROJECT_ROOT / "nih_chestxray14"
MODEL_PATH = PROJECT_ROOT / "baseline_model.keras"
COHORT_PATH = DATA_ROOT / "metadata" / "verified_test_manifest.csv"
IMAGE_DIR = DATA_ROOT / "cleaned" / "images"
OUTPUT_DIR = PROJECT_ROOT / "results" / "nih_baseline_partial"
BATCH_SIZE = 32
THRESHOLD = 0.5


def main():
    output_path = OUTPUT_DIR / "nih_predictions_terminal.csv"
    version = 1
    while output_path.exists():
        output_path = OUTPUT_DIR / f"nih_predictions_terminal_{version:02d}.csv"
        version += 1
    print("PROVISIONAL NIH CHECK: training preprocessing and positive-class meaning are unverified.")
    print("Using the current notebook assumption: RGB, 224x224, float32 pixels in [0,255].")
    print(f"Loading existing model: {MODEL_PATH}", flush=True)

    with COHORT_PATH.open(newline="", encoding="utf-8-sig") as f:
        manifest = list(csv.DictReader(f))
    cohort = [r for r in manifest
              if r["eligible"].strip().lower() == "true"
              and r["image_available"].strip().lower() == "true"]
    if not cohort:
        raise ValueError("No eligible locally available official-test images were found.")
    if len({r["image"] for r in cohort}) != len(cohort):
        raise ValueError("Duplicate image filenames found in the evaluation cohort.")
    print(f"Eligible official-test images: {len(cohort)}", flush=True)

    model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    if tuple(model.input_shape[1:]) != (224, 224, 3):
        raise ValueError(f"Expected input (224,224,3), found {model.input_shape}")
    if tuple(model.output_shape[1:]) != (1,):
        raise ValueError(f"Expected one sigmoid output, found {model.output_shape}")
    print(f"Model input: {model.input_shape}; output: {model.output_shape}", flush=True)

    results = []
    n_batches = (len(cohort) + BATCH_SIZE - 1) // BATCH_SIZE
    for batch_idx, start in enumerate(range(0, len(cohort), BATCH_SIZE), start=1):
        batch_rows = cohort[start:start + BATCH_SIZE]
        arrays = []
        for row in batch_rows:
            image_path = IMAGE_DIR / row["image"]
            if not image_path.is_file():
                raise FileNotFoundError(image_path)
            with Image.open(image_path) as im:
                im = im.convert("RGB")
                if im.size != (224, 224):
                    raise ValueError(f"Unexpected prepared image size for {row['image']}: {im.size}")
                arrays.append(np.asarray(im, dtype=np.float32))
        scores = np.asarray(model.predict_on_batch(np.stack(arrays))).reshape(-1)
        if len(scores) != len(batch_rows):
            raise RuntimeError("Prediction count did not match batch size.")
        for row, score in zip(batch_rows, scores):
            score = float(score)
            pred = int(score >= THRESHOLD)
            results.append({
                "image": row["image"],
                "patient_id": row["patient_id"],
                "ground_truth_label": int(row["binary_label"]),
                "ground_truth_class": row["class_name"],
                "raw_model_probability": score,
                "predicted_binary_class_at_0_5": pred,
                "predicted_class_at_0_5": "PNEUMONIA" if pred else "NORMAL",
                "threshold": THRESHOLD,
                "official_test_split": True,
                "preprocessing_assumption": "RGB 224x224 float32 [0,255]; unverified against training",
                "positive_class_assumption": "PNEUMONIA; unverified against training",
            })
        print(f"Batch {batch_idx}/{n_batches}: {min(start + len(batch_rows), len(cohort))}/{len(cohort)} images", flush=True)

    y_true = np.asarray([r["ground_truth_label"] for r in results], dtype=int)
    y_pred = np.asarray([r["predicted_binary_class_at_0_5"] for r in results], dtype=int)
    correct = int((y_true == y_pred).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tp = int(((y_true == 1) & (y_pred == 1)).sum())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)

    print("\nPROVISIONAL ACCURACY (not validated against training preprocessing):")
    print(f"{correct}/{len(results)} = {correct / len(results):.4%}")
    print(f"TN={tn}  FP={fp}  FN={fn}  TP={tp}")
    print(f"Saved filename-matched predictions: {output_path}")
    print("Do not report this as validated model accuracy until preprocessing and class mapping are confirmed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
