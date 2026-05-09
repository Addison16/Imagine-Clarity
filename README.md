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

Suggested public image tags after publishing:

- `ghcr.io/addison16/imagine-clarity:latest`: default CPU-compatible image.
- `ghcr.io/addison16/imagine-clarity:cpu`: explicit CPU-compatible image.
- `ghcr.io/addison16/imagine-clarity:gpu`: NVIDIA CUDA image for hosts with Docker GPU support.

For most users, the easiest setup is:

```powershell
docker compose -f docker-compose.prebuilt.yml up -d
```

NVIDIA users can use:

```powershell
docker compose -f docker-compose.prebuilt.yml -f docker-compose.prebuilt.gpu.yml up -d
```

## Approach

The default neural path uses Real-ESRGAN because it is designed for practical blind super-resolution: unknown blur, noise, compression artifacts, and mixed real-world degradation. The app also includes:

- `Auto detect`: chooses a safer upscale type from the image: conservative for logos/text-like graphics, illustration mode for flat artwork, general clean for noisy images, and photo detail for natural images.
- `Photo detail`: RealESRGAN_x4plus for photos and mixed natural images.
- `General clean`: Real-ESRGAN general v3 with denoise blending for noisy or compressed images.
- `Illustration/anime`: RealESRGAN_x4plus_anime_6B for flat colors and drawn line work.
- `Face restore`: optional GFPGAN pass for low-quality faces.
- `Conservative`: alpha-aware Lanczos plus mild sharpening when exact geometry, text, transparent PNGs, or logos matter more than generated texture.
- `Remove Back Ground`: rembg/ISNet, U2Net, BiRefNet-lite, and a safe logo/sticker edge-color cutter for transparent background extraction. Alpha matting is available for hair, fur, and soft edges. Edge trim, fringe cleanup, and inner pocket cleanup help remove thin halos and missed background gaps while "Protect inside detail" keeps enclosed artwork from getting random missing spots inside the foreground.
- `All-in-One`: removes the background first, then upscales the transparent result to the selected scale or target resolution.
- `Batch processing`: select multiple images and the server runs them in the background one at a time. Closing the browser does not cancel the queued batch.
- `Batch ZIP downloads`: completed batch outputs can be downloaded together as one ZIP file, with per-image result links still available.
- `Comparison tools`: results open in the slider comparison view by default, with side-by-side, original-only, result-only, difference preview, fit, 100%, and 200% zoom views available from compact dropdowns.
- `Prepress controls`: non-AI resize methods, target fit/fill/pad/crop behavior, transparent canvas sizing, DPI metadata, print-size readout, output sharpening, JPEG/WebP quality, and TIFF export for controlled print/web prep.
- `Saved jobs`: completed outputs are saved in Docker storage and listed in the UI for later download, preview, and before/after comparison when a source preview is available. Users can delete individual saved jobs or clear recent saved jobs after a confirmation prompt.
- `Runtime diagnostics`: the UI and `/api/diagnostics` show CPU/GPU visibility, ONNX providers, storage usage, and practical hardware recommendations.
- `Presets`: Smart Auto, Logo/Sticker, Photo, Artwork, Product Cutout, Print-Ready, and Transparent Sticker presets set safer defaults quickly.

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

Outputs are stored in the `upscaler-storage` Docker volume at `/tmp/upscaler/outputs` inside the container. Source previews for new single-image jobs are stored at `/tmp/upscaler/sources`; batch source files are stored under `/tmp/upscaler/batches`. This keeps downloads, previews, and completed batch ZIPs available after the browser refreshes or closes.

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

Interactive OpenAPI docs are available at:

- `http://localhost:8794/docs`
- `http://localhost:8794/redoc`

Capabilities and valid settings:

```powershell
curl.exe http://localhost:8794/api/capabilities
```

Unified automation endpoint:

```powershell
curl.exe -X POST http://localhost:8794/api/process `
  -F "image=@input.png" `
  -F "tool=remove-background-upscale" `
  -F "response_mode=image" `
  -F "model=logo" `
  -F "cut_mode=balanced" `
  -F "edge_trim=2" `
  -F "fringe_cleanup=70" `
  -F "inner_cleanup=45" `
  -F "scale=4" `
  -F "mode=auto" `
  -F "device=auto" `
  -F "output_format=png" `
  --output result.png
```

Use `response_mode=json` when another program wants metadata plus a download URL instead of raw image bytes:

```powershell
curl.exe -X POST http://localhost:8794/api/process `
  -F "image=@input.png" `
  -F "tool=remove-background" `
  -F "response_mode=json" `
  -F "model=auto" `
  -F "cut_mode=balanced" `
  -F "output_format=png"
```

The JSON response includes `job_id`, `download_url`, `relative_download_url`, and the saved job metadata. Download later with:

```powershell
curl.exe -L http://localhost:8794/api/results/JOB_ID --output result.png
```

Valid `tool` values for `/api/process`:

- `upscale`
- `remove-background`
- `remove-background-upscale`

