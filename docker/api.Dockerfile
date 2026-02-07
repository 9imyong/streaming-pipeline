# ========== 빌드 스테이지: uv로 휠만 다운로드 (런타임에 uv 미포함) ==========
FROM python:3.11-slim AS builder
WORKDIR /build

RUN pip install --no-cache-dir uv

COPY docker/api-requirements.in ./
# lock 생성 → wheelhouse 다운로드 (PyGObject 제외)
RUN uv pip compile api-requirements.in -o requirements.lock \
    && pip download -d /wheelhouse -r requirements.lock

COPY app/ ./app/

# ========== 런타임 스테이지: pip만 사용, 오프라인 설치 ==========
FROM python:3.11-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /wheelhouse /wheelhouse
COPY --from=builder /build/requirements.lock /tmp/requirements.lock
RUN pip install --no-cache-dir --no-index --find-links=/wheelhouse \
    -r /tmp/requirements.lock --target /install \
    && rm -rf /wheelhouse /tmp/requirements.lock

COPY --from=builder /build/app ./app
ENV PYTHONPATH=/install:/app

CMD ["python", "-m", "uvicorn", "app.gateway.main:app", "--port=8000", "--host=0.0.0.0"]
