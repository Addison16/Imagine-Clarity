from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from redis import Redis
from rq import Queue, Worker
from rq.job import Job
from rq.registry import FailedJobRegistry, StartedJobRegistry

from app.jobs import get_job

STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "/tmp/upscaler"))
QUEUE_DIR = STORAGE_DIR / "queued"
BATCH_DIR = STORAGE_DIR / "batches"

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE_NAME = os.getenv("RQ_QUEUE_NAME", "image-jobs")
REDIS_PREFIX = os.getenv("CLARITY_REDIS_PREFIX", "clarity")
QUEUE_HISTORY_LIMIT = int(os.getenv("QUEUE_HISTORY_LIMIT", "100"))
BATCH_HISTORY_LIMIT = int(os.getenv("BATCH_HISTORY_LIMIT", "50"))
JOB_TIMEOUT_SECONDS = int(os.getenv("JOB_TIMEOUT_SECONDS", "7200"))

JOB_INDEX_KEY = f"{REDIS_PREFIX}:jobs"
BATCH_INDEX_KEY = f"{REDIS_PREFIX}:batches"

_redis_text: Redis | None = None
_redis_rq: Redis | None = None


def redis_client() -> Redis:
    global _redis_text
    if _redis_text is None:
        _redis_text = Redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_text


def rq_redis_client() -> Redis:
    global _redis_rq
    if _redis_rq is None:
        _redis_rq = Redis.from_url(REDIS_URL)
    return _redis_rq


def image_queue() -> Queue:
    return Queue(QUEUE_NAME, connection=rq_redis_client(), default_timeout=JOB_TIMEOUT_SECONDS)


def create_job_id() -> str:
    return uuid.uuid4().hex


def create_batch_id() -> str:
    return uuid.uuid4().hex


def job_key(job_id: str) -> str:
    return f"{REDIS_PREFIX}:job:{job_id}"


def batch_key(batch_id: str) -> str:
    return f"{REDIS_PREFIX}:batch:{batch_id}"


def event_channel(kind: str, item_id: str) -> str:
    if kind not in {"job", "batch"}:
        raise ValueError("kind must be job or batch")
    return f"{REDIS_PREFIX}:events:{kind}:{item_id}"


def enqueue_single_job(job_id: str) -> str:
    from app.tasks import process_single_job

    rq_job = image_queue().enqueue(
        process_single_job,
        job_id,
        job_id=f"single-{job_id}",
        job_timeout=JOB_TIMEOUT_SECONDS,
        result_ttl=86400,
        failure_ttl=604800,
    )
    update_job(job_id, {"rq_job_id": rq_job.id, "phase": "queued", "message": "Waiting for a worker.", "current_progress": 5, "percent": 5})
    return rq_job.id


def enqueue_batch_job(batch_id: str) -> str:
    from app.tasks import process_batch_job

    rq_job = image_queue().enqueue(
        process_batch_job,
        batch_id,
        job_id=f"batch-{batch_id}",
        job_timeout=JOB_TIMEOUT_SECONDS,
        result_ttl=86400,
        failure_ttl=604800,
    )
    update_batch(batch_id, {"rq_job_id": rq_job.id, "phase": "queued", "message": "Waiting for a worker.", "current_progress": 5, "percent": 5})
    return rq_job.id


def store_job(entry: dict[str, Any]) -> dict[str, Any]:
    client = redis_client()
    safe = _json_safe(entry)
    client.set(job_key(str(safe["id"])), json.dumps(safe))
    client.zadd(JOB_INDEX_KEY, {str(safe["id"]): _timestamp(str(safe.get("created_at") or _now()))})
    _trim_index(JOB_INDEX_KEY, QUEUE_HISTORY_LIMIT, _delete_job_storage)
    _publish("job", str(safe["id"]), public_job(safe))
    return safe


