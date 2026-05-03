from __future__ import annotations

import io
import sys

import requests
from PIL import Image, ImageDraw


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8794"
    health = requests.get(f"{base_url}/health", timeout=10)
    health.raise_for_status()
    assert health.json()["max_image_dimension"] == 16384, health.json()

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
    out = Image.open(io.BytesIO(response.content))
    assert out.size == (512, 384), out.size

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
    assert "Maximum output resolution is 16384 x 16384" in response.text, response.text

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
    assert "Maximum output resolution is 16384 x 16384" in response.text, response.text

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

    print("smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
