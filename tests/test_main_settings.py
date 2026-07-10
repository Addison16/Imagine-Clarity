from __future__ import annotations

import unittest

from fastapi import HTTPException

from app.main import _build_tool_settings, _validate_input_resolution, _validate_upscale_resolution, _validate_vector_resolution
from app.upscaler import UpscaleOptions


class ToolSettingsDeviceTests(unittest.TestCase):
    def _common(self) -> dict[str, object]:
        return {
            "metadata": {"width": 64, "height": 48, "mode": "RGB", "has_alpha": False},
            "scale": 2.0,
            "mode": "conservative",
            "face_enhance": False,
            "denoise": 0.55,
            "tile": 256,
            "device": "legacy-invalid",
            "output_format": "png",
            "target_width": None,
            "target_height": None,
            "resize_method": "lanczos",
            "target_fit": "stretch",
            "canvas_width": None,
            "canvas_height": None,
            "canvas_anchor": "center",
            "dpi": None,
            "export_quality": 95,
            "sharpen_amount": 70,
            "model": "logo",
            "cut_mode": "balanced",
            "alpha_matting": False,
            "edge_refine": 8,
            "edge_trim": 0,
            "fringe_cleanup": 0,
            "inner_cleanup": 0,
            "background_tolerance": 34,
            "post_process_mask": True,
            "preserve_interior": True,
            "respect_existing_alpha": True,
            "upscale_device": "cpu",
            "background_device": "cpu",
        }

    def test_separate_devices_override_legacy_device(self) -> None:
        common = self._common()
        upscale = _build_tool_settings(normalized_tool="upscale", **common)
        background = _build_tool_settings(normalized_tool="remove-background", **common)
        combined = _build_tool_settings(normalized_tool="remove-background-upscale", **common)

        self.assertEqual(upscale["device"], "cpu")
        self.assertEqual(background["device"], "cpu")
        self.assertEqual(combined["upscale"]["device"], "cpu")
        self.assertEqual(combined["background"]["device"], "cpu")

    def test_legacy_device_remains_the_fallback(self) -> None:
        common = self._common()
        common.update(device="cpu", upscale_device=None, background_device=None)
        upscale = _build_tool_settings(normalized_tool="upscale", **common)
        background = _build_tool_settings(normalized_tool="remove-background", **common)
        combined = _build_tool_settings(normalized_tool="remove-background-upscale", **common)

        self.assertEqual(upscale["device"], "cpu")
        self.assertEqual(background["device"], "cpu")
        self.assertEqual(combined["upscale"]["device"], "cpu")
        self.assertEqual(combined["background"]["device"], "cpu")


class PixelLimitTests(unittest.TestCase):
    def test_general_pixel_limit_rejects_large_decoded_image(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            _validate_input_resolution({"width": 8001, "height": 8000})
        self.assertEqual(raised.exception.status_code, 413)

    def test_vector_pixel_limit_is_lower(self) -> None:
        with self.assertRaisesRegex(ValueError, "Maximum vector input area"):
            _validate_vector_resolution({"width": 5001, "height": 5000})

    def test_crop_intermediate_is_bounded(self) -> None:
        options = UpscaleOptions(target_width=1000, target_height=16000, target_fit="crop")
        with self.assertRaisesRegex(ValueError, "intermediate"):
            _validate_upscale_resolution({"width": 16000, "height": 2000}, options)


if __name__ == "__main__":
    unittest.main()
