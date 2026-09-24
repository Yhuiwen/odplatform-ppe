"""Provider-independent contracts for Phase 8 LLM report generation.

This module owns request, transport and structured error boundaries. It does
not contain a real network transport, provider SDK, credential, or retry
policy. A later authorized phase may provide a transport implementation.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from core.schemas.safety_report import StructuredSafetyReport

__all__ = [
    "DEFAULT_RESPONSE_MAX_BYTES",
    "DEFAULT_TIMEOUT_SECONDS",
    "PROVIDER_PROMPT_VERSION",
    "PROVIDER_REQUEST_VERSION",
    "ProviderCandidate",
    "ProviderError",
    "ProviderErrorCode",
    "ProviderMessage",
    "ProviderRequest",
    "ProviderTransport",
    "ProviderTransportError",
    "SchemaDiagnostic",
    "SchemaDiagnosticCode",
    "SchemaDiagnostics",
    "TransportResponse",
]

PROVIDER_REQUEST_VERSION = "phase8-provider-request-v1"
PROVIDER_PROMPT_VERSION = "phase8-provider-prompt-v2"
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_RESPONSE_MAX_BYTES = 262_144
MAX_SCHEMA_DIAGNOSTICS = 20

_SAFE_LABEL_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:/+-]{0,159}$"
)
_PROVIDER_REF_PATTERN = re.compile(
    r"^[A-Za-z][A-Za-z0-9._:-]{0,159}$"
)
_SAFE_CONTEXT_FIELDS = frozenset(
    {
        "observed_facts",
        "calculated_metrics",
        "metadata",
        "unavailable_fields",
    }
)
_ABSOLUTE_PATH = re.compile(
    r'(?i)(?:^|[\s"\'(\[{=:,])'
    r"(?:[A-Za-z]:[\\/]|\\\\[^\\/\s]+\\|/(?:[^/\s\"']+/)+)"
)
_CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|"
    r"password|passwd|credential|authorization|bearer)\b\s*[:=]"
)
_SCHEMA_PATH_PATTERN = re.compile(
    r"^\$(?:\.(?:[A-Za-z_][A-Za-z0-9_]*|<unexpected>)|\[\d+\])*$"
)
_SAFE_DIAGNOSTIC_TEXT_PATTERN = re.compile(
    r"^[A-Za-z0-9 _.,:;()\[\]{}'|+\-*/%=<>#?]+$"
)
_SAFE_ACTUAL_TYPES = frozenset(
    {
        "array",
        "boolean",
        "integer",
        "non_finite",
        "null",
        "number",
        "object",
        "string",
        "unknown",
    }
)


class ProviderErrorCode(str, Enum):
    """Frozen, caller-visible provider-layer error categories."""

    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_HTTP_ERROR = "PROVIDER_HTTP_ERROR"
    PROVIDER_RATE_LIMITED = "PROVIDER_RATE_LIMITED"
    PROVIDER_AUTH_ERROR = "PROVIDER_AUTH_ERROR"
    PROVIDER_RESPONSE_TOO_LARGE = "PROVIDER_RESPONSE_TOO_LARGE"
    PROVIDER_EMPTY_RESPONSE = "PROVIDER_EMPTY_RESPONSE"
    PROVIDER_MALFORMED_RESPONSE = "PROVIDER_MALFORMED_RESPONSE"
    REPORT_SCHEMA_INVALID = "REPORT_SCHEMA_INVALID"
    GROUNDING_REJECTED = "GROUNDING_REJECTED"


class SchemaDiagnosticCode(str, Enum):
    """Bounded, project-owned categories for report-schema failures."""

    MISSING_FIELD = "MISSING_FIELD"
    UNEXPECTED_FIELD = "UNEXPECTED_FIELD"
    INVALID_TYPE = "INVALID_TYPE"
    INVALID_ENUM = "INVALID_ENUM"
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_VALUE = "INVALID_VALUE"
    INVALID_COLLECTION = "INVALID_COLLECTION"
    SCHEMA_CONSTRUCTION_FAILED = "SCHEMA_CONSTRUCTION_FAILED"


@dataclass(frozen=True, slots=True)
class SchemaDiagnostic:
    """One sanitized schema failure that never contains a provider value."""

    path: str
    code: SchemaDiagnosticCode | str
    expected: str
    actual_type: str
    constraint: str | None = None

    def __post_init__(self) -> None:
        try:
            code = SchemaDiagnosticCode(self.code)
        except ValueError as exc:
            raise ValueError("unsupported schema diagnostic code") from exc
        object.__setattr__(self, "code", code)
        if (
            not isinstance(self.path, str)
            or _SCHEMA_PATH_PATTERN.fullmatch(self.path) is None
        ):
            raise ValueError("schema diagnostic path must be a safe JSON path")
        object.__setattr__(
            self,
            "expected",
            _safe_diagnostic_text(self.expected, "expected"),
        )
        if self.actual_type not in _SAFE_ACTUAL_TYPES:
            raise ValueError("actual_type must be a bounded JSON type name")
        if self.constraint is not None:
            object.__setattr__(
                self,
                "constraint",
                _safe_diagnostic_text(self.constraint, "constraint"),
            )

    def to_dict(self) -> dict[str, str | None]:
        return {
            "path": self.path,
            "code": self.code.value,
            "expected": self.expected,
            "actual_type": self.actual_type,
            "constraint": self.constraint,
        }


@dataclass(frozen=True, slots=True)
class SchemaDiagnostics:
    """A bounded deterministic collection of sanitized schema diagnostics."""

    diagnostics: tuple[SchemaDiagnostic, ...] = ()
    truncated: bool = False
    maximum_errors: int = MAX_SCHEMA_DIAGNOSTICS

    def __post_init__(self) -> None:
        if (
            isinstance(self.maximum_errors, bool)
            or not isinstance(self.maximum_errors, int)
            or self.maximum_errors <= 0
        ):
            raise ValueError("maximum_errors must be a positive integer")
        if not isinstance(self.truncated, bool):
            raise TypeError("truncated must be a boolean")
        diagnostics = tuple(self.diagnostics)
        if len(diagnostics) > self.maximum_errors:
            raise ValueError("schema diagnostics exceed maximum_errors")
        if any(
            not isinstance(item, SchemaDiagnostic)
            for item in diagnostics
        ):
            raise TypeError("diagnostics must contain SchemaDiagnostic objects")
        object.__setattr__(self, "diagnostics", diagnostics)

    def to_dict(self) -> dict[str, object]:
        return {
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "truncated": self.truncated,
            "maximum_errors": self.maximum_errors,
        }


@dataclass
class ProviderError(RuntimeError):
    """A safe provider failure that never contains a raw response or secret."""

    code: ProviderErrorCode | str
    message: str
    provider_ref: str | None = None
    schema_diagnostics: SchemaDiagnostics | None = None

    def __post_init__(self) -> None:
        try:
            code = ProviderErrorCode(self.code)
        except ValueError as exc:
            raise ValueError("code must be a provider error category") from exc
        object.__setattr__(self, "code", code)
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("message must be a non-empty string")
        object.__setattr__(self, "message", self.message.strip())
        if self.provider_ref is not None:
            if (
                not isinstance(self.provider_ref, str)
                or _PROVIDER_REF_PATTERN.fullmatch(self.provider_ref) is None
            ):
                raise ValueError("provider_ref must be a safe provider label")
        if (
            self.schema_diagnostics is not None
            and not isinstance(self.schema_diagnostics, SchemaDiagnostics)
        ):
            raise TypeError(
                "schema_diagnostics must be SchemaDiagnostics or None"
            )
        super().__init__(self.message)

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "message": self.message,
            "provider_ref": self.provider_ref,
            "schema_diagnostics": (
                None
                if self.schema_diagnostics is None
                else self.schema_diagnostics.to_dict()
            ),
        }


@dataclass
class ProviderTransportError(ProviderError):
    """A transport-owned failure with a frozen provider error category."""


@dataclass(frozen=True, slots=True)
class ProviderMessage:
    """One deterministic provider message."""

    role: str
    content: str

    def __post_init__(self) -> None:
        if self.role not in {"system", "user"}:
            raise ValueError("role must be system or user")
        if not isinstance(self.content, str) or not self.content:
            raise ValueError("content must be a non-empty string")

    def to_dict(self) -> dict[str, str]:
        return {
            "role": self.role,
            "content": self.content,
        }


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    """A provider-independent request containing only safe context data."""

    provider_ref: str
    model_ref: str
    timeout_seconds: float
    maximum_response_bytes: int
    source_context_sha256: str
    safe_context_canonical_json: str
    messages: tuple[ProviderMessage, ...]
    request_version: str = PROVIDER_REQUEST_VERSION
    prompt_version: str = PROVIDER_PROMPT_VERSION
    expected_report_schema_version: str = "phase8-report-v1"

    def __post_init__(self) -> None:
        if (
            not isinstance(self.provider_ref, str)
            or _PROVIDER_REF_PATTERN.fullmatch(self.provider_ref) is None
        ):
            raise ValueError("provider_ref must be a safe provider label")
        if (
            not isinstance(self.model_ref, str)
            or _SAFE_LABEL_PATTERN.fullmatch(self.model_ref) is None
        ):
            raise ValueError("model_ref must be a safe model label")
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
        ):
            raise TypeError("timeout_seconds must be numeric")
        timeout = float(self.timeout_seconds)
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout_seconds must be finite and positive")
        object.__setattr__(self, "timeout_seconds", timeout)
        if (
            isinstance(self.maximum_response_bytes, bool)
            or not isinstance(self.maximum_response_bytes, int)
            or self.maximum_response_bytes <= 0
        ):
            raise ValueError("maximum_response_bytes must be a positive integer")
        if self.request_version != PROVIDER_REQUEST_VERSION:
            raise ValueError("unsupported request_version")
        if self.prompt_version != PROVIDER_PROMPT_VERSION:
            raise ValueError("unsupported prompt_version")
        if self.expected_report_schema_version != "phase8-report-v1":
            raise ValueError("unsupported expected_report_schema_version")
        if not re.fullmatch(r"[0-9a-f]{64}", self.source_context_sha256):
            raise ValueError("source_context_sha256 must be a lowercase SHA256")
        if not isinstance(self.safe_context_canonical_json, str):
            raise TypeError("safe_context_canonical_json must be a string")
        payload = json.loads(self.safe_context_canonical_json)
        if not isinstance(payload, dict):
            raise ValueError("safe context must be a JSON object")
        if set(payload) != _SAFE_CONTEXT_FIELDS:
            raise ValueError(
                "safe context must contain only the frozen context sections"
            )
        metadata = payload.get("metadata")
        if not isinstance(metadata, dict) or "generated_at" in metadata:
            raise ValueError(
                "safe context metadata must omit generated_at"
            )
        if _ABSOLUTE_PATH.search(self.safe_context_canonical_json):
            raise ValueError("safe context must not contain absolute paths")
        if _CREDENTIAL_ASSIGNMENT.search(self.safe_context_canonical_json):
            raise ValueError("safe context must not contain credentials")
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        if canonical != self.safe_context_canonical_json:
            raise ValueError("safe context JSON must be canonical")
        messages = tuple(self.messages)
        if len(messages) != 2:
            raise ValueError("provider request requires exactly two messages")
        if any(not isinstance(item, ProviderMessage) for item in messages):
            raise TypeError("messages must contain ProviderMessage objects")
        if messages[0].role != "system" or messages[1].role != "user":
            raise ValueError("messages must contain one system and one user turn")
        object.__setattr__(self, "messages", messages)

    @property
    def safe_context_payload(self) -> dict[str, Any]:
        """Return a fresh copy of the provider-safe context payload."""

        return json.loads(self.safe_context_canonical_json)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_version": self.request_version,
            "prompt_version": self.prompt_version,
            "expected_report_schema_version": (
                self.expected_report_schema_version
            ),
            "provider_ref": self.provider_ref,
            "model_ref": self.model_ref,
            "timeout_seconds": self.timeout_seconds,
            "maximum_response_bytes": self.maximum_response_bytes,
            "source_context_sha256": self.source_context_sha256,
            "context": self.safe_context_payload,
            "messages": [item.to_dict() for item in self.messages],
        }

    def to_canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )


@dataclass(frozen=True, slots=True)
class TransportResponse:
    """One response returned by an injected provider transport."""

    status_code: int
    body: bytes

    def __post_init__(self) -> None:
        if (
            isinstance(self.status_code, bool)
            or not isinstance(self.status_code, int)
            or not 100 <= self.status_code <= 599
        ):
            raise ValueError("status_code must be a valid HTTP status integer")
        if not isinstance(self.body, bytes):
            raise TypeError("body must be bytes")


class ProviderTransport(Protocol):
    """Injectable transport boundary; P8-4 provides no real implementation."""

    def send(self, request: ProviderRequest) -> TransportResponse:
        """Send one request and return a response or a structured failure."""


@dataclass(frozen=True, slots=True)
class ProviderCandidate:
    """One parsed, but not yet accepted, provider report candidate."""

    report: StructuredSafetyReport
    request: ProviderRequest

    def __post_init__(self) -> None:
        if not isinstance(self.report, StructuredSafetyReport):
            raise TypeError("report must be a StructuredSafetyReport")
        if not isinstance(self.request, ProviderRequest):
            raise TypeError("request must be a ProviderRequest")


def _safe_diagnostic_text(value: object, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 160
        or _SAFE_DIAGNOSTIC_TEXT_PATTERN.fullmatch(value) is None
    ):
        raise ValueError(
            f"{field_name} must be bounded non-secret diagnostic text"
        )
    return value
