"""
streams / jobs 테이블 스키마 정의 (참조용).
- 실제 DDL은 migrations 또는 배포 스크립트에서 수행.
- 비즈니스 판단 없음. 상태 전이 검증은 domain에서.
"""

# streams 테이블 (스트림 상태 + lease)
#   channel_id         VARCHAR(64) PRIMARY KEY
#   status              VARCHAR(32)  -- pending | assigned | running | failed | stopped (domain.StreamState)
#   desired_state       VARCHAR(32)  -- running | stopped
#   assigned_worker_id  VARCHAR(128) NULL  -- lease 소유 워커
#   lease_expires_at    DATETIME(3) NULL
#   pipeline_params    JSON NULL     -- source_rtsp, output, ai_profile 등
#   restart_count       INT DEFAULT 0
#   last_error         TEXT NULL
#   updated_at         DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)

# jobs 테이블 (멱등성)
#   id              BIGINT AUTO_INCREMENT PRIMARY KEY
#   job_id          VARCHAR(64) UNIQUE NOT NULL
#   channel_id      VARCHAR(64) NOT NULL
#   idempotency_key VARCHAR(256) UNIQUE NOT NULL
#   command         VARCHAR(32) NOT NULL  -- START | STOP
#   created_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3)

STREAMS_TABLE = "streams"
JOBS_TABLE = "jobs"
