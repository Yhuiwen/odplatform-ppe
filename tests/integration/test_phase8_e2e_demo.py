from __future__ import annotations

import json
from pathlib import Path

from examples.phase8_e2e_demo import (
    DEMO_SCHEMA_VERSION,
    EXPECTED_FIXTURE_PATH,
    run_demo,
)
from utils.paths import PROJECT_ROOT

_FORBIDDEN_UI_MARKERS = (
    "C:\\",
    "/home/",
    "/root/",
    "provider_output",
    "raw_candidate",
    "raw_provider_response",
    "ToolRegistry",
    "AgentService",
    "sqlite",
    "SELECT ",
    "rm -rf",
)


def _expected_result() -> dict:
    return json.loads(EXPECTED_FIXTURE_PATH.read_text(encoding="utf-8"))


def test_phase8_e2e_demo_matches_frozen_expected_fixture() -> None:
    assert run_demo() == _expected_result()


def test_phase8_e2e_demo_keeps_provider_disabled_and_source_read_only() -> None:
    result = run_demo()

    assert result["schema_version"] == DEMO_SCHEMA_VERSION
    assert result["scenario_order"] == ["summary", "report", "refused"]
    assert result["invariants"] == {
        "provider_client": "DISABLED",
        "model_loaded": False,
        "report_generation_path": "TEMPLATE_FALLBACK",
        "report_degraded": True,
        "report_grounded": True,
        "refused_result_payload_empty": True,
        "source_of_truth_unchanged": True,
    }
    assert result["source_of_truth"]["event"]["id"] == result["source_event_id"]


def test_phase8_e2e_demo_audit_records_success_and_refusal() -> None:
    result = run_demo()
    events = result["audit_events"]
    by_request: dict[str, list[dict]] = {}
    for event in events:
        by_request.setdefault(event["request_id"], []).append(event)

    assert [
        event["execution_status"]
        for event in by_request["REQ-P8-E2E-SUMMARY"]
    ] == ["PLANNED", "SUCCESS"]
    assert [
        event["execution_status"]
        for event in by_request["REQ-P8-E2E-REPORT"]
    ] == ["PLANNED", "SUCCESS"]
    assert [
        event["execution_status"]
        for event in by_request["REQ-P8-E2E-REFUSED"]
    ] == ["REFUSED"]
    assert by_request["REQ-P8-E2E-REFUSED"][0]["tools_requested"] == []
    assert all(
        event["timestamp"] == "2026-09-24T18:00:00Z"
        for event in events
    )


def test_phase8_e2e_demo_ui_projection_releases_no_internal_data() -> None:
    result = run_demo()
    serialized = json.dumps(
        result["projections"],
        ensure_ascii=False,
        sort_keys=True,
    )

    assert all(
        set(projection) == {
            "answer",
            "summary",
            "evidence_references",
            "recommendations",
            "safe_status",
        }
        for projection in result["projections"].values()
    )
    assert all(marker not in serialized for marker in _FORBIDDEN_UI_MARKERS)
    assert result["projections"]["report"]["safe_status"] == (
        "success / TEMPLATE_FALLBACK / degraded / grounding=valid"
    )
    assert result["projections"]["refused"]["summary"] == []
    assert result["projections"]["refused"]["recommendations"] == []


def test_phase8_e2e_demo_does_not_import_model_provider_or_network_code() -> None:
    source = (
        PROJECT_ROOT / "examples" / "phase8_e2e_demo.py"
    ).read_text(encoding="utf-8")
    forbidden = (
        "best.pt",
        "ultralytics",
        "torch",
        "PPE_LLM_",
        "chat_transport",
        "requests",
        "httpx",
    )

    assert all(marker not in source for marker in forbidden)


def test_expected_fixture_is_repository_relative() -> None:
    expected_path = Path(EXPECTED_FIXTURE_PATH).resolve()

    assert expected_path.is_relative_to(PROJECT_ROOT.resolve())
