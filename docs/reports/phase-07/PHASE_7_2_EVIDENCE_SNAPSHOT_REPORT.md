# PHASE_7_2_EVIDENCE_SNAPSHOT_REPORT

Date: 2026-09-23

Result: COMPLETE FOR HUMAN REVIEW

## 1. Scope

Phase 7-2 implements evidence snapshot file persistence and its association
with an existing Phase 7 event. It does not change the Phase 6
`ComplianceEvent`, its JSONL wire representation, the detector, tracker,
association adapter, compliance engine, model, dataset, mapping or training
artifacts.

The implementation writes a caller-supplied image/frame as JPEG. Annotation
rendering, orphan reconciliation automation, retention cleanup, dashboard,
alerts/TTS, Camera/RTSP and runtime acceptance are outside this slice.

Phase 7-1 was authorized as human-reviewed PASS before this work.

## 2. Changed Files

Contracts and storage:

- `core/schemas/events.py`
- `infra/storage/snapshot_storage.py`
- `infra/database/snapshot_repository.py`
- `infra/database/__init__.py`
- `services/snapshot_service.py`

Tests:

- `tests/unit/test_snapshot_storage.py`
- `tests/unit/test_snapshot_repository.py`
- `tests/integration/test_snapshot_integration.py`
- `tests/unit/test_placeholders.py`
- `tests/unit/test_imports.py`

Documentation:

- `README.md`
- `docs/01_MASTER_PLAN.md`
- `docs/02_CURRENT_STATUS.md`
- `docs/04_CHANGELOG.md`
- `docs/05_TEST_GATES.md`
- `docs/08_RISK_REGISTER.md`
- `docs/phases/PHASE_07_WEB_ALERTS.md`
- `docs/reports/phase-07/PHASE_7_2_EVIDENCE_SNAPSHOT_REPORT.md`
- `docs/worklogs/2026/09/2026-09-23-11-phase7-p2-evidence-snapshot.md`

No migration was added or changed. Migration `0001_phase7_events` retains its
frozen checksum
`c83c59e91f1278b01cecbf75a4236032c21a0e82009d5f15d65cd65366eac9f4`.

## 3. Architecture

```text
ComplianceEvent
      |
      v
EventIngestService
      |
      v
EventRepository / SQLite events
      |
      v
SnapshotService
      |----------------------|
      v                      v
SnapshotStorage        SnapshotRepository
JPEG file only         SQLite metadata only
```

Responsibilities are separated:

- `SnapshotStorage` accepts an image payload, normalizes it to JPEG, checks
  dimensions, computes SHA256 and performs an atomic file replacement.
- `SnapshotRepository` persists and queries metadata. It contains no image
  encoding, rendering or filesystem inspection.
- `SnapshotService` checks event existence, coordinates file and metadata
  operations and never allocates a new event ID.
- `EventRepository` continues to project `snapshots.relative_path` through
  `PersistedEvent.snapshot`.

## 4. Evidence Path and Metadata

The frozen path is:

```text
artifacts/events/snapshots/YYYYMMDD/event_<event-id>.jpg
```

SQLite stores only a relative POSIX path such as:

```text
20260923/event_EVT-integration-01.jpg
```

`SnapshotReference` records:

```text
snapshot_id
event_id
relative_path
sha256
width
height
mime_type
captured_at
```

The event ID is copied from the existing event. The snapshot ID is derived
from that same identity (`SNP-<event-id>`) and does not replace the event ID.

## 5. Integrity and Duplicate Policy

New evidence follows this order:

1. Verify that the event exists.
2. Encode and normalize the supplied image into JPEG bytes.
3. Verify any existing snapshot metadata and file.
4. Return the existing reference when the same event already has identical
   evidence.
5. Reject a different evidence payload for the same event instead of
   overwriting it.
6. For new evidence, generate the UTC date path, write a same-directory
   temporary file, atomically replace the final path and verify SHA256 and
   dimensions.
7. Insert snapshot metadata only after the file is verified.

If metadata insertion fails after a successful file write, the file is not
deleted. It remains an orphan candidate for later reconciliation. No
retention cleanup is implemented or authorized in this subphase.

## 6. Tests

Commands:

```text
python -m pytest
python -m compileall .
git diff --check
git diff HEAD -- docs/00_PROJECT_CHARTER.md
```

Results:

- `python -m pytest`: `361 passed, 1 skipped`.
- `python -m compileall .`: PASS.
- `git diff --check`: PASS.
- Charter diff: PASS, empty.
- Skip: existing optional Torch evaluation test because Torch is not
  installed on this governance host.

Coverage includes:

- UTC date partition and `event_<event-id>.jpg` path generation;
- unsafe event ID/path rejection;
- valid JPEG creation, dimensions and SHA256 verification;
- idempotent identical snapshot retry;
- conflicting snapshot replacement rejection;
- missing-event foreign-key rejection;
- Phase 6 `ComplianceEvent -> EventIngestService -> SnapshotService ->
  SQLite/file` integration;
- `PersistedEvent.snapshot` pointing to a real file;
- database path remaining relative;
- Phase 6 four-field `ComplianceEvent.to_dict()` compatibility.

## 7. Gates

| Gate | Status |
| --- | --- |
| P7-2-G1 Atomic evidence file storage | PASS |
| P7-2-G2 Metadata and relative path contract | PASS |
| P7-2-G3 Phase 6 event identity association | PASS |
| P7-2-G4 Duplicate and conflict behavior | PASS |
| P7-2-G5 Unit and integration tests | PASS |
| P7-2-G6 Upstream/frozen asset boundaries | PASS |
| P7-2-G7 No commit, push or tag | PASS |

## 8. Known Limitations

- The caller supplies the image/frame; annotation rendering is not
  implemented in Phase 7-2.
- Reconciliation of files without metadata and metadata without files is not
  automated.
- Disk monitoring, retention and archive policy remain open under RISK-023.
- `statistics`, dashboard, alerts/TTS, Camera/RTSP and runtime acceptance
  remain pending.
- M-015 through M-020 remain `待实现` in the locked Charter until full
  acceptance evidence is reviewed.

## 9. Final Decision

Phase 7-2 is `COMPLETE FOR HUMAN REVIEW`.

Next allowed step:

```text
WAIT FOR PHASE 7-2 HUMAN REVIEW
```

Commit, push and tag: `NO`.
