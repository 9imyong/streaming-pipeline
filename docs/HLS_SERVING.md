# HLS 서빙 안정화

- **Streamlit**: m3u8 URL만 받아 **hls.js**로 재생한다. FastAPI가 스트리밍하는 구조가 아니다.
- **m3u8/ts 서빙**: FastAPI(StaticFiles)로 할 수도 있고, **nginx**로 할 수 있다. nginx 사용 시 영상 트래픽은 전부 nginx가 담당하고 FastAPI는 관여하지 않는다.

현재 기본은 **FastAPI**가 `/hls`를 StaticFiles로 서빙한다. 트래픽이 많거나 재생이 불안정할 때 아래처럼 nginx로 넘기면 된다.

## 1. 현재 구성 (FastAPI 단일)

- **API** 컨테이너가 `/hls`를 StaticFiles로 서빙 (`/data/hls` 볼륨).
- 구현이 단순하고 포트 8000 하나로 API·HLS 모두 제공.
- 동시 시청자·요청이 많으면 FastAPI/ASGI 한계로 지연·멈춤이 생길 수 있음.

## 2. nginx 리버스 프록시 (권장)

HLS는 **nginx가 디스크에서 직접** 서빙(sendfile), API만 FastAPI로 프록시한다.

- **장점**: sendfile로 커널이 파일 전송, 연결·캐시 제어에 유리. 재생 안정성·동시 접속에 강함.
- **구성**: `docker/nginx.conf` + `docker-compose.nginx.yml`.

### 사용 방법

```bash
cd docker
docker compose -f docker/docker-compose.yml -f docker/docker-compose.nginx.yml up -d
```

- **HLS**: `http://localhost/hls/{channel_id}/index.m3u8`
- **API**: `http://localhost/v1/streams`, `http://localhost/health` 등 (기존 경로 동일)
- **Streamlit UI**: `http://localhost:8501` — HLS 플레이어는 자동으로 nginx(`http://localhost/hls`)에서 m3u8을 로드하도록 오버라이드됨.

nginx가 80 포트로 들어오는 요청을 받고, `/hls/`는 디스크, 나머지는 `api:8000`으로 프록시.  
다른 PC에서 UI에 접속할 때는 해당 호스트로 HLS가 나가야 하므로, `.env`나 컴포즈에서 `HLS_BASE_URL=http://<서버IP 또는 호스트명>/hls` 로 설정하면 된다.

API 포트(8000)를 외부에 안 열고 nginx만 쓰려면 `docker-compose.nginx.yml`에서 `api.ports`를 비우면 된다.

## 3. FastAPI만 쓸 때 보완 (Cache-Control)

nginx를 쓰지 않을 때도, HLS 응답에 **Cache-Control**을 주면 플레이어·중간 캐시 동작이 조금 안정될 수 있다.

- **세그먼트(.ts)**: `max-age=2` 수준의 짧은 캐시.
- **플레이리스트(.m3u8)**: `no-cache`로 항상 최신 목록 조회.

이 동작은 nginx 설정에 이미 반영되어 있다. FastAPI 단일 구성에서도 동일한 정책을 쓰려면, `/hls` 마운트에 커스텀 응답 헤더를 주는 방식으로 구현할 수 있다(선택).

## 요약

| 구성            | 용도                     | 안정성/확장성 |
|----------------|--------------------------|----------------|
| FastAPI 단일   | 개발·소규모              | 보통           |
| nginx + FastAPI| 운영·동시 시청 다수      | 높음           |

운영 환경에서는 **nginx 리버스 프록시** 사용을 권장한다.
