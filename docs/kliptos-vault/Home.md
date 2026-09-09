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
- [[Pitch]] — the thesis, the story, the cross-questions, and what must not be overclaimed
- [[Funding]] — programmes, competitions and accelerators Kliptos can actually enter, with deadlines and the incorporation gate (2026-09-08)
- [[S1 Build Log]] — running log of the actual build
- [[AI Content System]] — the video-inspired features: link→script, your footage, teach-a-style, feedback memory, studio voice

## Status — 2026-09-09
- **The always-on box is bought: Hostinger KVM 2, ₹799/month** (2 vCPU, 8 GB, 100 GB NVMe, 8 TB). Runbook rewritten as [[../DEPLOY-VPS|DEPLOY-VPS.md]]; the GCP one is superseded. Once it is up, renders no longer depend on the dev laptop being awake — which is the last thing blocking a stranger using the product.
- **Why not GCP:** an e2-medium is ~₹2,300/month, so renting for ₹799 frees the **entire ₹28,694 Google credit for Vertex**, where AI images have no cheap substitute. The credit expires 16 Nov.
- **Reversed an earlier call: the VPS goes in Malaysia, not Mumbai.** Neon is in Singapore and the app is DB-chatty — co-locating with the database beats co-locating with users, since Vercel and R2 already serve from the edge.
- **Ruled out on the way:** Cloudways (no root, PHP-only), IONOS/Namecheap/DreamHost/Hetzner (no Asian data centre). Real fallback is Vultr or DigitalOcean.

## Status — 2026-09-08
- **Funding routes researched globally** — see [[Funding]]. The August "hackathons cannot fund Kliptos" call still holds (they all demand a brand-new build), but startup competitions and accelerators are the inverse: they want a working product. Pre-revenue is fine everywhere found.
- ⏰ **Open now:** **a16z Speedrun — 25 Sept** (best thematic fit anywhere on the list: they fund games/AI/consumer/**media** tooling, take solo and non-US founders, $500k + $10M in credits, no entity needed) · **YC W2027 — 2 Nov** · **SXSW Pitch — 13 Nov** · **Web Summit ALPHA/PITCH — event 9–12 Nov** · **Startup League — 15 Sept** but needs a registered entity.
- **The gate is incorporation, not stage.** Indian programmes want Pvt Ltd / LLP / Partnership; global accelerators incorporate you themselves. That splits the list cleanly into "apply this month" and "after registration".
- **Missed by one day: Slush 100 closed 7 Sept.** €500k equity-free and the eligibility fit exactly (founded 2023+, under €10M raised, seed or earlier). Diarise June 2027.
- **Free and always open:** OpenVC — 20,000+ investors, deck open/read analytics. Lowest-effort item and the only one that tells you whether the deck works.

## Status — 2026-09-06
- **The pitch has a thesis now.** Not "AI makes videos" — *people quit content creation because it takes too long, not because they are bad at it.* The line that carries it: **"I cannot make them famous, but I could pave an easier and faster path."** Everything else follows from that. See [[Pitch]].
- A judge/possible investor rated the first write-up **1/10** — it had been written for technical due diligence (architecture, margins, weaknesses first) when what was wanted was the product and the story. Register matters as much as honesty.
- ⚠️ Several things described in the pitch **do not exist yet** — gaming montage with highlight detection, an interface that adapts per video type, trend mash-ups, payments. [[Pitch]] lists them so they are never claimed as built.
- **Founder time, stated correctly:** employed, degree completes **16 Sept 2026**, building evenings and weekends. That is a stronger pitch answer than a student one — a nine-format pipeline shipped around a job is an execution signal. The follow-up to prepare for is *"would you leave the job, and when?"*, which needs a concrete trigger.
- ⚠️ **Unresolved: employment IP.** Indian contracts often assign work created during employment, sometimes covering own-time work. Worth reading the clause **before** incorporating or taking money — it surfaces during diligence otherwise.

## Status — 2026-08-31
- **What Kliptos is, stated plainly:** an AI Shorts studio. Start from a trend, a link, your own script or your own footage; pick a **format** (a full recipe: script style, visual look, narration pace, captions, music, sub-mood); Kliptos writes, narrates, sources or generates the visuals, burns captions and renders a vertical video. You approve every word and can render one scene free first. Standing orders run it unattended. India-first: Hindi voices, Devanagari captions, shayari and music formats, ₹ pricing.
- **The studio can restructure a script now** — move, add and delete scenes, not just rewrite lines. And it is one editor: trend-created and library videos open the same screen.
- **Autopilot no longer ships blind** — a series carries mood, length and visual engine, gets the format's tone, and an episode with a broken script is skipped with the reason recorded instead of failing after the credit is spent.
- ⚠️ **Render is warning about bandwidth (>70%).** Video playback is on R2 so it should be trivial; worth reading the breakdown, but it is really a nudge to do the Google Cloud migration while the ₹28,694 credit lasts (expires 16 Nov).
- **Still yours:** incorporation + DPIIT, Razorpay KYC, and a judgement call on whether output quality is finally good enough.

## Status — 2026-08-30
- **Formats are genuinely different now.** Each declares its own script style, visual look and narration pace — before, 7 of 9 shared a viral-Shorts writer and *every* format rendered as corporate flat-vector art at news pace. See [[S1 Build Log]].
- **Hindi captions fixed**, and not for the reason we assumed: it was ASS letter-spacing detaching the vowel marks, not a missing font.
- **The full cloud path is verified** — deployed API → shared Redis → worker → Vertex → R2.
- **Hackathons dropped.** Both required a brand-new project, so Kliptos could not be entered and a win would have credited an unrelated demo. The route to funding is incorporation → DPIIT → Startup India Seed Fund (₹20 lakh).
- **Next up:** sub-moods (sad/love/nostalgic), a real music library (two tracks today), and the studio — per-scene manual control, which is the big one.
- ⚠️ Owner still has not run a full render through the UI, and Razorpay KYC has not started.

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
