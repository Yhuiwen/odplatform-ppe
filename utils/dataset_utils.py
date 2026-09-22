"""Deterministic file-level utilities for Phase 1B dataset snapshots."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path, PurePosixPath
import re
import zipfile


SPLIT_NAMES = ("train", "valid", "test")
IMAGE_EXTENSIONS = frozenset(
    {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
)
LABEL_EXTENSION = ".txt"


@dataclass(frozen=True)
class ManifestEntry:
    """One deterministic source-file manifest entry."""

    relative_path: str
    file_size_bytes: int
    sha256: str

    def as_dict(self) -> dict[str, str | int]:
        return asdict(self)


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 digest for one readable file."""

    resolved = Path(path)
    if not resolved.is_file():
        raise FileNotFoundError(resolved)

    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_lines(lines: tuple[str, ...]) -> str:
    """Return the SHA-256 digest of newline-terminated manifest lines."""

    digest = hashlib.sha256()
    for line in lines:
        digest.update(line.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _directory(path: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_dir():
        raise NotADirectoryError(resolved)
    return resolved


def _relative_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _source_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in root.rglob("*") if path.is_file()))


def _files_with_suffix(
    path: Path,
    suffixes: frozenset[str] | set[str],
) -> tuple[Path, ...]:
    if not path.is_dir():
        return ()
    return tuple(
        sorted(
            candidate
            for candidate in path.rglob("*")
            if candidate.is_file() and candidate.suffix.lower() in suffixes
        )
    )


def build_manifest(source_dir: str | Path) -> tuple[ManifestEntry, ...]:
    """Hash every source file and return entries sorted by relative POSIX path."""

    root = _directory(source_dir)
    return tuple(
        ManifestEntry(
            relative_path=_relative_posix(path, root),
            file_size_bytes=path.stat().st_size,
            sha256=sha256_file(path),
        )
        for path in _source_files(root)
    )


def manifest_lines(entries: tuple[ManifestEntry, ...]) -> tuple[str, ...]:
    """Render manifest entries in the conventional ``HASH  path`` format."""

    return tuple(
        f"{entry.sha256}  {entry.relative_path}"
        for entry in sorted(entries, key=lambda item: item.relative_path)
    )


