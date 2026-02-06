"""
streams 테이블 CRUD, lease 갱신.
- get(channel_id), set_desired_state(channel_id, state)
- acquire_lease(channel_id, worker_id, ttl_sec) -> bool
- renew_lease(channel_id, worker_id, ttl_sec) -> bool
- list_expired_leases() -> list[channel_id]
"""
