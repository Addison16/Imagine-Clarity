from __future__ import annotations

import io
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from app import background, upscaler
from app.background import BackgroundOptions
from app.upscaler import UpscaleOptions


class ProviderFailureTests(unittest.TestCase):
    @staticmethod
    def _png() -> bytes:
        buffer = io.BytesIO()
        Image.new("RGB", (8, 8), "white").save(buffer, format="PNG")
        return buffer.getvalue()

    def test_background_session_initialization_error_is_translated(self) -> None:
        fake_rembg = SimpleNamespace(
            new_session=lambda *args, **kwargs: (_ for _ in ()).throw(OSError("provider failed")),
            remove=lambda *args, **kwargs: b"",
        )
        background._session_cache.clear()
        with (
            patch.dict(sys.modules, {"rembg": fake_rembg}),
            patch("app.background._select_onnx_providers", return_value=["CPUExecutionProvider"]),
        ):
            with self.assertRaisesRegex(RuntimeError, "provider initialization failed"):
                background.remove_background(self._png(), BackgroundOptions(model="accurate", device="cpu"))

    def test_background_provider_selection_error_is_translated(self) -> None:
        fake_rembg = SimpleNamespace(new_session=lambda *args, **kwargs: None, remove=lambda *args, **kwargs: b"")
        with (
            patch.dict(sys.modules, {"rembg": fake_rembg}),
            patch("app.background._select_onnx_providers", side_effect=OSError("discovery failed")),
        ):
            with self.assertRaisesRegex(RuntimeError, "provider selection failed"):
                background.remove_background(self._png(), BackgroundOptions(model="accurate", device="cpu"))

    def test_upscaler_download_error_is_translated(self) -> None:
        upscaler._upsampler_cache.clear()
        with patch("app.upscaler._download_model", side_effect=OSError("download failed")):
            with self.assertRaisesRegex(RuntimeError, "initialization failed"):
                upscaler._neural_resize(Image.new("RGB", (8, 8), "white"), UpscaleOptions(mode="photo", device="cpu"))


if __name__ == "__main__":
    unittest.main()
