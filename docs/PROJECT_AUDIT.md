# Kliptos — Project Audit (Phase 1 + 2)
**Date:** 2026-07-28
**Scope:** `Kushvanshi-Shubham/frontend` (master @ ed5fcad) and `Kushvanshi-Shubham/Automation` (master @ ed60025), plus `implementation_plan.md` (Master Plan v3)
**Method:** Complete source read of every file in both repositories. No assumptions — every claim below cites actual code.

---

## 0. Executive Summary — The Honest Verdict

**This is not a partially built product. It is a design prototype + API skeleton with zero working business logic.**

- **Every backend endpoint returns hardcoded dummy data.** `auth.py` returns `"dummy_token"`, `topics.py` returns `{"items": []}`, `billing.py` returns a fake Stripe URL string. Not one endpoint touches the database.
- **The Celery "pipeline" is three `time.sleep(1)` calls** (`tasks.py`). No script generation, no TTS, no video rendering, no YouTube upload exists anywhere.
- **The frontend is a good-looking mock.** Landing page, dashboard, and topics page render hardcoded arrays (`MOCK_TOPICS`, "128 Total Shorts", "2.4M views"). The Google sign-in button has no onClick handler. 6 of 8 dashboard pages literally say "Coming soon."
- **The two repos are not connected.** No frontend page calls the backend. The two hooks that *could* (`use-credits`, `use-pipeline`) target endpoints/message-shapes the backend doesn't serve (details in §4).
- **Zero tests, zero migrations, zero CI/CD, zero logging, zero error handling, zero auth.**

The plan's own status column (🔶 Stub everywhere) is accurate. Completion estimate: **~5–10% of an MVP** — essentially the scaffold and UI shell, i.e., roughly what "Phase 1 ✅ DONE — Foundation" claims, and nothing more.

**The good news:** the scaffold is clean, the stack choices are sensible, the plan document is genuinely well thought out, and the UI design taste is above average. There is nothing here that needs to be thrown away — but nearly everything remains to be built.

---

## 1. Repository & Architecture Map

### Repo 1: `Automation` (backend only — despite README claiming a monorepo)
```
backend/app/
├── main.py          FastAPI app, CORS, router mounting, WS endpoint, create_all on startup
├── config.py        pydantic-settings; SECRET_KEY defaults to "secret"
├── database.py      async SQLAlchemy engine + session factory
├── models/          User, Channel, Video, CreditLedger, PipelineJob, Topic (real, decent)
├── schemas/         Pydantic request/response models (thin but present)
├── routers/         8 routers — ALL hardcoded stub responses
├── middleware/      auth.py (placeholder returns {"id": "user_id"}), credits.py (no-op)
├── pipeline/        celery_app.py (configured), tasks.py (sleep-loop), visuals/base.py (empty ABC)
└── websocket/       In-memory ConnectionManager (single-process only)
docker-compose.yml   postgres + redis + api + worker (no frontend service)
```

### Repo 2: `frontend` (Next.js 16.2.12, React 19, Tailwind v4, shadcn/ui)
```
src/app/
├── page.tsx                     Landing page — polished, static
├── (auth)/sign-in/page.tsx      Google button with NO handler
├── dashboard/layout.tsx         Sidebar shell — hardcoded "42/50 credits", "Shubham / Pro Plan"
├── dashboard/page.tsx           Stats + pipeline card — all mock data
├── dashboard/topics/page.tsx    MOCK_TOPICS array, fake refresh (setTimeout)
└── dashboard/{studio,uploads,analytics,settings,billing,preview/[id]}  → "Coming soon" stubs
src/hooks/  use-credits.ts, use-pipeline.ts   (written but unused by any page)
src/lib/    api-client.ts (hardcoded http://localhost:8000, localStorage token)
```

### Data flow as it exists today
`Frontend mock data → screen`. `Backend request → hardcoded dict → response`. The two never meet.

### Data flow as designed (plan v3)
Vercel (Next.js + NextAuth) → Railway (FastAPI + Celery + Redis + Postgres) → R2/YouTube/Stripe. Reasonable and cost-appropriate.

---

## 2. Scorecard

