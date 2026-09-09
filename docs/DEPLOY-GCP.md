# Moving Kliptos to a Google Cloud VM

> **SUPERSEDED 2026-09-09 — follow [[DEPLOY-VPS]] instead.** The box is now a
> Hostinger KVM 2 at ₹799/month (2 vCPU, 8 GB, 100 GB NVMe, 8 TB) rather than a
> ~₹2,300 `e2-medium`, so the whole ₹28,694 Google credit goes to Vertex, where
> it cannot be substituted. Kept for the reasoning; do not follow the steps.
> Note also that its Hetzner fallback suggestion was wrong — Hetzner has no
> Asian data centre.

## Why

Render's free plan has no background workers, sleeps after 15 minutes, caps at
512 MB, and is now warning about bandwidth. So the render worker has been
running on the dev laptop — which means **renders only work while that laptop
is awake**, and you cannot put a stranger in front of the product.

One VM fixes that, plus two things that were never right:

- **Redis moves onto the box.** It lived in `us-east-1` while Neon and the API
  were in Asia; the worker logged four disconnect/reconnect cycles in 3.5
  hours because of it. Also removes the Redis Cloud dependency entirely.
- **The API gets a real always-on host** at `api.kliptos.app`, so no cold
  starts and no bandwidth cap.

Neon keeps the data, R2 keeps the media. **This machine is disposable** —
rebuild it and nothing is lost. That is deliberate: it means switching to a
Hostinger or Hetzner box later is an afternoon, not a migration.

## Cost, and why this size

`e2-medium` (2 vCPU, 4 GB) ≈ **$27/month**. The ₹28,694 Google credit expires
**16 November 2026**, so it covers roughly 2.5 months of VM and leaves about
₹22,000 for Vertex — which matters, because AI images are the expensive lane.

`e2-standard-4` (4 vCPU) would render faster at ~$100/month, but it would eat
the whole credit in three months with nothing left for AI. Start at medium.

**When the credit runs out**, a Hostinger or Hetzner VPS is ₹400–900/month for
similar specs. Everything here is Docker plus env vars, so moving is a copy.

## 1. Create the VM

```bash
gcloud config set project kliptos-505809

gcloud compute instances create kliptos-vm \
  --zone=asia-south1-c \
  --machine-type=e2-medium \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-balanced \
  --tags=http-server,https-server \
  --scopes=cloud-platform
```

- **`asia-south1`** is Mumbai — closest to your users. Neon is in Singapore
  (`ap-southeast-1`), so there is a small cross-region hop to the database;
  that is far cheaper than the cross-Pacific Redis hop it replaces. Use
  `asia-southeast1` instead if you would rather be next to Neon.
- **30 GB disk**, not the 10 GB default: renders need scratch space and Docker
  images are large.
- **`--scopes=cloud-platform`** lets the VM's own service account reach Vertex,
  which is a fallback if the JSON key is ever the problem.

Open the firewall (once per project):

```bash
gcloud compute firewall-rules create allow-http-https \
  --allow=tcp:80,tcp:443 --target-tags=http-server,https-server
```

## 2. Point DNS at it

```bash
gcloud compute instances describe kliptos-vm --zone=asia-south1-c \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

In Cloudflare, add an **A record**: `api` → that IP.

⚠️ **Set it to "DNS only" (grey cloud).** A proxied record makes Cloudflare
answer the ACME challenge and Caddy never gets a certificate — the same trap
as the Vercel records.

## 3. Install Docker

```bash
gcloud compute ssh kliptos-vm --zone=asia-south1-c

curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
exit   # log back in so the group takes effect
```

## 4. Bring it up

```bash
gcloud compute ssh kliptos-vm --zone=asia-south1-c

git clone https://github.com/Kushvanshi-Shubham/Automation.git
cd Automation/deploy
cp .env.prod.example .env
nano .env          # fill every value — see the notes in the file

docker compose -f docker-compose.prod.yml --env-file .env up -d --build
docker compose -f docker-compose.prod.yml logs -f api
```

The API container runs `alembic upgrade head` before uvicorn, so migrations
apply on deploy. Only the API does this — the worker must not race it.

**`GOOGLE_SA_JSON` needs the whole service-account JSON on one line.** Easiest
route: run this locally and paste the result.

```powershell
(Get-Content backend\secrets\vertex-sa.json -Raw | ConvertFrom-Json | ConvertTo-Json -Compress -Depth 10)
```

## 5. Verify before switching traffic

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
**Redeploy Vercel**; env vars are baked in at build time.

Add `https://api.kliptos.app/api/channels/callback` as an authorised redirect
URI in the Google OAuth console, or connecting a YouTube channel breaks.

## 6. Retire the old pieces

Only after the new stack has served real traffic:

1. Stop the laptop worker: `Stop-Process -Name celery`
2. Suspend the Render service (keep it a week as a fallback)
3. Delete the Redis Cloud database

## Updating

```bash
cd ~/Automation && git pull
cd deploy && docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

## Honest status of this runbook

The **image itself is proven** — the same `backend/Dockerfile` builds and runs
on Render today. What is **unverified** is this compose orchestration and the
Caddy TLS step, because the dev machine has no Docker, so none of it has been
run end to end. Expect one or two small corrections on the first attempt;
nothing here is destructive, and the existing Render deployment keeps serving
until step 5 passes.

Links: [[DEPLOY]] · [[kliptos-vault/Home]]