def get_raw_job(job_id: str) -> dict[str, Any] | None:
    raw = redis_client().get(job_key(job_id))
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def update_job(job_id: str, patch: dict[str, Any], *, publish: bool = True) -> dict[str, Any] | None:
    raw = get_raw_job(job_id)
    if not raw:
        return None
    raw.update(_json_safe(patch))
    raw["updated_at"] = _now()
    _normalize_progress_fields(raw)
    redis_client().set(job_key(job_id), json.dumps(raw))
    if publish:
        _publish("job", job_id, public_job(raw))
    return raw


def list_raw_jobs(limit: int = 25, include_done: bool = False) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit), QUEUE_HISTORY_LIMIT))
    ids = redis_client().zrevrange(JOB_INDEX_KEY, 0, max(safe_limit * 3, safe_limit) - 1)
    jobs: list[dict[str, Any]] = []
    for job_id in ids:
        raw = get_raw_job(str(job_id))
        if not raw:
            continue
        if include_done or raw.get("status") != "done":
            jobs.append(raw)
        if len(jobs) >= safe_limit:
            break
    return jobs


def list_public_jobs(limit: int = 25, include_done: bool = False) -> list[dict[str, Any]]:
    return [public_job(raw) for raw in list_raw_jobs(limit, include_done)]


def public_job(job: dict[str, Any]) -> dict[str, Any]:
    job_id = str(job.get("id") or "")
    server_time = _now()
    percent = _percent(job)
    public: dict[str, Any] = {
        "id": job_id,
        "queue_job_id": job_id,
        "rq_job_id": job.get("rq_job_id"),
        "kind": "queued",
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "started_at": job.get("started_at"),
        "finished_at": job.get("finished_at"),
        "status": job.get("status") or "queued",
        "phase": job.get("phase") or job.get("status") or "queued",
        "message": job.get("message") or _default_message(str(job.get("status") or "queued")),
        "current_progress": int(job.get("current_progress") or percent),
        "max_progress": int(job.get("max_progress") or 100),
        "percent": percent,
        "progress": percent,
        "tool": job.get("tool") or "upscale",
        "source_filename": job.get("source_filename") or "image",
        "source_url": f"/api/jobs/{job_id}/source" if job_id else None,
        "error": job.get("error"),
        "server_time": server_time,
        "elapsed_seconds": _elapsed_seconds(job, server_time),
        "worker_id": job.get("worker_id"),
        "queue_position": queue_position(str(job.get("rq_job_id") or "")),
    }
    if job.get("input"):
        public["input"] = job["input"]
    if job.get("output"):
        public["output"] = job["output"]
    if job.get("engine"):
        public["engine"] = job["engine"]
    if job.get("result_job_id"):
        public["result_job_id"] = job["result_job_id"]
        public["download_url"] = job.get("result_download_url")
        public["source_download_url"] = job.get("result_source_url")
        public["filename"] = job.get("result_filename")
        saved = get_job(str(job["result_job_id"]))
        if saved:
            public.update(
                {
                    "download_url": saved.get("download_url"),
                    "source_download_url": saved.get("source_download_url"),
                    "filename": saved.get("filename"),
                    "output": saved.get("output"),
                    "engine": saved.get("engine"),
                }
            )
    return public


def delete_job_meta(job_id: str) -> dict[str, Any] | None:
    raw = get_raw_job(job_id)
    if not raw:
        return None
    if raw.get("status") == "running":
        return {"deleted": False, "reason": "running", "job": public_job(raw)}
    _delete_rq_job(str(raw.get("rq_job_id") or ""))
    _delete_job_storage(job_id)
    redis_client().delete(job_key(job_id))
    redis_client().zrem(JOB_INDEX_KEY, job_id)
    return {"deleted": True, "deleted_jobs": 1, "deleted_files": 1, "job": public_job(raw)}


def clear_job_meta() -> dict[str, Any]:
    deleted = 0
    kept_running = 0
    for raw in list_raw_jobs(QUEUE_HISTORY_LIMIT, include_done=True):
        job_id = str(raw.get("id") or "")
        if raw.get("status") == "running":
            kept_running += 1
            continue
        _delete_rq_job(str(raw.get("rq_job_id") or ""))
        _delete_job_storage(job_id)
        redis_client().delete(job_key(job_id))
        redis_client().zrem(JOB_INDEX_KEY, job_id)
        deleted += 1
    return {"deleted_jobs": deleted, "deleted_files": deleted, "kept_running": kept_running}