def write_manifest(
    source_dir: str | Path,
    manifest_path: str | Path,
    *,
    entries: tuple[ManifestEntry, ...] | None = None,
) -> tuple[ManifestEntry, ...]:
    """Write a deterministic manifest using only source-relative paths."""

    resolved_entries = entries or build_manifest(source_dir)
    ordered = tuple(sorted(resolved_entries, key=lambda item: item.relative_path))
    output = Path(manifest_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(manifest_lines(ordered))
    if text:
        text += "\n"
    output.write_text(text, encoding="utf-8", newline="\n")
    return ordered


def read_manifest(manifest_path: str | Path) -> tuple[ManifestEntry, ...]:
    """Read and validate a Phase 1B manifest file."""

    path = Path(manifest_path)
    if not path.is_file():
        raise FileNotFoundError(path)

    entries: list[ManifestEntry] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        parts = raw_line.split(maxsplit=1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
            raise ValueError(f"Invalid manifest line {line_number}")
        source_path = Path(parts[1])
        if source_path.is_absolute() or ".." in source_path.parts:
            raise ValueError(f"Unsafe manifest path on line {line_number}")
        entries.append(
            ManifestEntry(
                relative_path=PurePosixPath(parts[1]).as_posix(),
                file_size_bytes=-1,
                sha256=parts[0].lower(),
            )
        )
    return tuple(sorted(entries, key=lambda item: item.relative_path))


def verify_manifest(
    source_dir: str | Path,
    manifest_path: str | Path,
) -> dict[str, object]:
    """Compare current source files with a recorded manifest."""

    expected = {
        entry.relative_path: entry.sha256 for entry in read_manifest(manifest_path)
    }
    actual_entries = build_manifest(source_dir)
    actual = {entry.relative_path: entry.sha256 for entry in actual_entries}

    expected_paths = set(expected)
    actual_paths = set(actual)
    hash_mismatches = sorted(
        path
        for path in expected_paths & actual_paths
        if expected[path] != actual[path]
    )
    return {
        "passed": not (
            expected_paths - actual_paths
            or actual_paths - expected_paths
            or hash_mismatches
        ),
        "missing_files": sorted(expected_paths - actual_paths),
        "new_files": sorted(actual_paths - expected_paths),
        "hash_mismatches": hash_mismatches,
    }


def _pair_index(
    root: Path,
    split: str,
) -> tuple[
    tuple[Path, ...],
    tuple[Path, ...],
    dict[str, list[str]],
    dict[str, list[str]],
]:
    images = _files_with_suffix(root / split / "images", set(IMAGE_EXTENSIONS))
    labels = _files_with_suffix(root / split / "labels", {LABEL_EXTENSION})

    images_by_stem: dict[str, list[str]] = defaultdict(list)
    labels_by_stem: dict[str, list[str]] = defaultdict(list)
    for image in images:
        images_by_stem[image.stem].append(_relative_posix(image, root))
    for label in labels:
        labels_by_stem[label.stem].append(_relative_posix(label, root))

    return (
        images,
        labels,
        dict(sorted(images_by_stem.items())),
        dict(sorted(labels_by_stem.items())),
    )


def _is_empty_label(path: Path) -> bool:
    return not path.read_bytes().strip()


def validate_image_label_pairs(source_dir: str | Path) -> dict[str, object]:
    """Validate file-level image/label pairing without parsing label contents."""

    root = _directory(source_dir)
    split_reports: dict[str, dict[str, object]] = {}
    flat_missing: list[str] = []
    flat_orphan: list[str] = []
    flat_empty: list[str] = []
    flat_zero_images: list[str] = []

    for split in SPLIT_NAMES:
        images, labels, images_by_stem, labels_by_stem = _pair_index(root, split)
        missing = sorted(
            path
            for stem, paths in images_by_stem.items()
            if stem not in labels_by_stem
            for path in paths
        )
        orphan = sorted(
            path
            for stem, paths in labels_by_stem.items()
            if stem not in images_by_stem
            for path in paths
        )
        empty = sorted(
            _relative_posix(path, root)
            for path in labels
            if _is_empty_label(path)
        )
        zero_images = sorted(
            _relative_posix(path, root)
            for path in images
            if path.stat().st_size == 0
        )
        duplicate_images = sorted(
            stem for stem, paths in images_by_stem.items() if len(paths) > 1
        )
        duplicate_labels = sorted(
            stem for stem, paths in labels_by_stem.items() if len(paths) > 1
        )

        split_reports[split] = {
            "images": len(images),
            "labels": len(labels),
            "missing_labels": missing,
            "orphan_labels": orphan,
            "empty_labels": empty,
            "zero_byte_images": zero_images,
            "duplicate_image_basenames": duplicate_images,
            "duplicate_label_basenames": duplicate_labels,
        }
        flat_missing.extend(missing)
        flat_orphan.extend(orphan)
        flat_empty.extend(empty)
        flat_zero_images.extend(zero_images)

    normalized_paths: dict[str, list[str]] = defaultdict(list)
    zero_byte_non_label_metadata: list[str] = []
    for path in _source_files(root):
        relative_path = _relative_posix(path, root)
        normalized_paths[relative_path.casefold()].append(relative_path)
        if (
            path.suffix.lower() != LABEL_EXTENSION
            and path.suffix.lower() not in IMAGE_EXTENSIONS
            and path.stat().st_size == 0
        ):
            zero_byte_non_label_metadata.append(relative_path)

    duplicate_relative_paths = sorted(
        path
        for paths in normalized_paths.values()
        if len(paths) > 1
        for path in paths
    )
    return {
        "data_yaml_exists": (root / "data.yaml").is_file(),
        "splits": split_reports,
        "missing_labels": sorted(flat_missing),
        "orphan_labels": sorted(flat_orphan),
        "empty_labels": sorted(flat_empty),
        "zero_byte_images": sorted(flat_zero_images),
        "zero_byte_non_label_metadata": sorted(zero_byte_non_label_metadata),
        "duplicate_relative_paths": duplicate_relative_paths,
        "duplicate_count": len(duplicate_relative_paths),
    }


def find_exact_duplicate_files(
    source_dir: str | Path,
    *,
    entries: tuple[ManifestEntry, ...] | None = None,
) -> dict[str, object]:
    """Report exact duplicate files by SHA-256 without deleting any file."""

    manifest_entries = entries or build_manifest(source_dir)
    by_hash: dict[str, list[str]] = defaultdict(list)
    for entry in manifest_entries:
        by_hash[entry.sha256].append(entry.relative_path)
    groups = [
        sorted(paths)
        for _, paths in sorted(by_hash.items())
        if len(paths) > 1
    ]
    return {
        "duplicate_file_count": sum(len(group) - 1 for group in groups),
        "duplicate_groups": groups,
    }


def count_split_files(
    source_dir: str | Path,
    *,
    entries: tuple[ManifestEntry, ...] | None = None,
) -> dict[str, object]:
    """Count split files and pairing conditions."""

    root = _directory(source_dir)
    pairing = validate_image_label_pairs(root)
    splits = pairing["splits"]
    assert isinstance(splits, dict)

    report_splits: dict[str, dict[str, int]] = {}
    total_images = 0
    total_labels = 0
    for split in SPLIT_NAMES:
        split_report = splits[split]
        assert isinstance(split_report, dict)
        images = int(split_report["images"])
        labels = int(split_report["labels"])
        total_images += images
        total_labels += labels
        report_splits[split] = {
            "images": images,
            "labels": labels,
        }

    split_roots = tuple(
        root / split / directory
        for split in SPLIT_NAMES
        for directory in ("images", "labels")
    )

    def is_split_file(path: Path) -> bool:
        return any(
            split_root == path.parent or split_root in path.parents
            for split_root in split_roots
        )

    exact_duplicates = find_exact_duplicate_files(root, entries=entries)
    return {
        "splits": report_splits,
        "other_files": sum(not is_split_file(path) for path in _source_files(root)),
        "total_images": total_images,
        "total_labels": total_labels,
        "empty_label_files": len(pairing["empty_labels"]),
        "missing_label_files": len(pairing["missing_labels"]),
        "orphan_label_files": len(pairing["orphan_labels"]),
        "zero_byte_images": len(pairing["zero_byte_images"]),
        "zero_byte_non_label_metadata": len(
            pairing["zero_byte_non_label_metadata"]
        ),
        "duplicate_relative_paths": int(pairing["duplicate_count"]),
        "exact_duplicate_files": int(exact_duplicates["duplicate_file_count"]),
        "exact_duplicate_groups": exact_duplicates["duplicate_groups"],
    }


def _safe_archive_parts(member_name: str) -> tuple[str, ...]:
    normalized = member_name.replace("\\", "/")
    if re.match(r"^[A-Za-z]:", normalized):
        raise ValueError(f"Absolute archive member is not allowed: {member_name}")
    pure_path = PurePosixPath(normalized)
    parts = tuple(part for part in pure_path.parts if part not in {"", "."})
    if pure_path.is_absolute() or ".." in parts:
        raise ValueError(f"Unsafe archive member: {member_name}")
    return parts


def extract_archive_safely(
    archive_path: str | Path,
    destination: str | Path,
) -> Path:
    """Extract a ZIP while rejecting absolute paths and traversal members."""

    archive = Path(archive_path)
    if not archive.is_file():
        raise FileNotFoundError(archive)
    root = Path(destination).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            parts = _safe_archive_parts(member.filename)
            if not parts:
                continue
            target = (root / Path(*parts)).resolve()
            if root != target and root not in target.parents:
                raise ValueError(f"Unsafe archive target: {member.filename}")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(member) as source, target.open("wb") as output:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    output.write(chunk)
    return root


def verify_source_against_archive(
    archive_path: str | Path,
    source_dir: str | Path,
) -> dict[str, object]:
    """Verify that source files are byte-identical to their archive members."""

    archive = Path(archive_path)
    root = _directory(source_dir)
    if not archive.is_file():
        raise FileNotFoundError(archive)

    archive_entries: dict[str, zipfile.ZipInfo] = {}
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            parts = _safe_archive_parts(member.filename)
            if parts and not member.is_dir():
                relative_path = PurePosixPath(*parts).as_posix()
                if relative_path in archive_entries:
                    raise ValueError(f"Duplicate archive member: {relative_path}")
                archive_entries[relative_path] = member

    source_entries = {
        _relative_posix(path, root): path for path in _source_files(root)
    }
    archive_paths = set(archive_entries)
    source_paths = set(source_entries)
    hash_mismatches: list[str] = []
    with zipfile.ZipFile(archive) as bundle:
        for relative_path in sorted(archive_paths & source_paths):
            digest = hashlib.sha256()
            with bundle.open(archive_entries[relative_path]) as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != sha256_file(source_entries[relative_path]):
                hash_mismatches.append(relative_path)

    missing_source_files = sorted(archive_paths - source_paths)
    extra_source_files = sorted(source_paths - archive_paths)
    return {
        "passed": not (
            missing_source_files or extra_source_files or hash_mismatches
        ),
        "missing_source_files": missing_source_files,
        "extra_source_files": extra_source_files,
        "hash_mismatches": hash_mismatches,
    }
