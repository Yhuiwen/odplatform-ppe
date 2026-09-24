from __future__ import annotations

import json
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from infra.llm.chat_transport import OpenAICompatibleChatTransport
from infra.llm.config import LLMConfigurationError, LLMProviderConfig
from infra.llm.provider import (
    ProviderErrorCode,
    ProviderTransportError,
)
from infra.llm.request_builder import ProviderRequestBuilder
from scripts.run_p8_5_provider_smoke import main as provider_smoke_main
import tests.test_provider_e2e as e2e


@dataclass
class FakeResponse:
    status: int
    body: bytes

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, limit: int) -> bytes:
        return self.body[:limit]


@dataclass
class FakeOpener:
    response: FakeResponse | None = None
    error: Exception | None = None

    def __post_init__(self) -> None:
        self.requests: list[Any] = []
        self.timeouts: list[float] = []

    def __call__(self, request: Any, *, timeout: float) -> FakeResponse:
        self.requests.append(request)
        self.timeouts.append(timeout)
        if self.error is not None:
            raise self.error
        if self.response is None:
            raise AssertionError("fake opener has no response")
        return self.response


def _config(
    *,
    endpoint: str = "http://127.0.0.1:9999/v1/chat/completions",
) -> LLMProviderConfig:
    return LLMProviderConfig(
        schema_version="phase8-llm-config-v1",
        provider_ref="fake-provider",
        endpoint=endpoint,
        model_ref="fake-model",
        api_key_env="PPE_LLM_API_KEY",
        api_key="test-secret",
        timeout_seconds=12.5,
        maximum_response_bytes=262144,
        response_format_json_object=True,
    )


def _request():
    return ProviderRequestBuilder(
        provider_ref="fake-provider",
        model_ref="fake-model",
        timeout_seconds=12.5,
        maximum_response_bytes=262144,
    ).build(e2e._context())


def _envelope(content: str) -> bytes:
    return json.dumps(
        {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": content,
                    }
                }
            ]
        }
    ).encode("utf-8")


def test_config_loads_env_names_without_persisting_values(tmp_path: Path) -> None:
    path = tmp_path / "llm.yaml"
    path.write_text(
        "\n".join(
            (
                "schema_version: phase8-llm-config-v1",
                "provider_ref: fake-provider",
                "endpoint_env: PPE_LLM_ENDPOINT",
                "model_env: PPE_LLM_MODEL",
                "api_key_env: PPE_LLM_API_KEY",
                "timeout_seconds: 12.5",
                "maximum_response_bytes: 262144",
                "response_format_json_object: true",
            )
        ),
        encoding="utf-8",
    )
    config = LLMProviderConfig.from_file(
        path,
        environ={
            "PPE_LLM_ENDPOINT": "http://127.0.0.1:9999/v1/chat/completions",
            "PPE_LLM_MODEL": "fake-model",
            "PPE_LLM_API_KEY": "test-secret",
        },
    )

    assert config.provider_ref == "fake-provider"
    assert config.model_ref == "fake-model"
    assert "test-secret" not in repr(config)
    assert "test-secret" not in path.read_text(encoding="utf-8")


def test_config_missing_credential_reports_only_env_name() -> None:
    with pytest.raises(LLMConfigurationError) as error:
        LLMProviderConfig.from_file(
            "llm.yaml",
            environ={
                "PPE_LLM_ENDPOINT": "https://provider.invalid/v1/chat/completions",
                "PPE_LLM_MODEL": "fake-model",
            },
        )

    assert "PPE_LLM_API_KEY" in str(error.value)
    assert "test-secret" not in str(error.value)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://provider.example/v1/chat/completions",
        "https://user:password@provider.example/v1/chat/completions",
        "https://provider.example/v1/chat/completions?api_key=secret",
    ],
)
def test_config_rejects_unsafe_endpoint_shapes(endpoint: str) -> None:
    with pytest.raises(LLMConfigurationError):
        _config(endpoint=endpoint)


