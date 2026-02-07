# DB migrations

DDL (MySQL). 배포 스크립트 또는 수동 실행용.

**실행 예시 (Docker MySQL 컨테이너):**
```bash
docker exec -i streaming-mysql mysql -uroot -pdevpass streaming_pipeline_dev < app/infrastructure/persistence/migrations/001_streams_jobs_mysql.sql
```

**파일:** `001_streams_jobs_mysql.sql` — streams, jobs 테이블 생성.