def queued_source_path(job_id: str) -> Path | None:
    raw = get_raw_job(job_id)
    if not raw:
        return None
    source = Path(str(raw.get("source_path", "")))
    source_dir = QUEUE_DIR / job_id / "source"
    try:
        if source.exists() and source.is_file() and source.resolve().is_relative_to(source_dir.resolve()):
            return source
    except (OSError, ValueError):
        return None
    return None


def store_batch(entry: dict[str, Any]) -> dict[str, Any]:
    client = redis_client()
    safe = _json_safe(entry)
    client.set(batch_key(str(safe["id"])), json.dumps(safe))
    client.zadd(BATCH_INDEX_KEY, {str(safe["id"]): _timestamp(str(safe.get("created_at") or _now()))})
    _trim_index(BATCH_INDEX_KEY, BATCH_HISTORY_LIMIT, _delete_batch_storage)
    _publish("batch", str(safe["id"]), public_batch(safe))
    return safe


def get_raw_batch(batch_id: str) -> dict[str, Any] | None:
    raw = redis_client().get(batch_key(batch_id))
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def update_batch(batch_id: str, patch: dict[str, Any], *, publish: bool = True) -> dict[str, Any] | None:
    raw = get_raw_batch(batch_id)
    if not raw:
        return None
    raw.update(_json_safe(patch))
    raw["updated_at"] = _now()
    _recount_batch(raw)
    _normalize_progress_fields(raw)
    redis_client().set(batch_key(batch_id), json.dumps(raw))
    if publish:
        _publish("batch", batch_id, public_batch(raw))
    return raw


def update_batch_item(batch_id: str, item_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    raw = get_raw_batch(batch_id)
    if not raw:
        return None
    for item in raw.get("items", []):
        if str(item.get("id")) == str(item_id):
            item.update(_json_safe(patch))
            item["updated_at"] = _now()
            break
    raw["updated_at"] = _now()
    _recount_batch(raw)
    _normalize_progress_fields(raw)
    redis_client().set(batch_key(batch_id), json.dumps(raw))
    _publish("batch", batch_id, public_batch(raw))
    return raw


def list_raw_batches(limit: int = 10) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit), BATCH_HISTORY_LIMIT))
    ids = redis_client().zrevrange(BATCH_INDEX_KEY, 0, safe_limit - 1)
    batches: list[dict[str, Any]] = []
    for batch_id in ids:
        raw = get_raw_batch(str(batch_id))
        if raw:
            batches.append(raw)
    return batches


def list_public_batches(limit: int = 10) -> list[dict[str, Any]]:
    return [public_batch(raw) for raw in list_raw_batches(limit)]


def public_batch(batch: dict[str, Any]) -> dict[str, Any]:
    batch_id = str(batch.get("id") or "")
    server_time = _now()
    redacted = dict(batch)
    percent = _percent(redacted)
    redacted["zip_url"] = f"/api/batches/{batch_id}/zip" if batch_id else None
    redacted["server_time"] = server_time
    redacted["elapsed_seconds"] = _elapsed_seconds(redacted, server_time)
    redacted["phase"] = redacted.get("phase") or redacted.get("status") or "queued"
    redacted["message"] = redacted.get("message") or _default_message(str(redacted.get("status") or "queued"))
    redacted["current_progress"] = int(redacted.get("current_progress") or percent)
    redacted["max_progress"] = int(redacted.get("max_progress") or 100)
    redacted["percent"] = percent
    redacted["progress"] = percent
    redacted["queue_position"] = queue_position(str(redacted.get("rq_job_id") or ""))
    redacted.pop("settings", None)
    items: list[dict[str, Any]] = []
    for item in batch.get("items", []):
        clean = dict(item)
        item_id = str(clean.get("id") or "")
        if batch_id and item_id:
            clean["source_url"] = f"/api/batches/{batch_id}/source/{item_id}"
        clean.pop("source_path", None)
        items.append(clean)
    redacted["items"] = items
    return redacted


