# P9-B.2 Monitoring Stop Lifecycle — 2026-09-25

## Root cause and bounded fix

`MonitoringService.stop()` requests cancellation and joins the worker for the configured 5 seconds. The diagnostic run `20260925T100121Z-97477388` requested Stop during `source.read()`. Read returned 142 ms later, but the worker began a new cold YOLO inference; `stop()` reported `MONITORING_STOP_TIMEOUT` after 5.017 s. Inference ended at T0+11.502 s, source close finished at T0+12.164 s, and the worker exited at T0+12.164 s. This establishes a missing stop check after read, plus a noninterruptible cold inference longer than the bounded join.

The worker now checks `stop_event` after a successful read and before `_process_frame`. A stop requested during read no longer starts an unnecessary inference. No timeout, model, dependency, tracker, association or compliance setting changed. The timeout remains observable if Stop lands during an inference already in progress: diagnostic run `20260925T100508Z-934e63ef` returned `MONITORING_STOP_TIMEOUT` at T0+5.009 s, inference ended at T0+8.280 s, camera close ended at T0+8.904 s, and the worker exited at T0+8.905 s. That residual cold-start case is not claimed fixed.

The focused integration tests cover idle/repeated stop, active processing and observable timeout, stop during blocking read, exactly-one close, eventual worker exit, and restart. Focused suite: 9 passed, including dashboard contract tests.

## Five real USB cycles

Run `20260925T101508Z-04cd2839` used one real `MonitoringService`, Camera 0, and the frozen verification environment. Each cycle waited until at least three actual frames had been processed before Stop. The same service reopened the device in the next cycle. `outputs/full_chain.json` contains start/stop perf-counter operations and full status per cycle.

| Cycle | Processed frames | Elapsed start-to-worker-exit | Final state | Error | Worker exited / next reopen |
| --- | ---: | ---: | --- | --- | --- |
| 1 | 4 | 15.36 s (cold inference) | stopped | none | yes / yes |
| 2 | 4 | 4.24 s | stopped | none | yes / yes |
| 3 | 4 | 4.73 s | stopped | none | yes / yes |
| 4 | 4 | 4.92 s | stopped | none | yes / yes |
| 5 | 4 | 4.49 s | stopped | none | yes / source closed |

**5/5 normal processed-frame exits**, with no stop timeout. This does not erase the earlier reproduced cold-inference timeout. Each later camera open demonstrates release of the previous handle; source close and worker exit are recorded in the timeline.
