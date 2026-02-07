# InMemory → DB(MySQL) 저장소 교체 · 검증

## 1. 변경 파일 목록

| 파일 | 변경 내용 |
|------|-----------|
| `app/application/ports/stream_repository.py` | 유지 (변경 없음) |
| `app/application/ports/job_repository.py` | 유지 (변경 없음) |
| `app/infrastructure/persistence/stream_repository.py` | DbStreamRepository (기존). 메서드별 1 connection = 1 트랜잭션 |
| `app/infrastructure/persistence/job_repository.py` | DbJobRepository (기존). 멱등성 UNIQUE 제약 |
| `app/infrastructure/persistence/lease_db.py` | DbLeaseStore (기존). lease 획득/갱신/해제 조건부 UPDATE |
| `app/infrastructure/persistence/mysql.py` | get_connection() commit/rollback (기존) |
| `app/infrastructure/persistence/inmem.py` | InMemory 테스트 전용 명시, 운영은 DB 사용 주석 |
| `app/infrastructure/persistence/migrations/001_streams_jobs_mysql.sql` | 기존 DDL (streams, jobs) |
| `app/infrastructure/persistence/migrations/README.md` | 트랜잭션/동시성 보장 설명 추가 |
| `docker/docker-compose.yml` | stream-worker에 MySQL env(HOST/PORT/USERNAME/PASSWORD/DBNAME) 및 depends_on mysql 추가 |
| `scripts/smoke_test.sh` | GET으로 상태 조회 검증, API 재시작 후 GET으로 DB 영속성 검증 단계 추가 |

**이미 적용된 사항:** Gateway/Orchestrator/Stream Worker 진입점에서 모두 DbStreamRepository, DbJobRepository, DbLeaseStore 사용 중. InMemory는 테스트 전용으로만 유지.

---

## 2. 커밋 메시지 제안

```
feat(persistence): DB(MySQL) 저장소 사용 고정, 재시작 후 상태 유지 검증

- application port 인터페이스 유지, infrastructure에 DB 구현체 사용
- 상태 전이/lease 획득·갱신·해제: 메서드별 1 connection 트랜잭션, 조건부 UPDATE로 동시성 보장
- DDL: 001_streams_jobs_mysql.sql, compose MySQL 연동
- stream-worker에 MySQL env 및 depends_on 추가
- smoke_test.sh: GET 검증 + API 재시작 후 GET으로 DB 영속성 검증
- InMemory는 테스트 전용 명시, migrations README에 트랜잭션 설명
```

---

## 3. 검증 절차

### 전제
- Docker Compose로 MySQL·Kafka·API·Orchestrator 기동
- DB 초기화 1회 실행

### 3.1 DB 초기화
```bash
docker exec -i streaming-mysql mysql -uroot -pdevpass streaming_pipeline_dev \
  < app/infrastructure/persistence/migrations/001_streams_jobs_mysql.sql
```

### 3.2 스모크 테스트 (curl + 재시작 후 상태 유지)
```bash
make smoke
```
또는
```bash
./scripts/smoke_test.sh http://localhost:8000 ch1
```

**검증 단계 요약**
1. **POST /v1/streams/** → 202, 본문에 job_id
2. **GET /v1/streams/{channel_id}** → 200, 본문에 `channel_id` (DB에서 조회)
3. **API 재시작** (docker 사용 시): `docker restart streaming-api`, 5초 대기
4. **GET /v1/streams/{channel_id}** → 200, 동일 채널 상태 유지 (DB 영속성)
5. **DELETE /v1/streams/{channel_id}** → 202

**재시작 단계 스킵** (로컬만 띄운 경우 등):  
`RESTART_API_FOR_PERSISTENCE=0 ./scripts/smoke_test.sh`

### 3.3 기대 출력 예
```
Smoke test: http://localhost:8000 (channel=ch1)
OK: START 202
OK: GET 200 (state persisted)
Waiting for API after restart (5s)...
OK: GET after API restart 200 (state persisted in DB)
OK: STOP 202
smoke_test done. DB persistence verified (GET after POST, GET after API restart). ...
```

### 3.4 DB 직접 확인 (선택)
```bash
docker exec -it streaming-mysql mysql -uroot -pdevpass streaming_pipeline_dev -e \
  "SELECT channel_id, status, desired_state, assigned_worker_id FROM streams;"
```