def batch_source_path(batch_id: str, item_id: str) -> Path | None:
    batch = get_raw_batch(batch_id)
    if not batch:
        return None
    for item in batch.get("items", []):
        if str(item.get("id")) != str(item_id):
            continue
        source = Path(str(item.get("source_path", "")))
        batch_dir = BATCH_DIR / batch_id / "source"
        try:
            if source.exists() and source.is_file() and source.resolve().is_relative_to(batch_dir.resolve()):
                return source
        except (OSError, ValueError):
            return None
    return None


def queue_position(rq_job_id: str) -> int | None:
    if not rq_job_id:
        return None
    try:
        for index, queued_id in enumerate(image_queue().get_job_ids()):
            if queued_id == rq_job_id:
                return index + 1
    except Exception:
        return None
    return None


def refresh_job_from_rq(job_id: str) -> dict[str, Any] | None:
    raw = get_raw_job(job_id)
    if not raw or raw.get("status") not in {"queued", "running"}:
        return raw
    rq_status = rq_job_status(str(raw.get("rq_job_id") or ""))
    if rq_status in {"failed", "stopped", "canceled", "cancelled"}:
        return update_job(
            job_id,
            {
                "status": "error",
                "phase": "worker-stopped",
                "message": "Worker stopped before finishing. Retry this job from History.",
                "current_progress": 100,
                "percent": 100,
                "finished_at": _now(),
                "error": f"RQ job is {rq_status}.",
            },
        )
    return raw


def refresh_batch_from_rq(batch_id: str) -> dict[str, Any] | None:
    raw = get_raw_batch(batch_id)
    if not raw or raw.get("status") not in {"queued", "running"}:
        return raw
    rq_status = rq_job_status(str(raw.get("rq_job_id") or ""))
    if rq_status in {"failed", "stopped", "canceled", "cancelled"}:
        return update_batch(
            batch_id,
            {
                "status": "error",
                "phase": "worker-stopped",
                "message": "Worker stopped before finishing. Retry this batch from History.",
                "current_progress": 100,
                "percent": 100,
                "finished_at": _now(),
                "error": f"RQ job is {rq_status}.",
            },
        )
    return raw


def rq_job_status(rq_job_id: str) -> str | None:
    if not rq_job_id:
        return None
    try:
        job = Job.fetch(rq_job_id, connection=rq_redis_client())
        status = job.get_status(refresh=True)
    except Exception:
        return None
    value = getattr(status, "value", str(status))
    return str(value).replace("JobStatus.", "").lower()


def queue_health() -> dict[str, Any]:
    health: dict[str, Any] = {
        "redis_url": _redacted_redis_url(),
        "queue": QUEUE_NAME,
        "redis_connected": False,
        "queue_depth": None,
        "started_count": None,
        "failed_count": None,
        "workers": [],
    }
    try:
        redis_client().ping()
        rq_conn = rq_redis_client()
        queue = image_queue()
        started = StartedJobRegistry(queue.name, connection=rq_conn)
        failed = FailedJobRegistry(queue.name, connection=rq_conn)
        started_count = started.count() if callable(getattr(started, "count", None)) else started.count
        failed_count = failed.count() if callable(getattr(failed, "count", None)) else failed.count
        health.update(
            {
                "redis_connected": True,
                "queue_depth": len(queue),
                "started_count": started_count,
                "failed_count": failed_count,
            }
        )
        workers = []
        for worker in Worker.all(connection=rq_conn):
            workers.append(
                {
                    "name": worker.name,
                    "state": str(getattr(worker, "state", "")),
                    "queues": [queue.name for queue in getattr(worker, "queues", [])],
                    "last_heartbeat": _datetime_to_iso(getattr(worker, "last_heartbeat", None)),
                    "birth_date": _datetime_to_iso(getattr(worker, "birth_date", None)),
                }
            )
        health["workers"] = workers
    except Exception as exc:
        health["error"] = str(exc)
    return health


