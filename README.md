# streaming-pipeline
- - - - - - - - - - - - - - - - - - - - -
## 목차
- 배포 주소
- 화면
- 프로젝트 정보
- 시작 가이드
- 주요 기능
- 시작 가이드
### 배포 주소
- http://localhost:1223(로컬배포)
### 화면
![image](https://github.com/user-attachments/assets/0aaf67f6-cd62-4135-b8ab-edb70979e1ef)
## 프로젝트 정보 
   ### 영상 스트리밍 AI 서버 (streaming-pipeline)

### 프로젝트 구조 (streaming-platform 레이아웃)
```
app/          # 진입점(app.main:app), API, core, domain, application, infrastructure, worker, tests
legacy/       # 이전 서비스 (FastAPI 라우트, Celery tasks, GStreamer) — app에서 로드
docker/       # api.Dockerfile, worker.Dockerfile, docker-compose.dev.yml|prod.yml
scripts/      # dev_up.sh, dev_down.sh, lint.sh, smoke_test.sh
deployments/  # k8s/, helm/
docs/         # diagrams/, adr/, 코딩 컨벤션
```
- API 실행: `uvicorn app.main:app` (legacy 앱 + /health)
- Celery: `celery -A legacy.tasks worker`
- 아키텍처: [ARCHITECTURE.md](ARCHITECTURE.md)  
- 운영: [RUNBOOK.md](RUNBOOK.md)  
- 변경 이력: [CHANGELOG.md](CHANGELOG.md)
   
## 시작 가이드
   ### Requirements
   
```
+ Docker (다운: https://docs.docker.com/engine/install/ubuntu/)
+ Docker compose
+ NVIDIA CUDA 11.3 이상
```
   ### 실행 방법
```
1. 도커 실행
   docker-compose up -d (V1.13.0 부턴 docker compose up -d)
2. web 접속
   http://localhost:1223
```

## 주요 기능
+ CCTV리스트 체크
+ CCTV AI 감지
## 개발환경
+ 사용언어: <img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white">
+ 사용 웹 프레임 워크: <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white">
+ 데이터 베이스: <img src="https://img.shields.io/badge/sqlite3-121212?style=for-the-badge&logo=sqlite3&logoColor=white">
+ 운영체제: <img src="https://img.shields.io/badge/Linux-898989?style=for-the-badge&logo=Linux&logoColor=white">
+ IDE: <img src="https://img.shields.io/badge/VSCODE-676767?style=for-the-badge&logo=VSCODE&logoColor=white">
-----------------------------------------







