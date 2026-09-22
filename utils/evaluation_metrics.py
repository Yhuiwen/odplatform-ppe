"""Replayable detection metrics; no model execution or dataset writes."""

from __future__ import annotations

from collections import Counter
import math
from typing import Any

import numpy as np


IOU_THRESHOLDS = tuple(0.5 + 0.05 * i for i in range(10))


def iou(a: list[float], b: list[float]) -> float:
    """IoU for normalized xyxy boxes."""
    intersection = max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(
        0.0, min(a[3], b[3]) - max(a[1], b[1])
    )
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - intersection
    return intersection / union if union > 0 else 0.0


def match_boxes(
    truth: list[dict], predictions: list[dict], threshold: float,
    *, same_class: bool = True,
) -> list[tuple[int, int, float]]:
    """IoU-descending one-to-one matches with deterministic index tie breaks.

    Each prediction first claims its highest-IoU eligible target, then each
    target retains its first claimant in prediction-index order. Matches are recomputed at every
    threshold. This follows the default Ultralytics validation matching policy.
    """
    pairs = []
    for gi, gt in enumerate(truth):
        for pi, pred in enumerate(predictions):
            if same_class and gt["class_id"] != pred["class_id"]:
                continue
            overlap = iou(gt["box"], pred["box"])
            if overlap >= threshold:
                pairs.append((gi, pi, overlap))
    pairs.sort(key=lambda p: (-p[2], p[0], p[1]))
    seen_predictions: set[int] = set()
    candidates = []
    for pair in pairs:
        if pair[1] not in seen_predictions:
            candidates.append(pair)
            seen_predictions.add(pair[1])
    seen_truth: set[int] = set()
    matches = []
    candidates.sort(key=lambda p: p[1])
    for pair in candidates:
        if pair[0] not in seen_truth:
            matches.append(pair)
            seen_truth.add(pair[0])
    return matches


def average_precision(tp: list[bool], target_count: int) -> float | None:
    """101-point interpolated PR-envelope trapezoidal AP (Ultralytics policy)."""
    if target_count == 0:
        return None
    if not tp:
        return 0.0
    true = np.cumsum(tp, dtype=float)
    recall = true / target_count
    precision = true / np.arange(1, len(tp) + 1)
    # 8.4.157 closes the envelope at achieved recall before the endpoint at 1.
    # This avoids awarding interpolated area beyond the maximum recall.
    recall = np.concatenate(([0.0], recall, [recall[-1]], [1.0]))
    precision = np.concatenate(([1.0], precision, [0.0], [0.0]))
    envelope = np.maximum.accumulate(precision[::-1])[::-1]
    values = np.interp(np.linspace(0, 1, 101), recall, envelope)
    return float(np.sum((values[:-1] + values[1:]) * 0.005))


def validate_records(records: list[dict], class_count: int) -> None:
    if not records:
        raise ValueError("Evaluation records cannot be empty")
    paths = [r["image"] for r in records]
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate image record")
    for record in records:
        for key in ("truth", "predictions"):
            for box in record[key]:
                cid, xyxy = box["class_id"], box["box"]
                if type(cid) is not int or not 0 <= cid < class_count:
                    raise ValueError("Invalid class ID")
                if len(xyxy) != 4 or not all(math.isfinite(x) for x in xyxy):
                    raise ValueError("Invalid box coordinates")
                if not (0 <= xyxy[0] < xyxy[2] <= 1 and 0 <= xyxy[1] < xyxy[3] <= 1):
                    raise ValueError("Invalid normalized xyxy box")
                if key == "predictions" and not (
                    math.isfinite(box["confidence"]) and 0 <= box["confidence"] <= 1
                ):
                    raise ValueError("Invalid confidence")


