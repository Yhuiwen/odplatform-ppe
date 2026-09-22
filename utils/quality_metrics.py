"""Pure, deterministic metrics for the P1D dataset quality framework."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from PIL import Image


DEFAULT_CLASS_NAMES = (
    "person",
    "hardhat",
    "no_hardhat",
    "vest",
    "no_vest",
    "machinery",
    "vehicle",
)


@dataclass(frozen=True)
class QualityThresholds:
    """Frozen thresholds used to make quality findings reproducible."""

    small_object_max_area: float = 0.01
    medium_object_max_area: float = 0.09
    small_share_medium_risk: float = 0.20
    small_share_high_risk: float = 0.40
    perceptual_hash_hamming_distance: int = 5

    def __post_init__(self) -> None:
        if not 0 < self.small_object_max_area < 1:
            raise ValueError("small_object_max_area must be between 0 and 1")
        if not (
            self.small_object_max_area
            < self.medium_object_max_area
            <= 1
        ):
            raise ValueError(
                "medium_object_max_area must be greater than the small threshold "
                "and at most 1"
            )
        if not (
            0
            <= self.small_share_medium_risk
            < self.small_share_high_risk
            <= 1
        ):
            raise ValueError("small-object risk thresholds are invalid")
        if self.perceptual_hash_hamming_distance < 0:
            raise ValueError("perceptual hash distance cannot be negative")

    def as_dict(self) -> dict[str, float | int]:
        return {
            "small_object_max_area": self.small_object_max_area,
            "medium_object_max_area": self.medium_object_max_area,
            "small_share_medium_risk": self.small_share_medium_risk,
            "small_share_high_risk": self.small_share_high_risk,
            "perceptual_hash_hamming_distance": (
                self.perceptual_hash_hamming_distance
            ),
        }


@dataclass(frozen=True)
class BBoxRecord:
    """One syntactically valid YOLO bounding-box record."""

    split: str
    image_relative_path: str
    label_relative_path: str
    line_number: int
    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def x_min(self) -> float:
        return self.x_center - self.width / 2

    @property
    def y_min(self) -> float:
        return self.y_center - self.height / 2

    @property
    def x_max(self) -> float:
        return self.x_center + self.width / 2

    @property
    def y_max(self) -> float:
        return self.y_center + self.height / 2


def parse_yolo_values(raw_line: str) -> tuple[int, float, float, float, float]:
    """Parse one YOLO label line without normalizing its values."""

    parts = raw_line.split()
    if len(parts) != 5:
        raise ValueError("YOLO label line must contain exactly 5 fields")
    try:
        class_id = int(parts[0])
    except ValueError as exc:
        raise ValueError("class ID must be an integer") from exc
    try:
        values = tuple(float(value) for value in parts[1:])
    except ValueError as exc:
        raise ValueError("bounding-box coordinates must be numeric") from exc
    if not all(math.isfinite(value) for value in values):
        raise ValueError("bounding-box coordinates must be finite")
    return (class_id, *values)


def bbox_issue_codes(
    class_id: int,
    x_center: float,
    y_center: float,
    width: float,
    height: float,
    *,
    class_count: int,
) -> tuple[str, ...]:
    """Return deterministic issue codes for one parsed bounding box."""

    issues: list[str] = []
    if not 0 <= class_id < class_count:
        issues.append("unknown_class_id")
    if not 0 <= x_center <= 1:
        issues.append("x_center_out_of_range")
    if not 0 <= y_center <= 1:
        issues.append("y_center_out_of_range")
    if not 0 < width <= 1:
        issues.append("width_out_of_range")
    if not 0 < height <= 1:
        issues.append("height_out_of_range")
    if (
        not issues
        and (
            x_center - width / 2 < 0
            or x_center + width / 2 > 1
            or y_center - height / 2 < 0
            or y_center + height / 2 > 1
        )
    ):
        issues.append("bbox_out_of_image_bounds")
    return tuple(issues)


def classify_object_size(
    area: float,
    thresholds: QualityThresholds,
) -> str:
    """Classify normalized bbox area into the frozen size buckets."""

    if area < thresholds.small_object_max_area:
        return "small"
    if area < thresholds.medium_object_max_area:
        return "medium"
    return "large"


def class_distribution(
    records: Iterable[BBoxRecord],
    class_names: Sequence[str],
) -> dict[str, dict[str, int]]:
    """Count boxes per split and class in a stable output shape."""

    counts: dict[str, Counter[int]] = {
        split: Counter() for split in ("train", "valid", "test")
    }
    for record in records:
        if record.split in counts and 0 <= record.class_id < len(class_names):
            counts[record.split][record.class_id] += 1

    output: dict[str, dict[str, int]] = {}
    for split in ("train", "valid", "test"):
        output[split] = {
            class_name: int(counts[split][class_id])
            for class_id, class_name in enumerate(class_names)
        }
    output["total"] = {
        class_name: sum(output[split][class_name] for split in ("train", "valid", "test"))
        for class_name in class_names
    }
    return output


def _small_object_risk(
    small_share: float,
    thresholds: QualityThresholds,
    *,
    total: int,
) -> str:
    if total == 0:
        return "NO_DATA"
    if small_share >= thresholds.small_share_high_risk:
        return "HIGH"
    if small_share >= thresholds.small_share_medium_risk:
        return "MEDIUM"
    return "LOW"


def small_object_summary(
    records: Iterable[BBoxRecord],
    class_names: Sequence[str],
    thresholds: QualityThresholds,
) -> dict[str, object]:
    """Summarize area buckets globally and for each target class."""

    global_counts: Counter[str] = Counter()
    per_class: dict[str, Counter[str]] = defaultdict(Counter)
    class_totals: Counter[str] = Counter()
    for record in records:
        if not 0 <= record.class_id < len(class_names):
            continue
        class_name = class_names[record.class_id]
        bucket = classify_object_size(record.area, thresholds)
        global_counts[bucket] += 1
        per_class[class_name][bucket] += 1
        class_totals[class_name] += 1

    classes: dict[str, dict[str, object]] = {}
    for class_name in class_names:
        total = int(class_totals[class_name])
        counts = per_class[class_name]
        small = int(counts["small"])
        small_share = small / total if total else 0.0
        classes[class_name] = {
            "total": total,
            "small": small,
            "medium": int(counts["medium"]),
            "large": int(counts["large"]),
            "small_share": small_share,
            "small_object_risk": _small_object_risk(
                small_share,
                thresholds,
                total=total,
            ),
        }

    total = sum(global_counts.values())
    return {
        "thresholds": thresholds.as_dict(),
        "total": total,
        "small": int(global_counts["small"]),
        "medium": int(global_counts["medium"]),
        "large": int(global_counts["large"]),
        "classes": classes,
    }


def group_exact_duplicates(
    hash_records: Iterable[tuple[str, str]],
) -> list[dict[str, object]]:
    """Group ``(relative_path, sha256)`` records by exact content."""

    by_hash: dict[str, list[str]] = defaultdict(list)
    for relative_path, digest in hash_records:
        by_hash[digest].append(relative_path)
    return [
        {
            "sha256": digest,
            "paths": sorted(paths),
            "count": len(paths),
        }
        for digest, paths in sorted(by_hash.items())
        if len(paths) > 1
    ]


def split_from_relative_path(relative_path: str) -> str | None:
    """Return a frozen split name when a relative path starts with one."""

    first = relative_path.replace("\\", "/").split("/", maxsplit=1)[0]
    return first if first in {"train", "valid", "test"} else None


def cross_split_duplicate_groups(
    groups: Iterable[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Select exact-duplicate groups that contain multiple dataset splits."""

    cross_split: list[dict[str, object]] = []
    for group in groups:
        raw_paths = group.get("paths")
        if not isinstance(raw_paths, list):
            continue
        paths = sorted(str(path) for path in raw_paths)
        splits = sorted(
            {
                split
                for path in paths
                if (split := split_from_relative_path(path)) is not None
            }
        )
        if len(splits) > 1:
            cross_split.append(
                {
                    "sha256": str(group["sha256"]),
                    "paths": paths,
                    "splits": splits,
                    "count": len(paths),
                }
            )
    return sorted(cross_split, key=lambda item: str(item["sha256"]))


