# ========== 빌드 스테이지: uv로 휠만 다운로드 ==========
FROM python:3.11-slim AS builder
WORKDIR /build

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv pip compile pyproject.toml -o requirements.lock \
    && uv pip download -d /wheelhouse -r requirements.lock

COPY app/ ./app/

# ========== 런타임: 오프라인 pip 설치만 ==========
FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /wheelhouse /wheelhouse
COPY --from=builder /build/requirements.lock /tmp/requirements.lock
RUN pip install --no-cache-dir --no-index --find-links=/wheelhouse \
    -r /tmp/requirements.lock --target /install \
    && rm -rf /wheelhouse /tmp/requirements.lock

COPY --from=builder /build/app ./app
ENV PYTHONPATH=/install:/app

CMD ["python", "-m", "app.services.orchestrator.main"]
