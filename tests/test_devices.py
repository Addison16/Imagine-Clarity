from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.devices import _tensorrt_runtime_available, normalize_device, select_torch_device, usable_onnx_providers


class _FakeCuda:
    def __init__(self, available: bool) -> None:
        self._available = available

    def is_available(self) -> bool:
        return self._available


class _FakeMps:
    def __init__(self, available: bool) -> None:
        self._available = available

    def is_available(self) -> bool:
        return self._available


class _FakeTorch:
    def __init__(self, *, cuda: bool = False, mps: bool = False) -> None:
        self.cuda = _FakeCuda(cuda)
        self.backends = SimpleNamespace(mps=_FakeMps(mps))

    @staticmethod
    def device(value: str) -> str:
        return value


class DeviceSelectionTests(unittest.TestCase):
    def test_normalize_device_uses_environment_for_auto(self) -> None:
        with patch.dict(os.environ, {"UPSCALER_DEVICE": "gpu"}, clear=False):
            self.assertEqual(normalize_device("auto"), "cuda")

    def test_auto_prefers_cuda_then_mps_then_cpu(self) -> None:
        with patch.dict(os.environ, {"UPSCALER_DEVICE": "auto"}, clear=False):
            self.assertEqual(select_torch_device(_FakeTorch(cuda=True), "auto"), "cuda")
            self.assertEqual(select_torch_device(_FakeTorch(mps=True), "auto"), "mps")
            self.assertEqual(select_torch_device(_FakeTorch(), "auto"), "cpu")

    def test_background_only_provider_is_rejected_for_upscaling(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "available only for background removal"):
            select_torch_device(_FakeTorch(cuda=True), "tensorrt")

    def test_explicit_cuda_requires_cuda_visibility(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "CUDA is not available"):
            select_torch_device(_FakeTorch(cuda=False), "cuda")

    def test_unloadable_tensorrt_provider_is_not_advertised(self) -> None:
        ort = SimpleNamespace(
            get_available_providers=lambda: [
                "TensorrtExecutionProvider",
                "CUDAExecutionProvider",
                "CPUExecutionProvider",
            ]
        )
        with patch("app.devices._tensorrt_runtime_available", return_value=False):
            self.assertEqual(
                usable_onnx_providers(ort),
                ["CUDAExecutionProvider", "CPUExecutionProvider"],
            )

    def test_loadable_tensorrt_provider_is_retained(self) -> None:
        ort = SimpleNamespace(get_available_providers=lambda: ["TensorrtExecutionProvider", "CPUExecutionProvider"])
        with patch("app.devices._tensorrt_runtime_available", return_value=True):
            self.assertEqual(
                usable_onnx_providers(ort),
                ["TensorrtExecutionProvider", "CPUExecutionProvider"],
            )

    def test_tensorrt_requires_explicit_opt_in(self) -> None:
        with patch.dict(os.environ, {"ENABLE_TENSORRT_PROVIDER": ""}, clear=False):
            self.assertFalse(_tensorrt_runtime_available())

    def test_tensorrt_requires_core_plugin_and_parser_libraries(self) -> None:
        with (
            patch.dict(os.environ, {"ENABLE_TENSORRT_PROVIDER": "true"}, clear=False),
            patch("app.devices._load_shared_library", side_effect=[True, True, False]) as loader,
        ):
            self.assertFalse(_tensorrt_runtime_available())
            self.assertEqual(loader.call_count, 3)


if __name__ == "__main__":
    unittest.main()
