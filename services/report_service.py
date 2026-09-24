"""Report orchestration with provider-first fallback and grounding validation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any

from core.schemas.safety import SafetyAnalysisContext
from core.schemas.safety_report import (
    GroundingStatus,
    StructuredSafetyReport,
)
from infra.llm.fallback import TemplateFallback, TemplateFallbackError
from infra.llm.llm_client import SafetyLLMClient
from infra.llm.provider import (
    ProviderCandidate,
    ProviderError,
    ProviderRequest,
    SchemaDiagnostics,
)
from services.safety_report_grounding_validator import (
    ReportValidationResult,
    SafetyReportGroundingValidator,
)

__all__ = [
    "ProviderReportResult",
    "ProviderRuntimeMetadata",
    "ReportService",
    "ReportServiceError",
    "ReportGenerationPath",
    "ReportGenerationResult",
    "ReportGenerationStatus",
    "SafeProviderError",
]


class ReportGenerationStatus(str, Enum):
    """Caller-visible outcome of the provider-first report flow."""

    PROVIDER_VALIDATED = "PROVIDER_VALIDATED"
    TEMPLATE_FALLBACK = "TEMPLATE_FALLBACK"
    REPORT_UNAVAILABLE = "REPORT_UNAVAILABLE"


class ReportGenerationPath(str, Enum):
    """Selected report generation path."""

    PROVIDER = "PROVIDER"
    TEMPLATE_FALLBACK = "TEMPLATE_FALLBACK"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class ReportServiceError(RuntimeError):
    """A deterministic report generation or validation failure."""

    code: str
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code:
            raise ValueError("code must be a non-empty string")
        if not isinstance(self.message, str) or not self.message:
            raise ValueError("message must be a non-empty string")
        super().__init__(self.message)


@dataclass(frozen=True, slots=True)
class ProviderReportResult:
    """One provider candidate plus its unchanged P8-2 validation result."""

    candidate: ProviderCandidate
    validation: ReportValidationResult

    def __post_init__(self) -> None:
        if not isinstance(self.candidate, ProviderCandidate):
            raise TypeError("candidate must be a ProviderCandidate")
        if not isinstance(self.validation, ReportValidationResult):
            raise TypeError("validation must be a ReportValidationResult")

    @property
    def valid(self) -> bool:
        return self.validation.valid

    @property
    def request(self) -> ProviderRequest:
        return self.candidate.request


@dataclass(frozen=True, slots=True)
class ProviderRuntimeMetadata:
    """Non-secret provider metadata retained by the orchestration wrapper."""

    provider_ref: str
    model_ref: str
    request_version: str
    prompt_version: str
    report_schema_version: str

    def to_dict(self) -> dict[str, str]:
        return {
            "provider_ref": self.provider_ref,
            "model_ref": self.model_ref,
            "request_version": self.request_version,
            "prompt_version": self.prompt_version,
            "report_schema_version": self.report_schema_version,
        }


@dataclass(frozen=True, slots=True)
class SafeProviderError:
    """One sanitized provider or fallback failure."""

    code: str
    message: str
    provider_ref: str | None = None
    schema_diagnostics: SchemaDiagnostics | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code:
            raise ValueError("code must be a non-empty string")
        if not isinstance(self.message, str) or not self.message:
            raise ValueError("message must be a non-empty string")
        if self.provider_ref is not None and (
            not isinstance(self.provider_ref, str) or not self.provider_ref
        ):
            raise ValueError("provider_ref must be a non-empty string or None")
        if (
            self.schema_diagnostics is not None
            and not isinstance(self.schema_diagnostics, SchemaDiagnostics)
        ):
            raise TypeError(
                "schema_diagnostics must be SchemaDiagnostics or None"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            "provider_ref": self.provider_ref,
            "schema_diagnostics": (
                None
                if self.schema_diagnostics is None
                else self.schema_diagnostics.to_dict()
            ),
        }


@dataclass(frozen=True, slots=True)
class ReportGenerationResult:
    """Structured provider-first report outcome without invalid report escape."""

    status: ReportGenerationStatus | str
    generation_path: ReportGenerationPath | str
    degraded: bool
    report: StructuredSafetyReport | None
    provider_metadata: ProviderRuntimeMetadata | None
    safe_error: SafeProviderError | None
    grounding_status: GroundingStatus | None

    def __post_init__(self) -> None:
        try:
            status = ReportGenerationStatus(self.status)
            path = ReportGenerationPath(self.generation_path)
        except ValueError as exc:
            raise ValueError("unsupported report generation status or path") from exc
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "generation_path", path)
        if not isinstance(self.degraded, bool):
            raise TypeError("degraded must be a boolean")
        if self.provider_metadata is not None and not isinstance(
            self.provider_metadata, ProviderRuntimeMetadata
        ):
            raise TypeError("provider_metadata must be ProviderRuntimeMetadata")
        if self.safe_error is not None and not isinstance(
            self.safe_error, SafeProviderError
        ):
            raise TypeError("safe_error must be SafeProviderError")
        if self.grounding_status is not None:
            try:
                grounding = GroundingStatus(self.grounding_status)
            except ValueError as exc:
                raise ValueError("grounding_status is unsupported") from exc
            object.__setattr__(self, "grounding_status", grounding)

        if status is ReportGenerationStatus.PROVIDER_VALIDATED:
            if path is not ReportGenerationPath.PROVIDER:
                raise ValueError("provider success must use PROVIDER path")
            if self.degraded:
                raise ValueError("provider success cannot be degraded")
            if self.report is None or self.grounding_status is not GroundingStatus.VALID:
                raise ValueError("provider success requires a valid report")
            if self.provider_metadata is None or self.safe_error is not None:
                raise ValueError("provider success requires clean metadata")
        elif status is ReportGenerationStatus.TEMPLATE_FALLBACK:
            if path is not ReportGenerationPath.TEMPLATE_FALLBACK:
                raise ValueError("fallback must use TEMPLATE_FALLBACK path")
            if not self.degraded:
                raise ValueError("fallback must be degraded")
            if self.report is None or self.grounding_status is not GroundingStatus.VALID:
                raise ValueError("fallback success requires a valid report")
        else:
            if path is not ReportGenerationPath.UNAVAILABLE:
                raise ValueError("unavailable result must use UNAVAILABLE path")
            if not self.degraded:
                raise ValueError("unavailable result must be degraded")
            if self.report is not None or self.safe_error is None:
                raise ValueError("unavailable result cannot contain a report")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "generation_path": self.generation_path.value,
            "degraded": self.degraded,
            "report": (
                None if self.report is None else self.report.to_dict()
            ),
            "provider_metadata": (
                None
                if self.provider_metadata is None
                else self.provider_metadata.to_dict()
            ),
            "safe_error": (
                None if self.safe_error is None else self.safe_error.to_dict()
            ),
            "grounding_status": (
                None
                if self.grounding_status is None
                else self.grounding_status.value
            ),
        }


class ReportService:
    """Generate and validate a report through the frozen P8-2 boundary."""

    def __init__(
        self,
        fallback: TemplateFallback | None = None,
        validator: SafetyReportGroundingValidator | None = None,
    ) -> None:
        self.fallback = fallback or TemplateFallback()
        self.validator = validator or SafetyReportGroundingValidator()

    def generate(
        self,
        context: SafetyAnalysisContext,
    ) -> StructuredSafetyReport:
        if not isinstance(context, SafetyAnalysisContext):
            raise ReportServiceError(
                code="REPORT_SCHEMA_INVALID",
                message="context must be a SafetyAnalysisContext",
            )

        try:
            report = self.fallback.generate(context)
        except TemplateFallbackError as exc:
            raise ReportServiceError(
                code=exc.code,
                message=exc.message,
            ) from exc

        result = self.validator.validate(report, context)
        if not result.valid:
            codes = ", ".join(
                sorted({item.code for item in result.errors})
            )
            raise ReportServiceError(
                code="GROUNDING_VALIDATION_FAILED",
                message=(
                    "deterministic fallback failed grounding validation: "
                    f"{codes}"
                ),
            )
        return replace(
            report,
            grounding_status=GroundingStatus.VALID,
        )

    def generate_provider_report(
        self,
        context: SafetyAnalysisContext,
        client: SafetyLLMClient,
    ) -> ProviderReportResult:
        """Return a provider candidate and validator result without fallback.

        P8-4 intentionally does not select or mutate the candidate and does
        not silently substitute the local fallback. P8-5 owns the complete
        provider-first plus fallback decision after separate authorization.
        """

        if not isinstance(context, SafetyAnalysisContext):
            raise ReportServiceError(
                code="REPORT_SCHEMA_INVALID",
                message="context must be a SafetyAnalysisContext",
            )
        if not isinstance(client, SafetyLLMClient):
            raise ReportServiceError(
                code="PROVIDER_UNAVAILABLE",
                message="client must be a SafetyLLMClient",
            )

        candidate = client.generate_candidate(context)
        validation = self.validator.validate(candidate.report, context)
        return ProviderReportResult(
            candidate=candidate,
            validation=validation,
        )

    def generate_provider_or_fallback(
        self,
        context: SafetyAnalysisContext,
        client: SafetyLLMClient,
    ) -> ReportGenerationResult:
        """Validate a provider candidate or use the deterministic fallback.

        Provider output is never returned unless the unchanged P8-2 validator
        accepts it. Operational and semantic provider failures both route to
        the same fallback validation path. A fallback failure is represented
        as ``REPORT_UNAVAILABLE`` with no report object.
        """

        if not isinstance(context, SafetyAnalysisContext):
            raise ReportServiceError(
                code="REPORT_SCHEMA_INVALID",
                message="context must be a SafetyAnalysisContext",
            )
        if not isinstance(client, SafetyLLMClient):
            raise ReportServiceError(
                code="PROVIDER_UNAVAILABLE",
                message="client must be a SafetyLLMClient",
            )

        provider_metadata = self._provider_metadata(client)
        provider_error: SafeProviderError | None = None
        try:
            candidate = client.generate_candidate(context)
        except ProviderError as exc:
            provider_error = SafeProviderError(
                code=exc.code.value,
                message=exc.message,
                provider_ref=exc.provider_ref or client.request_builder.provider_ref,
                schema_diagnostics=exc.schema_diagnostics,
            )
        else:
            provider_metadata = self._provider_metadata_from_request(
                candidate.request
            )
            validation = self.validator.validate(candidate.report, context)
            if validation.valid:
                return ReportGenerationResult(
                    status=ReportGenerationStatus.PROVIDER_VALIDATED,
                    generation_path=ReportGenerationPath.PROVIDER,
                    degraded=False,
                    report=replace(
                        candidate.report,
                        grounding_status=GroundingStatus.VALID,
                    ),
                    provider_metadata=provider_metadata,
                    safe_error=None,
                    grounding_status=GroundingStatus.VALID,
                )
            provider_error = SafeProviderError(
                code="GROUNDING_REJECTED",
                message=(
                    "provider report was rejected by the unchanged grounding "
                    "validator"
                ),
                provider_ref=candidate.request.provider_ref,
            )

        try:
            report = self.fallback.generate(context)
        except TemplateFallbackError as exc:
            return self._unavailable_result(
                provider_metadata=provider_metadata,
                code=exc.code,
                message=exc.message,
                provider_ref=client.request_builder.provider_ref,
            )
        validation = self.validator.validate(report, context)
        if not validation.valid:
            return self._unavailable_result(
                provider_metadata=provider_metadata,
                code="FALLBACK_FAILED",
                message=(
                    "deterministic fallback failed the unchanged grounding "
                    "validator"
                ),
                provider_ref=client.request_builder.provider_ref,
            )

        fallback_report = replace(
            report,
            generation=replace(
                report.generation,
                failure_code=provider_error.code,
            ),
            grounding_status=GroundingStatus.VALID,
        )
        return ReportGenerationResult(
            status=ReportGenerationStatus.TEMPLATE_FALLBACK,
            generation_path=ReportGenerationPath.TEMPLATE_FALLBACK,
            degraded=True,
            report=fallback_report,
            provider_metadata=provider_metadata,
            safe_error=provider_error,
            grounding_status=GroundingStatus.VALID,
        )

    @staticmethod
    def _provider_metadata(
        client: SafetyLLMClient,
    ) -> ProviderRuntimeMetadata:
        builder = client.request_builder
        return ProviderRuntimeMetadata(
            provider_ref=builder.provider_ref,
            model_ref=builder.model_ref,
            request_version=builder.request_version,
            prompt_version=builder.prompt_version,
            report_schema_version=builder.expected_report_schema_version,
        )

    @staticmethod
    def _provider_metadata_from_request(
        request: ProviderRequest,
    ) -> ProviderRuntimeMetadata:
        return ProviderRuntimeMetadata(
            provider_ref=request.provider_ref,
            model_ref=request.model_ref,
            request_version=request.request_version,
            prompt_version=request.prompt_version,
            report_schema_version=request.expected_report_schema_version,
        )

    @staticmethod
    def _unavailable_result(
        *,
        provider_metadata: ProviderRuntimeMetadata | None,
        code: str,
        message: str,
        provider_ref: str | None,
    ) -> ReportGenerationResult:
        return ReportGenerationResult(
            status=ReportGenerationStatus.REPORT_UNAVAILABLE,
            generation_path=ReportGenerationPath.UNAVAILABLE,
            degraded=True,
            report=None,
            provider_metadata=provider_metadata,
            safe_error=SafeProviderError(
                code=code,
                message=message,
                provider_ref=provider_ref,
            ),
            grounding_status=None,
        )