| Dimension | Score | Why |
|:---|:---:|:---|
| **Architecture** | 5/10 | Planned shape is sound (FastAPI + Celery + Redis + Postgres is the right choice for a video pipeline). Deductions: split-brain repos, unresolved Prisma-vs-SQLAlchemy conflict (§3.1), WS design that can't work across processes (§3.2). |
| **Code Quality** | 4/10 | What exists is clean and idiomatic, but it's trivial — there's no logic to judge. `Any` return types on every router defeat FastAPI's validation. |
| **Maintainability** | 6/10 | Small, well-organized, consistent naming. Easy to build on. |
| **Scalability** | 3/10 | In-memory WebSocket manager breaks with >1 API instance or any Celery worker (§3.2). No pagination anywhere. No caching. |
| **Security** | 1/10 | No auth at all; `SECRET_KEY="secret"` default; OAuth tokens as plaintext columns; localStorage JWT (XSS-prone, contradicts plan's own httpOnly claim); no rate limiting; no RBAC; no roles column even in the model. |
| **Performance** | 3/10 | N/A mostly (no logic). `create_all` on startup, sync `time.sleep` in async-adjacent worker are bad omens. |
| **Database Design** | 4/10 | 6 models are a decent v1 core. Missing: roles, subscriptions, OneFlancer entities (brand/campaign/media_kit), indexes on FKs, enums (status/plan are free-text String), soft deletes, audit tables, and there are **no Alembic migrations** despite alembic being in requirements. |
| **UI (visual)** | 7/10 | Genuinely good dark-mode design — glassmorphism, motion, consistent violet/blue system. Best asset in the codebase. |
| **UX (functional)** | 2/10 | Nothing is clickable-through. No loading/empty/error states beyond decoration. Sign-in does nothing. |
| **API Design** | 5/10 | RESTful, sensibly grouped, tagged. Missing: pagination, filtering, versioning, error envelope, auth dependencies actually applied (routers import `Depends` but never use `get_current_user`). |
| **Business Logic** | 1/10 | None exists. |
| **Error Handling** | 1/10 | Zero try/except in the entire backend; frontend `fetchApi` throws raw strings. |
| **Logging** | 1/10 | Not a single logger anywhere. |
| **Testing** | 0/10 | Zero test files in either repo. |
| **Documentation** | 5/10 | Plan v3 is excellent. READMEs are stale/wrong (claim Next.js 15 + monorepo frontend that doesn't exist; `.env.example` still says "Brainly"). |
| **Deployment Readiness** | 2/10 | Backend Dockerfile OK; docker-compose works for local dev only. No frontend Dockerfile/service, no CI/CD, no prod config, no health checks beyond `/api/health`. |

**Overall: 3/10** — a well-drawn blueprint with a foundation slab poured. Not launchable, not demo-able beyond static screens.

---

## 3. Critical Findings (fix-before-anything-else)

### 3.1 Unresolved ORM/ownership conflict: Prisma vs SQLAlchemy
`frontend/package.json` includes `prisma`, `@prisma/client`, and `@auth/prisma-adapter` — but there is **no `prisma/schema.prisma`** in the repo, and the backend owns Postgres via SQLAlchemy. Two ORMs in two languages against one database is a recipe for drift. **Decision needed:** either NextAuth uses JWT-only sessions (no adapter, no Prisma — backend owns all data), or auth tables live in Prisma and everything else in SQLAlchemy (painful). Recommendation: **drop Prisma entirely; JWT session strategy; FastAPI owns the DB.**

### 3.2 The WebSocket progress design cannot work as written
`ConnectionManager` holds connections in a Python dict inside the API process. Celery workers run in a **separate container** — they can never call `manager.broadcast()`. Progress updates will silently never arrive. Fix: worker publishes to **Redis pub/sub**; API's WS handler subscribes and forwards. (Also: the WS endpoint has no auth — anyone can subscribe to any job_id.)

### 3.3 Frontend/backend contract mismatches (already, with only 2 hooks)
- `use-credits.ts` calls `GET /users/me/credits` → backend serves `GET /billing/credits`. 404.
- `use-pipeline.ts` expects WS messages `{status, stage, progress}` → `tasks.py` emits `{stage, percent}`. Fields never match.
- `api-client.ts` reads `localStorage["auth_token"]` → nothing ever writes it, and plan v3 promises httpOnly cookies (mutually exclusive with localStorage).
**Fix:** define one OpenAPI-generated client (FastAPI exports the spec for free) before writing more hooks.

### 3.4 Secrets & token handling
- `SECRET_KEY: str = "secret"` default will ship to prod silently. Make it required (no default) so boot fails loudly.
- `Channel.access_token/refresh_token` are plaintext `String` columns. Plan promises AES-256 at rest — implement before storing a single real YouTube token.
- `.env.example` shows a real-looking structure but branding says "Brainly" — stale copy-paste; also `CORS_ORIGINS` as JSON-in-env needs a pydantic validator or it will crash on parse.

### 3.5 `create_all` instead of migrations
`main.py` runs `Base.metadata.create_all` at startup. With Alembic already in requirements, this is pure debt: it can't alter columns, can't roll back, and will fight Alembic later. Initialize Alembic now, delete the lifespan create_all.

### 3.6 No auth applied anywhere
`get_current_user` exists but **no router uses it**. Every endpoint is public. When implemented, it must be a dependency on every non-auth router via `APIRouter(dependencies=[...])`, not per-endpoint opt-in (opt-in is how endpoints get forgotten).

---

## 4. Notable Inconsistencies

| Where | Issue |
|:---|:---|
| Landing page pricing | Sells "720p/1080p/4K exports, voice cloning, API access" — none of which appear in plan v3's feature set (plan sells watermark/engines/OneFlancer). Two different products are being advertised. |
| Logo | Says "B" (Brainly leftover) next to the name "Kliptos", in 3 places. |
| Automation README | Claims `Automation/frontend` exists (it doesn't) and says Next.js 15 (actual: 16.2.12 in the other repo). |
| `next-auth` v5 beta | Installed, never configured — no `auth.ts`, no route handler, no middleware. |
| `shadcn` | Listed as a runtime dependency — it's a CLI; remove it. |
| Dashboard sidebar | Missing routes the plan requires: billing page exists as stub but isn't in nav; no preview link; no OneFlancer section. |
| docker-compose | `version: "3.9"` key is deprecated; no frontend service; `--reload` + volume mount fine for dev but the same file is the only deployment story. |
| Frontend repo | No `.env.example`, no Dockerfile, `AGENTS.md` warns Next 16 has breaking APIs vs training data (relevant for AI-assisted dev: read `node_modules/next/dist/docs/` after `npm install`). |

---

## 5. What's Genuinely Good (keep it)

1. **Stack selection** — FastAPI + Celery + Redis + Postgres + Next.js is the correct, cheap, boring choice for this product.
2. **Data model core** — User/Channel/Video/CreditLedger/PipelineJob/Topic with a proper credit *ledger* (not just a balance int) shows good instinct. Extend, don't rewrite.
3. **UI design system** — the dark violet/blue glass aesthetic is consistent and launch-quality visually.
4. **Plan v3 itself** — competitive analysis, phased delivery, cost model, and verification plan are more rigorous than most seed-stage teams produce.
5. **Repo hygiene** — small files, single responsibility, consistent naming.

---

## 6. Effort Estimate to Reach Plan v3's Own Milestones

| Milestone | Real state | Est. effort (1 competent dev + AI assistance) |
|:---|:---|:---|
| Phase 2 — Auth, migrations, Stripe, RBAC, security | 0% (models only) | 2–3 weeks |
| Phase 3 — Full video pipeline (script→TTS→visuals→render) | 0% (sleep stub) | 3–5 weeks (the hard part; MoviePy/ffmpeg edge cases eat time) |
| Phase 4 — Preview + YouTube publish | 0% | 1–2 weeks |
| Phase 5–6 — OneFlancer MVP | 0% (no models even) | 4–6 weeks |
| Phase 7–8 — Analytics, polish, deploy | 0% | 2–3 weeks |
| **Total to soft launch (shorts engine only, no OneFlancer)** | | **~8–12 weeks** |
| **Total including OneFlancer MVP** | | **~14–20 weeks** |

Biggest schedule risks: (1) video rendering pipeline reliability, (2) YouTube API quota/verification process for OAuth apps (Google's app review for `youtube.upload` scope takes weeks — **start it early**), (3) Veo/HiggsField API cost per video vs credit pricing (unit economics unvalidated).

---

## 7. Recommended Immediate Order of Work

1. **Decide monorepo vs two repos** (recommend: merge frontend into `Automation/frontend` to match README/plan; one PR pipeline, one deploy story).
2. Fix §3.1 (drop Prisma), §3.5 (Alembic), §3.4 (secret/config hardening) — cheap now, expensive later.
3. Build **auth end-to-end** (NextAuth Google → backend JWT verify → `get_current_user` real) — everything depends on it.
4. Generate the frontend API client from FastAPI's OpenAPI spec to kill contract drift (§3.3) permanently.
5. Redis pub/sub progress bridge (§3.2) before writing any real pipeline task.
6. Then Phase 3 pipeline, one stage at a time, with a real E2E test per stage.

---

*Phases 3–5 of the engagement (business-idea challenge, questions, business audit) follow in conversation.*
