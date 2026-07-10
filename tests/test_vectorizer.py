from __future__ import annotations

import io
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from app.vectorizer import VectorizeOptions, normalize_vector_options, vectorize_image


class VectorPresetTests(unittest.TestCase):
    def test_line_art_uses_binary_defaults(self) -> None:
        options = normalize_vector_options(VectorizeOptions(preset="line-art"))
        self.assertEqual(options.colormode, "binary")
        self.assertEqual(options.mode, "spline")
        self.assertEqual(options.filter_speckle, 3)
        self.assertEqual(options.path_precision, 3)

    def test_explicit_values_override_preset_defaults(self) -> None:
        options = normalize_vector_options(
            VectorizeOptions(
                preset="photo",
                colormode="binary",
                mode="polygon",
                filter_speckle=2,
                path_precision=7,
            )
        )
        self.assertEqual(options.colormode, "binary")
        self.assertEqual(options.mode, "polygon")
        self.assertEqual(options.filter_speckle, 2)
        self.assertEqual(options.path_precision, 7)

    def test_numeric_values_are_clamped(self) -> None:
        options = normalize_vector_options(
            VectorizeOptions(preset="logo", color_precision=99, layer_difference=-10)
        )
        self.assertEqual(options.color_precision, 8)
        self.assertEqual(options.layer_difference, 0)

    def test_unknown_preset_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Vector preset must be one of"):
            normalize_vector_options(VectorizeOptions(preset="unknown"))

    def test_malformed_svg_output_is_rejected(self) -> None:
        source = io.BytesIO()
        Image.new("RGB", (4, 4), "white").save(source, format="PNG")
        fake_vtracer = SimpleNamespace(convert_raw_image_to_svg=lambda *args, **kwargs: "NOT XML\n<svg xmlns='http://www.w3.org/2000/svg'/>")
        with patch.dict(sys.modules, {"vtracer": fake_vtracer}):
            with self.assertRaisesRegex(RuntimeError, "malformed SVG"):
                vectorize_image(source.getvalue(), VectorizeOptions())


if __name__ == "__main__":
    unittest.main()
