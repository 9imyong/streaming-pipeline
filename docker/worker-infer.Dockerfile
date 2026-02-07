# =========================================================
# Stage 1) Builder: download wheels only (uv)
# =========================================================
FROM openmmlab/mmdeploy:ubuntu20.04-cuda11.8-mmdeploy AS builder
ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /build
# python + pip만 (gstreamer 제거)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      python3 python3-pip \
      ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*
# uv 설치 (빌더에만 존재)
RUN pip install --no-cache-dir -U pip uv
# wheelhouse 폴더
RUN mkdir -p /wheelhouse
# # 1) 프로젝트 requirements 다운로드
# COPY legacy/requirements.txt /build/legacy/requirements.txt
# uv로 휠/소스 패키지 다운로드 (런타임 네트워크 없이 설치 가능)
# --only-binary=:all: 를 강제하면 일부 패키지(환경별 wheel 없음)에서 실패할 수 있어 기본은 미적용
RUN pip download -d /wheelhouse -r /build/legacy/requirements.txt
# 2) 네가 Dockerfile에서 추가로 설치하던 패키지도 wheelhouse에 다운로드
# (런타임에서 pip install로 설치할 예정)
RUN pip download -d /wheelhouse \
     onnxruntime mmdeploy_runtime openmim==0.3.9 tensorrt
# 3) mim으로 설치하던 것들은 "mim install" 자체가 런타임 설치 행위라서
# wheelhouse 방식으로는 보통 pip 패키지로 직접 받는 쪽이 낫다.
# mmengine/mmcv/mmyolo/mmdeploy 를 pip로 받도록 다운로드
# (환경에 따라 mmcv는 CUDA/torch 매칭이 필요해서 추가 조정이 필요할 수 있음)
RUN pip download -d /wheelhouse \
    mmengine mmdeploy==1.2.0 mmyolo
# =========================================================
# Stage 2) Runtime: install from wheelhouse (no uv, no gstreamer)
# =========================================================
FROM openmmlab/mmdeploy:ubuntu20.04-cuda11.8-mmdeploy AS runtime

ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# 런타임에 필요한 최소 패키지 (gstreamer 제거)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      python3 python3-pip \
      ffmpeg \
      libglib2.0-0 libsm6 libxext6 \
