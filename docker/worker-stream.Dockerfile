# ========== 빌드: worker 전용 requirements만 lock·다운로드 (PyGObject/gi 제외) ==========
FROM python:3.11-slim AS builder
WORKDIR /build

RUN pip install --no-cache-dir -U uv
RUN mkdir -p /wheelhouse

# worker-requirements.in만 사용 (pyproject.toml 미사용)
COPY docker/worker-requirements.in ./

RUN uv pip compile worker-requirements.in -o requirements.lock \
    && pip download -r requirements.lock -d /wheelhouse

COPY app/ ./app/


# ========== 런타임: gi는 apt로만 제공 (python3-gi + gir) ==========
FROM debian:bookworm-slim AS runtime
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    python3-gi \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    libgirepository-1.0-1 \
    libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-tools \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /wheelhouse /wheelhouse
COPY --from=builder /build/requirements.lock /tmp/requirements.lock

RUN python3 -m pip install --no-cache-dir --no-index --find-links=/wheelhouse \
    -r /tmp/requirements.lock --target /install \
    && rm -rf /wheelhouse /tmp/requirements.lock

COPY --from=builder /build/app ./app
ENV PYTHONPATH=/install:/app

CMD ["python3", "-m", "app.services.worker_stream.main"]