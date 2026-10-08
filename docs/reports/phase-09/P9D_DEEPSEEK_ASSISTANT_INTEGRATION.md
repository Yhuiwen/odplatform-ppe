# DeepSeek safety assistant integration

Date: 2026-10-08. User request: connect the large model to the safety assistant. Decision: ADR-027.

## Implementation

The server resolves the existing configured provider without exposing credentials. ASK uses the existing bounded planner candidate validator and static read tools. Caller-selected dates and filters remain authoritative. After querying, the model selects/orders supplied Chinese statements by ID; unsupported claims cannot enter the UI. Provider or validation failure retains the local query answer. Request caching prevents refresh from repeating calls. Explicit report composition remains intact.

Direct question submission no longer depends on a disabled button computed inside the form. Version-aware module upgrades support the current credential-bearing Streamlit process. JSON selection prompts explicitly name JSON as required by provider JSON mode.

## Validation

90 tests passed in 9.26 seconds across configured assistant/report applications, transport, planner/candidate validation, Web boundary, Phase 8 integration and P9-D pages. Successful provider behavior is covered with mocked transports; scope conflicts, forbidden requests, invalid selections, timeout fallback and deduplication are covered.

The running browser confirms provider configuration and actual outbound invocation. The first live composition request returned an HTTP error; after correcting the JSON prompt, a new request timed out. The UI correctly showed the verified 50-event local result and Chinese timeout notice. **A successful live DeepSeek response has not been observed.** No claim of provider availability or full Phase 9 acceptance is made. No credentials were read from the user terminal or logged. Screenshot: [live status](P9D_DEEPSEEK_ASSISTANT_STATUS.png).

## Remaining verification

Repeat a question when the configured provider responds normally. USB/RTSP, detection throughput and unrelated UI behavior were not retested in this increment. No project restart was performed because the existing process owns the user's session-only API variables.
