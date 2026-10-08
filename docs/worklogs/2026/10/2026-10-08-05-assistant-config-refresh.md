# Assistant configuration refresh repair

Changed: Session runtime rebuilds when resolved provider settings change; live runtime version bumped.
Reason: Cached sessions could continue using pre-update credentials and cached fallback results.
Validation: 37 targeted tests passed; DeepSeek HTTP 200; full assistant pipeline returned success / assistant_llm on temporary fixture. No key printed or persisted in test artifacts.
Evidence: tests/integration/test_local_llm_config.py; docs/05_TEST_GATES.md; live terminal validation.
Risk: External provider availability and latency vary.
Not Verified: Original browser session rendering and production query results in this increment.
Next Step: Refresh assistant page and submit a new question.