The older direct endpoints below are still supported.

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
  -F "edge_trim=1" `
  -F "fringe_cleanup=45" `
  -F "inner_cleanup=25" `
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

List saved jobs:

```powershell
curl.exe http://localhost:8794/api/jobs
```

Download a saved result:

```powershell
curl.exe -L http://localhost:8794/api/results/JOB_ID --output result.png
```

Download a saved source preview, when available:

```powershell
curl.exe -L http://localhost:8794/api/sources/JOB_ID --output original.png
```

Create a server-side batch:

```powershell
curl.exe -X POST http://localhost:8794/api/batches `
  -F "images=@input-1.png" `
  -F "images=@input-2.png" `
  -F "tool=remove-background-upscale" `
  -F "model=logo" `
  -F "cut_mode=balanced" `
  -F "scale=4" `
  -F "mode=auto" `
  -F "output_format=png"
```

List and inspect batches:

```powershell
curl.exe http://localhost:8794/api/batches
curl.exe http://localhost:8794/api/batches/BATCH_ID
```

Download all completed images from a batch:

```powershell
curl.exe -L http://localhost:8794/api/batches/BATCH_ID/zip --output batch.zip
```

Preview an original source image from a batch item:

```powershell
curl.exe -L http://localhost:8794/api/batches/BATCH_ID/source/ITEM_ID --output original.png
```

Delete one saved job:

```powershell
curl.exe -X DELETE http://localhost:8794/api/jobs/JOB_ID
```

Clear all recent saved jobs:

```powershell
curl.exe -X DELETE http://localhost:8794/api/jobs
```

Runtime diagnostics:

```powershell
curl.exe http://localhost:8794/api/diagnostics
```

Automation capability discovery:

```powershell
curl.exe http://localhost:8794/api/capabilities
```

Unified automation endpoint (`response_mode=image` returns bytes directly, `response_mode=json` returns metadata and download URL):

```powershell
curl.exe -X POST http://localhost:8794/api/process `
  -F "image=@input.png" `
  -F "tool=remove-background-upscale" `
  -F "response_mode=json" `
  -F "model=logo" `
  -F "cut_mode=balanced" `
  -F "edge_trim=2" `
  -F "fringe_cleanup=70" `
  -F "inner_cleanup=45" `
  -F "scale=4" `
  -F "mode=auto" `
  -F "device=auto" `
  -F "output_format=png"
```

## Settings

- `HOST_PORT`: host port, default `8794`.
- `MAX_UPLOAD_MB`: upload limit, default `64`.
- `MAX_BATCH_FILES`: maximum files in one batch, default `100`.
- `MAX_BATCH_TOTAL_MB`: maximum total upload size for one batch, default `512`.
- `MAX_IMAGE_DIMENSION`: maximum input side and generated output side, default `16384` for a 16K x 16K cap.
- `UPSCALER_DEVICE`: `auto`, `cpu`, or `cuda`. The provided image installs CPU PyTorch wheels for broad compatibility.
- GPU mode uses `Dockerfile.gpu`, CUDA-enabled PyTorch wheels, and `onnxruntime-gpu` so both upscaling and background removal can use the NVIDIA GPU. It requires an NVIDIA driver plus Docker's NVIDIA runtime.
- `REMBG_DEVICE`: optional override for background removal, defaults to `UPSCALER_DEVICE`. Use `cpu` to force background removal to CPU.
- `U2NET_HOME`: rembg model cache path, default `/models/rembg` inside the Compose volume.
- `STORAGE_DIR`: saved output and job history path inside the container, default `/tmp/upscaler`.
- `HISTORY_LIMIT`: number of saved jobs kept in the JSON history, default `100`.
- `BATCH_HISTORY_LIMIT`: number of saved batch records kept in the JSON history, default `50`.
- `JOB_TTL_HOURS`: optional auto-cleanup window for saved jobs/results. `0` disables TTL cleanup (default).
- `CLARITY_API_KEY`: optional API key for `/api/process`. If set, callers must send `X-API-Key: <value>` or `Authorization: Bearer <value>`.
- `CORS_ALLOW_ORIGINS`: comma-separated CORS allowlist. Default is `*` for local/dev convenience.

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
- Optional controlled-prep fields: `resize_method` (`nearest`, `bilinear`, `bicubic`, `lanczos`, `mitchell`, `preserve`), `target_fit` (`stretch`, `contain`, `pad`, `crop`), `canvas_width`, `canvas_height`, `canvas_anchor`, `dpi`, `export_quality`, and `sharpen_amount`.
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

Background refinement values:

- `edge_trim`: 0-8 pixels. Removes a thin amount from the alpha edge to clear white or colored halos.
- `fringe_cleanup`: 0-100. Targets background-colored fringe pixels close to transparent areas.
- `inner_cleanup`: 0-100. Removes background-colored pockets connected to transparent space. Leave `preserve_interior=true` for logos and lettering; set it false only when you intentionally want more aggressive enclosed cleanup.

## Verify

```powershell
python scripts/smoke_test.py http://localhost:8794
```
