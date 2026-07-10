from __future__ import annotations

import multiprocessing
import tempfile
import unittest
from pathlib import Path


def _append_entries(history_path: str, lock_path: str, prefix: str, count: int) -> None:
    import app.jobs as jobs

    jobs.HISTORY_PATH = Path(history_path)
    jobs.HISTORY_LOCK_PATH = Path(lock_path)
    for index in range(count):
        jobs._append_history({"id": f"{prefix}-{index}", "created_at": "2026-07-09T00:00:00+00:00"})


class HistoryLockTests(unittest.TestCase):
    def test_parallel_process_updates_are_not_lost(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history_path = str(Path(tmp) / "jobs.json")
            lock_path = str(Path(tmp) / "jobs.lock")
            context = multiprocessing.get_context("spawn")
            processes = [
                context.Process(target=_append_entries, args=(history_path, lock_path, f"worker-{worker}", 15))
                for worker in range(4)
            ]
            for process in processes:
                process.start()
            for process in processes:
                process.join(30)
                self.assertEqual(process.exitcode, 0)

            import app.jobs as jobs

            jobs.HISTORY_PATH = Path(history_path)
            jobs.HISTORY_LOCK_PATH = Path(lock_path)
            entries = jobs._read_history()
            self.assertEqual(len(entries), 60)
            self.assertEqual(len({entry["id"] for entry in entries}), 60)


if __name__ == "__main__":
    unittest.main()
