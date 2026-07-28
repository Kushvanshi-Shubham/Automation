# Kliptos — Local Runbook

How to start, verify, and administer the full stack on this machine (Windows).
Everything below assumes you opened the repo root (`Automation/`) in VS Code.

---

## 0. One-time prerequisites — ALREADY DONE on this machine
- PostgreSQL 16 (Windows service `postgresql-x64-16`, starts automatically)
- Redis 5.0.14 (Windows service `Redis`, starts automatically)
- FFmpeg 8.1 (on PATH)
- Python venv at `backend/.venv` with all deps
- `node_modules` installed in `frontend/`
- `.env` (repo root, copied to `backend/.env`) and `frontend/.env.local` filled with keys

On a NEW machine: install those four, `pip install -r backend/requirements-dev.txt`,
`npm install` in frontend, copy `.env.example` → `.env` and fill it.

---

## 1. Start everything (the short way)

```powershell
.\scripts\dev.ps1
```

Opens three terminal windows: API (port 8000), Celery worker, frontend (port 3000).

## 2. Start everything (manually, three VS Code terminals)

**Terminal 1 — API**
```powershell
cd backend
Copy-Item ..\.env .env -Force
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

**Terminal 2 — Celery worker (renders + uploads happen here)**
```powershell
cd backend
.\.venv\Scripts\celery.exe -A app.pipeline.celery_app worker --loglevel=info --pool=solo
```

**Terminal 3 — Frontend**
```powershell
cd frontend
npm run dev
```

Open http://localhost:3000 — sign in with Google.

> If Postgres/Redis aren't running (rare — they're auto-start services):
> `Start-Service postgresql-x64-16; Start-Service Redis`

---

## 3. Verify it's healthy

```powershell
curl.exe http://localhost:8000/api/health        # {"status":"ok",...}
cd backend; .\.venv\Scripts\python.exe -m pytest tests -q   # 32 passed
cd frontend; npm run build                        # compiles clean
```

Full manual smoke test (2 minutes):
1. Sign in → dashboard shows your videos and credits
2. Topics → Refresh → real trends appear → Create Short
3. Studio → edit → Generate Video (1 credit) → watch progress → preview plays
4. (With a connected channel) Publish → video appears on YouTube

---

## 4. Admin: grant credits to any user

```powershell
.\scripts\grant_credits.ps1 -Email "friend@gmail.com" -Amount 10
```

(Writes both the balance update AND a ledger entry — never edit the balance alone.)

---

## 5. Adding a friend as a tester (while app is in Google "Testing" mode)
1. console.cloud.google.com → project `kliptos` → APIs & Services → OAuth consent screen → **Test users → Add** their Gmail.
2. Send them the app URL. They sign in with Google → get 3 free credits automatically.
3. Top them up with the script above if needed.

## 6. Known limits of local mode
- Rendered videos live in `backend/output/` (served at `/media/...`) — deploy will move this to a persistent volume/R2.
- YouTube publishing works only for accounts listed as test users until Google verifies the `youtube.upload` scope.
- Only Windows quirk: Celery must run with `--pool=solo`.

## 7. Troubleshooting
| Symptom | Fix |
|:---|:---|
| `ffmpeg` not recognized | Open a NEW terminal (PATH refreshes), or reboot VS Code |
| Renders stuck in "queued" | Worker terminal not running, or task not registered → restart Terminal 2 |
| 401 everywhere after backend restart | Sign out/in (token still valid usually; check backend .env SECRET_KEY unchanged) |
| Google OAuth redirect error | Redirect URIs must include `http://localhost:3000/api/auth/callback/google` (sign-in) and `http://localhost:8000/api/channels/callback` (channel connect) |
| Topics refresh empty | Check API terminal for source warnings; Trends RSS can rate-limit briefly |
