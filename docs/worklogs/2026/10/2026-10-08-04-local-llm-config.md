# Local LLM configuration

Changed: Ignored configs/llm.local.json and server resolver; live module refresh.
Reason: Explicit user authorization to persist a project-only DeepSeek credential outside remote Git.
Validation: 35 targeted tests passed; real configuration loaded; git check-ignore and untracked check passed; tracked-file credential scan passed.
Evidence: tests/integration/test_local_llm_config.py; docs/05_TEST_GATES.md.
Risk: Local plaintext credential is accessible to users who can read this workspace; it must not be force-added to Git.
Not Verified: Successful live provider response in this increment.
Next Step: Refresh the assistant page and submit a query. No environment assignment is required for this project configuration.
