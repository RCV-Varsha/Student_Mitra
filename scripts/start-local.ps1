param([switch]$Seed)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
Set-Location $root
if (!(Test-Path '.env')) { Copy-Item '.env.example' '.env'; Write-Host 'Configure .env, then rerun.'; exit 1 }
if (!(Test-Path '.venv')) { python -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock
Push-Location frontend
npm.cmd ci
npm.cmd run build
Pop-Location
& .\.venv\Scripts\python.exe backend/manage.py migrate
& .\.venv\Scripts\python.exe backend/manage.py collectstatic --noinput
if ($Seed) { & .\.venv\Scripts\python.exe backend/manage.py seed_demo --admin }
Start-Process -FilePath "$root\.venv\Scripts\python.exe" -ArgumentList @('backend/manage.py','worker') -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput "$root\worker.log" -RedirectStandardError "$root\worker-error.log"
& .\.venv\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8000 --noreload
