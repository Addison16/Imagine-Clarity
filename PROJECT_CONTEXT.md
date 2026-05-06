# Imagine Clarity Project Context

Last updated: 2026-05-04

## What This Is

Imagine Clarity is a Docker-hosted image utility with a local web UI at port `8794`.
It upscales images, removes backgrounds, and can run an all-in-one workflow that removes the background first and then upscales the transparent result.

The app is designed to run on CPU by default and use NVIDIA CUDA automatically when available. The UI also exposes hardware selectors so users can choose Auto, CPU, or GPU behavior for upscale and background removal jobs.

## Current Main Features

- Image upscaling with 2x, 4x, and 8x scale options.
- Target resolution upscaling with a maximum output limit of `16,384 x 16,384`.
- Auto upscale mode that chooses a conservative path for text, logos, alpha images, and target-size jobs.
- Alpha-aware transparent PNG resizing to reduce bright halos during conservative upscaling.
- Background removal with multiple model/cut options and detail-preserving cleanup for logos and graphics.
- Background refinement controls for edge trim, fringe cleanup, and inner background pocket cleanup.
- All-in-One mode: background removal followed by upscale to a selected scale or target resolution.
- Batch processing from the UI by selecting multiple image files.
- Saved Jobs panel backed by persisted Docker storage.
- Saved Jobs supports deleting individual results and clearing recent jobs after a UI confirmation prompt.
- Runtime Diagnostics panel backed by `/api/diagnostics`.
- Unified automation endpoint at `/api/process` for tool selection + image/json response modes.
- Capability discovery endpoint at `/api/capabilities`.
- Presets for Smart Auto, logo/sticker, photo, artwork, product cutout, print-ready upscale, and transparent sticker workflows.
- Preview background controls for checkerboard, white, gray, and black result inspection.
- PNG, JPEG, and WEBP output for upscaling.
- PNG and WEBP output for background removal and All-in-One so transparency is preserved.
- Docker Compose files for CPU and GPU-oriented runs.
- GitHub Actions workflow support for publishing Docker images.

## Important Files

- `README.md`: user-facing setup, Docker, API, and publishing instructions.
- `PUBLISHING.md`: GitHub Container Registry publishing notes.
- `Dockerfile`: CPU/default image build.
- `Dockerfile.gpu`: NVIDIA CUDA-oriented image build.
- `docker-compose.yml`: default local compose setup.
- `docker-compose.gpu.yml`: local GPU compose setup.
- `docker-compose.prebuilt.yml`: pull-and-run prebuilt image setup.
- `docker-compose.prebuilt.gpu.yml`: pull-and-run GPU prebuilt image setup.
- `app/main.py`: FastAPI routes, validation, health endpoint, and API responses.
- `app/jobs.py`: saved output files and JSON job history.
- `app/upscaler.py`: upscale logic, hardware selection, target sizing, and alpha-aware transparent resizing.
- `app/static/index.html`: web UI markup.
- `app/static/app.js`: web UI behavior and form/API wiring.
- `app/static/styles.css`: web UI styling.
- `scripts/smoke_test.py`: API smoke tests for upscale, target resolution, background removal, and All-in-One.

## Hardware Behavior

The app reports runtime hardware from `/health`.

Expected behavior:

- CPU-only systems run normally using CPU paths.
- NVIDIA GPU systems can use CUDA when the NVIDIA container runtime and drivers are available.
- Users can leave hardware on Auto for best default behavior.
- Upscale and background removal have separate hardware selectors in the UI.
- AMD and Intel GPUs are not automatically accelerated through Docker right now; they fall back to CPU unless a future backend is added for those runtimes.

## Current Local State

The development container is named:

```powershell
clarity-upscaler
```

The local app URL is:

```text
http://localhost:8794
```

The local GPU-tagged image is:

```text
clarity-image-tools:gpu
```

Saved outputs are stored inside the container at:

```text
/tmp/upscaler/outputs
```

## Useful Verification Commands

```powershell
docker ps --filter name=clarity-upscaler
Invoke-RestMethod -Uri http://localhost:8794/health | ConvertTo-Json -Depth 5
Get-Content scripts\smoke_test.py | docker exec -i clarity-upscaler python - http://127.0.0.1:8794
python -m py_compile app\main.py app\upscaler.py app\background.py app\jobs.py scripts\smoke_test.py
node --check app\static\app.js
```

## Recent Work

- Added target resolution upscaling.
- Capped maximum output resolution at `16,384 x 16,384`.
- Added Auto upscale type.
- Added help text with CPU/GPU recommendations.
- Added All-in-One mode in the UI and `/api/remove-background-upscale` in the backend.
- Updated smoke tests to cover the All-in-One pipeline.
- Added saved jobs, persisted output downloads, runtime diagnostics, presets, batch UI processing, and preview background controls.
- Added Saved Jobs delete/clear controls backed by `DELETE /api/jobs/{job_id}` and `DELETE /api/jobs`.
- Added alpha-aware transparent resize plus edge trim, fringe cleanup, and inner cleanup controls for cleaner transparent cutouts.
- Added optional API-key gate for automation endpoint via `CLARITY_API_KEY` and `X-API-Key` header.
- Added optional CORS allowlist via `CORS_ALLOW_ORIGINS` and optional job/result TTL cleanup via `JOB_TTL_HOURS`.

## Known Limits And Next Improvements

- The app saves processed outputs and job metadata, but it still does not save original uploaded files by default.
- Background removal can still need tuning for unusual artwork, fully enclosed background pockets, transparent edges, or busy images.
- AMD and Intel GPU acceleration are not currently implemented; CPU fallback is expected.
- A future improvement could add a real progress stream for long-running upscale/background jobs.
