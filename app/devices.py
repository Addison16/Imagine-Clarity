from __future__ import annotations

import ctypes
import ctypes.util
import os
from typing import Any


ONNX_PROVIDER_BY_DEVICE = {
    "cuda": "CUDAExecutionProvider",
    "nvidia": "CUDAExecutionProvider",
    "gpu": "CUDAExecutionProvider",
    "tensorrt": "TensorrtExecutionProvider",
    "rocm": "ROCMExecutionProvider",
    "amd": "ROCMExecutionProvider",
    "directml": "DmlExecutionProvider",
    "dml": "DmlExecutionProvider",
    "openvino": "OpenVINOExecutionProvider",
    "intel": "OpenVINOExecutionProvider",
    "coreml": "CoreMLExecutionProvider",
}

DEVICE_LABELS = {
    "auto": "Auto select",
    "cpu": "CPU",
    "cuda": "NVIDIA CUDA GPU",
    "tensorrt": "NVIDIA TensorRT GPU",
    "rocm": "AMD ROCm GPU",
    "directml": "DirectML GPU",
    "openvino": "Intel/OpenVINO accelerator",
    "coreml": "Apple Core ML accelerator",
    "mps": "Apple Silicon GPU",
}


def normalize_device(requested: str | None, *, env_var: str = "UPSCALER_DEVICE", fallback_env_var: str | None = None) -> str:
    device = (requested or "auto").lower().strip()
    if device == "auto":
        env_value = os.getenv(env_var, "").strip() or (os.getenv(fallback_env_var, "").strip() if fallback_env_var else "")
        device = env_value.lower() or "auto"
    aliases = {"gpu": "cuda", "nvidia": "cuda", "amd": "rocm", "dml": "directml", "intel": "openvino"}
    return aliases.get(device, device)


def runtime_info() -> dict[str, Any]:
    info: dict[str, Any] = {
        "requested_device": os.getenv("UPSCALER_DEVICE", "auto"),
        "background_requested_device": os.getenv("REMBG_DEVICE", os.getenv("UPSCALER_DEVICE", "auto")),
        "available_devices": ["cpu"],
        "processing_devices": [_device_option("auto"), _device_option("cpu", available=True)],
        "torch": None,
        "cuda_available": False,
        "cuda_device": None,
        "mps_available": False,
        "onnxruntime": None,
        "onnx_providers": [],
    }
    try:
        import torch

        cuda_available = bool(torch.cuda.is_available())
        mps_available = bool(getattr(getattr(torch, "backends", None), "mps", None) and torch.backends.mps.is_available())
        info.update(
            {
                "torch": torch.__version__,
                "cuda_available": cuda_available,
                "cuda_device": torch.cuda.get_device_name(0) if cuda_available else None,
                "mps_available": mps_available,
            }
        )
        if cuda_available:
            info["available_devices"].append("cuda")
        if mps_available:
            info["available_devices"].append("mps")
    except Exception as exc:
        info["torch_error"] = str(exc)

    try:
        import onnxruntime as ort

        providers = usable_onnx_providers(ort)
        info["onnxruntime"] = ort.__version__
        info["onnx_providers"] = providers
        for provider in providers:
            mapped = _device_from_provider(provider)
            if mapped and mapped not in info["available_devices"]:
                info["available_devices"].append(mapped)
    except Exception as exc:
        info["onnxruntime_error"] = str(exc)

    seen = set()
    options: list[dict[str, Any]] = []
    for value in ["auto", "cpu", *info["available_devices"]]:
        if value in seen:
            continue
        seen.add(value)
        options.append(_device_option(value, available=True, runtime=info))
    info["processing_devices"] = options
    return info


def runtime_recommendations(runtime: dict[str, Any]) -> list[str]:
    recommendations = [
        "Leave hardware selectors on Auto unless you are troubleshooting a specific job.",
        "Use CPU for maximum compatibility, small graphics, simple vectorization, and simple logo cutouts.",
    ]
    if runtime.get("cuda_available"):
        recommendations.insert(1, "Use NVIDIA GPU for 4x/8x upscales, large photos, all-in-one jobs, and batches.")
    else:
        recommendations.insert(1, "No NVIDIA CUDA GPU is visible to PyTorch inside this container; CUDA-only upscaling will fall back or error.")

    providers = runtime.get("onnx_providers") or []
    accelerator_providers = [provider for provider in providers if provider != "CPUExecutionProvider"]
    if accelerator_providers:
        recommendations.append(f"Background removal can use ONNX accelerators visible in Docker: {', '.join(accelerator_providers)}.")
    else:
        recommendations.append("Background removal is not seeing ONNX GPU/accelerator providers; use CPU or rebuild with provider-specific dependencies.")
    return recommendations


