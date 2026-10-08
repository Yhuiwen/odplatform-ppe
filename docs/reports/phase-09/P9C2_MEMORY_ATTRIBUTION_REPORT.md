# P9-C.2 Memory Attribution — 2026-09-25

## Finding

The bounded observer explains much of the P9-C.1 USB diagnostic growth, but **the MP4 loop still shows sustained process RSS growth whose owner is unproven**. This is a resource-stability finding, not a confirmed business-service leak. P9-C.2 remains PARTIAL and P9-C.3 RESOURCE LEAK ATTRIBUTION REQUIRED.

## Evidence and comparison

P9-C.1 retained every per-frame timing, tracking and association record. Its 10-minute warm slopes were about +5.785 MiB/min on USB and +5.882 MiB/min on repeated MP4; its USB recorder held 50,687 stage samples, 5,631 per-frame track dictionaries, 11,282 associations and 11,324 candidates. P9-C.2 streams these records to JSONL and retains at most 200 in each rolling container. A 20,000-record synthetic test verified the cap and complete disk output.

Under this bounded recorder, the USB 10–60-minute slope is +0.0484 MiB/min and warm-window means approach a 439 MiB plateau. That supports the interpretation that the earlier USB slope was mainly diagnostic retention. The MP4 slope is still +1.2478 MiB/min, with five consecutive warm-window mean increases (471.65 → 485.78 → 497.63 → 509.57 → 522.09 MiB). Absolute RSS is not mechanically compared across the two harnesses because their recording paths and run durations differ.

The MP4 produced 675 events and restarted its 47-frame source 675 times, while USB produced 15 events and only two source lifecycles. MP4 threads stayed near 69, handles near 622 and open files near 10. All 675 sources closed, workers exited, and SQLite/snapshot integrity passed. Database and snapshot growth were on disk and proportionate to events. Stable handles/open files make an accumulating open-handle leak less likely, but do not exclude retained objects, native buffers or allocator behavior.

## Attribution boundary and P9-C.3 work

Current evidence does not isolate event-related caches, repeated OpenCV source construction, Torch/NumPy/OpenCV native memory, Python heap retention or allocator fragmentation. `gc`/`tracemalloc` snapshots at warm start, 30 and 60 minutes would locate Python allocation changes, but cannot cover all native allocations. P9-C.3 should run controlled A/B diagnostics with the same frozen model/config/runtime and event/source lifecycle, measuring Python object and native RSS trends separately; compare repeated MP4 open/close with a single long source and compare event-producing versus non-event-producing segments without modifying production parameters. Inspect bounded alert completion/history caches, snapshot buffers and service lifecycle references. Any production fix requires a focused regression and fresh affected long-run evidence. No optimization or production change was made here.
