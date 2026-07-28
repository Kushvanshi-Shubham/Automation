# Decision Log

| # | Date | Decision | Rationale |
|:--|:---|:---|:---|
| 1 | 2026-07-28 | **Monorepo**: merge `frontend` repo into `Automation/frontend`; archive old repo | One deploy story; README/plan already assume it |
| 2 | 2026-07-28 | **Drop Prisma** — NextAuth JWT sessions; FastAPI/SQLAlchemy owns Postgres | Two ORMs on one DB = drift; adapter was never configured anyway |
| 3 | 2026-07-28 | **Alembic from day one**; delete startup `create_all` | Migrations debt is cheapest at t=0 |
| 4 | 2026-07-28 | **Redis pub/sub** for pipeline progress (worker → API → WS) | In-memory ConnectionManager unreachable from Celery containers |
| 5 | 2026-07-28 | **OpenAPI-generated TS client** for all frontend API calls | Contract drift appeared with only 2 hooks written |
| 6 | 2026-07-28 | **Security baseline**: required SECRET_KEY, AES-encrypted YouTube tokens, httpOnly cookies (no localStorage), router-level auth dependencies | See [[Project Audit]] §3.4/3.6 |
| 7 | 2026-07-28 | **Variable credit pricing** (1/8–10/25–30 cr by engine) | [[Unit Economics]] — flat pricing loses $7–24/video |
| 8 | 2026-07-28 | **No cold-email infrastructure** — briefs board + AI-written applications + creator-sent warm outreach | Legal/deliverability/marketplace-poisoning risk |
| 9 | 2026-07-28 | **OneFlancer deferred to S3/S4** | Different customer than faceless creators; marketplace cold-start needs manual seeding first |
| 10 | 2026-07-28 | **India + US launch, localized pricing** (Pro ₹499/$19), Razorpay + Stripe | $19 non-viable in India; UPI is the payment rail |
| 11 | 2026-07-28 | **S1 visuals = Pexels + edge-tts only** | Ship revenue-capable product in ~8 wks at survivable cost |

Links: [[Home]] · [[Roadmap]] · [[S1 Build Log]]
