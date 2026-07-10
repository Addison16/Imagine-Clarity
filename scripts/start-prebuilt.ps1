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

function Wait-ContainerHealthy {
    param([int]$Seconds = 180)
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        $status = docker inspect clarity-upscaler --format "{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}" 2>$null
        if ($LASTEXITCODE -eq 0 -and $status -match "running healthy") {
            return $true
        }
        Start-Sleep -Seconds 3
    }
    return $false
}

function Test-ContainerCuda {
    $cuda = docker exec clarity-upscaler python -c "import torch; print(torch.cuda.is_available())" 2>$null
    return $LASTEXITCODE -eq 0 -and (($cuda | Select-Object -First 1) -eq "True")
}

function Start-Cpu {
    $env:CLARITY_IMAGE = "$ImagePrefix`:cpu"
    Write-Host "Pulling and starting CPU image $env:CLARITY_IMAGE on port $Port."
    docker compose -f docker-compose.prebuilt.yml up -d --pull always --remove-orphans
    if ($LASTEXITCODE -ne 0 -or -not (Wait-ContainerHealthy)) {
        throw "CPU container failed to become healthy."
    }
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
    docker compose -f docker-compose.prebuilt.yml -f docker-compose.prebuilt.gpu.yml up -d --pull always --remove-orphans
    $gpuReady = $LASTEXITCODE -eq 0 -and (Wait-ContainerHealthy) -and (Test-ContainerCuda)
    if ($gpuReady) {
        Write-Host "GPU runtime verified inside the container."
    } elseif ($ForceGpu) {
        throw "GPU image started but CUDA verification failed."
    } else {
        Write-Warning "GPU startup or verification failed. Falling back to CPU."
        Start-Cpu
    }
} else {
    Start-Cpu
}

Write-Host "Open http://localhost:$Port"
