from __future__ import annotations

import io
import unittest

from fastapi.testclient import TestClient
from PIL import Image

import app.main as main


class ApiValidationTests(unittest.TestCase):
    @staticmethod
    def _png() -> bytes:
        payload = io.BytesIO()
        Image.new("RGB", (8, 8), "white").save(payload, format="PNG")
        return payload.getvalue()

    def setUp(self) -> None:
        self.client = TestClient(main.app)

    def test_queue_invalid_background_model_returns_400(self) -> None:
        response = self.client.post(
            "/api/jobs/queue",
            files={"image": ("tiny.png", self._png(), "image/png")},
            data={"tool": "remove-background", "model": "not-a-model"},
        )
        self.assertEqual(response.status_code, 400, response.text)

    def test_batch_invalid_background_model_returns_400(self) -> None:
        response = self.client.post(
            "/api/batches",
            files=[("images", ("tiny.png", self._png(), "image/png"))],
            data={"tool": "remove-background", "model": "not-a-model"},
        )
        self.assertEqual(response.status_code, 400, response.text)

    def test_combined_batch_rejects_opaque_output_format(self) -> None:
        response = self.client.post(
            "/api/batches",
            files=[("images", ("tiny.png", self._png(), "image/png"))],
            data={"tool": "remove-background-upscale", "output_format": "jpeg"},
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("transparency", response.text.lower())


if __name__ == "__main__":
    unittest.main()
