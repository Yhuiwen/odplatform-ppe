# Configured DeepSeek report application

Date: 2026-10-08. Offline integration: PASS. Real-provider validation: pending.

The runtime composes the existing strict SafetyLLMClient from configured process or Windows user environment variables. Only typed GENERATE_REPORT operations use the internal provider-enabled facade; ASK operations retain the default local facade even when their question asks for a report. Credentials, model and endpoint are server-owned. The identity router uses the existing SYSTEM capability policy within the report-only path; it changes no role policy or tool registry. See ADR-026.

The page reports configuration status and distinguishes actual LLM output from deterministic fallback. The official endpoint `https://api.deepseek.com/chat/completions` with `deepseek-flash` uses explicit non-thinking mode. Other compatible provider payloads are unchanged. The startup helper reads existing environment settings and prompts with Read-Host -AsSecureString if the credential is absent, then starts Streamlit; it does not write the key to disk.

Verification: 81 focused tests passed across configured application routing, provider success/timeout, legacy Web boundaries, pages, transport, strict report generation and grounding. PowerShell launcher parsed without errors. The process and Windows user settings both had no expected endpoint/model/key variables; no remote provider request was made. Restarted Streamlit to load the new composition.

User next action: run `& 'E:\大四\创业实训\odplatform-ppe\scripts\start_deepseek_demo.ps1'` in local PowerShell, enter the key if prompted, refresh the AI report page and generate a report. Provider errors continue through the existing validated fallback.

References: [DeepSeek API documentation](https://api-docs.deepseek.com/guides/codex), [JSON output](https://api-docs.deepseek.com/guides/json_mode/).

Live browser inspection after restart confirmed the AI report page displays the unconfigured/local-template message, consistent with the missing credential checks. Screenshot: [configuration status](P9D_DEEPSEEK_CONFIG_STATUS.png). A one-time Streamlit Page not found notice appeared on the cold-start direct URL; closing it showed the correct registered report page. No real-provider success is claimed.
