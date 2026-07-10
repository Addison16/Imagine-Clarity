from __future__ import annotations

import io
import sys
import time
import zipfile
from xml.etree import ElementTree as ET

import requests
from PIL import Image, ImageDraw


def assert_svg(payload: bytes) -> None:
    root = ET.fromstring(payload.strip())
    assert root.tag.rsplit("}", 1)[-1].lower() == "svg", payload[:100]


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8794"
    health = requests.get(f"{base_url}/health", timeout=10)
    health.raise_for_status()
    assert health.json()["max_image_dimension"] == 16384, health.json()
    assert health.json()["max_output_pixels"] == 64000000, health.json()
    diagnostics = requests.get(f"{base_url}/api/diagnostics", timeout=10)
    diagnostics.raise_for_status()
    assert diagnostics.json()["status"] == "ok", diagnostics.text
    queue_health = requests.get(f"{base_url}/api/queue/health", timeout=10)
    queue_health.raise_for_status()
    assert queue_health.json()["redis_connected"], queue_health.text
    capabilities = requests.get(f"{base_url}/api/capabilities", timeout=10)
    capabilities.raise_for_status()
    capabilities_body = capabilities.json()
    assert "remove-background-upscale" in capabilities_body["tools"], capabilities.text
    assert "vectorize" in capabilities_body["tools"], capabilities.text
    assert "svg" in capabilities_body["output_formats"], capabilities.text
    assert "tiff" in capabilities_body["output_formats"], capabilities.text
    assert "lanczos" in capabilities_body["upscale"]["resize_methods"], capabilities.text
    assert capabilities_body["vectorize"]["engine"] == "vtracer", capabilities.text
    runtime_devices = capabilities_body["runtime"].get("processing_devices") or []
    assert any(device.get("value") == "cpu" for device in runtime_devices), capabilities.text
    assert any(device.get("upscale_supported") for device in runtime_devices), capabilities.text
    assert any(device.get("background_supported") for device in runtime_devices), capabilities.text
    assert capabilities_body["recommendations"], capabilities.text
    assert capabilities_body["queue"]["backend"] == "redis-rq", capabilities.text
    presets = requests.get(f"{base_url}/api/presets", timeout=10)
    presets.raise_for_status()
    preset_payload = presets.json()
    assert any(preset["id"] == "smart" for preset in preset_payload["presets"]), preset_payload
    user_preset = requests.post(
        f"{base_url}/api/presets",
        json={
            "name": f"Smoke Preset {int(time.time())}",
            "description": "Smoke-test saved preset",
            "tool": "upscale",
            "settings": {"tool": "upscale", "scale": "2", "sizing": "scale", "format": "png"},
        },
        timeout=10,
    )
    user_preset.raise_for_status()
    preset_id = user_preset.json()["preset"]["id"]
    assert preset_id.startswith("user-"), user_preset.text
    protected = requests.delete(f"{base_url}/api/presets/smart", timeout=10)
    assert protected.status_code == 403, protected.text
    deleted_preset = requests.delete(f"{base_url}/api/presets/{preset_id}", timeout=10)
    deleted_preset.raise_for_status()
    assert deleted_preset.json()["deleted"], deleted_preset.text

    img = Image.new("RGB", (64, 48), "#f8fafc")
    draw = ImageDraw.Draw(img)
    draw.rectangle((8, 8, 56, 40), outline="#2563eb", width=3)
    draw.line((10, 38, 54, 10), fill="#0f766e", width=3)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    response = requests.post(
        f"{base_url}/api/upscale",
        files={"image": ("smoke.png", buffer, "image/png")},
        data={
            "scale": "8",
            "mode": "auto",
            "face_enhance": "false",
            "denoise": "0.55",
            "tile": "256",
            "device": "cpu",
            "output_format": "png",
        },
        timeout=30,
    )
    response.raise_for_status()
    assert response.headers["X-Upscaler-Engine"].startswith("Auto:"), response.headers["X-Upscaler-Engine"]
    assert response.headers["X-Job-Id"], response.headers
    assert response.headers["X-Download-URL"].startswith("/api/results/"), response.headers
    assert response.headers["X-Source-URL"].startswith("/api/sources/"), response.headers
    out = Image.open(io.BytesIO(response.content))
    assert out.size == (512, 384), out.size
    saved = requests.get(f"{base_url}{response.headers['X-Download-URL']}", timeout=10)
    saved.raise_for_status()
    assert len(saved.content) == len(response.content), (len(saved.content), len(response.content))
    source = requests.get(f"{base_url}{response.headers['X-Source-URL']}", timeout=10)
    source.raise_for_status()
    source_img = Image.open(io.BytesIO(source.content))
    assert source_img.size == (64, 48), source_img.size
    assert not response.headers.get("X-Listing-Pack-URL"), response.headers
    listing_pack = requests.get(f"{base_url}{response.headers['X-Download-URL']}/listing-pack", timeout=10)
    assert listing_pack.status_code == 404, listing_pack.text
    meta = requests.patch(
        f"{base_url}{response.headers['X-Download-URL'].replace('/api/results/', '/api/jobs/')}/metadata",
        json={"display_name": "Smoke renamed job", "note": "Smoke note"},
        timeout=10,
    )
    meta.raise_for_status()
    assert meta.json()["job"]["display_name"] == "Smoke renamed job", meta.text
    assert meta.json()["job"]["note"] == "Smoke note", meta.text

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    response = requests.post(
        f"{base_url}/api/upscale",
        files={"image": ("target.png", buffer, "image/png")},
        data={
            "scale": "4",
            "mode": "conservative",
            "face_enhance": "false",
            "denoise": "0.55",
            "tile": "256",
            "device": "cpu",
            "target_width": "320",
            "target_height": "240",
            "output_format": "png",
        },
        timeout=30,
    )
    response.raise_for_status()
    out = Image.open(io.BytesIO(response.content))
    assert out.size == (320, 240), out.size

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    response = requests.post(
        f"{base_url}/api/upscale",
        files={"image": ("pad.png", buffer, "image/png")},
        data={
            "scale": "2",
            "mode": "conservative",
            "face_enhance": "false",
            "denoise": "0.55",
            "tile": "256",
            "device": "cpu",
            "target_width": "120",
            "target_height": "120",
            "target_fit": "pad",
            "resize_method": "nearest",
            "dpi": "300",
            "sharpen_amount": "0",
            "output_format": "png",
        },
        timeout=30,
    )
    response.raise_for_status()
    assert response.headers["X-Output-DPI"] == "300", response.headers
    out = Image.open(io.BytesIO(response.content)).convert("RGBA")
    assert out.size == (120, 120), out.size
    assert out.getpixel((0, 0))[3] == 0, out.getpixel((0, 0))

    rgba = Image.new("RGBA", (20, 10), (0, 0, 0, 0))
    rgba.putpixel((10, 5), (255, 0, 0, 128))
    buffer = io.BytesIO()
    rgba.save(buffer, format="PNG")
    buffer.seek(0)
    response = requests.post(
        f"{base_url}/api/upscale",
        files={"image": ("alpha-pad.png", buffer, "image/png")},
        data={
            "mode": "conservative",
            "device": "cpu",
            "target_width": "40",
            "target_height": "40",
            "target_fit": "pad",
            "resize_method": "nearest",
            "sharpen_amount": "0",
            "output_format": "png",
        },
        timeout=30,
    )
    response.raise_for_status()
    out = Image.open(io.BytesIO(response.content)).convert("RGBA")
    assert out.getpixel((20, 20))[3] == 128, out.getpixel((20, 20))

    too_large = Image.new("RGB", (2050, 2050), "#ffffff")
    buffer = io.BytesIO()
    too_large.save(buffer, format="PNG")
    buffer.seek(0)
    response = requests.post(
        f"{base_url}/api/upscale",
        files={"image": ("too-large.png", buffer, "image/png")},
        data={
            "scale": "8",
            "mode": "conservative",
            "face_enhance": "false",
            "denoise": "0.55",
            "tile": "256",
            "device": "cpu",
            "output_format": "png",
        },
        timeout=30,
    )
    assert response.status_code == 400, response.text
    assert "Maximum raster resolution is 16384 x 16384" in response.text, response.text

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    response = requests.post(
        f"{base_url}/api/upscale",
        files={"image": ("target-too-large.png", buffer, "image/png")},
        data={
            "scale": "4",
            "mode": "conservative",
            "face_enhance": "false",
            "denoise": "0.55",
            "tile": "256",
            "device": "cpu",
            "target_width": "17000",
            "output_format": "png",
        },
        timeout=30,
    )
    assert response.status_code == 400, response.text
    assert "Maximum raster resolution is 16384 x 16384" in response.text, response.text

    logo = Image.new("RGB", (90, 70), "white")
    draw = ImageDraw.Draw(logo)
    draw.rectangle((18, 16, 72, 54), fill="#111827")
    draw.rectangle((30, 26, 60, 44), fill="#f97316")
    draw.ellipse((40, 30, 50, 40), fill="white")
    buffer = io.BytesIO()
    logo.save(buffer, format="PNG")
    buffer.seek(0)

    response = requests.post(
        f"{base_url}/api/remove-background",
        files={"image": ("logo.png", buffer, "image/png")},
        data={
            "model": "logo",
            "cut_mode": "balanced",
            "alpha_matting": "false",
            "edge_refine": "8",
            "background_tolerance": "34",
            "device": "cpu",
            "post_process_mask": "true",
            "preserve_interior": "true",
            "respect_existing_alpha": "true",
            "output_format": "png",
        },
        timeout=30,
    )
    response.raise_for_status()
    out = Image.open(io.BytesIO(response.content)).convert("RGBA")
    assert out.size == (90, 70), out.size
    assert out.getpixel((0, 0))[3] == 0, out.getpixel((0, 0))
    assert out.getpixel((45, 35))[3] > 240, out.getpixel((45, 35))

    buffer = io.BytesIO()
    logo.save(buffer, format="PNG")
    buffer.seek(0)
    response = requests.post(
        f"{base_url}/api/process",
        files={"image": ("api-logo.png", buffer, "image/png")},
        data={
            "tool": "remove-background",
            "response_mode": "json",
            "model": "logo",
            "cut_mode": "balanced",
            "alpha_matting": "false",
            "edge_refine": "8",
            "edge_trim": "1",
            "fringe_cleanup": "20",
            "inner_cleanup": "10",
            "background_tolerance": "34",
            "device": "cpu",
            "post_process_mask": "true",
            "preserve_interior": "true",
            "respect_existing_alpha": "true",
            "output_format": "png",
        },
        timeout=30,
    )
    response.raise_for_status()
    api_result = response.json()
    assert api_result["job_id"], api_result
    assert api_result["download_url"].startswith(base_url), api_result
    assert api_result["relative_download_url"].startswith("/api/results/"), api_result
    assert api_result["relative_source_url"].startswith("/api/sources/"), api_result
    saved = requests.get(api_result["download_url"], timeout=10)
    saved.raise_for_status()
    out = Image.open(io.BytesIO(saved.content)).convert("RGBA")
    assert out.size == (90, 70), out.size

    buffer = io.BytesIO()
    logo.save(buffer, format="PNG")
    buffer.seek(0)
    response = requests.post(
        f"{base_url}/api/remove-background-upscale",
        files={"image": ("combo-logo.png", buffer, "image/png")},
        data={
            "scale": "2",
            "mode": "auto",
            "face_enhance": "false",
            "denoise": "0.55",
            "tile": "256",
            "upscale_device": "cpu",
            "target_width": "180",
            "target_height": "140",
            "model": "logo",
            "cut_mode": "balanced",
            "alpha_matting": "false",
            "edge_refine": "8",
            "background_tolerance": "34",
            "background_device": "cpu",
            "post_process_mask": "true",
            "preserve_interior": "true",
            "respect_existing_alpha": "true",
            "output_format": "png",
        },
        timeout=60,
    )
    response.raise_for_status()
    assert "X-Pipeline-Engine" in response.headers, response.headers
    out = Image.open(io.BytesIO(response.content)).convert("RGBA")
    assert out.size == (180, 140), out.size
    assert out.getpixel((0, 0))[3] == 0, out.getpixel((0, 0))
    assert out.getpixel((90, 70))[3] > 220, out.getpixel((90, 70))

    buffer = io.BytesIO()
    logo.save(buffer, format="PNG")
    buffer.seek(0)
    response = requests.post(
        f"{base_url}/api/process",
        files={"image": ("process-combo-logo.png", buffer, "image/png")},
        data={
            "tool": "remove-background-upscale",
            "response_mode": "json",
            "device": "definitely-invalid-device",
            "upscale_device": "cpu",
            "background_device": "cpu",
            "scale": "2",
            "mode": "auto",
            "face_enhance": "false",
            "denoise": "0.55",
            "tile": "256",
            "target_width": "180",
            "target_height": "140",
            "model": "logo",
            "cut_mode": "balanced",
            "alpha_matting": "false",
            "edge_refine": "8",
            "background_tolerance": "34",
            "post_process_mask": "true",
            "preserve_interior": "true",
            "respect_existing_alpha": "true",
            "output_format": "png",
        },
        timeout=60,
    )
    response.raise_for_status()
    process_combo = response.json()
    assert process_combo["metadata"]["engine"], process_combo
    saved = requests.get(process_combo["download_url"], timeout=10)
    saved.raise_for_status()
    out = Image.open(io.BytesIO(saved.content)).convert("RGBA")
    assert out.size == (180, 140), out.size

    buffer = io.BytesIO()
    logo.save(buffer, format="PNG")
    buffer.seek(0)
    response = requests.post(
        f"{base_url}/api/vectorize",
        files={"image": ("vector-logo.png", buffer, "image/png")},
        data={
            "vector_preset": "logo",
            "vector_colormode": "color",
            "vector_hierarchical": "stacked",
            "vector_mode": "spline",
            "vector_filter_speckle": "4",
            "vector_color_precision": "6",
            "vector_layer_difference": "16",
            "vector_path_precision": "3",
        },
        timeout=30,
    )
    response.raise_for_status()
    assert response.headers["X-Vector-Engine"].startswith("VTracer"), response.headers
    assert response.headers["X-Download-URL"].startswith("/api/results/"), response.headers
    assert_svg(response.content)
    vector_pack = requests.get(f"{base_url}{response.headers['X-Download-URL']}/listing-pack", timeout=10)
    assert vector_pack.status_code == 404, vector_pack.text

    buffer = io.BytesIO()
    logo.save(buffer, format="PNG")
    buffer.seek(0)
    response = requests.post(
        f"{base_url}/api/process",
        files={"image": ("process-vector-logo.png", buffer, "image/png")},
        data={"tool": "vectorize", "response_mode": "json", "vector_preset": "logo"},
        timeout=30,
    )
    response.raise_for_status()
    vector_payload = response.json()
    assert vector_payload["job_id"], vector_payload
    assert vector_payload["relative_download_url"].startswith("/api/results/"), vector_payload
    assert vector_payload["metadata"]["engine"].startswith("VTracer"), vector_payload

    buffer = io.BytesIO()
    logo.save(buffer, format="PNG")
    buffer.seek(0)
    response = requests.post(
        f"{base_url}/api/process",
        files={"image": ("process-line-art-vector.png", buffer, "image/png")},
        data={"tool": "vectorize", "response_mode": "json", "vector_preset": "line-art"},
        timeout=30,
    )
    response.raise_for_status()
    line_art_payload = response.json()
    assert "line-art" in line_art_payload["metadata"]["engine"], line_art_payload
    assert "binary" in line_art_payload["metadata"]["engine"], line_art_payload
    line_art_job = requests.get(f"{base_url}/api/jobs/{line_art_payload['job_id']}", timeout=10)
    line_art_job.raise_for_status()
    line_art_job_payload = line_art_job.json()
    assert line_art_job_payload["settings"]["colormode"] == "binary", line_art_job_payload
    assert any("Color mode: binary" in check["message"] for check in line_art_job_payload["quality_report"]["checks"]), line_art_job_payload

    batch_files = []
    for idx, color in enumerate(("#2563eb", "#f97316"), start=1):
        batch_img = Image.new("RGB", (32, 24), "#f8fafc")
        batch_draw = ImageDraw.Draw(batch_img)
        batch_draw.rectangle((5, 5, 27, 19), fill=color)
        buffer = io.BytesIO()
        batch_img.save(buffer, format="PNG")
        batch_files.append(("images", (f"batch-{idx}.png", buffer.getvalue(), "image/png")))

    response = requests.post(
        f"{base_url}/api/batches",
        files=batch_files,
        data={
            "tool": "upscale",
            "scale": "2",
            "mode": "conservative",
            "device": "definitely-invalid-device",
            "upscale_device": "cpu",
            "output_format": "png",
        },
        timeout=30,
    )
    response.raise_for_status()
    batch = response.json()["batch"]
    assert batch["id"], batch
    assert batch["zip_url"].startswith("/api/batches/"), batch
    assert "source_path" not in batch["items"][0], batch
    for _ in range(30):
        poll = requests.get(f"{base_url}/api/batches/{batch['id']}", timeout=10)
        poll.raise_for_status()
        batch = poll.json()
        if batch["status"] in {"done", "completed"}:
            break
        time.sleep(1)
    assert batch["completed"] == 2 and batch["failed"] == 0, batch
    assert batch["items"][0]["source_url"].startswith("/api/batches/"), batch
    source = requests.get(f"{base_url}{batch['items'][0]['source_url']}", timeout=10)
    source.raise_for_status()
    assert Image.open(io.BytesIO(source.content)).size == (32, 24)
    zipped = requests.get(f"{base_url}{batch['zip_url']}", timeout=10)
    zipped.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(zipped.content)) as archive:
        assert len(archive.namelist()) == 2, archive.namelist()

    vector_batch_files = []
    for idx, color in enumerate(("#111827", "#2563eb"), start=1):
        batch_img = Image.new("RGB", (40, 40), "#ffffff")
        batch_draw = ImageDraw.Draw(batch_img)
        batch_draw.rectangle((10, 10, 30, 30), fill=color)
        buffer = io.BytesIO()
        batch_img.save(buffer, format="PNG")
        vector_batch_files.append(("images", (f"vector-batch-{idx}.png", buffer.getvalue(), "image/png")))

    response = requests.post(
        f"{base_url}/api/batches",
        files=vector_batch_files,
        data={"tool": "vectorize", "vector_preset": "line-art"},
        timeout=30,
    )
    response.raise_for_status()
    vector_batch = response.json()["batch"]
    assert vector_batch["tool"] == "vectorize", vector_batch
    for _ in range(30):
        poll = requests.get(f"{base_url}/api/batches/{vector_batch['id']}", timeout=10)
        poll.raise_for_status()
        vector_batch = poll.json()
        if vector_batch["status"] in {"done", "completed"}:
            break
        time.sleep(1)
    assert vector_batch["completed"] == 2 and vector_batch["failed"] == 0, vector_batch
    assert vector_batch["items"][0]["result_filename"].endswith(".svg"), vector_batch
    vector_zipped = requests.get(f"{base_url}{vector_batch['zip_url']}", timeout=10)
    vector_zipped.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(vector_zipped.content)) as archive:
        names = archive.namelist()
        assert len(names) == 2 and all(name.endswith(".svg") for name in names), names
        assert_svg(archive.read(names[0]))

    buffer = io.BytesIO()
    logo.save(buffer, format="PNG")
    buffer.seek(0)
    response = requests.post(
        f"{base_url}/api/process",
        files={"image": ("process-logo.png", buffer, "image/png")},
        data={
            "tool": "remove-background",
            "response_mode": "json",
            "model": "logo",
            "cut_mode": "balanced",
            "output_format": "png",
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    assert payload["job_id"], payload
    assert payload["download_url"].startswith(base_url), payload
    assert payload["listing_pack_url"].startswith(base_url), payload
    listing_pack = requests.get(payload["listing_pack_url"], timeout=10)
    listing_pack.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(listing_pack.content)) as archive:
        names = archive.namelist()
        assert any("-transparent-" in name and name.endswith(".png") for name in names), names
        assert any(name.endswith("-white-bg.jpg") for name in names), names
        assert any(name.endswith("-web.webp") for name in names), names
        assert any(name.endswith("-metadata.txt") for name in names), names

    subject = Image.new("RGB", (64, 64), "#e8eef6")
    draw = ImageDraw.Draw(subject)
    draw.ellipse((18, 10, 46, 50), fill="#c2410c")
    draw.rectangle((26, 42, 38, 58), fill="#c2410c")
    buffer = io.BytesIO()
    subject.save(buffer, format="PNG")
    buffer.seek(0)

    response = requests.post(
        f"{base_url}/api/remove-background",
        files={"image": ("subject.png", buffer, "image/png")},
        data={
            "model": "accurate",
            "cut_mode": "balanced",
            "alpha_matting": "true",
            "edge_refine": "8",
            "background_tolerance": "34",
            "device": "auto",
            "post_process_mask": "true",
            "preserve_interior": "true",
            "respect_existing_alpha": "true",
            "output_format": "png",
        },
        timeout=180,
    )
    response.raise_for_status()
    out = Image.open(io.BytesIO(response.content))
    assert out.mode == "RGBA", out.mode
    assert out.size == (64, 64), out.size

    jobs = requests.get(f"{base_url}/api/jobs?limit=5", timeout=10)
    jobs.raise_for_status()
    assert jobs.json()["jobs"], jobs.text

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    response = requests.post(
        f"{base_url}/api/jobs/queue",
        files={"image": ("queued.png", buffer, "image/png")},
        data={
            "tool": "upscale",
            "scale": "2",
            "mode": "conservative",
            "device": "definitely-invalid-device",
            "upscale_device": "cpu",
            "output_format": "png",
        },
        timeout=30,
    )
    response.raise_for_status()
    queued = response.json()["job"]
    assert queued["status"] in {"queued", "running", "done"}, queued
    assert queued["percent"] >= 0, queued
    for _ in range(30):
        poll = requests.get(f"{base_url}/api/jobs/{queued['id']}", timeout=10)
        poll.raise_for_status()
        queued = poll.json()
        if queued["status"] == "done":
            break
        if queued["status"] == "error":
            raise AssertionError(queued)
        time.sleep(1)
    assert queued["download_url"].startswith("/api/results/"), queued
    invalid_reprocess = requests.post(
        f"{base_url}/api/jobs/{queued['id']}/reprocess",
        json={"settings": {"mode": 123}},
        timeout=10,
    )
    assert invalid_reprocess.status_code == 400, invalid_reprocess.text
    reprocess = requests.post(
        f"{base_url}/api/jobs/{queued['id']}/reprocess",
        json={"quick_fix": "preserve-more-detail"},
        timeout=10,
    )
    reprocess.raise_for_status()
    requeued = reprocess.json()["job"]
    assert requeued["id"] != queued["id"], requeued
    assert requeued["status"] in {"queued", "running", "done"}, requeued
    for _ in range(30):
        poll = requests.get(f"{base_url}/api/jobs/{requeued['id']}", timeout=10)
        poll.raise_for_status()
        requeued = poll.json()
        if requeued["status"] == "done":
            break
        if requeued["status"] == "error":
            raise AssertionError(requeued)
        time.sleep(1)
    assert requeued["download_url"].startswith("/api/results/"), requeued

    buffer = io.BytesIO()
    logo.save(buffer, format="PNG")
    buffer.seek(0)
    response = requests.post(
        f"{base_url}/api/jobs/queue",
        files={"image": ("queued-vector.png", buffer, "image/png")},
        data={"tool": "vectorize", "vector_preset": "logo", "vector_colormode": "color"},
        timeout=30,
    )
    response.raise_for_status()
    queued_vector = response.json()["job"]
    assert queued_vector["tool"] == "vectorize", queued_vector
    for _ in range(30):
        poll = requests.get(f"{base_url}/api/jobs/{queued_vector['id']}", timeout=10)
        poll.raise_for_status()
        queued_vector = poll.json()
        if queued_vector["status"] == "done":
            break
        if queued_vector["status"] == "error":
            raise AssertionError(queued_vector)
        time.sleep(1)
    assert queued_vector["download_url"].startswith("/api/results/"), queued_vector
    assert queued_vector["output"]["format"] == "svg", queued_vector
    assert not queued_vector.get("listing_pack_url"), queued_vector
    saved_vector = requests.get(f"{base_url}{queued_vector['download_url']}", timeout=10)
    saved_vector.raise_for_status()
    assert_svg(saved_vector.content)

    print("smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
