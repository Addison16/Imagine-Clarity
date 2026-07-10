from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from app import jobs
from app.jobs import build_quality_report


class QualityReportTests(unittest.TestCase):
    @staticmethod
    def _png(color: tuple[int, int, int, int]) -> bytes:
        image = Image.new("RGBA", (32, 32), color)
        output = io.BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()

    def test_opaque_rgba_is_not_reported_as_transparent(self) -> None:
        data = self._png((20, 40, 60, 255))
        report = build_quality_report(
            input_metadata={"width": 32, "height": 32},
            output_data=data,
            output_width=32,
            output_height=32,
            output_format="png",
            output_size_bytes=len(data),
            tool="remove-background",
            settings={},
        )
        self.assertTrue(report["has_alpha"])
        self.assertFalse(report["has_transparency"])
        self.assertNotIn("Likely shop-ready", report["verdict"])

    def test_transparent_pixels_are_detected(self) -> None:
        data = self._png((20, 40, 60, 0))
        report = build_quality_report(
            input_metadata={"width": 32, "height": 32},
            output_data=data,
            output_width=32,
            output_height=32,
            output_format="png",
            output_size_bytes=len(data),
            tool="remove-background",
            settings={},
        )
        self.assertTrue(report["has_transparency"])

    def test_oversized_transparent_result_does_not_advertise_listing_pack(self) -> None:
        data = self._png((20, 40, 60, 0))
        with tempfile.TemporaryDirectory() as directory, patch.object(jobs, "OUTPUT_DIR", Path(directory)), patch.object(
            jobs, "_append_history"
        ):
            saved = jobs.save_job_result(
                tool="remove-background",
                source_filename="shirt.png",
                output_filename="shirt-transparent.png",
                data=data,
                input_metadata={"width": 32, "height": 32, "mode": "RGBA", "has_alpha": True},
                output_width=4800,
                output_height=5400,
                output_format="png",
                engine="test",
                settings={},
            )
        self.assertNotIn("listing_pack_url", saved)


if __name__ == "__main__":
    unittest.main()
