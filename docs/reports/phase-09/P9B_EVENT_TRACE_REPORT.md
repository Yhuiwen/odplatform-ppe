# P9-B Event Trace — 2026-09-25

Run `20260925T091230Z-21b1895e`; source SHA256 `b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852`. This is real video evidence from `MonitoringService`.

| Field | Real event |
| --- | --- |
| event_id | `EVT-24f103485b5849a4a818c57dfac9df95` |
| source | `mp4:construction-workers-public-domain.mp4` |
| frame / source timestamp | 24 / 1.001 s |
| session track_id | 1 |
| type / confidence | `PPE_UNKNOWN` / 0.0 |
| temporal confirmation | frame 24 |
| SQLite persisted ID | same event_id; reopened query returned the row |
| snapshot | `20260925/event_EVT-24f103485b5849a4a818c57dfac9df95.jpg` |
| SHA256 | `92452ae640a19bab64bca4e194612eff72143f95c00cb9a10ef2731aa6721b40` |
| dimensions | 1280 × 720 |
| evidence verification | true |
| alerts | Console delivered; Web delivered; 0 failed |

The run trace records separate monotonic T0–T5 timestamps in `outputs/full_chain.json`; the persisted business event timestamp is `2026-09-25T09:12:49Z`. A separate SQLite persisted wall-clock timestamp is not stored, so it must not be inferred from the monotonic measurement. `NO_HELMET`: **MISSING_SCENARIO**. `NO_VEST`: **MISSING_SCENARIO** (one detector `no_vest` at frame 0 had unknown association, so it was not a confirmed violation event). No synthetic event was substituted.

## P9-B.1 clean-runtime and live Camera traces

The clean MP4 run `20260925T093935Z-c9530763` produced `EVT-bcd51353ea144f6195733231da35f27c`, a `PPE_UNKNOWN` event for session track 1 at frame 24/source time 1.001 s. Its SQLite ID was unchanged; snapshot `20260925/event_EVT-bcd51353ea144f6195733231da35f27c.jpg` verified at 1280×720 with SHA256 `92452ae640a19bab64bca4e194612eff72143f95c00cb9a10ef2731aa6721b40`. Console and Web alerts were delivered.

The real USB run `20260925T094052Z-24a066b4` produced two frame-4/session-track-1 events at source time 10.062 s:

| Type | Event ID | Confidence | Snapshot SHA256 | SQLite / evidence / alerts |
| --- | --- | ---: | --- | --- |
| NO_HELMET | `EVT-36a94696a2944cd0a07bd8c6191d4d83` | 0.834899 | `e74ef87b4aed8f187743874c20c54b698edd88d2908831a1c419ccd313ec9f5c` | Same ID; 640×480 verified; Console/Web delivered |
| NO_VEST | `EVT-766d4ad4760e45ca8731f68a91a729f0` | 0.581883 | `e74ef87b4aed8f187743874c20c54b698edd88d2908831a1c419ccd313ec9f5c` | Same ID; 640×480 verified; Console/Web delivered |

Both events use distinct relative snapshot paths under `20260925/`; identical SHA256 reflects the same captured frame. Raw monotonic T0–T5 measurements and full alert results are in the two run `outputs/full_chain.json` files. The USB picture is a live Camera scene; this report does not label it a construction-site MP4.
