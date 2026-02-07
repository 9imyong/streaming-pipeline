"""
Prometheus 지표: streams_running, streams_failed_total, streams_reassign_total, worker_restarts_total.
- Orchestrator: /metrics에서 DB 기반 gauge 갱신, 재할당 시 counter inc.
- Worker: /metrics에서 재시작 시 worker_restarts_total inc.
"""
from app.core.observability import create_counter, create_gauge

streams_running_gauge = create_gauge(
    "streams_running",
    "Number of streams in running state",
)
streams_failed_total_counter = create_counter(
    "streams_failed_total",
    "Total number of streams that transitioned to failed",
)
streams_reassign_total_counter = create_counter(
    "streams_reassign_total",
    "Total number of lease-expired reassignments (START re-published)",
)
worker_restarts_total_counter = create_counter(
    "worker_restarts_total",
    "Total number of pipeline restarts on this worker",
)