def select_torch_device(torch: Any, requested: str) -> Any:
    device = normalize_device(requested)
    if device == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        mps = getattr(getattr(torch, "backends", None), "mps", None)
        if mps and mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    if device == "cpu":
        return torch.device("cpu")
    if device == "mps":
        mps = getattr(getattr(torch, "backends", None), "mps", None)
        if not mps or not mps.is_available():
            raise RuntimeError("Apple MPS was selected, but it is not available in this container.")
        return torch.device("mps")
    if device.startswith("cuda"):
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was selected for this upscale job, but CUDA is not available in this container.")
        return torch.device(device)
    if device in {"tensorrt", "rocm", "directml", "openvino", "coreml"}:
        raise RuntimeError(
            f"{DEVICE_LABELS.get(device, device)} is available only for background removal in this build. "
            "Choose Auto, CPU, CUDA, or MPS for PyTorch upscaling."
        )
    raise ValueError("Upscale device must be auto, cpu, cuda, or mps.")


def select_onnx_providers(requested: str) -> list[str]:
    device = normalize_device(requested, env_var="REMBG_DEVICE", fallback_env_var="UPSCALER_DEVICE")
    import onnxruntime as ort

    available = usable_onnx_providers(ort)
    if device == "cpu":
        return ["CPUExecutionProvider"]
    if device == "auto":
        preferred = [
            "TensorrtExecutionProvider",
            "CUDAExecutionProvider",
            "ROCMExecutionProvider",
            "DmlExecutionProvider",
            "OpenVINOExecutionProvider",
            "CoreMLExecutionProvider",
        ]
        return [provider for provider in preferred if provider in available] + ["CPUExecutionProvider"]

    provider = ONNX_PROVIDER_BY_DEVICE.get(device)
    if not provider:
        raise ValueError("Background device must be auto, cpu, cuda, tensorrt, rocm, directml, openvino, or coreml.")
    if provider not in available:
        raise RuntimeError(f"{DEVICE_LABELS.get(device, device)} was selected, but {provider} is not available in this container.")
    return [provider, "CPUExecutionProvider"]


def _device_option(value: str, *, available: bool = True, runtime: dict[str, Any] | None = None) -> dict[str, Any]:
    providers = set((runtime or {}).get("onnx_providers") or [])
    upscale_supported = value in {"auto", "cpu", "cuda", "mps"}
    if value == "cuda" and runtime is not None:
        upscale_supported = bool(runtime.get("cuda_available"))
    if value == "mps" and runtime is not None:
        upscale_supported = bool(runtime.get("mps_available"))
    background_supported = value in {"auto", "cpu"} or ONNX_PROVIDER_BY_DEVICE.get(value) in providers
    return {
        "value": value,
        "label": DEVICE_LABELS.get(value, value.upper()),
        "available": available,
        "upscale_supported": upscale_supported,
        "background_supported": background_supported,
    }


def usable_onnx_providers(ort: Any) -> list[str]:
    """Return providers whose required local runtime libraries are loadable."""
    providers = list(ort.get_available_providers())
    if "TensorrtExecutionProvider" in providers and not _tensorrt_runtime_available():
        providers.remove("TensorrtExecutionProvider")
    return providers


def _tensorrt_runtime_available() -> bool:
    if os.getenv("ENABLE_TENSORRT_PROVIDER", "").strip().lower() not in {"1", "true", "yes", "on"}:
        return False
    required_library_groups = [
        [ctypes.util.find_library("nvinfer"), "libnvinfer.so.10", "libnvinfer.so.8", "nvinfer_10.dll", "nvinfer.dll"],
        [ctypes.util.find_library("nvinfer_plugin"), "libnvinfer_plugin.so.10", "libnvinfer_plugin.so.8", "nvinfer_plugin_10.dll", "nvinfer_plugin.dll"],
        [ctypes.util.find_library("nvonnxparser"), "libnvonnxparser.so.10", "libnvonnxparser.so.8", "nvonnxparser_10.dll", "nvonnxparser.dll"],
    ]
    return all(_load_shared_library(candidates) for candidates in required_library_groups)


def _load_shared_library(candidates: list[str | None]) -> bool:
    for candidate in candidates:
        if not candidate:
            continue
        try:
            ctypes.CDLL(candidate)
            return True
        except OSError:
            continue
    return False


def _device_from_provider(provider: str) -> str | None:
    return {
        "CUDAExecutionProvider": "cuda",
        "TensorrtExecutionProvider": "tensorrt",
        "ROCMExecutionProvider": "rocm",
        "DmlExecutionProvider": "directml",
        "OpenVINOExecutionProvider": "openvino",
        "CoreMLExecutionProvider": "coreml",
    }.get(provider)
