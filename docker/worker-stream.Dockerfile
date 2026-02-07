# ========== 빌드 스테이지: uv로 휠만 다운로드 ==========
FROM python:3.11-slim AS builder
WORKDIR /build

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv pip compile pyproject.toml -o requirements.lock \
    && pip download -d /wheelhouse -r requirements.lock

COPY app/ ./app/

# ========== 런타임: 오프라인 pip 설치 + GStreamer(gst-launch-1.0) ==========
# rtspsrc/h264/HLSSink2 등: plugins-base, good, bad, ugly, libav
FROM python:3.11-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav \
    gstreamer1.0-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /wheelhouse /wheelhouse
COPY --from=builder /build/requirements.lock /tmp/requirements.lock
RUN pip install --no-cache-dir --no-index --find-links=/wheelhouse \
    -r /tmp/requirements.lock --target /install \
    && rm -rf /wheelhouse /tmp/requirements.lock

COPY --from=builder /build/app ./app
ENV PYTHONPATH=/install:/app

CMD ["python", "-m", "app.services.worker_stream.main"]
