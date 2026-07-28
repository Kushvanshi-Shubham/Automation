# Kliptos dev launcher — starts API, Celery worker, and frontend in separate windows.
$root = Split-Path $PSScriptRoot -Parent

foreach ($svc in @("postgresql-x64-16", "Redis")) {
    $s = Get-Service $svc -ErrorAction SilentlyContinue
    if ($s -and $s.Status -ne "Running") { Start-Service $svc }
}

Copy-Item "$root\.env" "$root\backend\.env" -Force

Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$root\backend'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"

Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$root\backend'; .\.venv\Scripts\celery.exe -A app.pipeline.celery_app worker --loglevel=info --pool=solo"

Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$root\frontend'; npm run dev"

Write-Host "Kliptos starting: API :8000 | worker | frontend :3000"
Write-Host "Open http://localhost:3000"
