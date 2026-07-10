from __future__ import annotations

import io
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image

import app.main as main


class EndpointAuthTests(unittest.TestCase):
    @staticmethod
    def _png() -> bytes:
        payload = io.BytesIO()
        Image.new("RGB", (4, 4), "white").save(payload, format="PNG")
        return payload.getvalue()

    def test_clear_history_rejects_invalid_key_before_mutation(self) -> None:
        with patch.object(main, "API_KEY", "test-secret"):
            with self.assertRaises(HTTPException) as raised:
                main.api_clear_jobs(x_api_key="wrong", authorization=None)
        self.assertEqual(raised.exception.status_code, 401)

    def test_delete_history_rejects_invalid_key_before_mutation(self) -> None:
        with patch.object(main, "API_KEY", "test-secret"):
            with self.assertRaises(HTTPException) as raised:
                main.api_delete_job("missing", x_api_key=None, authorization="Bearer wrong")
        self.assertEqual(raised.exception.status_code, 401)

    def test_processing_and_result_routes_require_configured_key(self) -> None:
        client = TestClient(main.app)
        with patch.object(main, "API_KEY", "test-secret"):
            for route in ("/api/upscale", "/api/remove-background", "/api/remove-background-upscale"):
                response = client.post(route, files={"image": ("tiny.png", self._png(), "image/png")})
                self.assertEqual(response.status_code, 401, (route, response.text))
            response = client.get("/api/results/missing")
            self.assertEqual(response.status_code, 401, response.text)
            response = client.get("/api/results/missing/listing-pack")
            self.assertEqual(response.status_code, 401, response.text)


if __name__ == "__main__":
    unittest.main()
