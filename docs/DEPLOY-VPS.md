# Deploying Kliptos on a Hostinger VPS

The live runbook. Supersedes `DEPLOY-GCP.md`.

## Why a VPS at all

Render's free plan has no background workers, sleeps after 15 minutes, caps at
512 MB and was warning about bandwidth — so the render worker has been running
on the dev laptop. That means **renders only work while that laptop is awake**,
and you cannot put a stranger in front of the product. One box fixes that, plus
two things that were never right:

- **Redis moves onto the box.** It lived in `us-east-1` while Neon and the API
  were in Asia; the worker logged four disconnect/reconnect cycles in 3.5
  hours because of it. Also removes the Redis Cloud dependency entirely.
- **The API gets a real always-on host** at `api.kliptos.app` — no cold starts,
  no bandwidth cap.

Neon keeps the data, R2 keeps the media, GitHub keeps the code. **This machine
is disposable** — rebuild it and nothing is lost. That is deliberate: it is why
picking a host on price is safe, and why moving to Vultr or DigitalOcean later
would be an afternoon rather than a migration.

## The box

**Hostinger KVM 2 — ₹799/month**: 2 vCPU, 8 GB RAM, 100 GB NVMe, 8 TB
bandwidth, full root, free weekly snapshots. Hostname `srv1966153.hstgr.cloud`.

Why this and not the alternatives: roughly a third the price of a comparable
DigitalOcean or Vultr droplet, with double the RAM and double the bandwidth.
Cloudways was disqualified (no root on any plan, PHP-only), and IONOS,
Namecheap and DreamHost all lack an Asian data centre — as does Hetzner, so
ignore the earlier note recommending it as the fallback. **Vultr or
DigitalOcean are the real fallback**, both with Singapore and Indian regions
and per-second billing.

### Why Malaysia and not Mumbai

Neon is in Singapore (`ap-southeast-1`) and Kliptos is database-chatty — a
single API request runs several queries and pays the round trip on each one.
Mumbai→Singapore is ~50–60 ms, so five queries silently add ~300 ms to every
request. Malaysia sits beside Neon, so that cost drops to near zero and the
user pays one ~60 ms hop instead. The frontend is on Vercel's edge and video is
on R2's edge, so neither cares. Renders are async and care least of all.

## Cost, and where the Google credit goes

₹799/month, flat. The ₹28,694 Google Cloud credit expires **16 November 2026**
and now goes **entirely to Vertex**, where AI image generation has no cheap
substitute. Spending it on a VM you can rent for ₹799 would waste it — that is
the whole reason this runbook replaced the GCP one.

Everything else stays free where it is: **Neon** (managed Postgres with
backups), **R2** (zero egress — do not serve video off this box; that is what
triggered Render's bandwidth warning), **Vercel** (global CDN, builds from git).

## 1. Point DNS at the box

Get the IP from hPanel → VPS → your server. Then in **Cloudflare**, add an
**A record**: `api` → that IP.

⚠️ **Set it to "DNS only" (grey cloud).** A proxied record makes Cloudflare
answer the ACME challenge and Caddy never gets a certificate — the same trap as
the Vercel records.

Hostinger's panel firewall has no rules by default, which means every port is
open, so there is nothing to do here. If you ever add a rule set, it must allow
**22, 80 and 443** or you lock yourself out and break certificate renewal.

## 2. Log in and check Docker

```bash
ssh root@<IP>
docker --version && docker compose version
```

The **Docker manager** add-on usually pre-installs it. If either command is
missing:

```bash
curl -fsSL https://get.docker.com | sudo sh
```

## 3. Bring the stack up

```bash
git clone https://github.com/Kushvanshi-Shubham/Automation.git
cd Automation/deploy
cp .env.prod.example .env
nano .env          # fill every value — the notes are in the file
```

`.env` is gitignored, and it must never be committed from the box either.

```bash
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
docker compose -f docker-compose.prod.yml logs -f api
```

The first build is slow on 2 vCPU — expect several minutes. The API container
runs `alembic upgrade head` before uvicorn, so migrations apply on deploy. Only
the API does this; the worker must not race it.

**`GOOGLE_SA_JSON` needs the whole service-account JSON on one line.** Easiest
route — run this locally and paste the result:

```powershell
(Get-Content backend\secrets\vertex-sa.json -Raw | ConvertFrom-Json | ConvertTo-Json -Compress -Depth 10)
```

## 4. Verify before switching traffic

```bash
curl -s https://api.kliptos.app/api/health          # {"status":"ok",...}
docker compose -f docker-compose.prod.yml ps        # 5 services up
docker compose -f docker-compose.prod.yml logs worker | grep ready
```

Then in **Vercel** → Production:

```
NEXT_PUBLIC_API_URL = https://api.kliptos.app/api
```

The `/api` suffix is not optional — `auth.ts` appends `/auth/google` to it, so
without it the call 404s and sign-in dies with a bare `CallbackRouteError`.
That exact mistake broke sign-in once already. **Redeploy Vercel**; env vars
are baked in at build time.

Add `https://api.kliptos.app/api/channels/callback` as an authorised redirect
URI in the Google OAuth console, or connecting a YouTube channel breaks.

## 5. Retire the old pieces

Only after the new stack has served real traffic:

1. Stop the laptop worker: `Stop-Process -Name celery`
2. Suspend the Render service (keep it a week as a fallback)
3. Delete the Redis Cloud database

## Updating

```bash
cd ~/Automation && git pull
cd deploy && docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

## Notes and gotchas

- **The free Hostinger domain is not part of this.** The API lives at
  `api.kliptos.app` so CORS, cookies and branding stay on one origin;
  `srv1966153.hstgr.cloud` is only the machine's own hostname. Claim the free
  domain only if it is one you would actually renew (`kliptos.in` protects the
  brand in the main market) — and check the auto-renew setting.
- **Do not install a control panel** (CyberPanel, CloudPanel, cPanel). They
  seize ports 80 and 443, which is exactly where Caddy needs to sit.
- **Email:** Cloudflare Email Routing is free but forward-only — it cannot
  *send*. The day you email a user or an investor from `shubham@kliptos.app`,
  you need a real mailbox (Hostinger sells one cheaply).
- **Backups:** the free weekly snapshots are enough. Nothing unique lives here
  — data is Neon's, media is R2's, code is GitHub's. The only box-local state
  is Caddy's certificates and the Redis queue, and both regenerate. Paid daily
  backups would be paying twice.
- **Worker concurrency stays 1.** ffmpeg already uses every core it can get, so
  two parallel renders on 2 vCPU make both slower than running them in turn.
  Raise it only alongside more vCPUs.

## Honest status of this runbook

The **image is proven** — the same `backend/Dockerfile` builds and runs on
Render today. What is **unverified** is this compose orchestration and the Caddy
TLS step, because the dev machine has no Docker, so none of it has been run end
to end. Expect one or two small corrections on the first attempt. Nothing here
is destructive, and the existing Render deployment keeps serving until step 4
passes.

Links: [[DEPLOY]] · [[kliptos-vault/Home]]
