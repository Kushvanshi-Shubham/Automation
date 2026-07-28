# 🧠 Kliptos — AI Shorts Automation Platform

> Turn trending topics into published YouTube Shorts — automatically.

Kliptos is a multi-user SaaS platform that discovers trending entertainment topics, generates AI-powered 60-second shorts (script → voice → visuals → render), and publishes them to YouTube with optimised metadata — all from one dashboard.

## Tech Stack

| Layer | Technology |
|:---|:---|
| **Frontend** | Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, shadcn/ui |
| **Backend** | FastAPI, Python 3.12+, SQLAlchemy, Pydantic |
| **Task Queue** | Celery + Redis |
| **Database** | PostgreSQL |
| **AI Pipeline** | OpenAI GPT-4o, edge-tts, Whisper, MoviePy, Veo 3.1, HiggsField |
| **Auth** | NextAuth.js v5 (Google OAuth) |
| **Billing** | Stripe (credit-based) |
| **Storage** | S3-compatible object storage |

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.12+
- Docker & Docker Compose
- FFmpeg

### 1. Clone & Configure
```bash
cp .env.example .env
# Fill in your API keys in .env
```

### 2. Start Infrastructure
```bash
docker-compose up -d postgres redis
```

### 3. Start Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

### 5. Start Celery Worker
```bash
cd backend
celery -A app.pipeline.celery_app worker --loglevel=info
```

Open [http://localhost:3000](http://localhost:3000) 🚀

## Project Structure

```
Automation/
├── frontend/          # Next.js 15 (App Router)
├── backend/           # FastAPI + Celery pipeline
├── docker-compose.yml # Local dev infrastructure
├── .env.example       # Environment template
└── README.md
```

## License

Private — All rights reserved.
