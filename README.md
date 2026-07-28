# 🎬 Kliptos — AI Shorts Automation Platform

> Turn trending topics into published YouTube Shorts — automatically.

Kliptos is a multi-user SaaS platform that discovers trending topics, generates AI-powered 60-second shorts (script → voice → visuals → render), and publishes them to YouTube with optimised metadata — all from one dashboard.

**Monorepo** — frontend, backend, and knowledge base live here.

## Tech Stack

| Layer | Technology |
|:---|:---|
| **Frontend** | Next.js 16 (App Router, Turbopack), React 19, TypeScript, Tailwind CSS v4, shadcn/ui |
| **Backend** | FastAPI, Python 3.12+, SQLAlchemy 2 (async), Pydantic v2, Alembic |
| **Task Queue** | Celery + Redis |
| **Database** | PostgreSQL 16 |
| **AI Pipeline** | OpenAI GPT-4o, edge-tts, Whisper, MoviePy, Pexels (S1) → Veo 3.1 hybrid (S2) |
| **Auth** | NextAuth.js v5 (Google OAuth) → FastAPI JWT |
| **Billing** | Stripe (US) + Razorpay (India), credit-based |
| **Storage** | S3-compatible object storage (Cloudflare R2) |

## Project Structure

```
Automation/
├── frontend/            # Next.js 16 app (App Router)
├── backend/             # FastAPI + Celery pipeline
│   ├── app/             # routers, models, schemas, services, pipeline
│   ├── alembic/         # database migrations
│   └── tests/           # pytest suite
├── docs/                # Audits + Obsidian knowledge vault
│   └── kliptos-vault/   # ← open this folder as an Obsidian vault
├── docker-compose.yml   # Local dev infrastructure
└── .env.example         # Environment template
```

## Quick Start

### Prerequisites
- Node.js 20.9+
- Python 3.12+
- PostgreSQL 16 + Redis (or Docker Compose)
- FFmpeg

### 1. Configure
```bash
cp .env.example .env                        # backend env — fill in secrets
cp frontend/.env.example frontend/.env.local # frontend env — fill in secrets
```
Generate the required secrets (see comments inside `.env.example`).

### 2. Database
```bash
cd backend
pip install -r requirements-dev.txt
alembic upgrade head
```

### 3. Run
```bash
# Backend API
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev

# Celery worker (once the pipeline milestone lands)
cd backend && celery -A app.pipeline.celery_app worker --loglevel=info
```

### 4. Test
```bash
cd backend && pytest
cd frontend && npm run build
```

Open [http://localhost:3000](http://localhost:3000) 🚀

## Documentation

- `docs/PROJECT_AUDIT.md` — full codebase audit
- `docs/BUSINESS_AUDIT.md` — business audit, pricing model, roadmap rationale
- `docs/kliptos-vault/` — Obsidian vault: decisions, risks, roadmap (S1–S4), build log

## License

Private — All rights reserved.
