# Changelog

형식: [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/).  
버전: [Semantic Versioning](https://semver.org/lang/ko/).

## [Unreleased]
### Added
- 프로젝트 구조 정리: streaming-platform 레이아웃 적용 (app/, docker/, scripts/, deployments/, docs/)
### Changed
- **구조 이전**: `fastapi/` → `legacy/` 로 이름 변경. 진입점을 `app.main:app` 으로 통일 (uvicorn app.main:app, celery -A legacy.tasks)

## [기존]
- CCTV 스트리밍, HLS 서빙, Celery 기반 AI 검출 파이프라인