def test_transport_sends_one_request_and_extracts_report_content() -> None:
    report = e2e._provider_report(e2e._context())
    opener = FakeOpener(
        response=FakeResponse(
            status=200,
            body=_envelope(report.to_canonical_json()),
        )
    )
    transport = OpenAICompatibleChatTransport(
        config=_config(),
        opener=opener,
    )

    response = transport.send(_request())

    assert response.status_code == 200
    assert response.body == report.to_canonical_json().encode("utf-8")
    assert len(opener.requests) == 1
    assert opener.timeouts == [12.5]
    sent = json.loads(opener.requests[0].data.decode("utf-8"))
    assert sent["model"] == "fake-model"
    assert sent["temperature"] == 0
    assert sent["stream"] is False
    assert sent["response_format"] == {"type": "json_object"}
    assert "Authorization" not in repr(transport)
    assert "test-secret" not in repr(transport)


@pytest.mark.parametrize(
    ("body", "code"),
    [
        (b"", ProviderErrorCode.PROVIDER_EMPTY_RESPONSE),
        (b"{not-json", ProviderErrorCode.PROVIDER_MALFORMED_RESPONSE),
        (b"{}", ProviderErrorCode.PROVIDER_MALFORMED_RESPONSE),
        (
            _envelope("   "),
            ProviderErrorCode.PROVIDER_EMPTY_RESPONSE,
        ),
    ],
)
def test_transport_rejects_malformed_or_empty_envelope(
    body: bytes,
    code: ProviderErrorCode,
) -> None:
    transport = OpenAICompatibleChatTransport(
        config=_config(),
        opener=FakeOpener(response=FakeResponse(200, body)),
    )

    with pytest.raises(ProviderTransportError) as error:
        transport.send(_request())

    assert error.value.code is code


def test_transport_rejects_oversized_provider_envelope() -> None:
    transport = OpenAICompatibleChatTransport(
        config=_config(),
        opener=FakeOpener(
            response=FakeResponse(
                200,
                b"x" * 262145,
            )
        ),
    )

    with pytest.raises(ProviderTransportError) as error:
        transport.send(_request())

    assert error.value.code is ProviderErrorCode.PROVIDER_RESPONSE_TOO_LARGE


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (401, ProviderErrorCode.PROVIDER_AUTH_ERROR),
        (403, ProviderErrorCode.PROVIDER_AUTH_ERROR),
        (429, ProviderErrorCode.PROVIDER_RATE_LIMITED),
        (500, ProviderErrorCode.PROVIDER_HTTP_ERROR),
    ],
)
def test_transport_maps_http_errors(
    status: int,
    code: ProviderErrorCode,
) -> None:
    error = urllib.error.HTTPError(
        "http://127.0.0.1:9999/v1/chat/completions",
        status,
        "fixture",
        hdrs=None,
        fp=None,
    )
    transport = OpenAICompatibleChatTransport(
        config=_config(),
        opener=FakeOpener(error=error),
    )

    with pytest.raises(ProviderTransportError) as raised:
        transport.send(_request())

    assert raised.value.code is code
    assert "fixture" not in str(raised.value)


def test_transport_maps_timeout_without_retry() -> None:
    opener = FakeOpener(error=TimeoutError("secret timeout detail"))
    transport = OpenAICompatibleChatTransport(
        config=_config(),
        opener=opener,
    )

    with pytest.raises(ProviderTransportError) as error:
        transport.send(_request())

    assert error.value.code is ProviderErrorCode.PROVIDER_TIMEOUT
    assert "secret timeout detail" not in str(error.value)
    assert len(opener.requests) == 1


def test_smoke_cli_requires_explicit_execution(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    for name in (
        "PPE_LLM_ENDPOINT",
        "PPE_LLM_MODEL",
        "PPE_LLM_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    exit_code = provider_smoke_main(
        ["--config", "configs/llm.yaml"]
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "NOT_EXECUTED"
