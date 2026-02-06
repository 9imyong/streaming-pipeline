"""
jobs 테이블, idempotency_key.
- create(job_id, channel_id, command, idempotency_key)
- get_by_idempotency_key(idempotency_key) -> job | None
"""
