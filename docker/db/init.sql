-- MySQL 컨테이너 최초 기동 시 /docker-entrypoint-initdb.d 에 마운트하여 DB 초기화.
-- 수동 실행: docker exec -i streaming-mysql mysql -uroot -pdevpass streaming_pipeline_dev < docker/db/init.sql

CREATE TABLE IF NOT EXISTS streams (
  channel_id         VARCHAR(64) PRIMARY KEY,
  status             VARCHAR(32) NOT NULL DEFAULT 'pending',
  desired_state      VARCHAR(32) NOT NULL DEFAULT 'running',
  assigned_worker_id VARCHAR(128) NULL,
  lease_expires_at   DATETIME(3) NULL,
  pipeline_params    JSON NULL,
  restart_count      INT NOT NULL DEFAULT 0,
  last_error         TEXT NULL,
  created_at         DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at         DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)
);

CREATE TABLE IF NOT EXISTS jobs (
  id              BIGINT AUTO_INCREMENT PRIMARY KEY,
  job_id          VARCHAR(64) NOT NULL UNIQUE,
  channel_id      VARCHAR(64) NOT NULL,
  idempotency_key VARCHAR(256) NOT NULL UNIQUE,
  command         VARCHAR(32) NOT NULL,
  created_at      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
);
