# Roadmap — S1 → S4

> Supersedes Master Plan v3 phases 5–6 timing. Each stage has a hard gate.

## S1 — Engine MVP ← ✅ FEATURE-COMPLETE 2026-07-29 (built in 2 days, not 8 weeks)
Auth end-to-end (Google via NextAuth ↔ FastAPI JWT) · Alembic · credit system · trend feed (Reddit + Google Trends) · script studio (GPT-4o) · pipeline **Pexels + edge-tts only** · 9:16 preview · YouTube publish · free-tier watermark · Stripe + Razorpay · India/US pricing
**Gate → S2:** 100 activated users, ≥25 finish 3+ videos
Build order: monorepo merge → foundation fixes → auth → OpenAPI client → Redis pub/sub → pipeline stages (E2E test each)

## S2 — Testable + Better (CURRENT, defined 2026-07-29)
Ordered by priority:
1. **Deploy for friend-testing** — Render or Railway (API+worker+Postgres+Redis+volume) + Vercel; rotate all secrets; prod OAuth redirect URIs; add friends as Google test users
2. **UI revamp** — full design pass (owner delivering logo); fix landing-page pricing truth
3. **Trend discovery v2** — region + category filters for existing sources (YT API supports regionCode + videoCategoryId natively); Twitter/Snapchat source research; compliant Insta signal research
4. **Studio power features** — model selection (Gemini/GPT), user-editable generation prompt, tone presets
4b. **Publish metadata editor** (owner request 2026-07-29) — edit title/description/hashtags, category, quality/resolution options, thumbnail choice BEFORE upload (currently auto-filled from script gen with no editing UI)
5. **BYO API keys** — users store their own encrypted LLM keys, platform fee per render applies
6. **Billing** — Stripe (US) + Razorpay (India), credit packs + subscriptions
7. Premium visuals (hybrid Veo hero clips 8–10 cr) + ElevenLabs voices — once billing exists
**Gate → S3:** ≥30 paying subscribers, gross margin ≥60%

## S3 — Media kit + marketplace lite (weeks 13–20)
Auto media kit from YouTube analytics · manually-seeded brand briefs board · creator applies with AI-written pitch · manual escrow (invoices)
**Gate → S4:** 10 briefs posted, 3 completed deals

## S4 — OneFlancer proper (month 6+)
Stripe Connect escrow · campaign dashboard · brand portal
**Only if S3 deals repeat.**

## Owner additions from S1 review (2026-07-29) — slot into S2/S3
- Trend hierarchy: region × category × music × platform; add Twitter/Snapchat sources; research compliant Instagram trend signal
- Multi-platform posting (Twitter, Snapchat, IG Reels — official APIs)
- BYO API keys (user's own Gemini/OpenAI quota, small platform fee)
- Model selection + user-editable/refinable prompts
- Full UI revamp (owner designing logo)
- Interim: deploy S1 to Railway+Vercel for friend-testing before billing

## Deleted from original plan
❌ Cold-email outreach engine · ❌ contract generator (until S4) · ❌ TikTok/IG posting (post-launch) · ❌ flat-credit Veo videos

Links: [[Home]] · [[Decisions]] · [[S1 Build Log]]
