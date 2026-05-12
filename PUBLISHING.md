# Publishing

This repo can be shared two ways:

1. Source distribution: users clone the repo and build locally with Docker Compose.
2. Prebuilt images: GitHub Actions publishes CPU and NVIDIA GPU images to GitHub Container Registry.

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

- `ghcr.io/addison16/imagine-clarity:cpu`
- `ghcr.io/addison16/imagine-clarity:gpu`

After pushing to GitHub, open the repo's Actions tab and run `Docker Publish`, or push to the `main` branch. If the package should be public, change the package visibility in GitHub's Packages settings.

Run prebuilt CPU image with Compose. This starts Redis, the web service, and the worker:

```powershell
$env:CLARITY_IMAGE="ghcr.io/addison16/imagine-clarity:cpu"
docker compose -f docker-compose.prebuilt.yml up -d
```

Run prebuilt NVIDIA GPU image with Compose. The GPU override gives both the web service and the worker NVIDIA access:

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
- Queued processing requires the Compose stack because Redis and the worker service must run beside the web service.
