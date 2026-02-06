"""DB lease 구현. 조건부 UPDATE로 lease 획득/갱신."""
# UPDATE streams SET worker_id=?, lease_expires_at=? WHERE channel_id=? AND (lease_expires_at < NOW() OR worker_id IS NULL)