def dhash64(path: str | Path) -> int:
    """Return a deterministic 64-bit difference hash for one image."""

    with Image.open(path) as image:
        grayscale = image.convert("L").resize(
            (9, 8),
            resample=Image.Resampling.LANCZOS,
        )
        pixels = tuple(grayscale.tobytes())

    digest = 0
    for row in range(8):
        offset = row * 9
        for column in range(8):
            digest <<= 1
            digest |= int(
                pixels[offset + column] > pixels[offset + column + 1]
            )
    return digest


def perceptual_duplicate_analysis(
    hash_records: Iterable[tuple[str, int]],
    *,
    hamming_distance_threshold: int,
    sample_pair_limit: int = 100,
) -> dict[str, object]:
    """Find dHash candidate pairs and connected groups without mutation."""

    if hamming_distance_threshold < 0:
        raise ValueError("hamming_distance_threshold cannot be negative")
    if sample_pair_limit < 0:
        raise ValueError("sample_pair_limit cannot be negative")

    records = sorted(
        ((str(path), int(digest)) for path, digest in hash_records),
        key=lambda item: item[0],
    )
    parents = list(range(len(records)))
    ranks = [0] * len(records)

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        if ranks[left_root] < ranks[right_root]:
            left_root, right_root = right_root, left_root
        parents[right_root] = left_root
        if ranks[left_root] == ranks[right_root]:
            ranks[left_root] += 1

    distance_histogram: Counter[int] = Counter()
    sample_pairs: list[dict[str, object]] = []
    same_split_pair_count = 0
    cross_split_pair_count = 0

    for right_index in range(1, len(records)):
        right_path, right_hash = records[right_index]
        right_split = split_from_relative_path(right_path)
        for left_index in range(right_index):
            left_path, left_hash = records[left_index]
            distance = (left_hash ^ right_hash).bit_count()
            if distance > hamming_distance_threshold:
                continue

            distance_histogram[distance] += 1
            union(left_index, right_index)
            left_split = split_from_relative_path(left_path)
            if left_split == right_split:
                same_split_pair_count += 1
            else:
                cross_split_pair_count += 1
            if len(sample_pairs) < sample_pair_limit:
                sample_pairs.append(
                    {
                        "left": left_path,
                        "right": right_path,
                        "distance": distance,
                    }
                )

    components: dict[int, list[int]] = defaultdict(list)
    for index in range(len(records)):
        components[find(index)].append(index)

    groups: list[dict[str, object]] = []
    for indices in components.values():
        if len(indices) < 2:
            continue
        paths = sorted(records[index][0] for index in indices)
        splits = sorted(
            {
                split
                for path in paths
                if (split := split_from_relative_path(path)) is not None
            }
        )
        groups.append(
            {
                "paths": paths,
                "count": len(paths),
                "splits": splits,
                "cross_split": len(splits) > 1,
            }
        )
    groups.sort(
        key=lambda group: (-int(group["count"]), str(group["paths"][0]))
    )

    candidate_pair_count = sum(distance_histogram.values())
    return {
        "algorithm": "dHash",
        "hash_size": 8,
        "hash_bit_count": 64,
        "hamming_distance_threshold": hamming_distance_threshold,
        "hashed_image_count": len(records),
        "candidate_pair_count": candidate_pair_count,
        "same_split_candidate_pair_count": same_split_pair_count,
        "cross_split_candidate_pair_count": cross_split_pair_count,
        "distance_histogram": {
            str(distance): int(distance_histogram[distance])
            for distance in range(hamming_distance_threshold + 1)
        },
        "group_count": len(groups),
        "cross_split_group_count": sum(
            bool(group["cross_split"]) for group in groups
        ),
        "groups": groups,
        "sample_pairs": sample_pairs,
        "sample_pair_limit": sample_pair_limit,
        "candidate_pairs_truncated": candidate_pair_count > len(sample_pairs),
        "mutation_allowed": False,
    }
