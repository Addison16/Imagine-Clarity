from __future__ import annotations

import unittest

from app.queued_jobs import _apply_quick_fix, _validate_job_limits, _validated_settings


class QueueSettingsTests(unittest.TestCase):
    def test_vector_quick_fix_is_rejected(self) -> None:
        settings = _validated_settings("vectorize", {})
        with self.assertRaisesRegex(ValueError, "not supported"):
            _apply_quick_fix("vectorize", settings, "fix-white-halo")

    def test_background_fix_is_rejected_for_upscale(self) -> None:
        settings = _validated_settings("upscale", {})
        with self.assertRaisesRegex(ValueError, "background-removal"):
            _apply_quick_fix("upscale", settings, "remove-leftover-background")

    def test_empty_vector_settings_resolve_to_valid_defaults(self) -> None:
        settings = _validated_settings("vectorize", {})
        self.assertEqual(settings["preset"], "logo")
        self.assertEqual(settings["colormode"], "color")

    def test_invalid_vector_preset_is_rejected_before_enqueue(self) -> None:
        with self.assertRaisesRegex(ValueError, "Vector preset"):
            _validated_settings("vectorize", {"preset": "invalid"})

    def test_unexpected_setting_is_reported_as_validation_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid settings"):
            _validated_settings("upscale", {"not_a_real_setting": True})

    def test_reprocessed_vector_job_respects_pixel_limit(self) -> None:
        settings = _validated_settings("vectorize", {})
        with self.assertRaisesRegex(ValueError, "Maximum vector input area"):
            _validate_job_limits("vectorize", {"width": 5001, "height": 5000}, settings)

    def test_reprocessed_upscale_job_respects_output_limit(self) -> None:
        settings = _validated_settings("upscale", {"target_width": 100000, "target_height": 100000})
        with self.assertRaisesRegex(ValueError, "Maximum raster resolution"):
            _validate_job_limits("upscale", {"width": 100, "height": 100}, settings)

    def test_reprocessed_crop_job_respects_intermediate_limit(self) -> None:
        settings = _validated_settings(
            "upscale",
            {"target_width": 1000, "target_height": 16000, "target_fit": "crop"},
        )
        with self.assertRaisesRegex(ValueError, "intermediate"):
            _validate_job_limits("upscale", {"width": 16000, "height": 2000}, settings)

    def test_wrong_setting_types_are_validation_errors(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid settings"):
            _validated_settings("upscale", {"mode": 123})
        with self.assertRaisesRegex(ValueError, "must be a JSON object"):
            _validated_settings("remove-background-upscale", {"background": "bad"})
        with self.assertRaisesRegex(ValueError, "Unknown combined setting"):
            _validated_settings("remove-background-upscale", {"unknown": {}})


if __name__ == "__main__":
    unittest.main()
