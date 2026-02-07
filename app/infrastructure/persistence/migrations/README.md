# DB migrations

DDL (MySQL). 배포 스크립트 또는 수동 실행용.

**실행 예시 (Docker MySQL 컨테이너):**
```bash
docker exec -i streaming-mysql mysql -uroot -pdevpass streaming_pipeline_dev < app/infrastructure/persistence/migrations/001_streams_jobs_mysql.sql
```

**파일:** `001_streams_jobs_mysql.sql` — streams, jobs 테이블 생성.

**트랜잭션:** StreamRepository/JobRepository/LeaseStore 각 메서드는 하나의 DB 연결로 실행되며, 성공 시 commit·실패 시 rollback으로 원자성 보장. 상태 전이(transition_status), lease 획득/갱신/해제(acquire/renew/release)는 조건부 UPDATE로 동시성 안전.
