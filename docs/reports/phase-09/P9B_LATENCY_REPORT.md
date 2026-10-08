# P9-B Latency — 2026-09-25

Run `20260925T091230Z-21b1895e`, Windows 11 AMD64 / Python 3.12.1 / CPU, real 47-frame MP4, one real `PPE_UNKNOWN` event. Timing instrumentation used monotonic nanoseconds and forwarded unchanged service results. Wall-clock event timestamps are separate. Source processing elapsed 21.674 s; effective throughput 2.169 FPS.

| Interval | One sample (ms) |
| --- | ---: |
| Detection candidate → temporal confirmation | 2225.131 |
| Confirmation → event creation | 0.664 |
| Event creation → SQLite persisted | 27.322 |
| SQLite persisted → snapshot persisted | 93.110 |
| Snapshot persisted → alert completion | 11.091 |
| Detection candidate → alert completion | 2357.317 |

For each interval `n=1`, so observed average, minimum and maximum equal the displayed sample. P50/P95 and broader performance conclusions are **NOT AVAILABLE**. The initial Ultralytics-triggered `lap` installation changed the frozen environment during this run, so this measurement is diagnostic rather than a clean final-demo benchmark. Raw T0–T5 values are in `artifacts/p9b/20260925T091230Z-21b1895e/outputs/full_chain.json`.

P9-B.1 clean runtime recheck: 47 frames in 20.007 s, 2.349 processing FPS, one `PPE_UNKNOWN` event. Its package inventory stayed identical before and after the run. This is still a one-event measurement, so no percentile is inferred. The 30-second USB run processed 143 frames at 4.708 processing FPS on this host; this is scene/hardware specific and is not a long-run performance benchmark.
