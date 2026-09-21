# Data Directory

This project does not contain training datasets in Phase 0.

| Directory | Intended use |
| --- | --- |
| `external/` | Unmodified third-party source data after approved download |
| `raw/` | Immutable raw snapshots with license and checksum evidence |
| `interim/` | Reproducible intermediate conversion output |
| `processed/` | Final YOLO-format datasets and split manifests |
| `samples/` | Small, license-cleared demonstration fixtures |

Large data files are ignored by Git. Phase 1 must record source, license,
version, checksum, class mapping, conversion, counts, and quality findings in
`docs/06_DATASET_CARD.md` before any dataset is treated as project data.
