param(
    [int]$Port = 8794,
    [switch]$ForceCpu,
    [switch]$ForceGpu
)

$ErrorActionPreference = "Stop"
$env:HOST_PORT = "$Port"

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
    $cuda = docker exec clarity-upscaler python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')" 2>$null
    return $LASTEXITCODE -eq 0 -and $cuda[0] -eq "True"
}

function Start-Cpu {
    Write-Host "Starting Clarity Image Tools with CPU support on port $Port."
    docker compose up --build -d
}

function Write-DetectedDisplayAdapters {
    $adapters = Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue
    if ($adapters) {
        $names = ($adapters | ForEach-Object { $_.Name }) -join "; "
        Write-Host "Detected display adapters: $names"
    }
}

$useGpu = $false
if ($ForceCpu -and $ForceGpu) {
    throw "Use either -ForceCpu or -ForceGpu, not both."
}
if ($ForceGpu) {
    $useGpu = $true
} elseif (-not $ForceCpu) {
    $useGpu = (Test-NvidiaHost) -and (Test-DockerNvidiaRuntime)
}

Write-DetectedDisplayAdapters

if ($useGpu) {
    Write-Host "Starting Clarity Image Tools with NVIDIA GPU support on port $Port."
    docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build -d
    if ($LASTEXITCODE -ne 0) {
        if ($ForceGpu) {
            exit $LASTEXITCODE
        }
        Write-Warning "GPU startup failed. Falling back to CPU."
        Start-Cpu
    } elseif ((Wait-ContainerHealthy) -and (Test-ContainerCuda)) {
        Write-Host "GPU runtime verified inside the container."
    } else {
        if ($ForceGpu) {
            throw "GPU container started, but CUDA was not available inside the container."
        }
        Write-Warning "GPU was detected on the host, but CUDA was not available inside the container. Falling back to CPU."
        Start-Cpu
    }
} else {
    if (-not $ForceCpu) {
        Write-Host "No usable NVIDIA Docker runtime was verified. Intel/AMD CPUs will run in CPU mode; AMD/Intel graphics are not accelerated by this image yet."
    }
    Start-Cpu
}

Write-Host "Open http://localhost:$Port"
