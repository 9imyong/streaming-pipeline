#!/usr/bin/env bash
# KIND 클러스터 생성 (streaming-platform 로컬 테스트용)
set -e
KIND_NAME="${KIND_NAME:-streaming}"
kind create cluster --name "$KIND_NAME" --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
EOF
kubectl config use-context "kind-$KIND_NAME"
echo "KIND cluster $KIND_NAME ready."
