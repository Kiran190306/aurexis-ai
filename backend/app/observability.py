"""Metrics and tracing primitives shared by the application runtime."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from prometheus_client import Counter, Histogram

from app.core.config import settings


HTTP_REQUESTS = Counter(
    "jarvis_http_requests_total",
    "Completed HTTP requests.",
    ("method", "path", "status_code"),
)
HTTP_REQUEST_DURATION = Histogram(
    "jarvis_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ("method", "path"),
)


def record_http_request(method: str, path: str, status_code: int, duration: float) -> None:
    """Record low-cardinality request metrics (path, never query parameters)."""
    HTTP_REQUESTS.labels(method, path, str(status_code)).inc()
    HTTP_REQUEST_DURATION.labels(method, path).observe(duration)


def configure_tracing(app: FastAPI) -> None:
    """Instrument FastAPI and export OTLP spans when an endpoint is configured."""
    if not settings.OTEL_ENABLED or getattr(app.state, "tracing_configured", False):
        return

    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        # Local test tooling may purposefully install only a small dependency
        # subset. The container image installs these pinned requirements.
        logging.getLogger(__name__).warning("OpenTelemetry packages are unavailable; tracing disabled")
        app.state.tracing_configured = False
        return

    resource = Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": settings.APP_VERSION,
            "deployment.environment": settings.APP_ENV,
        }
    )
    provider = TracerProvider(resource=resource)
    if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        # Import lazily: local/dev installs can trace without an OTLP collector.
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(endpoint=f"{settings.OTEL_EXPORTER_OTLP_ENDPOINT.rstrip('/')}/v1/traces")
            )
        )

    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, excluded_urls="health,metrics")
    app.state.tracing_provider = provider
    app.state.tracing_configured = True


def shutdown_tracing(app: FastAPI) -> None:
    provider = getattr(app.state, "tracing_provider", None)
    if provider is not None:
        provider.force_flush()
        provider.shutdown()
