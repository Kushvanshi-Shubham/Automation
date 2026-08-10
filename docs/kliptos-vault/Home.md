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
