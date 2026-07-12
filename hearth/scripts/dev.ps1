$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
Write-Host "Starting Hearth in development mode..."

$frontendDir = Join-Path $root "static\frontend"

# On Windows, npm is a .cmd file — use cmd.exe to launch it
$react = Start-Process -NoNewWindow -FilePath "cmd.exe" `
    -ArgumentList "/c", "npm.cmd", "run", "dev" `
    -WorkingDirectory $frontendDir `
    -PassThru

Write-Host "React dev server starting (PID $($react.Id))..."

# Start the backend (blocks until Ctrl+C)
# Use `python -m uvicorn` to avoid uv trampoline path issues on Windows
python -m uvicorn app.main:app --reload --port 8765

# Cleanup frontend process on exit
Stop-Process -Id $react.Id -ErrorAction SilentlyContinue

