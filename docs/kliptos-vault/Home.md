# 🎬 Kliptos — Command Center

> AI Shorts Automation + (later) Creator-Brand Marketplace.
> Solo founder build. India + US markets.

## Maps
- [[Competitors]] — AutoShorts/Vadoo/Crayo/Nullface matrix, table stakes, our moat, SEO playbook (2026-07-30)
- [[Creation Workflow v2]] — output types (script-only / narrated / visual / image / premium), credit matrix, priorities (2026-07-30)
- [[Project Audit]] — what the code actually was on 2026-07-28 (score 3/10)
- [[Business Audit]] — assumptions challenged, SWOT, investor verdict
- [[Unit Economics]] — the numbers that reshaped the pricing model
- [[Decisions]] — every locked decision with rationale
- [[Pricing]] — plans, credits, India/US localization
- [[Risks]] — top risks and mitigations
- [[Roadmap]] — S1 → S4 stages and gates
- [[S1 Build Log]] — running log of the actual build
- [[AI Content System]] — the video-inspired features: link→script, your footage, teach-a-style, feedback memory, studio voice

## Status — 2026-08-17
- **AI-illustrated video works for the first time**, proved end to end on the live stack. It was never a billing switch: the Gemini Developer API is a separate prepaid wallet that Cloud credits can't pay for on accounts created after 2 March 2026. Our calls now go through **Vertex**, which bills the Cloud account. See [[S1 Build Log]] and the memory note *Kliptos Google AI billing*.
- **Shared Redis is done** — the deployed API and the local worker use one queue. Cloud renders work while the dev PC is on; a real always-on worker still wants a VM (the ₹28,694 trial credit could fund one until 16 Nov).
- **⚠️ Hindi captions are broken** — Devanagari vowel marks render as detached dotted circles because every caption font is Latin-only. Affects every Hindi video ever made. Top of the bug list.
- **Two users on the live DB**, one of them not the owner's address — possibly a real first signup.

## Status — 2026-08-16
- **Kliptos has its own domain: https://www.kliptos.app** (live, TLS issued, serving from Vercel). Registered at Name.com, DNS on Cloudflare, two CNAMEs to Vercel set to **DNS only** — proxying breaks Vercel's cert issuance. www is canonical; the apex 308-redirects to it.
- ⚠️ **Until the env vars move, sign-in is broken on the new domain** — NextAuth still advertises `kliptos.vercel.app/api/auth/callback/google`, so users get bounced to the old host. Needs `NEXTAUTH_URL`/`AUTH_URL` on Vercel, the redirect URI in the Google OAuth console, and `FRONTEND_URL`/`CORS_ORIGINS` on Render.
- Next on the domain: Cloudflare **Email Routing** → `shubham@kliptos.app` (the business email Google for Startups requires, and it makes `support@kliptos.app` in the legal pages real), then `media.kliptos.app` for R2 to replace the rate-limited `pub-*.r2.dev`.

## Status — 2026-08-15
- **The front door works now.** Signup was never broken — Google OAuth creates the account on first sign-in with 3 free credits — but the page said "Sign in to Kliptos" and read as members-only. Reframed as **"Create your account"**, and the sign-in + legal pages (the last ones still on the old dark design) are now in the system. Live-verified on kliptos.vercel.app. See [[S1 Build Log]].
- **Unbuilt, and genuinely so:** email/password auth and the onboarding niche picker. Google is still the only way in.
- **Next build priorities** (supersedes the 08-06 list below — caption craft shipped 08-14): shared Redis so cloud renders work for anyone but the owner · email/password + onboarding niche picker · landing-page micro-interactions · mobile as its own product

## Status — 2026-08-14
- **New since the 6th:** free **proof renders** (approve one scene before spending), **free restyles** (3 per video when only the look changes), **caption craft** (5 animations, 6 fonts, brand colour, per-scene headline overlays), **AI-illustrated video** (a generated scene per line with Ken Burns motion — needs Gemini billing), and Pro films up to **5 minutes**. See [[S1 Build Log]].
- Owner is testing against a real 4.5-minute product deck (Tcher). Honest ceiling for that job: ~85% with AI visuals + his own screen recordings; the animated diagram and logo animation remain motion-design work no generative tool does well.

## Status — 2026-08-06
- **DEPLOYED:** frontend **kliptos.vercel.app** · API **kliptos-api.onrender.com** (free tier, sleeps) · Neon Postgres · Cloudflare R2 (verified end to end). See [[../DEPLOY|DEPLOY.md]].
- **Working end-to-end (local):** sign-in → India-first trends with recommended format → create from a **trend, a link, your own script, or your own footage** → 9 formats or **a style taught from your own reels** → edit every line, pin footage or auto-match it → render with **studio-grade voice** (Cartesia/ElevenLabs, Hindi included), captions, music → publish/schedule to YouTube → **feedback notes** that improve every future video → standing orders on autopilot.
- **Pro is a real tier now:** watermark + 720p + 45s on Free; no watermark, 1080p, 3-min, brand kit, priority, studio voices on Pro. Paywall behind `PLAN_ENFORCEMENT_ENABLED` (off until billing). Credit prices derive from true cost — see [[Pricing]].
- **⚠️ One blocker for cloud renders:** a Redis both the deployed API and the worker can reach (Render's free Key Value is internal-only). Plan: reuse the existing Redis Cloud DB, or fold it into a paid host.
- **Owner action items:** ① real ElevenLabs key (`sk_…`) ② R2 vars + `ADMIN_EMAILS` into Render env ③ `youtube.upload` verification (weeks of queue) ④ Razorpay KYC ⑤ Meta app for Instagram ⑥ **rotate every key in `../SECURITY_CHECKLIST.md` before real users**
- **Next build priorities:** caption craft (animated styles, fonts, brand colours, highlighted keywords) · sign-up + email/password + onboarding niche picker · landing-page micro-interactions · mobile as its own product
- **Gate to S3:** ≥30 paying subscribers, gross margin ≥60%
- Restart everything: `.\scripts\dev.ps1` (see `docs/RUNBOOK.md`); cloud worker: `backend\scripts\worker-cloud.ps1`

## Source documents
- Full codebase audit: `../PROJECT_AUDIT.md`
- Full business audit: `../BUSINESS_AUDIT.md`
- Original plan: `../../implementation_plan.md` (Master Plan v3 — superseded by [[Roadmap]])
