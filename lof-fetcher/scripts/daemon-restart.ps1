#!/usr/bin/env pwsh
# One-shot daemon restart helper (go-live convenience).
#
# Detect a running daemon -> graceful stop -> start a fresh one, so dev-003 /
# dev-005 never have to manually hunt and kill PIDs again. Run from anywhere;
# the script cds into the lof-fetcher dir relative to its own location.
#
# Usage:
#   pwsh scripts/daemon-restart.ps1            # stop old (if any) + start new (background)
#   pwsh scripts/daemon-restart.ps1 -Status    # just report status
#   pwsh scripts/daemon-restart.ps1 -Stop      # just stop
#   pwsh scripts/daemon-restart.ps1 -Foreground # run in this console (Ctrl+C to stop)
param(
    [switch]$Status,
    [switch]$Stop,
    [switch]$Foreground
)

$ErrorActionPreference = "Stop"
$fetcherDir = Split-Path -Parent $PSScriptRoot   # lof-fetcher/
Set-Location $fetcherDir

if ($Status) {
    python -m fetcher.main daemon --status
    exit $LASTEXITCODE
}

# Always stop any existing instance first (no-op if none running).
Write-Host "[daemon-restart] stopping any existing daemon..."
python -m fetcher.main daemon --stop

if ($Stop) {
    exit $LASTEXITCODE
}

if ($Foreground) {
    Write-Host "[daemon-restart] starting daemon in foreground (Ctrl+C to stop)..."
    python -m fetcher.main daemon
    exit $LASTEXITCODE
}

Write-Host "[daemon-restart] starting fresh daemon in background..."
$proc = Start-Process -FilePath "python" -ArgumentList "-m","fetcher.main","daemon" -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 2
python -m fetcher.main daemon --status
Write-Host "[daemon-restart] launched (host pid=$($proc.Id)). Use -Stop to terminate, -Status to check."
