from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


PROCESSES: dict[str, subprocess.Popen[bytes]] = {}
STOPPING = False


def _request_stop(*_: object) -> None:
    global STOPPING
    STOPPING = True


def _wait_for_redis(process: subprocess.Popen[bytes], timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Redis exited during startup with code {process.returncode}.")
        try:
            with socket.create_connection(("127.0.0.1", 6379), timeout=0.5):
                return
        except OSError:
            time.sleep(0.25)
    raise RuntimeError("Redis did not become ready within 30 seconds.")


def _start(command: list[str], name: str) -> subprocess.Popen[bytes]:
    print(f"[all-in-one] starting {name}: {' '.join(command)}", flush=True)
    process = subprocess.Popen(command)
    PROCESSES[name] = process
    return process


def _stop_process(name: str, timeout: float) -> None:
    process = PROCESSES.get(name)
    if process is None or process.poll() is not None:
        return
    print(f"[all-in-one] stopping {name}", flush=True)
    process.terminate()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"[all-in-one] {name} did not stop within {timeout:.0f}s; killing it", file=sys.stderr, flush=True)
        process.kill()
        process.wait(timeout=2)


def _shutdown() -> None:
    # Stop accepting requests, then let the worker unregister while Redis is still alive.
    _stop_process("web API", 3)
    _stop_process("RQ worker", 6)
    _stop_process("redis", 3)
    for name, process in PROCESSES.items():
        if process.poll() is None:
            print(f"[all-in-one] force-killing {name}", file=sys.stderr, flush=True)
            process.kill()


def main() -> int:
    redis_data = Path(os.getenv("REDIS_DATA_DIR", "/data/redis"))
    storage = Path(os.getenv("STORAGE_DIR", "/data/storage"))
    models = Path(os.getenv("MODEL_DIR", "/models"))
    for directory in (redis_data, storage, models):
        directory.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")
    os.environ.setdefault("RQ_QUEUE_NAME", "image-jobs")

    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)

    redis = _start(
        [
            "redis-server",
            "--bind",
            "127.0.0.1",
            "--protected-mode",
            "yes",
            "--appendonly",
            "yes",
            "--save",
            "60",
            "1",
            "--dir",
            str(redis_data),
        ],
        "redis",
    )
    try:
        _wait_for_redis(redis)
    except Exception as exc:
        print(f"[all-in-one] startup failed: {exc}", file=sys.stderr, flush=True)
        _stop_process("redis", 3)
        return 1

    _start([sys.executable, "-m", "app.worker"], "RQ worker")
    _start(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            os.getenv("APP_PORT", "8794"),
        ],
        "web API",
    )

    exit_code = 0
    try:
        while not STOPPING:
            for name, process in PROCESSES.items():
                code = process.poll()
                if code is not None:
                    print(
                        f"[all-in-one] {name} exited with code {code}; stopping container.",
                        file=sys.stderr,
                        flush=True,
                    )
                    exit_code = code or 1
                    _request_stop()
                    break
            time.sleep(0.5)
    finally:
        _shutdown()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
