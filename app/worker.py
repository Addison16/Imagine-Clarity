from __future__ import annotations

import logging
import multiprocessing
import os

from rq import Worker

from app import tasks  # noqa: F401 - imported so RQ can resolve queued task callables.
from app.job_queue import QUEUE_NAME, image_queue, rq_redis_client

logger = logging.getLogger(__name__)


def run_worker(name: str | None = None) -> None:
    queue = image_queue()
    worker = Worker([queue], connection=rq_redis_client(), name=name)
    logger.info("Starting Clarity worker %s on queue %s", worker.name, QUEUE_NAME)
    worker.work(with_scheduler=True)


def main() -> None:
    concurrency = max(1, int(os.getenv("WORKER_CONCURRENCY", "1")))
    if concurrency == 1:
        run_worker(os.getenv("WORKER_NAME"))
        return

    workers: list[multiprocessing.Process] = []
    for index in range(concurrency):
        name = os.getenv("WORKER_NAME", "clarity-worker")
        process = multiprocessing.Process(target=run_worker, args=(f"{name}-{index + 1}",), daemon=False)
        process.start()
        workers.append(process)

    for process in workers:
        process.join()


if __name__ == "__main__":
    main()
