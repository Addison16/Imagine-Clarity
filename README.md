# Clarity Upscaler

Docker Compose web app for local image upscaling and background removal.

## Quick Start

Clone the repo, install Docker, then run one script.

Windows:

```powershell
.\scripts\start.ps1
```

Linux/macOS:

```bash
chmod +x ./scripts/start.sh
./scripts/start.sh
```

Open:

```text
http://localhost:8794
```

The startup scripts use NVIDIA GPU acceleration when it is available and verified; otherwise the app runs on CPU. See [PUBLISHING.md](PUBLISHING.md) if you want to push prebuilt images to GitHub Container Registry.

Run a published CPU image directly with Docker:

```powershell
docker run --pull always --name clarity-upscaler -p 8794:8794 -v clarity-models:/models ghcr.io/addison16/imagine-clarity:cpu
```

Run a published NVIDIA GPU image directly with Docker:

```powershell
docker run --pull always --gpus all --name clarity-upscaler -p 8794:8794 -v clarity-models:/models ghcr.io/addison16/imagine-clarity:gpu
```

Or use the prebuilt-image helper scripts:

```powershell
.\scripts\start-prebuilt.ps1
```

```bash
chmod +x ./scripts/start-prebuilt.sh
./scripts/start-prebuilt.sh
```

## Approach

The default neural path uses Real-ESRGAN because it is designed for practical blind super-resolution: unknown blur, noise, compression artifacts, and mixed real-world degradation. The app also includes:

- `Auto detect`: chooses a safer upscale type from the image: conservative for logos/text-like graphics, illustration mode for flat artwork, general clean for noisy images, and photo detail for natural images.
- `Photo detail`: RealESRGAN_x4plus for photos and mixed natural images.
- `General clean`: Real-ESRGAN general v3 with denoise blending for noisy or compressed images.
- `Illustration/anime`: RealESRGAN_x4plus_anime_6B for flat colors and drawn line work.
- `Face restore`: optional GFPGAN pass for low-quality faces.
- `Conservative`: Lanczos plus mild sharpening when exact geometry, text, or logos matter more than generated texture.
- `Remove BG`: rembg/ISNet, U2Net, BiRefNet-lite, and a safe logo/sticker edge-color cutter for transparent background extraction. Alpha matting is available for hair, fur, and soft edges. The default "Protect inside detail" cleanup keeps enclosed artwork from getting random missing spots inside the foreground.
- `All-in-One`: removes the background first, then upscales the transparent result to the selected scale or target resolution.

AI upscalers infer detail that is not present in the source. For maximum fidelity, compare neural modes against `Conservative` on images with text, product labels, legal/medical imagery, or identity-sensitive faces.

Research references:

- Real-ESRGAN paper: https://arxiv.org/abs/2107.10833
- Real-ESRGAN implementation/model zoo: https://github.com/xinntao/Real-ESRGAN
- GFPGAN face restoration: https://github.com/TencentARC/GFPGAN
- SwinIR transformer restoration baseline: https://arxiv.org/abs/2108.10257
- rembg background removal: https://github.com/danielgatis/rembg

## Run From Source

Windows PowerShell, auto-detect NVIDIA GPU and fall back to CPU:

```powershell
.\scripts\start.ps1
```

Linux/macOS shell, auto-detect NVIDIA GPU and fall back to CPU:

```bash
chmod +x ./scripts/start.sh
./scripts/start.sh
```

Force CPU:

```powershell
.\scripts\start.ps1 -ForceCpu
```

```bash
./scripts/start.sh --cpu
```

Force GPU:

```powershell
.\scripts\start.ps1 -ForceGpu
```

```bash
./scripts/start.sh --gpu
```

Check what the host and running container can see:

```powershell
.\scripts\doctor.ps1
```

Plain CPU Compose path:

```powershell
docker compose up --build -d
```

Plain GPU Compose path:

```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build -d
```

Open:

```text
http://localhost:8794
```

The first neural upscale downloads model weights into the `upscaler-models` Docker volume. Conservative mode runs immediately.

## Hardware Auto-Detection

This app is packaged with a safe default: CPU mode works without special hardware, and the startup scripts use NVIDIA acceleration only when it can be verified.

| Hardware | Current behavior |
| --- | --- |
| Intel or AMD CPU | Supported through the base Docker image. This is the universal fallback. |
| NVIDIA GPU | Supported by the GPU Docker image when the host has NVIDIA drivers plus Docker GPU support. The app verifies CUDA inside the container before keeping GPU mode. |
| AMD GPU | Not accelerated by this Docker image yet. It will run in CPU mode. AMD GPU acceleration would need a separate ROCm build and is mostly practical on supported Linux/ROCm setups. |
| Intel GPU / Intel Arc / iGPU | Not accelerated by this Docker image yet. It will run in CPU mode. Intel GPU acceleration would need a separate OpenVINO or other provider-specific build. |
| Apple Silicon GPU | Not accelerated inside this Docker image. CPU mode may work depending on Docker/Python package compatibility. |

