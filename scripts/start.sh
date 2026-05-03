#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8794}"
FORCE_CPU=0
FORCE_GPU=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      PORT="${2:?Missing value for --port}"
      shift 2
      ;;
    --cpu)
      FORCE_CPU=1
      shift
      ;;
    --gpu)
      FORCE_GPU=1
      shift
      ;;
    -h|--help)
      echo "Usage: ./scripts/start.sh [--port 8794] [--cpu|--gpu]"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

if [[ "$FORCE_CPU" == "1" && "$FORCE_GPU" == "1" ]]; then
  echo "Use either --cpu or --gpu, not both." >&2
  exit 2
fi

export HOST_PORT="$PORT"

has_nvidia_host() {
  command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1
}

has_nvidia_docker_runtime() {
  docker info --format '{{json .Runtimes}}' 2>/dev/null | grep -qi nvidia
}

wait_container_healthy() {
  local deadline=$((SECONDS + 180))
  while [[ "$SECONDS" -lt "$deadline" ]]; do
    local status
    status="$(docker inspect clarity-upscaler --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' 2>/dev/null || true)"
    if [[ "$status" == *"running healthy"* ]]; then
      return 0
    fi
    sleep 3
  done
  return 1
}

container_has_cuda() {
  local cuda
  cuda="$(docker exec clarity-upscaler python -c "import torch; print(torch.cuda.is_available())" 2>/dev/null || true)"
  [[ "$cuda" == "True" ]]
}

start_cpu() {
  echo "Starting Clarity Image Tools with CPU support on port $PORT."
  docker compose up --build -d
}

USE_GPU=0
if [[ "$FORCE_GPU" == "1" ]]; then
  USE_GPU=1
elif [[ "$FORCE_CPU" != "1" ]] && has_nvidia_host && has_nvidia_docker_runtime; then
  USE_GPU=1
fi

if [[ "$USE_GPU" == "1" ]]; then
  echo "Starting Clarity Image Tools with NVIDIA GPU support on port $PORT."
  if ! docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build -d; then
    if [[ "$FORCE_GPU" == "1" ]]; then
      exit 1
    fi
    echo "GPU startup failed. Falling back to CPU." >&2
    start_cpu
  elif wait_container_healthy && container_has_cuda; then
    echo "GPU runtime verified inside the container."
  else
    if [[ "$FORCE_GPU" == "1" ]]; then
      echo "GPU container started, but CUDA was not available inside the container." >&2
      exit 1
    fi
    echo "GPU was detected on the host, but CUDA was not available inside the container. Falling back to CPU." >&2
    start_cpu
  fi
else
  start_cpu
fi

echo "Open http://localhost:$PORT"
