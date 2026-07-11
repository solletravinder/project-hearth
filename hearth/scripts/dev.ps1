$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
Write-Host "Starting Hearth in development mode..."
Set-Location "static/frontend"
$react = Start-Process -NoNewWindow -FilePath "npm" -ArgumentList "run","dev" -PassThru
Set-Location ".."
uvicorn app.main:app --reload --port 8765
Stop-Process -Id $react.Id -ErrorAction SilentlyContinue
