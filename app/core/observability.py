"""
Prometheus metrics / OTel tracing 초기화.
- 메트릭 레지스트리, 기본 카운터/게이지 생성 함수만 제공. 비즈니스 지표 수집은 infrastructure에서.
- tracing: OTel이 있으면 초기화, 없으면 no-op.
비즈니스 로직 없음.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Prometheus: 선택 의존 (없으면 no-op)
try:
    from prometheus_client import Counter, Gauge, Histogram, REGISTRY, start_http_server
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    REGISTRY = None
    start_http_server = None
    Counter = None
    Gauge = None
    Histogram = None


def is_prometheus_available() -> bool:
    return _PROMETHEUS_AVAILABLE


def create_counter(name: str, documentation: str, *labelnames: str) -> Any:
    """Counter 생성. 의존성 없으면 더미 반환."""
    if _PROMETHEUS_AVAILABLE and Counter is not None:
        return Counter(name, documentation, labelnames=labelnames or ())
    return _NoOpMetric()


def create_gauge(name: str, documentation: str, *labelnames: str) -> Any:
    """Gauge 생성."""
    if _PROMETHEUS_AVAILABLE and Gauge is not None:
        return Gauge(name, documentation, labelnames=labelnames or ())
    return _NoOpMetric()


def create_histogram(name: str, documentation: str, *labelnames: str) -> Any:
    """Histogram 생성 (지연 시간 등)."""
    if _PROMETHEUS_AVAILABLE and Histogram is not None:
        return Histogram(name, documentation, labelnames=labelnames or ())
    return _NoOpMetric()


class _NoOpMetric:
    """prometheus_client 미설치 시 더미."""

    def labels(self, **kwargs: Any) -> "_NoOpMetric":
        return self

    def inc(self, amount: float = 1) -> None:
        pass

    def dec(self, amount: float = 1) -> None:
        pass

    def set(self, value: float) -> None:
        pass

    def observe(self, amount: float) -> None:
        pass


def start_metrics_server(port: int = 9090) -> None:
    """메트릭 HTTP 서버 기동 (별도 스레드). prometheus_client 없으면 no-op."""
    if _PROMETHEUS_AVAILABLE and start_http_server is not None:
        start_http_server(port)
        logger.info("Prometheus metrics server started on port %s", port)
    else:
        logger.debug("Prometheus not available, metrics server not started")


# ----- OTel tracing (선택) -----

def init_tracing(service_name: str, endpoint: str | None = None) -> bool:
    """
    OTel tracer 초기화. opentelemetry 미설치 시 no-op, False 반환.
    endpoint 예: http://jaeger:4318 (OTLP HTTP).
    """
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.debug("OpenTelemetry not installed, tracing disabled")
        return False

    try:
        provider = TracerProvider()
        if endpoint:
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        trace.set_tracer_provider(provider)
        logger.info("Tracing initialized for service=%s", service_name)
        return True
    except Exception as e:
        logger.warning("Tracing init failed: %s", e)
        return False
