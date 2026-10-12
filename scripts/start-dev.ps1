[CmdletBinding()]
param(
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$backendRoot = Join-Path $repoRoot "backend\api"
$frontendRoot = Join-Path $repoRoot "frontend\web"
$backendPython = Join-Path $backendRoot ".venv\Scripts\python.exe"
$frontendPackage = Join-Path $frontendRoot "package.json"
$frontendModules = Join-Path $frontendRoot "node_modules"
$logRoot = Join-Path $repoRoot "tmp\dev-logs"
$frontendUrl = "http://localhost:3001"
# Uvicorn is bound to IPv4 below. Use the same address for the readiness probe because
# Windows may resolve localhost to ::1 first and never reach the IPv4-only listener.
$backendHealthUrl = "http://127.0.0.1:8000/health/live"
$startedProcesses = New-Object "System.Collections.Generic.List[System.Diagnostics.Process]"

function Assert-PortAvailable {
    param([int]$Port, [string]$ServiceName)

    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($listener) {
        $process = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
        $processName = if ($process) { $process.ProcessName } else { "PID $($listener.OwningProcess)" }
        throw "$ServiceName port $Port is already used by $processName. Stop it and try again."
    }
}

function Wait-ForHttp {
    param([string]$Url, [string]$ServiceName, [int]$TimeoutSeconds = 45)

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                Write-Host "[OK] $ServiceName is ready: $Url" -ForegroundColor Green
                return
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    } while ((Get-Date) -lt $deadline)

    throw "$ServiceName did not become ready in $TimeoutSeconds seconds. Check $logRoot."
}

function Stop-StartedProcess {
    param([System.Diagnostics.Process]$Process, [string]$ServiceName)

    if ($Process -and -not $Process.HasExited) {
        Write-Host "Stopping $ServiceName ..." -ForegroundColor DarkGray
        & taskkill.exe /PID $Process.Id /T /F 2>$null | Out-Null
    }
}

if (-not (Test-Path -LiteralPath $backendPython)) {
    throw "Backend virtual environment was not found: $backendPython"
}
if (-not (Test-Path -LiteralPath $frontendPackage)) {
    throw "Frontend project was not found: $frontendPackage"
}
if (-not (Test-Path -LiteralPath $frontendModules)) {
    throw "Frontend dependencies are missing. Run npm install in frontend/web first."
}

Assert-PortAvailable -Port 8000 -ServiceName "Backend"
Assert-PortAvailable -Port 3001 -ServiceName "Frontend"
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null

$previousEnvironment = @{
    APP_ENV = $env:APP_ENV
    AUTH_SECRET_KEY = $env:AUTH_SECRET_KEY
    CORS_ORIGINS = $env:CORS_ORIGINS
    NEXT_PUBLIC_API_BASE_URL = $env:NEXT_PUBLIC_API_BASE_URL
    NEXT_PUBLIC_ENABLE_DEMO_AUTH = $env:NEXT_PUBLIC_ENABLE_DEMO_AUTH
}

try {
    $randomBytes = New-Object byte[] 48
    $randomGenerator = New-Object System.Security.Cryptography.RNGCryptoServiceProvider
    try {
        $randomGenerator.GetBytes($randomBytes)
    }
    finally {
        $randomGenerator.Dispose()
    }

    $env:APP_ENV = "local"
    $env:AUTH_SECRET_KEY = [Convert]::ToBase64String($randomBytes)
    $env:CORS_ORIGINS = '["http://localhost:3001","http://127.0.0.1:3001"]'

    Write-Host "Starting backend API on port 8000 ..." -ForegroundColor Cyan
    $backendProcess = Start-Process -FilePath $backendPython `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $backendRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logRoot "backend.out.log") `
        -RedirectStandardError (Join-Path $logRoot "backend.err.log") `
        -PassThru
    $startedProcesses.Add($backendProcess)

    # Keep browser and API on the same localhost site so SameSite HttpOnly cookies work.
    $env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000"
    $env:NEXT_PUBLIC_ENABLE_DEMO_AUTH = "false"

    Write-Host "Starting frontend workspace on port 3001 ..." -ForegroundColor Cyan
    $frontendProcess = Start-Process -FilePath "npm.cmd" `
        -ArgumentList @("run", "dev") `
        -WorkingDirectory $frontendRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logRoot "frontend.out.log") `
        -RedirectStandardError (Join-Path $logRoot "frontend.err.log") `
        -PassThru
    $startedProcesses.Add($frontendProcess)

    Wait-ForHttp -Url $backendHealthUrl -ServiceName "Backend API"
    Wait-ForHttp -Url $frontendUrl -ServiceName "Frontend workspace"

    Write-Host ""
    Write-Host "Frontend and backend are running." -ForegroundColor Green
    Write-Host "Web app: $frontendUrl"
    Write-Host "API docs: http://localhost:8000/docs"
    Write-Host "Login mode: backend account authentication (HttpOnly Cookie)"
    Write-Host "Logs: $logRoot"
    Write-Host "Keep this window open. Press Ctrl+C to stop both services." -ForegroundColor Yellow

    if (-not $NoBrowser) {
        Start-Process $frontendUrl
    }

    while ($true) {
        if ($backendProcess.HasExited) {
            throw "Backend exited with code $($backendProcess.ExitCode). Check the backend log."
        }
        if ($frontendProcess.HasExited) {
            throw "Frontend exited with code $($frontendProcess.ExitCode). Check the frontend log."
        }
        Start-Sleep -Seconds 1
    }
}
finally {
    for ($index = $startedProcesses.Count - 1; $index -ge 0; $index--) {
        $serviceName = if ($index -eq 0) { "Backend API" } else { "Frontend workspace" }
        Stop-StartedProcess -Process $startedProcesses[$index] -ServiceName $serviceName
    }

    foreach ($name in $previousEnvironment.Keys) {
        $value = $previousEnvironment[$name]
        if ($null -eq $value) {
            Remove-Item "Env:$name" -ErrorAction SilentlyContinue
        }
        else {
            Set-Item "Env:$name" $value
        }
    }
}

