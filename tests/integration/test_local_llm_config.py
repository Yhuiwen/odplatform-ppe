import json
from services import configured_report_service as service


def test_project_config_overrides_stale_environment(tmp_path, monkeypatch):
    path = tmp_path / 'llm.local.json'
    values = {'PPE_LLM_ENDPOINT': 'https://api.deepseek.com/chat/completions', 'PPE_LLM_MODEL': 'deepseek-flash', 'PPE_LLM_API_KEY': 'test-project-key'}
    path.write_text(json.dumps(values), encoding='utf-8')
    monkeypatch.setattr(service, 'LOCAL_LLM_CONFIG', path)
    monkeypatch.setenv('PPE_LLM_API_KEY', 'test-stale-key')
    assert all(service.report_environment()[name] == value for name, value in values.items())


def test_invalid_local_config_keeps_environment(tmp_path, monkeypatch):
    path = tmp_path / 'llm.local.json'
    path.write_text('{invalid', encoding='utf-8')
    monkeypatch.setattr(service, 'LOCAL_LLM_CONFIG', path)
    monkeypatch.setenv('PPE_LLM_API_KEY', 'test-environment-key')
    assert service.report_environment()['PPE_LLM_API_KEY'] == 'test-environment-key'

def test_runtime_rebuilds_after_configuration_change(monkeypatch):
    from types import SimpleNamespace
    from web import agent_support
    from services import configured_report_service
    settings = {'PPE_LLM_API_KEY': 'test-first'}
    monkeypatch.setattr(configured_report_service, 'report_environment', lambda: settings)
    calls = []
    class Runtime:
        pass
    monkeypatch.setattr(agent_support, 'AgentWebRuntime', Runtime)
    def build(st):
        runtime = Runtime()
        calls.append(runtime)
        return runtime
    monkeypatch.setattr(agent_support, 'build_agent_runtime', build)
    st = SimpleNamespace(session_state={})
    first = agent_support.get_agent_runtime(st)
    assert agent_support.get_agent_runtime(st) is first
    settings['PPE_LLM_API_KEY'] = 'test-second'
    assert agent_support.get_agent_runtime(st) is not first
    assert len(calls) == 2
