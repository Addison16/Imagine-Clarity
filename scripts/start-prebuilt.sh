#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8794}"
IMAGE_PREFIX="${IMAGE_PREFIX:-ghcr.io/addison16/imagine-clarity}"
FORCE_CPU=0
FORCE_GPU=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="${2:?Missing value for --port}"; shift 2 ;;
    --image-prefix) IMAGE_PREFIX="${2:?Missing value for --image-prefix}"; shift 2 ;;
    --cpu) FORCE_CPU=1; shift ;;
    --gpu) FORCE_GPU=1; shift ;;
    -h|--help)
      echo "Usage: ./scripts/start-prebuilt.sh [--port 8794] [--image-prefix ghcr.io/addison16/imagine-clarity] [--cpu|--gpu]"
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

if [[ "$FORCE_CPU" == "1" && "$FORCE_GPU" == "1" ]]; then
  echo "Use either --cpu or --gpu, not both." >&2
  exit 2
fi

has_nvidia_host() {
  command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1
}

has_nvidia_docker_runtime() {
  docker info --format '{{json .Runtimes}}' 2>/dev/null | grep -qi nvidia
}

wait_healthy() {
  local deadline=$((SECONDS + 180))
  while [[ "$SECONDS" -lt "$deadline" ]]; do
    local status
    status="$(docker inspect clarity-upscaler --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' 2>/dev/null || true)"
    [[ "$status" == *"running healthy"* ]] && return 0
    sleep 3
  done
  return 1
}

container_has_cuda() {
  [[ "$(docker exec clarity-upscaler python -c 'import torch; print(torch.cuda.is_available())' 2>/dev/null || true)" == "True" ]]
}

start_cpu() {
  export CLARITY_IMAGE="${IMAGE_PREFIX}:cpu"
  echo "Pulling and starting CPU image $CLARITY_IMAGE on port $PORT."
  docker compose -f docker-compose.prebuilt.yml up -d --pull always --remove-orphans
  wait_healthy
}

export HOST_PORT="$PORT"
USE_GPU=0
if [[ "$FORCE_GPU" == "1" ]]; then
  USE_GPU=1
elif [[ "$FORCE_CPU" != "1" ]] && has_nvidia_host && has_nvidia_docker_runtime; then
  USE_GPU=1
fi

if [[ "$USE_GPU" == "1" ]]; then
  export CLARITY_IMAGE="${IMAGE_PREFIX}:gpu"
  echo "Pulling and starting NVIDIA GPU image $CLARITY_IMAGE on port $PORT."
  if docker compose -f docker-compose.prebuilt.yml -f docker-compose.prebuilt.gpu.yml up -d --pull always --remove-orphans && wait_healthy && container_has_cuda; then
    echo "GPU runtime verified inside the container."
  elif [[ "$FORCE_GPU" == "1" ]]; then
    echo "GPU image started but CUDA verification failed." >&2
    exit 1
  else
    echo "GPU startup or verification failed; falling back to CPU." >&2
    start_cpu
  fi
else
  start_cpu
fi

echo "Open http://localhost:$PORT"
