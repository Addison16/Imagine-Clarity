# Security

## Supported version

Security fixes are applied to the current `main` branch and the most recent published CPU/GPU images.

## Deployment guidance

Imagine Clarity is designed as a local or trusted-network image-processing service. Before exposing it beyond the host:

- Set `CLARITY_API_KEY` and require it from automation clients.
- Replace the default `CORS_ALLOW_ORIGINS=*` with the exact trusted origins.
- Put the service behind an authenticated TLS reverse proxy.
- Keep port `8794`, Redis, model storage, and result storage off the public internet.
- Use trusted model files and keep Docker images/dependencies updated.

Redis is intentionally not published to the host by the provided Compose files.

## Dependency auditing

Pull requests audit the installed CPU image with `pip-audit`. The app currently carries two explicitly documented exception groups:

- `PYSEC-2026-1215` in `basicsr==1.4.2` has no fixed PyPI release. The reported command-injection scenario requires a crafted local `SLURM_NODELIST` environment variable and BasicSR's SLURM host-discovery path. The provided containers do not set that variable and remote API requests cannot set process environment variables. The exception should be removed when a compatible fixed BasicSR/Real-ESRGAN dependency is available.

Pillow and python-multipart are pinned to patched versions compatible with the Python 3.11 images.

The rembg HTTP-server path-traversal advisories `CVE-2026-40086` / `GHSA-55v6-g8pm-pw4c` are also explicitly excepted. Imagine Clarity imports rembg as a library, selects model names from a fixed internal map, and does not run or expose rembg's HTTP server or its attacker-controlled `model_path` parameter. The fixed rembg release requires NumPy 2.3+, which is incompatible with this Real-ESRGAN/PyTorch stack; remove the exception when those dependencies can be upgraded together.

## Reporting a vulnerability

Do not open a public issue containing exploit details, credentials, private images, or private deployment information. Contact the repository owner privately with the affected version, reproduction conditions, impact, and any proposed fix.
