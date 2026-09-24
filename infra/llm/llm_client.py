"""Provider-independent Phase 8 safety report client."""

from __future__ import annotations

from core.schemas.safety import SafetyAnalysisContext
from core.schemas.safety_report import StructuredSafetyReport
from infra.llm.provider import (
    ProviderCandidate,
    ProviderError,
    ProviderErrorCode,
    ProviderTransport,
    TransportResponse,
)
from infra.llm.request_builder import ProviderRequestBuilder
from infra.llm.response_parser import ProviderResponseParser

__all__ = ["SafetyLLMClient"]


class SafetyLLMClient:
    """Build, transport and strictly parse one provider report candidate."""

    def __init__(
        self,
        *,
        transport: ProviderTransport,
        request_builder: ProviderRequestBuilder,
        response_parser: ProviderResponseParser | None = None,
    ) -> None:
        if not callable(getattr(transport, "send", None)):
            raise TypeError("transport must expose send(request)")
        if not isinstance(request_builder, ProviderRequestBuilder):
            raise TypeError("request_builder must be a ProviderRequestBuilder")
        parser = response_parser or ProviderResponseParser(
            maximum_response_bytes=request_builder.maximum_response_bytes
        )
        if not isinstance(parser, ProviderResponseParser):
            raise TypeError("response_parser must be a ProviderResponseParser")
        if (
            parser.maximum_response_bytes
            != request_builder.maximum_response_bytes
        ):
            raise ValueError(
                "response parser size limit must match the request policy"
            )
        self.transport = transport
        self.request_builder = request_builder
        self.response_parser = parser

    def generate_candidate(
        self,
        context: SafetyAnalysisContext,
    ) -> ProviderCandidate:
        if not isinstance(context, SafetyAnalysisContext):
            raise ProviderError(
                code=ProviderErrorCode.REPORT_SCHEMA_INVALID,
                message="context must be a SafetyAnalysisContext",
                provider_ref=self.request_builder.provider_ref,
            )

        request = self.request_builder.build(context)
        try:
            response = self.transport.send(request)
        except ProviderError as exc:
            raise ProviderError(
                code=exc.code,
                message=self._transport_error_message(exc.code),
                provider_ref=request.provider_ref,
                schema_diagnostics=exc.schema_diagnostics,
            ) from None
        except Exception:
            raise ProviderError(
                code=ProviderErrorCode.PROVIDER_UNAVAILABLE,
                message="provider transport failed",
                provider_ref=request.provider_ref,
            ) from None

        if not isinstance(response, TransportResponse):
            raise ProviderError(
                code=ProviderErrorCode.PROVIDER_UNAVAILABLE,
                message="provider transport returned an invalid response",
                provider_ref=request.provider_ref,
            )

        self._raise_for_status(response, provider_ref=request.provider_ref)
        report = self.response_parser.parse(
            response.body,
            expected_context_sha256=request.source_context_sha256,
            expected_provider_ref=request.provider_ref,
        )
        return ProviderCandidate(report=report, request=request)

    def generate_report(
        self,
        context: SafetyAnalysisContext,
    ) -> StructuredSafetyReport:
        """Return an unvalidated provider candidate for the P8-2 boundary."""

        return self.generate_candidate(context).report

    @staticmethod
    def _raise_for_status(
        response: TransportResponse,
        *,
        provider_ref: str,
    ) -> None:
        code: ProviderErrorCode | None = None
        if response.status_code in {401, 403}:
            code = ProviderErrorCode.PROVIDER_AUTH_ERROR
        elif response.status_code == 429:
            code = ProviderErrorCode.PROVIDER_RATE_LIMITED
        elif response.status_code < 200 or response.status_code >= 300:
            code = ProviderErrorCode.PROVIDER_HTTP_ERROR
        if code is not None:
            raise ProviderError(
                code=code,
                message=SafetyLLMClient._transport_error_message(code),
                provider_ref=provider_ref,
            )

    @staticmethod
    def _transport_error_message(code: ProviderErrorCode) -> str:
        messages = {
            ProviderErrorCode.PROVIDER_UNAVAILABLE: (
                "provider transport is unavailable"
            ),
            ProviderErrorCode.PROVIDER_TIMEOUT: (
                "provider request timed out"
            ),
            ProviderErrorCode.PROVIDER_HTTP_ERROR: (
                "provider request failed with an HTTP error"
            ),
            ProviderErrorCode.PROVIDER_RATE_LIMITED: (
                "provider request was rate limited"
            ),
            ProviderErrorCode.PROVIDER_AUTH_ERROR: (
                "provider authentication failed"
            ),
            ProviderErrorCode.REPORT_SCHEMA_INVALID: (
                "provider response does not satisfy phase8-report-v1"
            ),
        }
        return messages.get(
            code,
            "provider transport failed",
        )
