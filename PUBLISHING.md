# Publishing

This repo can be shared two ways:

1. Source distribution: users clone the repo and build locally with Docker Compose.
2. Prebuilt all-in-one images: GitHub Actions publishes CPU and NVIDIA GPU images to GitHub Container Registry. Each image contains the web app, private Redis server, and RQ worker.

## Source Distribution

Create a GitHub repo, then push this folder:

```powershell
git init
git add .
git commit -m "Initial Clarity Image Tools release"
git branch -M main
git remote add origin https://github.com/YOUR_NAME/YOUR_REPO.git
git push -u origin main
```

Do not commit local model caches or generated images. The `.gitignore` file excludes `models/`, `storage/`, Python bytecode, and packaged archives.

Users can run from source:

```powershell
git clone https://github.com/YOUR_NAME/YOUR_REPO.git
cd YOUR_REPO
.\scripts\start.ps1
```

Linux/macOS:

```bash
git clone https://github.com/YOUR_NAME/YOUR_REPO.git
cd YOUR_REPO
chmod +x ./scripts/start.sh
./scripts/start.sh
```

## Prebuilt Images

The included GitHub Actions workflow publishes:

- `ghcr.io/addison16/imagine-clarity:latest` (CPU-compatible default)
- `ghcr.io/addison16/imagine-clarity:cpu`
- `ghcr.io/addison16/imagine-clarity:gpu`
- immutable `cpu-<short-sha>` and `gpu-<short-sha>` tags for each published commit

After a change reaches `main`, the `CI` workflow must pass before `Docker Publish` starts automatically. The publisher creates immutable CPU and GPU SHA tags, serializes publication runs, confirms the tested revision is still the current `main`, and only then promotes `:cpu`, `:gpu`, and CPU-backed `:latest`. Promotion verifies all three final digests and restores the previous mutable tags if any promotion step fails. If the package should be public, confirm its visibility in GitHub's Packages settings.

Pull requests run the separate `CI` workflow first. It checks Python, JavaScript, workflow YAML, all source/prebuilt Compose combinations, and the submitted commit range for diff hygiene; builds the CPU image; runs unit tests inside that image; starts the all-in-one container; exercises direct, queued, batch, vector, history, download, and listing-pack paths with the smoke suite; and runs the documented dependency audit. Automatic publication occurs only after that CI succeeds on the current `main` revision.

Run the prebuilt CPU image directly as one container:

```powershell
docker run -d --name imagine-clarity -p 8794:8794 -v imagine-clarity-data:/data -v imagine-clarity-models:/models ghcr.io/addison16/imagine-clarity:latest
```

Or run the same all-in-one CPU image with Compose:

```powershell
$env:CLARITY_IMAGE="ghcr.io/addison16/imagine-clarity:cpu"
docker compose -f docker-compose.prebuilt.yml up -d
```

Run the prebuilt NVIDIA GPU image directly:

```powershell
docker run -d --gpus all --name imagine-clarity -p 8794:8794 -v imagine-clarity-data:/data -v imagine-clarity-models:/models ghcr.io/addison16/imagine-clarity:gpu
```

Or use the GPU Compose override:

```powershell
$env:CLARITY_IMAGE="ghcr.io/addison16/imagine-clarity:gpu"
docker compose -f docker-compose.prebuilt.yml -f docker-compose.prebuilt.gpu.yml up -d
```

Linux/macOS:

```bash
CLARITY_IMAGE=ghcr.io/addison16/imagine-clarity:cpu docker compose -f docker-compose.prebuilt.yml up -d
```

```bash
CLARITY_IMAGE=ghcr.io/addison16/imagine-clarity:gpu docker compose -f docker-compose.prebuilt.yml -f docker-compose.prebuilt.gpu.yml up -d
```

Run prebuilt images with the helper scripts:

```powershell
.\scripts\start-prebuilt.ps1
```

```bash
chmod +x ./scripts/start-prebuilt.sh
./scripts/start-prebuilt.sh
```

Open:

```text
http://localhost:8794
```

## Notes

- CPU mode works on normal Intel and AMD CPUs.
- NVIDIA GPU mode requires NVIDIA drivers plus Docker GPU support.
- AMD and Intel graphics cards currently fall back to CPU mode.
- The first AI run downloads model weights into the Docker volume.
- Queued processing works with a plain `docker run`; Redis and the RQ worker are supervised inside the same image and Redis is bound only to the container loopback interface.