Why: Docker GPU pass-through is not one universal interface. Docker documents GPU reservations for Compose, Docker Desktop documents NVIDIA GPU support on Windows with the WSL2 backend, and ONNX Runtime exposes hardware acceleration through provider-specific builds such as CUDA, ROCm, DirectML, and OpenVINO.

References:

- Docker Compose GPU support: https://docs.docker.com/compose/gpu-support/
- Docker Desktop GPU support on Windows: https://docs.docker.com/desktop/features/gpu/
- ONNX Runtime execution providers: https://onnxruntime.ai/docs/execution-providers

## API

Upscale:

```powershell
curl.exe -X POST http://localhost:8794/api/upscale `
  -F "image=@input.jpg" `
  -F "scale=8" `
  -F "mode=auto" `
  -F "face_enhance=false" `
  -F "tile=256" `
  -F "device=auto" `
  -F "output_format=png" `
  --output upscaled.png
```

Remove background:

```powershell
curl.exe -X POST http://localhost:8794/api/remove-background `
  -F "image=@input.jpg" `
  -F "model=accurate" `
  -F "cut_mode=balanced" `
  -F "alpha_matting=true" `
  -F "edge_refine=8" `
  -F "background_tolerance=34" `
  -F "device=auto" `
  -F "post_process_mask=true" `
  -F "preserve_interior=true" `
  -F "respect_existing_alpha=true" `
  -F "output_format=png" `
  --output transparent.png
```

Remove background, then upscale in one request:

```powershell
curl.exe -X POST http://localhost:8794/api/remove-background-upscale `
  -F "image=@input.jpg" `
  -F "model=auto" `
  -F "cut_mode=balanced" `
  -F "scale=4" `
  -F "mode=auto" `
  -F "target_width=2400" `
  -F "background_device=auto" `
  -F "upscale_device=auto" `
  -F "output_format=png" `
  --output transparent-upscaled.png
```

## Settings

- `HOST_PORT`: host port, default `8794`.
- `MAX_UPLOAD_MB`: upload limit, default `64`.
- `MAX_IMAGE_DIMENSION`: maximum input side and generated output side, default `16384` for a 16K x 16K cap.
- `UPSCALER_DEVICE`: `auto`, `cpu`, or `cuda`. The provided image installs CPU PyTorch wheels for broad compatibility.
- GPU mode uses `Dockerfile.gpu`, CUDA-enabled PyTorch wheels, and `onnxruntime-gpu` so both upscaling and background removal can use the NVIDIA GPU. It requires an NVIDIA driver plus Docker's NVIDIA runtime.
- `REMBG_DEVICE`: optional override for background removal, defaults to `UPSCALER_DEVICE`. Use `cpu` to force background removal to CPU.
- `U2NET_HOME`: rembg model cache path, default `/models/rembg` inside the Compose volume.

Per-job processing source:

- The UI includes a `Processing source` dropdown for both Upscale and Remove Background.
- `Auto select`: use CUDA when the running container can see it, otherwise CPU.
- `NVIDIA GPU`: require CUDA for that job.
- `CPU`: force that one job to CPU.
- API callers can send `device=auto`, `device=cuda`, or `device=cpu` to `/api/upscale` and `/api/remove-background`.

Upscale `mode` values:

- `auto`: choose the upscale type from the image. It prefers conservative resizing for transparent assets, logos, text-heavy graphics, and very flat hard-edged artwork; illustration mode for drawn/flat-color images; general clean for high denoise settings; and photo detail for natural images.
- `photo`: RealESRGAN_x4plus for photos and mixed natural images.
- `general`: Real-ESRGAN general v3 with denoise blending for noisy or compressed inputs.
- `anime`: RealESRGAN_x4plus_anime_6B for illustration, anime, and drawn line work.
- `conservative`: Lanczos resize plus mild sharpening for exact geometry, text, logos, and cases where AI detail should be avoided.

Upscale sizing:

- Use `scale=2`, `3`, `4`, or `8` for multiplier-based output.
- Or send `target_width`, `target_height`, or both to request a target resolution. If only one side is provided, the app preserves the source aspect ratio.
- Target output is capped at `MAX_IMAGE_DIMENSION` and at an 8x upscale factor from the source image.

Background `model` values:

- `auto`: use the safe logo/sticker cutter when the image looks like a flat graphic on an edge-connected background; otherwise use ISNet.
- `logo`: remove only background connected to the image edge, best for logos, decals, text art, and stickers.
- `accurate`: ISNet general-purpose background removal.
- `portrait`: U2Net human segmentation.
- `anime`: ISNet anime/illustration model.
- `biref-lite`: BiRefNet general-lite model.
- `balanced`: U2Net general model.
- `fast`: U2NetP lightweight preview model.

## Verify

```powershell
python scripts/smoke_test.py http://localhost:8794
```
