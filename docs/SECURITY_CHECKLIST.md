# Security Checklist

## 🔑 Secret rotation — MANDATORY before public launch
Every credential below was exchanged over chat during development and must be
treated as compromised. Rotate ALL of them when deploying:

| Secret | Where to rotate | New home |
|---|---|---|
| Google OAuth client secret | console.cloud.google.com → Credentials → regenerate secret | Render env `GOOGLE_CLIENT_SECRET` + Vercel `AUTH_GOOGLE_SECRET` |
| Gemini API key | aistudio.google.com → API keys → delete + create | Render env `GEMINI_API_KEY` |
| OpenAI API key | platform.openai.com → API keys | Render env `OPENAI_API_KEY` |
| Pexels API key | pexels.com/api → regenerate | Render env `PEXELS_API_KEY` |
| YouTube Data API key | console.cloud.google.com → Credentials | Render env `YOUTUBE_API_KEY` |
| `SECRET_KEY` (JWT signing) | generate fresh: `python -c "import secrets; print(secrets.token_urlsafe(48))"` | Render env — NOTE: invalidates all sessions |
| `TOKEN_ENCRYPTION_KEY` (Fernet) | generate fresh — NOTE: re-encrypt or force re-connect of all channel tokens | Render env |
| NextAuth `AUTH_SECRET` | `npx auth secret` | Vercel env |

Rules going forward:
- Secrets live ONLY in env vars on the hosting platform. Never in git, never in chat.
- `.env` files stay gitignored (verified — they are).
- BYO user keys are Fernet-encrypted at rest and never returned by the API (verified).

## ✅ Implemented protections (hardening sprint, 2026-08-02)
- Single-use Redis OAuth state nonces (YouTube + Instagram connect)
- Atomic status claims + commit-before-enqueue on render/publish
- Authenticated WebSocket progress (token + job ownership)
- Rate limiting (Redis fixed-window, per-user + per-IP on login): script
  generation, render start, uploads, clip creation, topic refresh, series
  creation. Kill-switch: `RATE_LIMITS_ENABLED`.
- Upload magic-byte sniffing (content must match extension) + 500MB cap +
  extension whitelist + per-user upload quota
- Retry-with-backoff on all external calls (Pexels, edge-tts, LLM providers)
- Security headers on both API and frontend (nosniff, frame DENY,
  referrer-policy, permissions-policy)
- JWT expiry 24h; placeholder SECRET_KEY rejected at boot
- WS auto-reconnect on the frontend

## 🔜 At deploy (tracked, not yet applicable on localhost)
- HTTPS everywhere (platform-provided TLS)
- `CORS_ORIGINS` → only `https://kliptos.app`
- Backend-token proxying via Next route handlers (token never in browser JS)
- Trusted proxy config so X-Forwarded-For is honest before IP rate limits rely on it
- Content-Security-Policy header (needs the final asset origins)
- Object storage (R2) with signed URLs instead of public /media mount
- Structured error tracking (Sentry free tier)

## Known upstream issues (monitored, no patched release yet — 2026-08-02)
- `next@16.2.12` bundles vulnerable `postcss`/`sharp` (3 highs). We are on
  the LATEST stable — the fixed range only exists in 16.3 previews. Impact
  is build-time / image-optimization paths, not our request handling.
  Action: bump Next when 16.3 stable lands.
- `ecdsa 0.19.2` (via python-jose): PYSEC-2026-1325, no fix version
  published (maintainers treat timing side-channels as out of scope). Our
  JWTs are HS256 (HMAC, not ECDSA), so the vulnerable path is unused.
- venv `pip` upgraded to 26.2 (was 25.2 with 5 advisories).

## Periodic
- `npm audit` / `pip-audit` monthly
- Review Google Cloud + Meta app access logs after launch
