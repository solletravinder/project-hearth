#!/usr/bin/env pwsh
# reset.ps1 — Remove DB & uploads for a fresh project start.

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Path (Split-Path -Path $PSScriptRoot -Parent) -Parent

Write-Host "This will DELETE all data (database + uploaded files) and reset Hearth to a fresh state." -ForegroundColor Yellow
$confirm = Read-Host "Are you sure? [y/N] "

if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Host "Aborted." -ForegroundColor Red
    exit 1
}

$dbDir = Join-Path $ProjectRoot 'data'
$dbFiles = @(
    Join-Path $dbDir 'hearth.db',
    Join-Path $dbDir 'hearth.db-wal',
    Join-Path $dbDir 'hearth.db-shm'
)

foreach ($f in $dbFiles) {
    if (Test-Path $f) {
        Remove-Item -Path $f -Force
        Write-Host "Removed: $f" -ForegroundColor DarkGray
    }
}

$uploadsDir = Join-Path $ProjectRoot 'data' 'uploads'
if (Test-Path $uploadsDir) {
    Remove-Item -Path $uploadsDir -Recurse -Force
    Write-Host "Removed: $uploadsDir" -ForegroundColor DarkGray
}

New-Item -ItemType Directory -Path $uploadsDir -Force | Out-Null
New-Item -ItemType File -Path (Join-Path $uploadsDir '.gitkeep') -Force | Out-Null

Write-Host ""
Write-Host "Done. All data has been reset." -ForegroundColor Green
Write-Host "Run the server and the first-run wizard will re-initialize the database." -ForegroundColor Gray
