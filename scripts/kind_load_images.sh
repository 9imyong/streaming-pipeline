#!/usr/bin/env bash
# 로컬 빌드 이미지를 KIND 클러스터에 로드
set -e
KIND_NAME="${KIND_NAME:-streaming}"
for img in streaming-api:latest streaming-orchestrator:latest streaming-worker-stream:latest streaming-worker-infer:latest; do
  if docker image inspect "$img" &>/dev/null; then
    kind load docker-image "$img" --name "$KIND_NAME"
    echo "Loaded $img"
  fi
done
