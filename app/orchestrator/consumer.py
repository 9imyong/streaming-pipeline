"""
stream.commands 소비, lease 획득, worker 지시.
Orchestrator main에서 consumer loop가 이 모듈 호출.
"""
# from app.infrastructure.kafka.client import get_consumer
# from app.infrastructure.kafka.topics import STREAM_COMMANDS
# from app.orchestrator.lease import acquire_lease
# from app.orchestrator.publisher import send_to_worker
