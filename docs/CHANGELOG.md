# Changelog

형식: [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/).  
버전: [Semantic Versioning](https://semver.org/lang/ko/).

## [Unreleased]
### Fixed
- Kafka 자동 커밋 비활성화 및 처리 완료된 파티션의 오프셋만 커밋. 핸들러 실패 시 같은 메시지 재시도 후 다음 메시지 처리.
- 스트림 워커별 소비 그룹 분리로 다른 워커에 할당된 START 명령의 소비 누락 방지. 각 워커의 고유하고 안정적인 `WORKER_ID` 필요.
- STOP 처리 중 재시작 대기에서 깨어난 워커가 종료된 파이프라인을 다시 기동하는 경합 차단.
- Lease 만료값 누락·오류를 유효한 Lease로 취급하던 동작 수정. MySQL의 timezone 없는 UTC 값 처리.
- 최초 Lease 갱신 실패 시 파이프라인 중지. 주기 갱신 예외 시 해당 채널 중지 후 다른 채널 갱신 유지.

### Added
- 프로젝트 구조 정리: streaming-platform 레이아웃 적용 (app/, docker/, scripts/, deployments/, docs/)
### Changed
- **구조 이전**: `fastapi/` → `legacy/` 로 이름 변경. 진입점을 `app.main:app` 으로 통일 (uvicorn app.main:app, celery -A legacy.tasks)

## [기존]
- CCTV 스트리밍, HLS 서빙, Celery 기반 AI 검출 파이프라인
