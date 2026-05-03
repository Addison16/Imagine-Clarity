param(
    [int]$Port = 8794,
    [string]$ImagePrefix = "ghcr.io/addison16/imagine-clarity",
    [switch]$ForceCpu,
    [switch]$ForceGpu
)

$ErrorActionPreference = "Stop"

if ($ForceCpu -and $ForceGpu) {
    throw "Use either -ForceCpu or -ForceGpu, not both."
}

function Test-NvidiaHost {
    if (-not (Get-Command nvidia-smi -ErrorAction SilentlyContinue)) {
        return $false
    }

    $gpuName = (& nvidia-smi --query-gpu=name --format=csv,noheader 2>$null | Select-Object -First 1)
    return -not [string]::IsNullOrWhiteSpace($gpuName)
}

function Test-DockerNvidiaRuntime {
    $runtimes = docker info --format "{{json .Runtimes}}" 2>$null
    return $LASTEXITCODE -eq 0 -and $runtimes -match '"nvidia"'
}

$useGpu = $false
if ($ForceGpu) {
    $useGpu = $true
} elseif (-not $ForceCpu) {
    $useGpu = (Test-NvidiaHost) -and (Test-DockerNvidiaRuntime)
}

$env:HOST_PORT = "$Port"

if ($useGpu) {
    $env:CLARITY_IMAGE = "$ImagePrefix`:gpu"
    Write-Host "Pulling and starting NVIDIA GPU image $env:CLARITY_IMAGE on port $Port."
    docker compose -f docker-compose.prebuilt.yml -f docker-compose.prebuilt.gpu.yml up -d
} else {
    $env:CLARITY_IMAGE = "$ImagePrefix`:cpu"
    Write-Host "Pulling and starting CPU image $env:CLARITY_IMAGE on port $Port."
    docker compose -f docker-compose.prebuilt.yml up -d
}

Write-Host "Open http://localhost:$Port"
