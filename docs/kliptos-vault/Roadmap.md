# Roadmap — S1 → S4

> Supersedes Master Plan v3 phases 5–6 timing. Each stage has a hard gate.

## S1 — Engine MVP ← ✅ FEATURE-COMPLETE 2026-07-29 (built in 2 days, not 8 weeks)
Auth end-to-end (Google via NextAuth ↔ FastAPI JWT) · Alembic · credit system · trend feed (Reddit + Google Trends) · script studio (GPT-4o) · pipeline **Pexels + edge-tts only** · 9:16 preview · YouTube publish · free-tier watermark · Stripe + Razorpay · India/US pricing
**Gate → S2:** 100 activated users, ≥25 finish 3+ videos
Build order: monorepo merge → foundation fixes → auth → OpenAPI client → Redis pub/sub → pipeline stages (E2E test each)

## S2 — Functionality First (re-prioritized 2026-07-29 evening: deploy POSTPONED by owner)
Build status 2026-07-30: ✅ script modes+BYO script · ✅ niche clustering · ✅ studio power features · ✅ publish metadata editor · ✅ BYO API keys · ✅ output types (script-only/visual) · ✅ Instagram code (flag-gated, Meta app pending) · ⬜ image gen · ⬜ premium engines · ⬜ UI revamp · ⬜ billing · ⬜ deploy
Ordered by priority:
1. **Script creation modes** — before generating, user picks intent: Viral Story (current default) · News/Update (e.g., "Apex Legends patch explained") · Educational/Explainer · Commentary/Opinion · **Bring-Your-Own-Script** (paste your script, we only segment it + add visual prompts, wording preserved). Foundation for later: story SERIES ("continue the story" — episode catalog per storyline).
2. **Niche clustering for trends** — user picks their niche (Gaming / Education / Memes / Tech / …) and sees only relevant trends instead of one big cluster. YT API natively supports videoCategoryId + regionCode; Google Trends RSS is uncategorized (LLM-classify at harvest time); per-user default niche on profile.
3. **New trend sources — honest feasibility (researched):**
   - **X/Twitter**: official API paid tiers only (Basic ~$200/mo, no trends on free) — defer until revenue or find budget
   - **Instagram**: NO public trends API; scraping = Meta ToS violation. Compliant path: Instagram oEmbed/hashtag via Graph API needs app review + business account; alternative signal = manually curated + LLM-expanded "audio/reel trends" feeds. Research item, not a quick win.
   - **Snapchat**: no public trends API at all — lowest priority.
   - Realistic order: YT category feeds (free, now) → Insta compliant research → X when budget allows → Snapchat last.
4. **Studio power features** — model selection (Gemini/GPT), user-editable generation prompt, tone presets
4b. **Publish metadata editor** — edit title/description/hashtags, category, quality, thumbnail BEFORE upload
5. **BYO API keys** — users store their own encrypted LLM keys, platform fee per render applies
6. **UI revamp** (owner: "later, functionality first"; logo in progress)
7. **Deploy for friend-testing** (postponed by owner until features feel right) → then **Billing** (Stripe/Razorpay) → premium visuals (Veo hybrid, ElevenLabs)
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
