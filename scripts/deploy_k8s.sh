#!/usr/bin/env bash
# streaming-platform 네임스페이스에 k8s 리소스 배포
set -e
cd "$(dirname "$0")/.."
KUBECTL="${KUBECTL:-kubectl}"
NS="${NS:-streaming-platform}"
DIR="${1:-deployments/k8s}"
echo "Applying $DIR (namespace: $NS)"
$KUBECTL apply -f "$DIR/namespace.yaml"
$KUBECTL apply -f "$DIR/configmap.yaml"
$KUBECTL apply -f "$DIR/api-deploy.yaml"
$KUBECTL apply -f "$DIR/orchestrator-deploy.yaml"
$KUBECTL apply -f "$DIR/stream-worker-deploy.yaml"
$KUBECTL apply -f "$DIR/infer-worker-deploy.yaml"
$KUBECTL apply -f "$DIR/service.yaml" 2>/dev/null || true
$KUBECTL apply -f "$DIR/ingress.yaml" 2>/dev/null || true
$KUBECTL apply -f "$DIR/hpa.yaml" 2>/dev/null || true
echo "Deploy done. Check: kubectl get pods -n $NS"
