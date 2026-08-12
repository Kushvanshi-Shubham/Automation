# Run the render worker on this machine against the DEPLOYED stack.
#
# Why: the free Render plan has no worker, so renders queued by the live
# API have nobody to run them. This box does the rendering (it has ffmpeg,
# Whisper and a CPU) while Neon holds the data and R2 holds the media —
# so finished videos are reachable from the live site.
#
#   .\scripts\worker-cloud.ps1
#
# Reads .env first, then .env.cloud on top (see .env.cloud.example).
# Ctrl+C stops it; nothing is left behind.

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

function Import-EnvFile($path) {
    if (-not (Test-Path $path)) { return $false }
    Get-Content $path | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $i = $line.IndexOf("=")
            $name = $line.Substring(0, $i).Trim()
            $value = $line.Substring($i + 1).Trim()
            Set-Item -Path "env:$name" -Value $value
        }
    }
    return $true
}

if (-not (Import-EnvFile ".env")) { throw ".env not found — run this from backend/" }
if (-not (Import-EnvFile ".env.cloud")) {
    throw ".env.cloud not found. Copy .env.cloud.example to .env.cloud and fill in the Neon + Redis values."
}

# Fail loudly rather than silently rendering against local Postgres.
if ($env:DATABASE_URL -notmatch "neon\.tech") {
    throw "DATABASE_URL does not look like Neon — refusing to start (check .env.cloud)."
}
if ($env:REDIS_URL -match "localhost|127\.0\.0\.1") {
    throw "REDIS_URL points at localhost — the live API cannot reach that queue (check .env.cloud)."
}
if (-not $env:S3_BUCKET_NAME) {
    throw "No S3 bucket configured — finished videos would be written to this PC and be unreachable."
}

Write-Host "Cloud worker starting" -ForegroundColor Cyan
Write-Host ("  database : " + ($env:DATABASE_URL -replace ":[^:@/]+@", ":***@"))
Write-Host ("  queue    : " + ($env:REDIS_URL -replace ":[^:@/]+@", ":***@"))
Write-Host ("  media    : " + $env:S3_BUCKET_NAME + " -> " + $env:S3_PUBLIC_URL)
Write-Host ""

# --pool=solo is required on Windows. Celery refuses -B (embedded beat) on
# Windows, so beat runs as its own process — it only drives standing orders
# and the stale-render reaper; renders work fine without it.
$beat = Start-Process -FilePath ".\.venv\Scripts\celery.exe" `
    -ArgumentList "-A", "app.pipeline.celery_app", "beat", "--loglevel=info" `
    -PassThru -NoNewWindow
Write-Host ("beat started (pid " + $beat.Id + ") — standing orders + stale-render reaper") -ForegroundColor DarkGray
Write-Host ""

try {
    & ".\.venv\Scripts\celery.exe" -A app.pipeline.celery_app worker --loglevel=info --pool=solo
}
finally {
    if ($beat -and -not $beat.HasExited) {
        Stop-Process -Id $beat.Id -Force -ErrorAction SilentlyContinue
        Write-Host "beat stopped" -ForegroundColor DarkGray
    }
}
