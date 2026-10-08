"""Offline tests must never consume a workstation's private provider settings."""
import pytest


@pytest.fixture(autouse=True)
def isolate_live_provider_settings(monkeypatch, tmp_path):
    from services import configured_report_service
    monkeypatch.setattr(configured_report_service, 'LOCAL_LLM_CONFIG', tmp_path / 'absent-provider.json')
    original = configured_report_service.report_environment
    monkeypatch.setattr(configured_report_service, 'report_environment', lambda: original(include_user=False))
    for name in ('PPE_LLM_ENDPOINT', 'PPE_LLM_MODEL', 'PPE_LLM_API_KEY'):
        monkeypatch.delenv(name, raising=False)
