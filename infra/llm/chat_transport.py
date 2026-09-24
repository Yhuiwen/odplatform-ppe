"""One real OpenAI-compatible chat-completions transport for Phase 8.

This module is the only concrete provider transport authorized by P8-5. It
knows the provider request/response envelope but does not know safety context
semantics, grounding rules, fallback behavior or event storage.
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

from infra.llm.config import LLMProviderConfig
from infra.llm.provider import (
    ProviderErrorCode,
    ProviderRequest,
    ProviderTransport,
    ProviderTransportError,
    TransportResponse,
)

__all__ = [
    "OpenAICompatibleChatTransport",
    "PROVIDER_TRANSPORT_VERSION",
]

PROVIDER_TRANSPORT_VERSION = "phase8-openai-compatible-transport-v1"

_OpenCall = Callable[..., Any]


@dataclass(slots=True)
class OpenAICompatibleChatTransport(ProviderTransport):
    """Send one request to an explicitly configured chat-completions endpoint."""

    config: LLMProviderConfig
    opener: _OpenCall = field(
        default=urllib.request.urlopen,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.config, LLMProviderConfig):
            raise TypeError("config must be an LLMProviderConfig")
        if not callable(self.opener):
            raise TypeError("opener must be callable")

    def send(self, request: ProviderRequest) -> TransportResponse:
        if not isinstance(request, ProviderRequest):
            raise TypeError("request must be a ProviderRequest")
        if request.provider_ref != self.config.provider_ref:
            raise ProviderTransportError(
                ProviderErrorCode.PROVIDER_UNAVAILABLE,
                "provider request does not match the configured provider",
                provider_ref=self.config.provider_ref,
            )
        if request.model_ref != self.config.model_ref:
            raise ProviderTransportError(
                ProviderErrorCode.PROVIDER_UNAVAILABLE,
                "provider request does not match the configured model",
                provider_ref=self.config.provider_ref,
            )
        if request.maximum_response_bytes != self.config.maximum_response_bytes:
            raise ProviderTransportError(
                ProviderErrorCode.PROVIDER_UNAVAILABLE,
                "provider response limit does not match configuration",
                provider_ref=self.config.provider_ref,
            )

        payload: dict[str, Any] = {
            "model": request.model_ref,
            "messages": [item.to_dict() for item in request.messages],
            "temperature": 0,
            "stream": False,
        }
        if self.config.response_format_json_object:
            payload["response_format"] = {"type": "json_object"}
        body = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        http_request = urllib.request.Request(
            self.config.endpoint,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "ODPlatform-PPE/0.1",
            },
        )

        try:
            with self.opener(
                http_request,
                timeout=request.timeout_seconds,
            ) as response:
                status_code = int(getattr(response, "status", 200))
                response_bytes = response.read(
                    request.maximum_response_bytes + 1
                )
        except urllib.error.HTTPError as exc:
            raise ProviderTransportError(
                _http_error_code(exc.code),
                "provider returned an HTTP error",
                provider_ref=request.provider_ref,
            ) from None
        except (
            TimeoutError,
            socket.timeout,
        ):
            raise ProviderTransportError(
                ProviderErrorCode.PROVIDER_TIMEOUT,
                "provider request timed out",
                provider_ref=request.provider_ref,
            ) from None
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                code = ProviderErrorCode.PROVIDER_TIMEOUT
                message = "provider request timed out"
            else:
                code = ProviderErrorCode.PROVIDER_UNAVAILABLE
                message = "provider transport is unavailable"
            raise ProviderTransportError(
                code,
                message,
                provider_ref=request.provider_ref,
            ) from None
        except OSError:
            raise ProviderTransportError(
                ProviderErrorCode.PROVIDER_UNAVAILABLE,
                "provider transport is unavailable",
                provider_ref=request.provider_ref,
            ) from None

        if len(response_bytes) > request.maximum_response_bytes:
            raise ProviderTransportError(
                ProviderErrorCode.PROVIDER_RESPONSE_TOO_LARGE,
                "provider response exceeded the configured size limit",
                provider_ref=request.provider_ref,
            )
        if status_code < 200 or status_code >= 300:
            raise ProviderTransportError(
                _http_error_code(status_code),
                "provider returned an HTTP error",
                provider_ref=request.provider_ref,
            )

        content = _extract_message_content(response_bytes)
        return TransportResponse(
            status_code=status_code,
            body=content,
        )


def _extract_message_content(raw_response: bytes) -> bytes:
    if not raw_response:
        raise ProviderTransportError(
            ProviderErrorCode.PROVIDER_EMPTY_RESPONSE,
            "provider response was empty",
        )
    try:
        payload = json.loads(
            raw_response.decode("utf-8"),
            object_pairs_hook=_without_duplicate_keys,
            parse_constant=_reject_non_finite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise ProviderTransportError(
            ProviderErrorCode.PROVIDER_MALFORMED_RESPONSE,
            "provider response envelope was malformed",
        ) from None
    if not isinstance(payload, dict):
        raise ProviderTransportError(
            ProviderErrorCode.PROVIDER_MALFORMED_RESPONSE,
            "provider response envelope was malformed",
        )
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ProviderTransportError(
            ProviderErrorCode.PROVIDER_MALFORMED_RESPONSE,
            "provider response envelope did not contain a choice",
        )
    first = choices[0]
    if not isinstance(first, dict):
        raise ProviderTransportError(
            ProviderErrorCode.PROVIDER_MALFORMED_RESPONSE,
            "provider response choice was malformed",
        )
    message = first.get("message")
    if not isinstance(message, dict):
        raise ProviderTransportError(
            ProviderErrorCode.PROVIDER_MALFORMED_RESPONSE,
            "provider response message was malformed",
        )
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ProviderTransportError(
            ProviderErrorCode.PROVIDER_EMPTY_RESPONSE,
            "provider response content was empty",
        )
    return content.encode("utf-8")


def _without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def _reject_non_finite(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is not allowed: {value}")


def _http_error_code(status_code: int) -> ProviderErrorCode:
    if status_code in {401, 403}:
        return ProviderErrorCode.PROVIDER_AUTH_ERROR
    if status_code == 429:
        return ProviderErrorCode.PROVIDER_RATE_LIMITED
    return ProviderErrorCode.PROVIDER_HTTP_ERROR
