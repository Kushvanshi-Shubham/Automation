# S1 Build Log

Running log of actual build work. Newest first.

## 2026-07-28 — Topic Harvester live (first pipeline feature)
- `app/services/harvester.py`: Google Trends RSS (no key needed, **live-verified: 10 real topics harvested**) + Reddit via app-only OAuth (skips cleanly until `REDDIT_CLIENT_ID/SECRET` provided — Reddit 403-blocks unauthenticated server calls since the 2023 API lockdown)
- Dedupe by sha256 content hash (cross-run and within-run); log-scaled 0–100 scores; template hooks (LLM hooks come with script studio)
- `POST /topics/refresh` implemented; Topics page rewritten: react-query on real API, loading skeletons, empty state, live Refresh button — MOCK_TOPICS deleted
- 16 backend tests green; frontend build green

## 2026-07-28 — ✅ AUTH CONFIRMED WORKING (owner browser test)
Owner signed in with Google end-to-end: dashboard shows real user + 3 signup credits. First fully-working user-facing feature. Next: topic harvester (key-free via Google Trends RSS + Reddit public JSON), then script studio (awaits OPENAI_API_KEY) and pipeline (awaits PEXELS_API_KEY).

## 2026-07-28 — OAuth live + pub/sub bridge + typed API client
- Google OAuth creds wired (backend `.env` + frontend `.env.local`); NextAuth providers endpoint confirms google/OIDC with correct callback; `/dashboard` unauthed → 307 to `/sign-in`. **Interactive browser sign-in test pending owner.**
- **Redis pub/sub progress bridge shipped** (audit §3.2 closed): workers publish via `app/services/progress.py`, WS endpoint is a pure subscriber. Dead in-memory `ConnectionManager` deleted. Integration test proves worker→Redis→WS delivery (12 tests green). redis-py pinned to RESP2 (`protocol=2`) for the Redis 5.0 Windows port.
- **OpenAPI-typed client**: spec exported (25 paths) → `frontend/src/lib/api-types.ts` via `npm run gen:api`. `use-pipeline` WS URL now derived from `NEXT_PUBLIC_API_URL`.
- Both dev servers running: API :8000, Next.js :3000.

## 2026-07-28 — Repo consolidation + local infra live
- **Monorepo pushed to GitHub** (`Kushvanshi-Shubham/Automation`) incl. docs + this vault; old `frontend` repo **archived** (delete pending `delete_repo` scope from owner)
- **Local stack installed and verified on this machine:**
  - FFmpeg 8.1 (winget) ✅
  - PostgreSQL 16.14 as Windows service, `kliptos` DB created, **Alembic migration applied — 6 tables live** ✅
  - Redis 5.0.14 (tporadowski Windows port) as service `Redis`, PONG ✅ — Memurai MSI failed twice (SFXCA temp-dir bug, error 1603)
  - Live API smoke test on real Postgres: `/api/health` OK; 401s enforced with no token; authed `/auth/me`, `/billing/credits`, `/videos` all return real DB data ✅
- Config fix: `CORS_ORIGINS` now `NoDecode` + validator (accepts comma-separated env values); `.env` files must be BOM-free (PowerShell `Out-File` gotcha)
- Server start: `cd backend; .venv\Scripts\python -m uvicorn app.main:app --port 8000`

## 2026-07-28 — Auth milestone shipped (commits 3da7243, 73090f1)
**Backend** (11 tests green):
- Monorepo merge done; hardened config (SECRET_KEY required + placeholder rejection, Fernet TOKEN_ENCRYPTION_KEY)
- Real Google ID-token verification → JWT → `get_current_user` from DB; signup grants 3 credits via ledger; idempotent login
- All routers auth-required; unbuilt features return **501**, never fake data; videos/topics/billing wired to real DB queries
- Alembic initialized with initial migration; startup `create_all` deleted; `User.role` + `country` added

**Frontend** (`next build` green):
- NextAuth v5: Google sign-in → backend token exchange in jwt callback; httpOnly session (localStorage token removed)
- Dashboard gated by server-component layout; shell shows real user + live credits
- Correction: `shadcn` v4 IS a runtime dep (`shadcn/tailwind.css`) — restored; only Prisma was unused
- Gotcha fixed: first commit recorded `frontend/` as a gitlink (submodule) — replaced with tracked files

**Environment notes:** no Docker/FFmpeg on this machine — Postgres/Redis and the render pipeline need infra decisions; tests run on SQLite meanwhile. Python 3.14, Node 24.

**Next up:** OpenAPI-generated TS client → Redis pub/sub progress bridge → topic harvester → script studio (GPT-4o) → Pexels+edge-tts pipeline.
**Blocked on owner:** Google OAuth client credentials (`AUTH_GOOGLE_ID/SECRET` + backend `GOOGLE_CLIENT_ID`) and starting the `youtube.upload` verification application.

## 2026-07-28 — Kickoff
- Audits complete ([[Project Audit]], [[Business Audit]]), scope approved, vault created
- Starting: monorepo merge → backend foundation (config hardening, Alembic, real auth) → frontend auth wiring
- ⚠️ Owner action item: start Google Cloud OAuth consent-screen verification for `youtube.upload` scope (longest external lead time)

Links: [[Home]] · [[Roadmap]]
