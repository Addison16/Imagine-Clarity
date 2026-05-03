param(
    [int]$Port = 8794
)

$ErrorActionPreference = "Continue"

function Write-Check {
    param(
        [string]$Name,
        [bool]$Ok,
        [string]$Detail = ""
    )

    $mark = if ($Ok) { "OK" } else { "WARN" }
    $line = "[$mark] $Name"
    if (-not [string]::IsNullOrWhiteSpace($Detail)) {
        $line = "$line - $Detail"
    }
    Write-Host $line
}

$docker = Get-Command docker -ErrorAction SilentlyContinue
Write-Check "Docker CLI" ([bool]$docker) ($(if ($docker) { $docker.Source } else { "Install Docker Desktop or Docker Engine." }))

if ($docker) {
    $dockerVersion = docker version --format "{{.Server.Version}}" 2>$null
    Write-Check "Docker daemon" ($LASTEXITCODE -eq 0) ($(if ($LASTEXITCODE -eq 0) { "server $dockerVersion" } else { "Docker daemon is not reachable." }))

    $composeVersion = docker compose version --short 2>$null
    Write-Check "Docker Compose" ($LASTEXITCODE -eq 0) ($(if ($LASTEXITCODE -eq 0) { $composeVersion } else { "Docker Compose v2 is required." }))

    $runtimes = docker info --format "{{json .Runtimes}}" 2>$null
    Write-Check "NVIDIA Docker runtime" ($LASTEXITCODE -eq 0 -and $runtimes -match '"nvidia"') "Needed only for NVIDIA GPU acceleration."
}

$adapters = Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue
if ($adapters) {
    Write-Host ""
    Write-Host "Detected display adapters:"
    $adapters | ForEach-Object {
        Write-Host "  - $($_.Name)"
    }
}

$nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvidiaSmi) {
    $gpuName = (& nvidia-smi --query-gpu=name --format=csv,noheader 2>$null | Select-Object -First 1)
    Write-Check "NVIDIA host GPU" (-not [string]::IsNullOrWhiteSpace($gpuName)) $gpuName
} else {
    Write-Check "NVIDIA host GPU" $false "nvidia-smi was not found. CPU mode will still work."
}

$health = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$Port/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
if ($health -and $health.StatusCode -eq 200) {
    Write-Check "Clarity service" $true "http://localhost:$Port"
    try {
        $body = $health.Content | ConvertFrom-Json
        $runtime = $body.runtime
        Write-Host "  Torch: $($runtime.torch)"
        Write-Host "  CUDA available: $($runtime.cuda_available)"
        Write-Host "  CUDA device: $($runtime.cuda_device)"
        Write-Host "  ONNX providers: $($runtime.onnx_providers -join ', ')"
    } catch {
        Write-Host "  Health endpoint returned non-JSON content."
    }
} else {
    Write-Check "Clarity service" $false "Not running on http://localhost:$Port."
}

Write-Host ""
Write-Host "Summary:"
Write-Host "  - CPU mode works on normal Intel/AMD CPUs through the base Docker image."
Write-Host "  - NVIDIA GPU mode requires an NVIDIA GPU plus Docker GPU support."
Write-Host "  - AMD/Intel graphics are detected as display adapters, but this Docker image does not accelerate with them yet."
