# Deploying Kliptos

Architecture: **Vercel** (frontend) · **Render** (API + render worker) ·
**Neon** (Postgres) · **Render Key Value** (Redis) · **Cloudflare R2** (media).
Realistic bill at launch: ~$14/mo (two Render starter services); everything
else free tier.

Local dev needs none of this — without the S3 vars, files stay on local disk
and everything runs exactly as before.

---

## 0. One-time accounts

| Service | What to create |
|---|---|
| vercel.com | project `kliptos`, root dir `frontend`, preset Next.js — DONE |
| render.com | account — DONE; services come from the Blueprint below |
| neon.tech | project `kliptos`, region **Singapore** |
| dash.cloudflare.com → R2 | bucket `kliptos-media` |

## 1. Neon (database)

1. Create the project → copy the **pooled** connection string ("Pooled connection" toggle ON).
2. Convert its scheme for our async driver: `postgresql://…` → `postgresql+asyncpg://…`
   and strip any `?sslmode=…&channel_binding=…` query params (asyncpg negotiates TLS itself).
3. That value is `DATABASE_URL`. (The code auto-detects `-pooler` hosts and
   disables asyncpg's statement cache — no extra config.)

## 2. Cloudflare R2 (media storage)

1. R2 → Create bucket → `kliptos-media`.
2. Bucket → Settings → **Public access** → allow (r2.dev subdomain is fine to
   start; a custom domain like `media.kliptos.app` can replace it later).
   Copy the public URL → `S3_PUBLIC_URL`.
3. R2 → **Manage API tokens** → Create token → permissions **Object Read & Write**,
   scoped to this bucket → copy Access Key ID (`AWS_ACCESS_KEY_ID`) and Secret
   (`AWS_SECRET_ACCESS_KEY`).
4. The token page shows the endpoint: `https://<account-id>.r2.cloudflarestorage.com`
   → `S3_ENDPOINT_URL`. And `S3_BUCKET_NAME=kliptos-media`.

## 3. Render (API + worker)

1. Dashboard → **New → Blueprint** → select the `Automation` repo → Render reads
   `render.yaml` and shows two services (`kliptos-api`, `kliptos-worker`) plus
   the `kliptos-secrets` env group.
2. Fill every prompted secret (values from `backend/.env`, plus the Neon and R2
   values above). `REDIS_URL`: create **New → Key Value** (`kliptos-redis`,
   Singapore, free) first, then paste its **Internal** URL.
3. Deploy. The API runs migrations automatically on boot (`alembic upgrade head`).
4. Verify: `https://kliptos-api.onrender.com/api/health` → `{"status":"ok"}`.

## 4. Point the frontend at the API

Vercel → kliptos project → Settings → Environment Variables:
- `NEXT_PUBLIC_API_URL` = `https://kliptos-api.onrender.com/api`
- `NEXTAUTH_URL` = the site URL
Then **Redeploy**.

## 5. Google OAuth

console.cloud.google.com → Credentials → OAuth client → Authorized redirect URIs:
- `https://<vercel-domain>/api/auth/callback/google` (sign-in)
- `https://kliptos-api.onrender.com/api/channels/callback` (YouTube connect)

## 6. Smoke test (in order)

1. Sign in with Google on the live site.
2. Discover → refresh harvest → topics appear.
3. Create a script from a topic → render 1 credit → watch the 5 steps.
4. The finished video plays (its URL should be the R2 public domain).
5. Upload footage → analyzing → ready → cut a clip.
6. Connect the YouTube channel → publish an unlisted short.

## Gotchas / notes

- **Free-tier spin-down**: Render starter services stay warm; if ever moved to
  free web services, the first request after idle takes ~50s.
- **Worker memory**: Whisper (base, int8) + ffmpeg fit in the 512MB starter for
  clips of moderate size; if analyze jobs OOM on long uploads, bump the worker
  to Standard (2GB).
- **Celery beat** runs inside the worker (`-B`) — one process, one service.
- **Local disk on Render is ephemeral**: anything not in R2 or Postgres is gone
  on redeploy. That's by design — media lives in R2.
- **Voice previews** regenerate lazily per API instance; first click per voice
  after a deploy is slow once.
- **Before real users**: rotate every credential listed in
  `docs/SECURITY_CHECKLIST.md`, and set `RATE_LIMITS_ENABLED=true` (default).
