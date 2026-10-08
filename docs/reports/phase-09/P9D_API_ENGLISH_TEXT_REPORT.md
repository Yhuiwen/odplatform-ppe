# API English text follow-up

Date: 2026-10-07. Gate: PASS for fixed, generated outward API text.

## Scope and inspection

The project exposes service and Agent contracts rather than a separate HTTP router. A scan of `core`, `services`, and `infra` found Chinese output only in the generated alert message. Other Chinese strings are Agent input-recognition patterns and the required TTS speech. The Streamlit pages and their local presentation translations remain Chinese.

The `AlertService` now produces English messages for `NO_HELMET`, `NO_VEST`, and `PPE_UNKNOWN`, which flow to Console JSON and Web alert history. `TTSAlertAdapter` constructs the spoken Chinese text from the typed alert. This keeps M-017's Chinese voice behavior while separating it from the outward API string. Existing keys, enums, persisted events, and delivery behavior remain unchanged. Agent API's fixed fields, error codes/messages, and deterministic response text were already English. User-provided or provider-generated content can still contain the original input language.

## Verification

- Focused alert/TTS/Agent Web boundary tests: 23 passed.
- Full repository suite: 790 passed in 308.11 seconds.
- Regression asserts English alert serialization and Chinese voice delivery from the same event.