def calculate_metrics(
    records: list[dict], names: list[str], *, confidence: float = 0.25,
    matching_iou: float = 0.5, small_area: float = 0.01,
) -> dict[str, Any]:
    """Return AP, fixed-operating-point PR, confusion matrix and error evidence.

    Matrix axes are predicted rows / true columns with background last.
    Correct-class matches are assigned before attributing remaining cross-class
    overlaps. A class confusion counts as an FP for the predicted class and FN
    for the true class. All AP uses detections at the saved confidence floor.
    """
    if not 0 <= confidence <= 1 or not 0 < matching_iou <= 1 or not 0 < small_area <= 1:
        raise ValueError("Invalid metric thresholds")
    validate_records(records, len(names))
    nc = len(names)
    matrix = [[0] * (nc + 1) for _ in range(nc + 1)]
    targets = Counter()
    ranked: dict[int, list] = {c: [] for c in range(nc)}
    size = {s: {"targets": 0, "tp": 0} for s in ("small", "non_small")}
    errors, per_image = [], []
    for record in records:
        gt, preds = record["truth"], record["predictions"]
        targets.update(x["class_id"] for x in gt)
        correct = [set(p for _, p, _ in match_boxes(gt, preds, t)) for t in IOU_THRESHOLDS]
        for pi, pred in enumerate(preds):
            ranked[pred["class_id"]].append(
                (pred["confidence"], [pi in mask for mask in correct])
            )
        visible = [p for p in preds if p["confidence"] >= confidence]
        matches = match_boxes(gt, visible, matching_iou)
        matched_gt = {g for g, _, _ in matches}
        matched_pred = {p for _, p, _ in matches}
        for g, p, _ in matches:
            matrix[visible[p]["class_id"]][gt[g]["class_id"]] += 1
        for gi, item in enumerate(gt):
            x1, y1, x2, y2 = item["box"]
            bucket = "small" if (x2 - x1) * (y2 - y1) < small_area else "non_small"
            size[bucket]["targets"] += 1
            size[bucket]["tp"] += int(gi in matched_gt)
        remaining_g = [i for i in range(len(gt)) if i not in matched_gt]
        remaining_p = [i for i in range(len(visible)) if i not in matched_pred]
        confused = match_boxes(
            [gt[i] for i in remaining_g], [visible[i] for i in remaining_p],
            matching_iou, same_class=False,
        )
        for g, p, overlap in confused:
            gi, pi = remaining_g[g], remaining_p[p]
            if gt[gi]["class_id"] == visible[pi]["class_id"]:
                continue
            matched_gt.add(gi)
            matched_pred.add(pi)
            matrix[visible[pi]["class_id"]][gt[gi]["class_id"]] += 1
            errors.append({"image": record["image"], "type": "class_confusion",
                           "truth": gt[gi], "prediction": visible[pi], "iou": overlap})
        for gi, item in enumerate(gt):
            if gi not in matched_gt:
                matrix[nc][item["class_id"]] += 1
                errors.append({"image": record["image"], "type": "missed_ground_truth",
                               "truth": item})
        for pi, item in enumerate(visible):
            if pi not in matched_pred:
                matrix[item["class_id"]][nc] += 1
                overlaps = [iou(item["box"], g["box"]) for g in gt]
                maximum = max(overlaps, default=0.0)
                kind = ("duplicate_or_unmatched_overlap" if maximum >= matching_iou
                        else "localization_candidate" if maximum >= 0.1
                        else "background_false_positive")
                errors.append({"image": record["image"], "type": kind,
                               "prediction": item, "max_iou": maximum})
        per_image.append({"image": record["image"], "targets": len(gt),
                          "predictions": len(visible), "tp": len(matches),
                          "fp": len(visible) - len(matches), "fn": len(gt) - len(matches)})
    per_class = []
    for c, name in enumerate(names):
        detections = sorted(ranked[c], key=lambda x: -x[0])
        aps = [average_precision([r[1][i] for r in detections], targets[c]) for i in range(10)]
        tp = matrix[c][c]
        fp = sum(matrix[c]) - tp
        fn = sum(row[c] for row in matrix) - tp
        per_class.append({"class_id": c, "name": name, "targets": targets[c],
                          "tp": tp, "fp": fp, "fn": fn,
                          "precision": tp / (tp + fp) if tp + fp else 0.0,
                          "recall": tp / targets[c] if targets[c] else None,
                          "AP50": aps[0], "AP50-95": float(np.mean(aps)) if targets[c] else None,
                          "AP_by_iou": aps})
    def aggregate(rows: list[dict]) -> dict:
        supported = [r for r in rows if r["targets"]]
        return {k: float(np.mean([r[col] for r in supported])) if supported else None
                for k, col in {"precision": "precision", "recall": "recall",
                               "mAP50": "AP50", "mAP50-95": "AP50-95"}.items()}
    for bucket in size.values():
        bucket["recall"] = bucket["tp"] / bucket["targets"] if bucket["targets"] else None
    return {"schema_version": "detection-evaluation-metrics-v1", "images": len(records),
            "instances": sum(targets.values()), "class_names": names,
            "iou_thresholds": list(IOU_THRESHOLDS),
            "operating_confidence": confidence, "matching_iou": matching_iou,
            "precision_recall_policy": "macro over supported classes at fixed confidence; no test-set tuning",
            "AP_policy": "IoU matching at 0.50:0.05:0.95; confidence ranked; 101-point PR envelope trapezoid",
            "overall": aggregate(per_class), "ppe_five_classes": aggregate(per_class[:5]),
            "per_class": per_class, "confusion_matrix": {
                "axis_order": "predicted rows / true columns", "labels": names + ["background"],
                "matching_policy": "correct-class first, then residual class-agnostic IoU matches",
                "counts": matrix}, "small_object_recall": size,
            "error_counts": dict(Counter(e["type"] for e in errors)),
            "per_image": per_image, "errors": errors}
