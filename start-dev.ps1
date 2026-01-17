$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendPath = Join-Path $repoRoot "frontend"
$backendPath = $repoRoot

if (-not (Test-Path $frontendPath)) {
	throw "Frontend folder not found at: $frontendPath"
}

# Start backend in background
Write-Host "🚀 Starting Backend Server..." -ForegroundColor Green
Set-Location $backendPath
$env:PYTHONPATH = "$backendPath"
$backendProcess = Start-Process powershell -PassThru -ArgumentList `
	"-NoExit", `
	"-Command", `
	".\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 3

# Start frontend
Write-Host "🌐 Starting Frontend Server..." -ForegroundColor Cyan
Set-Location $frontendPath

if (Get-Command bun -ErrorAction SilentlyContinue) {
	bun run dev
} else {
	npm run dev
}
