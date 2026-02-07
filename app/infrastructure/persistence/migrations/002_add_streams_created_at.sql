-- 기존 DB에 created_at 추가 (001을 created_at 없이 이미 실행한 환경만).
-- 이미 created_at 컬럼이 있으면 에러 발생 → 한 번만 실행하거나 스킵.
-- 실행: docker exec -i streaming-mysql mysql -uroot -pdevpass streaming_pipeline_dev < app/infrastructure/persistence/migrations/002_add_streams_created_at.sql

ALTER TABLE streams
  ADD COLUMN created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) AFTER last_error;
