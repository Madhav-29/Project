param(
    [int]$ApiPort = 8000,
    [int]$FrontendPort = 8501,
    [switch]$NoFrontend
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$FrontendRoot = Join-Path $ProjectRoot "frontend"

if (-not (Test-Path $Python)) {
    throw "Virtual environment not found. Run: python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
}

function Test-PortAvailable {
    param([int]$Port)
    return -not [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Get-NpmRunner {
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($npm) {
        return @{ FilePath = $npm.Source; PrefixArgs = @() }
    }

    $node = Get-Command node -ErrorAction SilentlyContinue
    $bundledNode = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
    if (-not $node -and (Test-Path $bundledNode)) {
        $node = @{ Source = $bundledNode }
    }
    if (-not $node) {
        return $null
    }

    $npmRoot = Join-Path $env:TEMP "codex-npm"
    $npmCli = Join-Path $npmRoot "package\bin\npm-cli.js"
    if (-not (Test-Path $npmCli)) {
        New-Item -ItemType Directory -Path $npmRoot -Force | Out-Null
        $archive = Join-Path $npmRoot "npm.tgz"
        Invoke-WebRequest -Uri "https://registry.npmjs.org/npm/-/npm-10.9.2.tgz" -OutFile $archive
        tar -xzf $archive -C $npmRoot
    }
    $nodeDir = Split-Path -Parent $node.Source
    $env:PATH = "$nodeDir;$env:PATH"
    return @{ FilePath = $node.Source; PrefixArgs = @($npmCli) }
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
$env:VITE_API_URL = $env:API_URL

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

    $NpmRunner = Get-NpmRunner
    if (-not $NpmRunner) {
        Write-Host "Node.js/npm was not found. Start the React frontend manually after installing Node.js/npm, or run with -NoFrontend."
    } else {
        if (-not (Test-Path (Join-Path $FrontendRoot "node_modules"))) {
            Write-Host "Installing React frontend dependencies..."
            Start-Process -FilePath $NpmRunner.FilePath -ArgumentList ($NpmRunner.PrefixArgs + @("install")) -WorkingDirectory $FrontendRoot -Wait -WindowStyle Hidden
        }
        Write-Host "Starting React frontend on http://127.0.0.1:$FrontendPort"
        Start-Process -FilePath $NpmRunner.FilePath -ArgumentList ($NpmRunner.PrefixArgs + @("run", "dev", "--", "--host", "127.0.0.1", "--port", "$FrontendPort")) -WorkingDirectory $FrontendRoot -WindowStyle Hidden
    }
}

Start-Sleep -Seconds 5
Write-Host "Swagger: http://127.0.0.1:$ApiPort/docs"
if (-not $NoFrontend) {
    Write-Host "Frontend: http://127.0.0.1:$FrontendPort"
}
