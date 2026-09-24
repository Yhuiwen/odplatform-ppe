"""Configuration loading for the Phase 8 provider transport.

Provider credentials are resolved from environment variables only. The YAML
file stores variable names and non-secret transport policy, never values.
"""

from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

from infra.llm.provider import (
    DEFAULT_RESPONSE_MAX_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
)
from utils.config_loader import load_config

__all__ = [
    "LLMConfigurationError",
    "LLMProviderConfig",
]

CONFIG_SCHEMA_VERSION = "phase8-llm-config-v1"

_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]{1,127}$")
_SAFE_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+-]{0,159}$")


@dataclass(frozen=True, slots=True)
class LLMProviderConfig:
    """Resolved non-secret provider settings plus one environment credential."""

    schema_version: str
    provider_ref: str
    endpoint: str
    model_ref: str
    api_key_env: str
    api_key: str = field(repr=False)
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    maximum_response_bytes: int = DEFAULT_RESPONSE_MAX_BYTES
    response_format_json_object: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != CONFIG_SCHEMA_VERSION:
            raise ValueError("unsupported LLM config schema_version")
        if (
            not isinstance(self.provider_ref, str)
            or _SAFE_LABEL.fullmatch(self.provider_ref) is None
        ):
            raise ValueError("provider_ref must be a safe label")
        if (
            not isinstance(self.model_ref, str)
            or _SAFE_LABEL.fullmatch(self.model_ref) is None
        ):
            raise ValueError("model_ref must be a safe label")
        if (
            not isinstance(self.api_key_env, str)
            or _ENV_NAME.fullmatch(self.api_key_env) is None
        ):
            raise ValueError("api_key_env must be an environment variable name")
        if not isinstance(self.api_key, str) or not self.api_key:
            raise ValueError("provider credential must be a non-empty string")
        _validate_endpoint(self.endpoint)
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
        if not isinstance(self.response_format_json_object, bool):
            raise TypeError("response_format_json_object must be a boolean")

    @classmethod
    def from_file(
        cls,
        path: str | Path = "llm.yaml",
        *,
        environ: Mapping[str, str] | None = None,
    ) -> "LLMProviderConfig":
        """Load the YAML policy and resolve values from the environment."""

        environment = os.environ if environ is None else environ
        data = load_config(path)
        expected = {
            "schema_version",
            "provider_ref",
            "endpoint_env",
            "model_env",
            "api_key_env",
            "timeout_seconds",
            "maximum_response_bytes",
            "response_format_json_object",
        }
        actual = set(data)
        if actual != expected:
            missing = sorted(expected - actual)
            unknown = sorted(actual - expected)
            raise LLMConfigurationError(
                "LLM configuration fields are invalid; "
                f"missing={missing}, unknown={unknown}"
            )
        if data["schema_version"] != CONFIG_SCHEMA_VERSION:
            raise LLMConfigurationError(
                "LLM configuration schema_version is unsupported"
            )

        endpoint_env = _environment_name(data["endpoint_env"])
        model_env = _environment_name(data["model_env"])
        api_key_env = _environment_name(data["api_key_env"])
        endpoint = _required_environment(environment, endpoint_env)
        model_ref = _required_environment(environment, model_env)
        api_key = _required_environment(environment, api_key_env)

        return cls(
            schema_version=CONFIG_SCHEMA_VERSION,
            provider_ref=_safe_label(data["provider_ref"], "provider_ref"),
            endpoint=endpoint,
            model_ref=_safe_label(model_ref, model_env),
            api_key_env=api_key_env,
            api_key=api_key,
            timeout_seconds=data["timeout_seconds"],
            maximum_response_bytes=data["maximum_response_bytes"],
            response_format_json_object=data[
                "response_format_json_object"
            ],
        )


class LLMConfigurationError(ValueError):
    """A safe configuration error that never contains a credential value."""


def _environment_name(value: object) -> str:
    if not isinstance(value, str) or _ENV_NAME.fullmatch(value) is None:
        raise LLMConfigurationError(
            "LLM environment variable names must be uppercase identifiers"
        )
    return value


def _required_environment(
    environment: Mapping[str, str],
    name: str,
) -> str:
    value = environment.get(name)
    if value is None or not str(value).strip():
        raise LLMConfigurationError(
            f"required runtime configuration is missing: {name}"
        )
    return str(value).strip()


def _safe_label(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _SAFE_LABEL.fullmatch(value) is None:
        raise LLMConfigurationError(
            f"{field_name} must be a safe provider/model label"
        )
    return value


def _validate_endpoint(value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise LLMConfigurationError("endpoint must be a non-empty URL")
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise LLMConfigurationError("endpoint must be an absolute HTTP URL")
    if parsed.username is not None or parsed.password is not None:
        raise LLMConfigurationError(
            "endpoint must not contain embedded credentials"
        )
    if parsed.query or parsed.fragment:
        raise LLMConfigurationError(
            "endpoint must not contain query strings or fragments"
        )
    host = (parsed.hostname or "").lower()
    if parsed.scheme == "http" and host not in {
        "127.0.0.1",
        "::1",
        "localhost",
    }:
        raise LLMConfigurationError(
            "non-local provider endpoints must use HTTPS"
        )
