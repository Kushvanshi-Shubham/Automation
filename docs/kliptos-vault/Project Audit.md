# Project Audit (2026-07-28)

**Verdict: design prototype + API skeleton. ~5–10% of an MVP. Overall 3/10.**
Full report: `../PROJECT_AUDIT.md`

## Key facts
- Every backend endpoint returned hardcoded dummy data; zero DB queries
- Celery "pipeline" = three `time.sleep(1)` calls
- Frontend = polished mock (hardcoded stats, dead sign-in button, 6/8 pages "Coming soon")
- Zero tests, migrations, CI/CD, logging, error handling, applied auth
- The two repos never talked; the only 2 API hooks target endpoints that don't exist

## Critical findings → all resolved via [[Decisions]]
1. Prisma vs SQLAlchemy conflict → drop Prisma
2. WebSocket progress can't reach Celery workers → Redis pub/sub
3. Frontend/backend contract drift → OpenAPI-generated client
4. `SECRET_KEY="secret"`, plaintext YouTube tokens, localStorage JWT → hardening
5. `create_all` at startup → Alembic
6. No router applies auth → router-level dependencies

## Worth keeping
- Stack choice (FastAPI + Celery + Redis + Postgres + Next.js) ✅
- Data model core incl. credit *ledger* ✅
- UI design system (violet/blue dark glass — launch quality) ✅
- Plan v3 rigor ✅

Scorecard details, effort estimates (8–12 wks engine, 14–20 wks incl. OneFlancer): see full report.

Links: [[Home]] · [[Business Audit]] · [[Decisions]]
