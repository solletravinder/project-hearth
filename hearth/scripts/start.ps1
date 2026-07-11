$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
Write-Host "Building React frontend..."
Set-Location "static/frontend"
npm run build
Set-Location ".."
Write-Host "Starting Hearth server..."
uvicorn app.main:app --reload --port 8765
