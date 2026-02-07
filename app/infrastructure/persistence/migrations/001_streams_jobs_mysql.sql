-- streams: 스트림 상태 + lease (API/Orchestrator/Worker 공통)
-- jobs: 멱등성 (API)
-- MySQL 5.7+ / 8.0. 실행: mysql -u root -p streaming_pipeline_dev < 001_streams_jobs_mysql.sql

CREATE TABLE IF NOT EXISTS streams (
  channel_id         VARCHAR(64) PRIMARY KEY,
  status             VARCHAR(32) NOT NULL DEFAULT 'pending',
  desired_state      VARCHAR(32) NOT NULL DEFAULT 'running',
  assigned_worker_id VARCHAR(128) NULL,
  lease_expires_at   DATETIME(3) NULL,
  pipeline_params    JSON NULL,
  restart_count      INT NOT NULL DEFAULT 0,
  last_error         TEXT NULL,
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