def snapshot(kind: str, item_id: str) -> dict[str, Any] | None:
    if kind == "job":
        raw = get_raw_job(item_id)
        return {"type": "job", "job": public_job(raw)} if raw else None
    if kind == "batch":
        raw = get_raw_batch(item_id)
        return {"type": "batch", "batch": public_batch(raw)} if raw else None
    return None


def safe_filename(filename: str) -> str:
    import re

    clean = re.sub(r"[^A-Za-z0-9_.-]+", "-", Path(filename).name).strip("-")
    return clean or "image.png"


def now() -> str:
    return _now()


def _publish(kind: str, item_id: str, payload: dict[str, Any]) -> None:
    try:
        redis_client().publish(event_channel(kind, item_id), json.dumps({"type": kind, kind: payload}))
    except Exception:
        return


def _delete_rq_job(rq_job_id: str) -> None:
    if not rq_job_id:
        return
    try:
        job = Job.fetch(rq_job_id, connection=rq_redis_client())
        job.cancel()
        job.delete()
    except Exception:
        return


def _trim_index(index_key: str, limit: int, delete_storage) -> None:
    client = redis_client()
    count = int(client.zcard(index_key) or 0)
    if count <= limit:
        return
    overflow = client.zrange(index_key, 0, count - limit - 1)
    for item_id in overflow:
        delete_storage(str(item_id))
        client.delete(job_key(str(item_id)) if index_key == JOB_INDEX_KEY else batch_key(str(item_id)))
        client.zrem(index_key, str(item_id))


def _delete_job_storage(job_id: str) -> None:
    if not job_id or Path(job_id).name != job_id:
        return
    path = QUEUE_DIR / job_id
    try:
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
    except OSError:
        return


def _delete_batch_storage(batch_id: str) -> None:
    if not batch_id or Path(batch_id).name != batch_id:
        return
    path = BATCH_DIR / batch_id
    try:
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
    except OSError:
        return


def _recount_batch(batch: dict[str, Any]) -> None:
    items = batch.get("items") or []
    batch["total"] = len(items)
    batch["completed"] = sum(1 for item in items if item.get("status") == "done")
    batch["failed"] = sum(1 for item in items if item.get("status") == "error")


def _normalize_progress_fields(item: dict[str, Any]) -> None:
    if "percent" not in item and "progress" in item:
        item["percent"] = item.get("progress")
    if "current_progress" not in item:
        item["current_progress"] = item.get("percent", item.get("progress", 0))
    if "max_progress" not in item:
        item["max_progress"] = 100
    item["percent"] = _percent(item)
    item["progress"] = item["percent"]


def _percent(item: dict[str, Any]) -> int:
    if "percent" in item:
        return max(0, min(100, int(round(float(item.get("percent") or 0)))))
    current = float(item.get("current_progress") or item.get("progress") or 0)
    maximum = float(item.get("max_progress") or 100)
    if maximum <= 0:
        return 0
    return max(0, min(100, int(round((current / maximum) * 100))))


def _default_message(status: str) -> str:
    return {
        "queued": "Waiting for a worker.",
        "running": "Processing on the server.",
        "done": "Complete.",
        "completed": "Complete.",
        "error": "Processing failed.",
    }.get(status, "Waiting for status.")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timestamp(value: str) -> float:
    parsed = _parse_time(value)
    return parsed.timestamp() if parsed else datetime.now(timezone.utc).timestamp()


def _elapsed_seconds(item: dict[str, Any], server_time: str) -> int:
    start = _parse_time(str(item.get("started_at") or item.get("created_at") or ""))
    end = _parse_time(str(item.get("finished_at") or server_time))
    if not start or not end:
        return 0
    return max(0, int((end - start).total_seconds()))


def _parse_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _datetime_to_iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return str(value) if value else None


def _redacted_redis_url() -> str:
    if "@" not in REDIS_URL:
        return REDIS_URL
    scheme, rest = REDIS_URL.split("://", 1)
    _, host = rest.rsplit("@", 1)
    return f"{scheme}://***@{host}"


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
