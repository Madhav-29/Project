param(
    [int]$ApiPort = 8000,
    [int]$FrontendPort = 8501,
    [switch]$NoFrontend
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Virtual environment not found. Run: python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
}

function Test-PortAvailable {
    param([int]$Port)
    return -not [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

if (-not (Test-PortAvailable $ApiPort)) {
    $fallback = 8001
    while (-not (Test-PortAvailable $fallback)) {
        $fallback++
    }
    Write-Host "API port $ApiPort is busy. Using $fallback instead."
    $ApiPort = $fallback
}

$env:API_URL = "http://127.0.0.1:$ApiPort"

Write-Host "Starting Clinical Gap Intelligence API on $env:API_URL"
Start-Process -FilePath $Python -ArgumentList "-m", "uvicorn", "app.api.main:app", "--host", "127.0.0.1", "--port", "$ApiPort" -WorkingDirectory $ProjectRoot -WindowStyle Hidden

if (-not $NoFrontend) {
    if (-not (Test-PortAvailable $FrontendPort)) {
        $fallbackFrontend = 8502
        while (-not (Test-PortAvailable $fallbackFrontend)) {
            $fallbackFrontend++
        }
        Write-Host "Frontend port $FrontendPort is busy. Using $fallbackFrontend instead."
        $FrontendPort = $fallbackFrontend
    }

    Write-Host "Starting Streamlit frontend on http://127.0.0.1:$FrontendPort"
    Start-Process -FilePath $Python -ArgumentList "-m", "streamlit", "run", "frontend\streamlit_app.py", "--server.port", "$FrontendPort", "--server.headless", "true", "--browser.gatherUsageStats", "false" -WorkingDirectory $ProjectRoot -WindowStyle Hidden
}

Start-Sleep -Seconds 5
Write-Host "Swagger: http://127.0.0.1:$ApiPort/docs"
if (-not $NoFrontend) {
    Write-Host "Frontend: http://127.0.0.1:$FrontendPort"
}
