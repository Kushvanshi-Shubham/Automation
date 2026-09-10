# Kliptos: full audit and strategy, 10 September 2026

> Produced by a 23-agent workflow: 6 audit lenses over the real code (engineering,
> product funnel, unit economics, claim-vs-code, mobile-vs-web, defensible assets),
> 4 market research streams (competitors, India creator economy, distribution,
> unmet needs), 4 independent strategy theses each scored by a judge, then 3
> adversarial passes whose only job was to break the winner. **All three broke it**,
> so the recommendation differs from the scoring. 3.2M tokens, 611 tool calls.

---

# KLIPTOS — top to bottom, and what to do about it
**10 September 2026. Written as your technical co-founder, not as a consultant.**

Before anything else: the thing you asked me to check, I checked. Five audit passes over the real code, five market passes, four competing strategies scored, then three adversarial passes whose only job was to break the winner. All three broke it. So this document does not recommend what the scoring recommended. Section 3 says why, in detail, and shows the modifications rather than hiding them.

---

## 1. WHERE KLIPTOS ACTUALLY STANDS

### Genuinely strong

The engineering is real and it is checkable, which matters because you have been burned by claims that weren't. `pytest --collect-only` reports 299 tests and a full run passes 299. There are 14 Alembic migrations, 0001 through 0014. CI runs pytest against a live Redis with ffmpeg installed, plus `tsc --noEmit` and a production frontend build. Every countable number in your handover doc that could be checked was correct: 11 sub-moods, 5 animations, 6 fonts, 4 looks, checkout genuinely returns 501.

Three specific things are better than most funded products in this category:

- **The atomic video claim.** `routers/pipeline.py:241-249` does `UPDATE videos SET status='rendering' WHERE id=… AND status NOT IN ('rendering','publishing')`, rowcount 0 → 409, then commits the job *before* calling `.delay()`. That is the exact race most one-person render pipelines lose — a double-clicked Render button charging twice, or a worker picking up an uncommitted row — solved at the SQL level, with a comment saying why.
- **Credit prices derived from measured marginal cost.** `services/credits.py` computes `ceil(cost × MARGIN / price)` from one hardcoded real-cost dict. That discipline already caught Veo priced at 25-30 credits against an $8.50 cost — a ₹450 loss per render — and repriced it to 170 *before* it shipped. Most people discover that error from a bill.
- **The trust mechanics.** A free single-scene proof render before any credit is spent, and it honours the expensive `ai_image` lane too (`pipeline/proof.py:92-105`). Free restyles when only the look changes. Automatic refunds on failure with a ledger row. A cancel-and-refund escape hatch. A pre-flight check that names the blank scene *by number* before taking the credit (`routers/pipeline.py:111-123`). Almost nobody in this category does the first one at all.

And the internal vault is honest. Pitch.md volunteers limits a weaker founder would hide — "the beat lands, the action does not move," "loudness cannot tell a clutch play from a menu jingle," "do not count the friend as a user." That is an asset. Keep it.

### Fragile

Three shipping blockers, all one root cause — the refund logic is written three times in three places and has drifted:

1. `pipeline/reaper.py:58-75` fails the job, refunds the credit, resets the video — and never calls `celery_app.control.revoke`. The cancel endpoint 200 lines away does exactly that. With `STALE_AFTER_MINUTES = 30`, one worker at concurrency 1, and a 10-minute beat, everything past roughly the 7th queued render crosses the stale line while still queued. Creators get told "your render timed out, credit returned" and then the worker delivers the video anyway, free.
2. `pipeline/runner.py:618` — `refund = video.credits_used or 1`. A free restyle never sets `credits_used`, so any failing free restyle mints a credit that was never charged. Not a theoretical attack: one transient edge-tts or Pexels blip does it.
3. `runner.py:204` and `runner.py:328` set `video_url = f"/media/{id}/final.mp4"` directly, bypassing `_store_media` — the only function that uploads to object storage. The api service in `deploy/docker-compose.prod.yml:31-54` has no volume. **The entire clip-mining and montage feature 404s in production.** Nobody has ever successfully used it on kliptos.app.

Five mocked tests over `runner.run()` would have caught all three. `runner.py` and `assembler.py` are 875 lines holding every money transition and all output quality, and they have effectively zero coverage — the only "test" of the montage lane asserts that the *string* "at least 2 clips" appears in runner.py's source text.

Two more:

- **Day 2 is silently broken.** The backend token lives 24 hours (`config.py:25`); the NextAuth session lives 30 days with no refresh (`auth.ts:19-49`). The Library and Discover pages destructure only `{data, isLoading}` and never render an error. So the most likely second-day experience is an app that looks signed in and says "Nothing here yet," 0 credits, and a Refresh button that does nothing.
- **Free proof renders are unmetered by design and can destroy your only expiring asset.** `PLAN_ENFORCEMENT_ENABLED = False` (`config.py:33`) makes `plans.effective_plan` return PRO to every signed-in stranger; proofs accept `engine="ai_image"`; the only ceiling is 20 per 300s in Redis. Four proofs a minute is roughly $8.40/hour of Vertex. The ₹28,694 credit that expires 16 November is gone in about forty hours, while simultaneously starving every paid render on the same single worker.

### Theatre

Four claims on the live landing page have no code behind them, and none carry the `soon: true` flag the same file uses correctly two lines away: "Priority render queue" (`page.tsx:239` — `plans.priority` has no consumer, and there is one worker at concurrency 1, where priority is meaningless by construction), "Your logo and brand colours" (only a caption fill colour exists; `plans.require(user, "brand_kit")` is never called anywhere), "Bulk creation queue" (no such endpoint), and "Multiple channels" as a Studio exclusive (`routers/channels.py` has no count check — every Free user already has it).

The owner-only economics endpoint is structurally incapable of reporting a loss: `costs.py:17` prices `llm:gemini` at `0.0 # free tier` while every platform call goes through Vertex; `image_gen.py` contains zero `track()` calls; `premium_voice` is tracked but absent from `UNIT_COSTS_USD`. It will report 100% margin no matter what the AI-image lane burns. That is the number an investor would be shown.

"9 formats" is 4 render lanes with 9 presets, and moods exist on only 3 of them. I checked: all nine carry `available: True`, and exactly one — shayari at `formats.py:197` — has a language override. Every other format is English-default. The rest are reddit story, fake text convo, viral story, breaking news, motivational, music visual, gaming update, image carousel — which is very close to the AutoShorts and Crayo feature list. An India-first product is currently one-ninth India-native.

And there is inverse theatre, which costs you money: studio-grade voices are wired, keyed, tested and live end to end — including the genuinely hard part, re-transcribing generated speech with the resident Whisper to recover word timings — while `page.tsx:240` still says "coming soon."

### The uncomfortable facts, flat

- **3 accounts. 6 videos. 1 render.** No feature in this product has ever been exercised by a stranger.
- **₹499 and ₹1,299 are already on the public landing page** (`page.tsx:231,243`) with a nav anchor. The price has been in market. The result is 3 accounts. That is the only real demand signal you have.
- **You cannot read it.** `routers/analytics.py` raises 501 on every route. A grep for `posthog|mixpanel|amplitude|plausible|gtag|segment` across `frontend/src` returns nothing. You cannot tell whether the 10 September stranger opened the studio or bounced in nine seconds.
- **Nobody has ever hit a paywall.** With enforcement off, every signed-in user gets Pro — no watermark, 1080p, 300s, publishing, standing orders. Every upgrade trigger the pricing design depends on is currently disabled.
- **There is no way to pay and no way to say you would have paid.** No email field, no waitlist, no outbound sender anywhere in the repo.
- **The first ceiling is not the box — it's the Pexels free key.** At roughly 14 requests per render against published free limits of 200/hour and 20,000/month, the *whole platform* caps near 1,400 renders/month, about 46 a day, shared across every user, every proof and every free restyle. Two independent passes computed this separately and agreed. Any plan that assumes thousands of signups is describing a different company than the one that exists.
- **There is no download or share button anywhere in 55 frontend files.** No `<a download>`, no `navigator.share`. A phone user physically cannot get a finished video out of Kliptos — while `page.tsx:32` promises "videos you can download and post." Instagram publishing isn't built, so on the platform your audience actually uses, there is no exit at all.
- **Your real build capacity is Sundays, not weekends.** The repo has 140 commits over 45 days, 24 of them active. The launch sprint was 77 commits in 6 days. The 28-day window while employed and finishing the degree was 30 commits in 11 days — roughly a 10x decay, and that window is the one that matches the next 90 days. By weekday: Sunday 36, Wednesday 30, Monday 27, Tuesday 21, Thursday 16, **Saturday 7, Friday 3.** 68% of commits land between 19:00 and 01:00. Any plan that estimates in "weekends" is estimating in a unit you do not have.
- **The ₹28,694 credit expires 16 November.** At 6 videos of lifetime traction, roughly 99% of it lapses unused. It is not runway. It is a use-it-or-lose-it subsidy your traction cannot eat.

---

## 2. HOW IT COMPARES GLOBALLY

Real prices, fetched live where marked.

| Product | Entry | Mid | Top | Funding / scale |
|---|---|---|---|---|
| InVideo AI | $9/seat/mo annual | $25-30 | $60-80 | $70M ARR on $52.5M raised, 184 staff (Tracxn/valueforstartups, partial) |
| OpusClip | Free → $15 | $29 | Business custom | $50-68M raised, $215M valuation Mar 2025, SoftBank (Sacra/PitchBook, partial) |
| Submagic | $19 or $12 annual | $39/$23 | $69/$41 | $8M ARR, **bootstrapped**, 13 people (getLatka, partial) |
| Captions.ai | Free → $24.99 | $69.99 | $279.99 | $100M raised, $500M valuation; +$75M growth Mar 2026 (Businesswire/Contrary, partial) |
| Crayo.ai | $13 | $27 | $55 | Verified live pricing |
| Vadoo.tv | $19/$15 annual | $39/$31 | $99/$79 | Verified live pricing |
| HeyGen | Free → $29/$24 | $49 | $149 | Verified live pricing |
| AutoShorts.ai | $19 | $39 | $69 | Partial — pricing page 404'd, from reviews |
| Magicroll (India) | $29 | $49 | Enterprise | INR billing + GST invoices; MIB / NVIDIA Inception / Microsoft for Startups |
| Scenith (India) | ₹349 | ₹749 | — | Partial |

The 2026 price floor for a paid plan in this category is **$9-15/month** (verified across InVideo, Submagic annual, Crayo, Nullface, OpusClip, Quso, SendShort). Your $19 Pro sits *above* that floor while offering less than InVideo at $9/seat.

**Where you are ahead.** The proof render is close to unique — converting "gamble a credit" into "look first" is not something a revenue-per-user-optimising competitor wants to build. Correct Devanagari caption rendering is real and hard-won: `captions.py:347-354` forces `spacing = 0` for Devanagari, with the comment "This — not the font — was the actual bug: the render stayed broken with Noto loaded until spacing went to 0," plus a bundled Noto handed to ffmpeg via a *relative* `fontsdir=.` to dodge Windows colon-parsing in filter args. **Important caveat: this is unproven against competitors.** CapCut advertises Hindi/Marathi/Tamil font support and Submagic claims 48+ languages, and nobody publishes whether their vowel marks compose correctly. And you run both directions through one studio — ingest *and* generate — which OpusClip and Submagic (ingest only) and AutoShorts, Crayo, Revid, Vadoo (generate only) do not.

**Where you are level, and this is the answer to "are we lagging."** On voice quality: no. That assumption is falsified. Fliki has 3,025 Trustpilot reviews at 4.3/5 and reviewers "consistently highlight natural-sounding artificial intelligence voices." Robotic voices are not a top-2026 complaint; TTS is a commodity layer. On beat sync: no — CapCut ships Auto Beat Sync free with no watermark. On watermarks: they barely register as a complaint anywhere in the corpora I read. On autopilot: you are level and that is bad news, because it is the category default across 10+ tools at $13-19.

**Where you are behind. On visuals — yes.** But so is everyone, and this is the single most important finding in the whole exercise. Your GTA disappointment is the #1 verbatim complaint in this entire market:

- AutoShorts, 1★: *"All the images it makes for videos are just static, nothing dynamic. You constantly need to fix the generated images"* ([Trustpilot](https://www.trustpilot.com/review/autoshorts.ai))
- InVideo, 1.9/5 across **1,014 reviews**: *"slow, super bad quality of videos, the frames do not make sense"*, *"shockingly poor—often unusable, incoherent"* ([Trustpilot](https://www.trustpilot.com/review/invideo.io))
- Faceless.video review: *"two of my videos had a Roman emperor mentioned while a clearly Greek statue filled the screen"* — concluding these tools *"struggle in any niche where visuals carry meaning"* ([crepal.ai](https://crepal.ai/blog/aivideo/faceless-video-review/))

You are behind your own expectation. You are level with the state of the art. **Nobody has solved this.**

You are also behind on distribution (VEED 8.76M monthly visits, InVideo 7.10M, OpusClip 5.81M, per aicpb.com; you have 3 accounts), on mobile, and on language breadth (Fliki 80+, HeyGen 175+ dialects; you ship English, Hindi, Spanish, Portuguese — and the two non-Indian ones serve markets you have no formats, trends or story for).

One thing you are *not* behind on, despite thinking you are: **AI video generation.** A full-repo search for veo, runway, kling, luma, pika, sora, higgsfield, image_to_video and stable-video found exactly two things — a dead price row `"veo_fast": 8.50` that `routers/pipeline.py:28` will reject, and an unused `HIGGSFIELD_API_KEY`. No abandoned branch. Nothing was started and given up on. And the market says do not start: six 5-second Seedance 2.0 scenes for one 45-second video is roughly $2.00-2.70 (devtk.ai / buildmvpfast, partial), which exceeds the entire gross revenue of a ₹499 month. OpenAI discontinued the Sora app on 26 April 2026 explicitly because video generation compute could not be contained (TechCrunch/TechXplore, partial). "AI illustrated" does exactly what your own UI label says — "A generated scene per line with slow pan/zoom." The label is honest. The word "illustrated" just doesn't read as "stills" to the person who built it either.

---

## 3. THE ANSWER TO "HOW DO I MAKE IT UNIQUE"

### The scoring winner lost, and I am not going to defend it

Four strategies were scored. India-first regional-language expansion won on points (49/48/47/45). Three adversarial passes then attacked it and all three returned FAILS. They are right, and here is specifically why:

- **A funded competitor neutralises all four of its declared differentiators in about a month.** The libass fix is fifteen lines and is the most visually obvious defect a renderer can produce — an Indian QA engineer files it on day two of Devanagari testing. Nine Noto Indic fonts are SIL OFL; anyone bundles them without asking. Sarvam Bulbul V3 at ₹30/10,000 chars beats ElevenLabs on Hindi prosody *by your own research* (blind study, 20,000+ votes, 500+ annotators — sarvam.ai, partial), so a funded player's paid voices are audibly *better* than your free edge-tts, and they ship 11 languages including Punjabi, Odia and Assamese, which — verified against the project's own venv — edge-tts has **zero voices for**. The format recipes are 2,347 characters of prose across nine formats; a shayari page runner with 200k followers, hired for one month, out-writes them and ships fifteen. And ₹99 gets answered with ₹0-forever by anyone who doesn't need profit.
- **The plan was 1.5-2.5x over capacity** — 150-190 honest hours against 70-110 net — and estimated in weekends you don't have, and shipped six languages you cannot proofread. Broken Telugu looks fine to a non-reader and looks like the competitor screenshot to a Telugu creator.
- **It contained no willingness-to-pay evidence of any kind.** Not one named person who said they'd pay, not one competitor's disclosed paying-user count in the Indic ₹99-499 band. The one *observed* behaviour it cites argues against it: a **shared** ₹149-299/YEAR Canva Pro login is ₹12-25/month effective, obtained specifically to avoid the retail price. ₹99 is a 4-8x increase over that revealed reservation price, and the predictable outcome is not churn, it's sharing — one login, five page runners, a WhatsApp group, on one worker.

### The positioning I am committing to

> **Kliptos will not put a wrong visual on your video. When it can't find the right shot for a line, it tells you which line and asks — instead of quietly dropping in stock footage that makes your video look fake.**

That is the whole pitch. No architecture, no margins, no format count. It is your own GTA render, turned into the product's spine.

Mechanically it is one new branch on a ladder you already built. I verified the ladder: `runner.py:502-528` resolves visuals in the order `asset_id` (your own footage — the comment literally reads "the creator's own footage beats stock") → generated still → `media_id` (pinned stock) → and then an unconditional `else` that always searches Pexels with the line text and always returns *something*. The fifth outcome goes before that `else`: if the line carries a named entity, no own-footage pin cleared threshold, and stock is the engine, **don't run the blind query.** Block the render, name the line, and say what's missing.

Underneath it, one line per scene explaining why that visual is there: "your clip at 02:14, matched 'oppressor'" / "library: rain on window (no entity in this line)" / "no shot found — title card." Copy the `describe()` pattern already in `highlights.py`, which states the measurement rather than implying understanding.

### Why this beat the alternatives

**Because the attacker told me it's the one thing they won't copy, and gave a reason with a number.** The competitor pass, having demolished everything else, wrote: *"I will not ship a state that says 'Line 4 says Oppressor MK2 — stock has nothing.' My entire funnel is 'video in 30 seconds, hands off.' A blocking state lowers my activation rate and my growth lead kills it at sprint review. I might ship it off-by-default as strict mode in Q2."* That is a **positioning lock, not a technical one** — and positioning locks are the only kind a solo founder can hold, because they cost the incumbent the metric their growth team is paid on.

Four supporting reasons:

1. It answers the category's #1 complaint with a designed behaviour rather than a quality promise nobody can verify. Everyone claims better visuals. Nobody says "I'll tell you when I don't have one."
2. It is already this codebase's culture. `highlights.py` says an empty list "is a real answer and must not be dressed up as a suggestion." `routers/pipeline.py:111-123` already refuses to charge for a blank scene and names the scene number. You have shipped this instinct twice; this makes it the product.
3. It is the product embodiment of the standard you hold yourself to. You rejected overclaiming in the pitch. This is a tool that refuses to overclaim about its own output.
4. It generates its own marketing asset and its own QA instrument. A receipt screenshots. A feature list does not. And thirty receipts tell you instantly where matching is wrong without touching the 501'd analytics router.

### What I grafted in, and from where

- **From the own-footage thesis, the single strongest idea in the exercise:** the cold DM that contains three finished Shorts cut from the prospect's own public VOD, sent with no ask. Zero cost, zero reach required, fully asynchronous, and structurally unavailable to a funded self-serve funnel — nobody's growth dashboard has a row for hand-making videos from strangers' handles. It inverts the sales motion from "try my tool" to "here is your content, finished."
- **From the vertical thesis:** burn the expiring Vertex credit into an owned mood-image library on R2 before 16 November. Roughly $300 buys ~7,700 flash images. This is not sentiment — it does three jobs at once: it removes the Pexels quota that is currently your first revenue ceiling, it makes marginal cost LLM tokens only, and it converts an asset that dies into one that compounds. **Be precise about what it cannot do:** a generated still cannot render an Oppressor MK2 correctly. The library serves mood and atmosphere lines. Entity lines with no own footage go to the title card and the refusal, and that is the correct answer, not a compromise.
- **From India-first:** the Razorpay Individual/Unregistered KYC correction (below), the ₹149 one-time top-up as first monetisation, the per-user proof cap, the `footage_match.py:11` Unicode regex fix, and Marathi — one evening, because it shares the Devanagari font that already works.
- **From the competitor attack:** the buyer moves up. Alongside the 5k-50k Hindi update-channel operator, pitch **regional coaching institutes and district news outfits at ₹2,999-9,999**. This is the one segment the attacker said it would leave on the table for a year — *"too small for my sales quota and too high-touch for my self-serve funnel"* — and Magicroll already proved it by walking upmarket to national media houses. For them a wrong visual is expensive, not annoying. Twenty customers at ₹5,000 is ₹1 lakh MRR from twenty relationships, and 20 × 30 renders = 600/month sits comfortably inside the ~1,400 Pexels ceiling that thousands of consumer signups detonates.
- **From the demand attack:** kill thresholds written down before the first DM, and the discovery that you can take money *this week* — `models/credit.py:13` already documents `purchase` as a ledger type, and `credit_grants.py` explicitly never reduces a balance already above the allowance. A hand-fulfilled sale is an already-designed state: a UPI QR and one INSERT. **"The 501 is the whole business" is false.** The 501 is a scaling convenience. The gate is that nobody has ever been asked for money.

### Modifications the attacks forced

1. **The consumer tier is a proof cohort, not the revenue thesis.** Cohort A (Hindi update channels) stays, because they are where the refusal is most visibly valuable. Cohort B (institutes, district news) gets pitched in the *same fortnight*, because that's where the money is and it was scheduled nowhere in the original plan.
2. **Two payment rails in the same month, not Razorpay-then-hedge.** Polar lists India for payouts via Stripe Connect Express and supports individuals; Dodo Payments is Bengaluru-based and explicitly serves individual founders. The USD tier is the default, not the fallback.
3. **The caption comparison test runs privately in week 1 and is never published.** *Disagreement surfaced:* the India-first thesis called it "THE demo… it goes at the top of every pitch." The competitor pass called publishing it "a free, precise bug report telling me exactly what to fix and that it converts." I side with the attacker. Use it as a sales demo, one-to-one.
4. **Six languages deleted from the quarter.** Marathi only.
5. **The footage-viability question gets tested before the refusal is built.** This is the wedge thesis's verified fatal flaw and nothing in the original plan tested it: `footage_match.py` scores script lines against Whisper transcripts, needing 3 shared content tokens. A BGMI or GTA screen recording is often silent, or music-only, with the Hindi commentary added later in InShot. In that case nothing pins on any line, and the refusal fires on every line — which converts *worse* than the generic stock it replaced. So: of ten real recordings from real prospects, how many arrive at all, and in how many does Whisper find enough speech to pin the entity line? That question comes before the build.

---

## 4. WEB OR MOBILE

**Web. Responsive, plus a PWA install. Not native, and not "mobile as its own product."**

The reason is in your own code. `preview/[id]/page.tsx:108-151` — render progress and the finished video, the single most phone-shaped screen in the product and the one you'd build a native app *for* — is already correct at 390px: `flex-col lg:flex-row`, player at `width:100%/maxWidth:380`, `playsInline`, a capped progress grid, and copy that says "you can leave this page." Twenty-two responsive Tailwind grid classes already collapse every content grid below 640px. "No mobile pass at all" overstates the damage: eight of twelve dashboard routes are cramped but usable, two overflow, and one — the shell nav — pushes controls off-screen.

The breaks are four named files: `transport-bar.tsx:87,95` (a `repeat(4,1fr)` grid demanding ~558px inside a 390px fixed bar, which pushes the credits chip and the *entire* Account menu — Settings, Billing, Standing orders, Sign out — off the right edge), `studio/page.tsx:247` (mode toggle at `width:"fit-content"`, ~460px intrinsic), `rail-conveyor.tsx:94` (a 340px minimum track in a 310px box), and `line-shell.tsx:51,66` (`100vh`, 80px of side padding on a 390px screen, no `env(safe-area-inset-bottom)`). That is two Sundays.

Against 8-14 weeks of evenings to fork roughly 3,350 lines of dashboard UI, after which every future feature costs double — and a store cut of 30% (15% under the Small Business Program) landing on top of a price you deliberately set at one third of US, with no India equivalent of the US-storefront link-out carve-out (that 0% route is an artifact of the Epic ruling; Google Play India's user-choice billing reduces the fee by about 4%). A ₹499 Pro nets roughly ₹349 through a store versus roughly ₹489 on web at Razorpay's ~2% + GST. And Submagic — $8M ARR, 13 people, the closest analogue in scope — publicly has no native app and tells users to upload from the phone browser.

**Do not build:** React Native, in-app purchases ever, a separate mobile product, push notifications before payments (a push about a free credit is not worth building).

**Do build, in this order — and the first two matter far more than layout:**

1. **The in-app-browser interstitial on `/sign-in`** (2 hours). `auth.ts:13` has Google as the sole provider and no email or magic-link path exists. Google returns `disallowed_useragent` for OAuth inside the WhatsApp and Instagram webviews — which is exactly what opens when someone taps a shared kliptos.app link. Your only distribution channel currently hard-fails at the door.
2. **The share/download button** (2 hours). `navigator.share({files})` with an `<a download>` fallback. Without it a phone creator cannot post a Kliptos video at all.
3. **Presigned multipart direct-to-R2 upload.** `clips/page.tsx:150-168` is one non-resumable POST, `media.py:27` caps at 500MB, and Caddy sets `write_timeout 300s` — which needs ~13 Mbps sustained against a typical Indian mobile uplink of 3-8 Mbps. Practical ceiling ~100-150MB, and anything over it dies with a bare error and no resume. This is the front door of the entire strategy.
4. The four-file layout pass. Then `manifest.ts` + web push, after payments.

---

## 5. THE PLAN

**Unit of account: Sundays, plus two or three evenings.** Roughly 8-12 hours a week, measured from your own commit history. **Block the festival dates yourself — I don't know the 2026 dates for Navratri, Dussehra or Diwali and I'm not going to guess them into your calendar.** Assume they cost you two Sundays inside this quarter.

### Week 1 (10-16 Sep) — one decision, one evening
- **Owner action, the only one:** read the employment agreement and get the IP answer. Nothing else this week. Your degree completes 16 September.
- **One evening of code:** the per-user *daily* proof cap in the database, not just the Redis window. This is the only item on the list where being wrong is unrecoverable — it protects the ₹28,694 credit from a single motivated signup.
- **One afternoon, free:** read 200 one- and two-star reviews of "Video Shayari" (~450k downloads) and its clones on Google Play. Those are people who wanted exactly this, already tried to pay, and wrote down why they stopped. It either hands you verbatim demand language or kills the consumer tier before you write a line of checkout code.

### Week 2 (17-23 Sep) — two rails, in parallel
- **Razorpay KYC as "Individual / Unregistered Business."** PAN, Aadhaar or photo ID, bank account, IFSC. That is the whole list, per [Razorpay's own KYC documentation](https://razorpay.com/docs/payments/business-types-kyc-documents/) — one of thirteen supported types. No Pvt Ltd, no LLP, no GST (you are far under the ₹20 lakh services threshold). **Registering as a Proprietorship is strictly harder** — it demands two business-identity documents. The belief that no company means no payments is the most expensive wrong assumption in your plan.
- **A merchant-of-record in the same week.** Polar or Dodo. This is not a hedge; it is the USD rail, and it is the difference between a ₹20k ceiling and a real business.
- **Email Razorpay support one precise question, in writing:** can an Individual/Unregistered business type enable Subscriptions? That is undocumented and bank-discretionary. Plan around the answer; don't guess it.
- **One evening:** flip `PLAN_ENFORCEMENT_ENABLED = True` and add five server-side events (signup, studio_open, script_generated, render_started, pricing_click). Not PostHog. Any record at all. Without enforcement nobody can *want* past a limit; without events you learn nothing from whoever does.

### Week 3 (24-30 Sep) — unbreak it, then take money by hand
- Two-line `_store_media` fix (~20 min). Unicode regex in `footage_match.py:11` (~2 hours with a Devanagari test). Share/download button (2 hours). OAuth interstitial (2 hours).
- **Then take money without any checkout code:** personal UPI QR, one INSERT into `CreditLedger` with `type='purchase'`, adjust the balance. Already-designed state.
- **MILESTONE: first ₹149 received by 30 September 2026.** If that date slips past 14 October, the problem is the pitch, not the product.

### Weeks 4-5 (1-14 Oct) — the priced pre-sale
Ten hand-made videos for cohort A, each cut from that prospect's own public VOD, delivered free with a price attached: "Yours, keep it. Ten more like it is ₹149 — pay this QR and I'll load your account tonight." Ten phone calls to cohort B.

Two questions in every cohort-A message, because their answers are worth more than the rest of the quarter: **what do you pay someone to cut Shorts today**, and **would you run this on your monetised channel.** The first tests a number nobody in this entire research pass could source — the "₹300-1,500 per Short" freelance editor rate is *unverified* and it is load-bearing for the whole pricing argument. The second tests whether the demonetisation risk is a structural no.

**Kill thresholds, written before the first DM:**
- **≥5 pay** → demand is real. Ship the top-up, run the rest as written.
- **1-4 pay** → price is real, channel is the constraint. Next quarter is DM volume and cohort B, not seven languages.
- **0 pay but ≥6 reply warmly asking for more free videos** → the most likely outcome. Pain confirmed, willingness-to-pay refuted. Redirect entirely to cohort B and the USD rail.
- **<5 of 20 even reply** → the artifact is the problem. Build the refusal first and re-test.
- **Any cohort-A operator who says "I won't run AI on my monetised channel"** → that is structural, not an objection to handle. Two of three is a rewrite.

### Weeks 6-8 (15 Oct - 4 Nov) — build what the twenty asked for
THE REFUSAL plus the relevance receipt. The four-file mobile pass. Marathi (one evening).

**Measure two numbers and nothing else,** both computable from `script_data` without touching analytics: share of scenes where the creator *kept* Kliptos's shot, and share of refusals that were *correct*. Under 60% on the first means matching isn't good enough to sell. Under 80% on the second means the refusal is noise and people will turn it off.

### Weeks 9-10 (5-18 Nov) — the credit, hard deadline
Script `image_gen.generate_image` over mood tags, curate, store on R2, add a `library` engine. **Must land before 16 November.**

### Weeks 11-13 (19 Nov - 9 Dec)
Resumable upload. Then the shot-pack export (numbered vertical clips + a `shots.txt` line-to-file-to-timestamp map), so you can be adopted *alongside* InShot rather than instead of it. Then four promo Reels every other Sunday, made with Kliptos, leading with the one honest format: "what the AI gave me for line 4 versus the shot I actually used."

### DELETE (all one-line changes unless noted)
| Delete | Where | Why |
|---|---|---|
| The four fake landing-page claims | `page.tsx:238-247` | No code exists. Easiest thing for diligence to falsify. |
| `priority`, `brand_kit`, `premium_engines` from `/billing/plan` | `plans.py`, `billing.py:41-46` | Advertising unimplemented features through an API |
| "Studio-grade voices — coming soon" | `page.tsx:240` | The lane is live, keyed and tested. One character, real revenue. |
| Image Carousel | `formats.py:267` → `available: False` | A carousel tool inside a Shorts tool, aimed at the one channel that can't publish, and the only format excluded from the free proof render |
| Breaking News, Gaming Update | `formats.py` → `available: False` | Entity-bound visuals the pipeline cannot fetch. Gaming Update's own recipe says "no copyrighted game footage" — this is your GTA render, specified. |
| 16:9 output | `assembler.py:18-22` | A widescreen "Short," unmarketed and unexercised |
| Spanish + Portuguese | `voices.py` LANGUAGES | Markets with no formats, no trends, no story — while Marathi is one evening away |
| HeyGen key slot | `user_keys.py:16`, `settings/page.tsx:328` | `validate_key` does a live `/v2/avatars` call, so a key **succeeds** and delivers nothing. Keep `heygen.py` on disk. |
| Orphan `educational`/`commentary` styles | `script_gen.py:80-127` | Reachable only behind Custom, named in no document |
| `test_montage.py:229-233` | — | Asserts a source-code string. Passes while the feature 404s. |
| The stale beat-sync comment | `runner.py:222-226` | Contradicted by `runner.py:269-288` twenty lines below |
| The word "moat" in a code comment | `harvester.py:333` | Self-marketing inside source is how a pitch scores 1/10 |
| "no human intervention" as a public promise | Everywhere | Keep the standing order. Kill the pitch. See §7. |

Also fix, cheap: `refund = video.credits_used or 0` and zero it after (15 min); `revoke` before the reaper refunds plus a status guard in `runner.run` (1 hr); atomic `UPDATE users SET credit_balance = credit_balance - :cost WHERE … AND credit_balance >= :cost` (1 hr); `SERIES_RENDER_COST = 1` → engine-aware, because `series.py:99` permits `ai_image` on autopilot so a daily 6-scene AI series bills ₹10 for ~$0.23 of images, unattended (30 min); montage watermark (2 hrs); Celery `task_soft_time_limit` (1 hr); `CREDIT_PRICE_USD` → 0.09, since the cheapest credit you actually sell is Studio India at ₹1,299/150 = $0.0906, which makes `MARGIN=2.0` really 1.81 and Pricing.md's "no render can lose money in any region" false (1 hr).

### Needs your decision, not mine
1. **The employment agreement.** Razorpay KYC attaches your PAN to a revenue-generating business while you are employed under a contract nobody has read. It is the only irreversible act in this plan.
2. **Cohort B's exact segment.** You know Indian coaching institutes and district news channels; I don't. Pick the ten.
3. **Instagram: delete or start.** Either remove `ig_upload_tasks.py`, the router and the doc (~250 lines, and line 35 concatenates `https://api.kliptos.app` + an absolute R2 URL, so it's wrong as well as unreachable), or submit the Meta app review this month. It is calendar-gated at 2-4 weeks per submission. The one unacceptable option is leaving it half-built while the handover says it doesn't exist — the next reader will trust the code over the doc. Also: no API tool can attach Instagram's licensed trending audio to a Reel. Say that in the product.
4. **Whether narrowing the *buyer* is acceptable to you.** You said explicitly you're building for content creators generally, and faceless shayari is one slice. I have not contradicted that — the product stays general-purpose, all nine formats stay in the code, and the refusal helps every entity-bound format. What narrows is who you *sell to first*. If that still feels wrong, say so, because it's the load-bearing assumption in this plan.

### Needs money
- **One month of competitor subscriptions for the private comparison test.** Submagic Starter $19/mo (verified), Magicroll Spark $29/mo (verified), Canva Pro ₹799/mo before 18% GST (partial), plus a phone for InShot. Roughly ₹5,000-6,000 total; the exact figure with GST and FX is unknown. The original plan budgeted ₹0 for this, which is not a plan.
- **A second ₹799 box**, when queues bite. Noise against any revenue.
- **Sarvam Bulbul V3 at ₹30 per 10,000 chars** (partial) if Hindi voice quality becomes the pitch. A 45s script is roughly 600 characters.
- **A raised Pexels quota** (free — email them) or the owned library. One of the two, before volume.

---

## 6. THE FIRST TEN USERS

**The channel is a DM containing a finished video they did not ask for. The venues:**

1. **YouTube search, tonight, as a prospecting tool.** "BGMI new update hindi", "GTA 6 news hindi", "Free Fire new event hindi", "iPhone 17 price India hindi" — last 7 days, sorted by upload date. Take every channel between 5,000 and 50,000 subscribers. Pull the Instagram handle from the About tab. DM.
2. **YouTube's Live-now filter** for the same searches. Their previous stream's VOD is public and downloadable. That is your raw material.
3. **Indian GTA 5 RP server Discords.** A hundred creators share one session, so one good clip circulates to ten prospects who were all in the same scene. Join as a viewer, post nothing publicly, DM the owner.
4. **[hashfame.com](https://hashfame.com/)** — Bengaluru, invite-only, 150,000+ manually verified Indian creators, run largely over WhatsApp. The only verifiable India-specific concentration of this exact buyer that any research pass could confirm. Apply as a creator first.
5. **Google Play review sections** for "Video Shayari" (~450k downloads per AppBrain), "Video Pe Shayari Likhe", "Heart Touching Video Shayari Status." Template apps, not pipelines. Their low-star reviews are a list of people who already tried to pay for this.
6. **Cohort B: regional coaching institutes and district news channels.** Searchable by language on YouTube. Ten phone calls, not DMs. Ask about GST invoices and volume in one language.
7. **Your own degree cohort**, completing 16 September. Warmest ten people you can reach, right age band, several already run pages.

**Not, with reasons:** Reddit — 39% of the subreddits founders pitch in ban self-promotion outright, r/SaaS banned this product category in mid-2026, and reddit.com was unreachable to every research pass, so **any subreddit name in this document would have been invented**. Verify venues yourself before spending time there. The global faceless Discords (Faceless Incubator ~37.8k, YouTube Faceless ~21.7k) — US-centric, and the larger explicitly bans self-promotion. Product Hunt as a plan — without a PH network the realistic landing is rank 11-40, which is 10-30 signups for a week of prep ([causo.ai traffic data](https://hub.causo.ai/guides/product-hunt-traffic-data-2026)); do it once later for the backlink. SEO for 12 months — Zapier, Synthesia and VEED own the head terms, domains under two years old are 2.03% of top-10 results (SE Ranking, 100k SERPs), and AI Overviews cut organic CTR 34-61%.

---

## 7. WHAT I WOULD NOT DO

**AI video generation, ever, at India pricing.** $2.00-2.70 per 45-second video exceeds a whole ₹499 month of gross revenue. OpenAI shut Sora's app down over exactly this. If it ships at all, it is a metered top-up with the rupee price shown before the render.

**A native app or in-app purchases.** §4.

**AppSumo, at any tier.** A $59 Marketplace deal nets $17.70 after their 70% share, which covers roughly seven months of one active user's real render cost before going permanently negative with no cancellation mechanism. And a thousand-buyer cohort each rendering three videos is thousands of serial renders through one worker at concurrency 1, inside a 60-day refund window, while you're at your day job. It would break Kliptos operationally before it broke it financially. It is also the most tempting thing on this list, which is why it's here.

**Sell "no human intervention."** Keep the standing order; kill the promise. YouTube's monetisation policy explicitly excludes *"AI-generated content made with generic or unoriginal templates giving the impression of mass production without adding the creator's original, authentic insights or perspective"* and requires content *"not be mass-produced, generic, repetitive"* ([support.google.com](https://support.google.com/youtube/answer/1311392), verbatim, live page; the rename from "repetitious content" was 15 July 2025). Instagram, 30 April 2026, Adam Mosseri: *"If most of what you post to Instagram is someone else's content, your account is no longer going to be recommendable"* ([Tubefilter](https://www.tubefilter.com/2026/04/30/instagram-removes-algorithm-recommendations-repost-content-aggregator/)). Your default output path — Pexels stock plus edge-tts narration plus burned captions, produced unattended on a schedule — is the closest possible match to what both policies name. Selling that to a monetised creator is selling him a demonetisation risk. And 85% of 16,000 surveyed creators said they would use AI **that learns their creative style** ([Adobe/Harris Poll, Sept 2025](https://news.adobe.com/news/2025/10/adobe-max-2025-creators-survey)) — not AI that replaces them. Reframe autopilot as "drafts waiting for your approval every morning." Same code, opposite pitch, and it's the pitch that matches your own thesis instead of contradicting it.

**Seven languages this quarter.** One, and it's Marathi.

**Incorporate a Pvt Ltd to unblock payments.** Not required, and slower than the thing that is.

**Publish the Devanagari comparison.** Private sales asset only.

**Chase the gaming-clipper category.** `beats.py` and `highlights.py` are the best-engineered files in the repo — hand-rolled FFT autocorrelation with parabolic interpolation and phase locking; relative-threshold RMS peak-picking with an asymmetric window; no GPU, no model download, honest docstrings. Genuinely good work. And OpusClip has SoftBank money, Eklipse reads actual game state across 3,000+ titles which is strictly better than loudness, and CapCut ships Auto Beat Sync free. Repurpose both as the mechanism that finds the *right moment* for a given script line. That is the wedge. "Best gaming clipper" is a fight you lose.

**Fix the whole test suite.** Five tests over `runner.run()` with tts, pexels, image_gen and assembler monkeypatched. That's the day; not more.

---

## 8. THE HONEST RISKS

**Platform policy toward AI content — and a disagreement inside my own research.** The *policy language* is verified verbatim from live pages, and it does not penalise AI use: YouTube explicitly permits monetising content that uses *"AI to visualize a unique character and narrative you invented"* or *"AI to edit your video scripts or generate a unique background visual."* The line is templated-versus-transformed, not AI-versus-human. YouTube also states AI labels *"won't have an impact on how a video is recommended or its ability to monetize,"* and Neal Mohan's 2026 letter says over 1 million channels used YouTube's AI tools daily in December. **The enforcement magnitude is not verified, and two of my research passes disagree about it.** One reported 16 channels with 35M combined subscribers terminated in January 2026 as fact; the other traced that figure — along with "4.7 billion views erased" and "$10 million in creator revenue vanished" — to SEO content-marketing blogs, several of which misdate the policy by a full year. **Do not repeat those numbers.** Treat the risk as real in direction and unsized in magnitude. One useful detail: photorealistic AI now attracts an on-video label overlay on Shorts, while *"lightly altered, animated, or unrealistic AI content keeps labels in the expanded description only"* — which is a real reason to prefer illustrated over photorealistic.

**The single-box dependency, and the ceiling nobody expected.** One 2 vCPU / 8 GB box running API, Celery beat, one worker at concurrency 1, and raw ffmpeg. The architecture is the right call and I would not change it — Neon and R2 hold the durable state, and the runbook is honest about it. But two things: the real ceiling is the Pexels free key at roughly 1,400 renders/month platform-wide, reached at maybe 90 subscribers, well before the VPS or any Vertex bill; and the "this box is disposable" claim in `DEPLOY-VPS.md:160-163` is **false** — `upload_tasks.py:27` reads rendered files from local disk with no storage fallback, so rebuilding the box makes every previously rendered video unpublishable. That doc actively tells the operator that destroying the volume is safe.

**Registration and payments.** The blocker you believe you have is not real — Razorpay's own documentation lists Individual/Unregistered as a supported type needing PAN, Aadhaar, a bank account and IFSC. What *is* genuinely open, and I am carrying it as unknown rather than guessing: whether an Individual account gets Subscriptions enabled. That is undocumented and sits with a partner bank. Which is precisely why the ₹149 one-time top-up ships first — no mandate, no RBI 24-hour pre-debit notification, no eligibility question.

**Is this market simply won?** Honestly, both halves. Clipping is won — OpusClip, Submagic and Captions took it on distribution. Prompt-to-video breadth is won — InVideo at $70M ARR gives Basic users more for $9/seat than you can match. Faceless autopilot is not won so much as *poisoned*: Crayo sits at 3.1/5 across 187 reviews with "ALL SALES ARE FINAL," AutoShorts at 3.4/5, and roughly 1 in 13 tracked AI image/video tools is already dead or acquired (tooldirectory.ai, partial). Positioning as "another faceless generator" inherits that distrust for free. What is *not* won is the thing you found by using your own product. Nobody has solved visual relevance, and the fix needs taste and iteration rather than capital — the one axis where being solo is an advantage.

**The demand risk, stated as plainly as I can.** ₹499 has already been public on your landing page and produced 3 accounts. RevenueCat's 2026 data puts India+SEA median Day-35 download-to-paid at 1.4% against 2.6% in North America, and year-one realised LTV per *paying* user at $14 against $32 — the worst region on both axes. Short-form is an audience-building mechanism, not an income mechanism, for most Indian creators, and only 8-10% of Indian creators monetise effectively (BCG via identitykit.in, partial). The most likely failure mode is not that the product fails. It is that it works, people like it, 200 of them pay a small amount forever, and it consumes every Sunday without ever clearing the bar to leave your job. **For the first year that looks exactly like success.** That is why the USD rail goes in the same month as Razorpay, and why cohort B gets called in week 4 rather than "later."

**Your capacity.** 8-12 hours a week, measured from your own commits. Saturday produced 7 commits in 45 days. A plan that assumes weekends assumes a different life.

**The employment-IP question**, unresolved, and it intersects week 2 directly.

**And one risk inside your own thesis.** "People quit content creation because it takes too long" is true and is also an argument against your buyer: a person who has quit is not a customer, they are gone. Your buyers are by definition the ones for whom the time cost is already affordable. That does not break the thesis — it means you sell to the person for whom a *wrong* video is expensive, not the person for whom a slow one is annoying. Which is the whole reason this document ended up where it did.

---

**The one thing to take from all of this:** your instinct about the GTA render was not a bug report, it was the strategy. You found the category's central unsolved defect by using your own product honestly, and you are the only person in this market whose stated values make shipping the fix — a tool that admits when it doesn't have the shot — feel like a feature rather than a conversion loss. Everything else in this document is sequencing.

---

## Completeness critique

## Verdict

The document is unusually good on the axes it covers — 30+ code claims I spot-checked came back exact (including `pytest --collect-only` → **299 tests collected**, which I ran). It commits to one answer on both questions asked. It is honest about the bad news. But it has one expensive structural gap that changes its central recommendation, one shipping-blocker-class bug it walked past while quoting the code it lives in, and a demand inference that contradicts itself.

---

## 1. It never engages the 298-line diagnosis of its own centerpiece, sitting in the repo, dated the same day

`C:\Users\Administrator\Desktop\Handover\Automation\docs\kliptos-vault\Visual Quality Diagnosis.md` — 2026-09-10, a 14-agent investigation into video `1bb26518-67bd-4110-a372-50a4b68ca825`, **the GTA render the document calls "the strategy."** The audit cites it nowhere and contradicts it on the central point. I re-verified its load-bearing claims:

- Root cause is `backend/app/services/formats.py:245-246` — the `gaming_update` recipe ends `visual_prompt = gaming setups, esports crowds, RGB keyboards, controller close-ups`. That is an assignment, not a constraint. All seven rejected visuals are that four-item list enumerated. **Confirmed verbatim.**
- The missing coupling clause ("filmable stock-footage description **matching that line**") **already exists** at `script_gen.py:136` — on the bring-your-own-script path only. **Confirmed.** The narrated path has neither.
- Same latent defect in `shayari` (`formats.py:192`) and `motivational` (`formats.py:133`). **Confirmed for shayari.**
- Its A1 is a **zero-code, same-day test**: standing feedback notes land last in the prompt (`services/feedback.py`, wired at `scripts.py:225-229`, "Apply ALL of it to this script"), so they should beat the recipe. Re-render, know in ten minutes.

Three consequences the audit's plan cannot absorb as written:

**(a) Its headline finding may be substantially wrong for Kliptos.** "Nobody has solved this… the fix needs taste and iteration rather than capital" is the load-bearing claim of §3 and §8. But the founder's own evidence of the unsolved problem was produced by four words in his own recipe file. Until A1/A2 runs (~1 hour + tests), nobody knows what share of "wrong visuals" is industry-hard versus own-goal — and that answer decides whether the refusal is a positioning lock or a workaround for a prompt bug.

**(b) Hard ordering error.** The refusal is scheduled weeks 6-8. It blocks a query built from `seg.get("visual_prompt") or seg["text"]` (`runner.py:531`). With `formats.py:246` intact, `visual_prompt` on gaming_update reads "gaming setups, RGB keyboards" — no entity in it. So the refusal fires on the *line's* entity while the pipeline had a serviceable generic query, which maximises the exact failure the document itself names as the wedge's fatal flaw (§3, modification 5: "the refusal fires on every line — which converts *worse* than the generic stock it replaced"). **A2 is a prerequisite and is on no list.**

**(c) A prerequisite the document doesn't name at all.** `runner.py:500-537` has **no try/except**, and `pexels.fetch_clip` raises on zero results (`pexels.py:84`). A "block the render, name the line" state landing in that loop is indistinguishable from the existing crash path — which fails the video and, via the `or 1` bug, refunds a credit that may never have been charged. The refusal needs a per-scene fallback layer first (vault A3, ~half a day).

---

## 2. A bug in the exact code the document holds up as evidence

The document cites `runner.py:502-528` as proof the refusal is "one new branch on a ladder you already built." I verified the ladder: `asset_id` (501) → `elif ai_visuals` (505) → `elif seg.get("media_id")` (525) → `else` Pexels (529).

**`media_id` sits below `ai_visuals`.** On the `ai_image` engine, a creator who hand-picks a Pexels clip for every scene in the studio gets green "Visual pinned" confirmations (`studio/page.tsx:875-925`), is charged, and receives byte-identical AI stills. The pin is silently discarded. That is precisely what the positioning promises Kliptos will never do — take money and quietly substitute — inside the file offered as proof of the culture.

It must ship with a pricing fix or it becomes a billing bug: `routers/pipeline.py:145-146` prices `ai_image` on the full segment count, so pinning 7 of 7 would charge 5 credits for 0 generated images.

---

## 3. The trend route fabricates its facts — a larger risk than anything in §8

Verified: `routers/scripts.py:232` sets `reference_text = None`; it is populated only inside the `source_url` branch (`:253`) and passed at `:307`. On the **Discover/topic route** the model receives `topic.title` + `topic.hook_text` and nothing else. The rejected GTA render's "Oppressor MK2 lock-on nerf," "Vigilante missile cooldown" and "Diamond Depot heist" were **invented from a stream title**.

§7 is right that "no human intervention" must stop being sold — but for the wrong reason. The real reason isn't policy optics: the unattended lane (`series_tasks.py`, standing orders) publishes fabricated factual claims in a *breaking news* format under a named real streamer, on a schedule. That is the strongest argument in the document's own favour and it never makes it.

Cheapest fix in either document, and it's omitted: `generate_script` **already accepts `reference_text`** (`script_gen.py:167`) and already injects "base the script on the FACTS in it (do not invent numbers or claims beyond it)" (`:186-190`). One call on the topic route. Also dead: `Topic.keywords` is written by the harvester at `harvester.py:103,161,200`, exposed in `schemas/topic.py:13`, and **read nowhere in the backend** — free anchoring for both the script and the Pexels query.

---

## 4. The cheap high-leverage move already built and hidden: `headline`

The document's answer is "studio-grade voices still say coming soon" — correct and worth one character. There is a bigger one, and it happens to be the fix for the formats the document proposes deleting.

`ScriptSegment.headline` exists (`schemas/script.py:52`). `captions.py` carries a complete per-scene Headline style — top-centre alignment, box padding, scaled font, `\fad(200,200)` fade (`:163-173, 274-293, 338-339, 376-395`). Both `runner.py:557` and `proof.py:143` already pass it. **All verified.** And: no prompt asks for it (`headline` appears in `script_gen.py`/`formats.py` only as an unrelated prose word at `formats.py:104`), and `grep -rn headline frontend/src` returns **nothing**.

So a designed news-card / motion-typography treatment that names the game *in text* — nominative use, zero reproduction of anyone's artwork, cheap on 2 vCPU, and the only honest way to make a Gaming Update or Breaking News video look on-topic — is one recipe line + one schema field + one studio input. A finished renderer with no user.

The document instead puts **Breaking News and Gaming Update → `available: False`** in the DELETE table, reasoning "entity-bound visuals the pipeline cannot fetch." That deletes the two formats the dormant renderer was built for, on a diagnosis (the brand ban) that the vault's three adversarial passes rejected as a red herring.

Two more in the same class:
- The per-scene **"Visual direction" input already exists** (`studio/page.tsx:897-903`) bound to `segment.visual_prompt`; the `ai_image` branch reads exactly that field; `FREE_RESTYLES_PER_VIDEO = 3` makes same-engine re-render free. **The founder could have fixed his rejected render by typing 7 prompts, for zero credits.** Not mentioned anywhere.
- `services/highlights.py` already solves the no-transcript gameplay case and is surfaced only on the clips page (`clips/page.tsx:290-346`), not in the studio's per-scene picker — which is where the document's own footage-viability test (modification 5) will fail without it.

---

## 5. The demand inference is invalid, and it's the document's most-cited fact

> "₹499 and ₹1,299 are already on the public landing page… The price has been in market. The result is 3 accounts. That is the only real demand signal you have."

`page.tsx:242` and `:249` — **both paid cards are `cta="Coming at launch" disabled`.** Verified. There was never a purchase affordance; the cards are a roadmap announcement. The document says this itself three paragraphs earlier ("Nobody has ever hit a paywall"; "no way to pay and no way to say you would have paid"), then uses the price-in-market reading twice, including as §8's headline demand risk.

Delete the inference. 3 accounts measures distribution, not price. Nothing in the repo has ever tested willingness to pay — which makes the week-3 "first ₹149 by 30 September" milestone the *first* demand datapoint, not a confirmation.

Related fifth fake claim the DELETE table misses: `page.tsx:228` lists **"Download and post it yourself"** as a Free feature, on the tier all 3 accounts are on, while no download button exists in any of the 55 frontend files (verified: no `<a download>`, no `navigator.share`). The table lists four fake claims at `238-247` and skips this one.

---

## 6. The Pexels ceiling is ~2x too pessimistic, and it's load-bearing three times

`fetch_clip` (`pexels.py:62-84`) makes **one** call to `api.pexels.com` per invocation. The media fetch that follows goes to the CDN link inside the search result — not an API request. `get_with_retries` adds calls only on transient failure (3 attempts max). One-background formats pass `set()` and query once for the whole video (`runner.py:359`).

A 6-scene narrated render is **~6 API calls, not ~14.** "Two independent passes computed this separately and agreed" is not evidence when both counted CDN downloads as API requests. At 6/render, 20,000/month is ~3,300 renders, and the binding constraint for one box is the **200/hour** burst limit, not the month. That moves the ceiling well past "90 subscribers."

The R2 library still makes sense — but on the argument that actually holds (an expiring asset becomes a compounding one, and marginal cost drops to tokens), not on urgency. And the document's own "email Pexels for a raised quota, free" should run *before* the two-week library build, not as an alternative to it.

---

## 7. Market facts and prices stated without a source

The document's sourcing is genuinely uneven — competitor *complaints* carry URLs, competitor *prices* mostly don't. Unsourced or under-sourced:

**Prices/market structure:** the "$9-15 2026 price floor (verified across InVideo, Submagic annual, Crayo, Nullface, OpusClip, Quso, SendShort)" — no link for any of seven, and three of them have no table row · Crayo $13/$27/$55, Vadoo, HeyGen "Verified live pricing" — no URL, no fetch date · AutoShorts $19/$39/$69 from reviews after its page 404'd, presented in the same table as verified rows · Magicroll $29/$49 plus its MIB/NVIDIA/Microsoft affiliations — nothing · Scenith ₹349/₹749 — nothing · **and `docs/kliptos-vault/Competitors.md` (2026-07-30) has Crayo at "$19-79, NO free plan"** — two internal docs disagree on a competitor's entry price and the newer one doesn't note it.

**Product claims:** CapCut ships Auto Beat Sync free with no watermark · CapCut Hindi/Marathi/Tamil font support · Submagic 48+ languages · Fliki 80+ / HeyGen 175+ dialects · Fliki's 3,025 Trustpilot reviews at 4.3/5 (a number, no URL, while the three complaint quotes beside it all have URLs) · "Submagic publicly has no native app."

**The two numbers that decide sections on their own:**
- **Seedance 2.0 at $2.00-2.70 per 45s video (`devtk.ai / buildmvpfast`)** carries the whole "AI video generation, ever" ban — and it overrides two better-sourced internal estimates. `Unit Economics.md` has Veo Fast at ~$0.12-0.15/sec with a hybrid at ~$3.00-3.60. `Visual Quality Diagnosis.md` has a full table from **Google's own pricing page** — Veo 3.1 Lite i2v $0.05/sec, Fast $0.10, Standard $0.40, MiniMax Hailuo-02 Fast ~$0.017/sec — and explicitly recommends a **hook-only hybrid at ≈$0.87 ≈ 18 credits** against 5 for stills. A content-marketing domain beat Google's price page to the opposite conclusion. "Never" should read "not as a default; hook-only, metered, rupee price shown before the render" — which is what the document's own escape clause says one sentence later.
- **"a shared ₹149-299/YEAR Canva Pro login"**, presented as *observed behaviour* and used as the revealed reservation price that kills the consumer tier. No provenance, no observer, no date — and the same document quotes Canva Pro India retail at ₹799/mo, so this is a grey-market resale figure doing the work of a market price.

**Also:** RevenueCat India+SEA 1.4% D35 / $14 LTV — publisher named, no report edition, and it's a *mobile-app* benchmark applied to web SaaS without noting it · "8-10% of Indian creators monetise" (BCG *via* identitykit.in) · "1 in 13 AI tools dead" (tooldirectory.ai) · "39% of subreddits ban self-promo" and "r/SaaS banned this category mid-2026" — **the document states reddit.com was unreachable to every research pass and warns that any subreddit name would be invented, then cites Reddit statistics without the same warning** · "AI Overviews cut CTR 34-61%" · Google Play India user-choice billing "about 4%", the 15% SBP tier, and the Epic-ruling attribution — all unsourced and all driving §4's economics · Razorpay "~2% + GST" unsourced, and the derived "₹499 nets ~₹489 on web" is 499×0.98, which drops the GST it just named · **Polar and Dodo India/individual eligibility** — the one fact that decides whether he can get paid at all, and it's the only rail without a link while Razorpay's KYC page is linked · "$300 buys ~7,700 flash images" implies $0.039/image against the repo's own `credits.py:18 IMAGE_COST_USD = 0.035`, and the vault records that the Cloud Billing API returns 403 for the service account, so **per-image cost is not measurable today** — the library's whole sizing rests on an unverifiable unit price, as does the "$8.40/hour of Vertex" proof-abuse figure · **"$0.0906" for the Studio-India credit states no FX rate** (₹1,299/150 = ₹8.66 implies ~₹95.6/USD). The conclusion holds; express the fix as a formula, not the constant `0.09`, or the same bug returns on the next rupee move.

---

## 8. What an experienced founder or investor asks that this cannot answer

- **"Show me one render a stranger kept."** 3 accounts / 6 videos / 1 render is stated, but not how many of the 6 reached `ready`, how many were his own, or what the one stranger did. `analytics.py` 501s, no product analytics. Unanswerable, and it is the first question.
- **"What's your measured gross margin on one real render?"** There isn't one anywhere. The document names the economics endpoint as theatre but never puts the 15-minute fix on the plan: **`image_gen.py` contains zero `track()` calls** (verified), so the only lane that costs money is invisible. Instrumenting it turns a diligence liability into the single number the entire pricing thesis rests on.
- **"What if the employment answer is no?"** Week 1 makes the IP question the only owner action — correct — and then every subsequent week assumes yes. No branch exists for no (nominee, a relative's proprietorship, USD-only through a MoR, or waiting). It's the one item that can zero the quarter.
- **"Why does someone open Kliptos in week 3?"** Day 2 is diagnosed in detail. Day 30 is absent — no retention mechanism anywhere in eight sections, for a product whose thesis is attrition. Standing orders were the only candidate and §7 says stop selling them.
- **"20 prospects or 10?"** Weeks 4-5 promise ten hand-made videos; the kill threshold reads "<5 of 20 even reply." The arithmetic doesn't close, and no assumed DM→reply rate is stated anywhere.
- **"Recovery procedure if the box dies while you're at work?"** Verified worse than described: the **api service has no volumes at all** (`docker-compose.prod.yml:31-54`) while the worker mounts `render_scratch:/app/output` (`:69-73`) and the api serves `/media` from its own empty dir (`main.py:76-78`) — so the montage/clip 404 claim is fully correct. `upload_tasks.py:27` reads finished MP4s from that named volume with no storage fallback. No runbook step exists.

---

## 9. One answer, or a menu?

**Committed, and this is the document's best quality.** One positioning sentence, one mechanism, three adversarial passes shown breaking the scoring winner, the loser named and buried rather than kept as an option. Web-vs-mobile is unambiguous with a numbered order and a do-not-build list. Don't let anyone soften either.

Two real hedges, both load-bearing:
- **Cohort A vs B is a menu.** The text says B is where the money is and A is only a proof cohort — then weeks 4-5 give A the expensive high-craft work (ten hand-made videos) and B "ten phone calls," and **every kill threshold is written about A.** If B is the thesis, the effort and the thresholds are both pointed at the wrong cohort.
- **"All nine formats stay in the code"** (§3) sits directly against the DELETE table removing three of nine. Pick one.

---

## 10. Honesty about the bad news

Genuinely honest, and rare. It opens with 3 accounts / 1 render, states that no feature has ever been touched by a stranger, names the likeliest outcome as "it works, 200 people pay a little forever, it never clears the bar to leave your job — for the first year that looks exactly like success," refuses to repeat unverified enforcement numbers its own research produced, and flags AppSumo as "the most tempting thing on this list, which is why it's here."

Two softenings:
- **"'The 501 is the whole business' is false."** Mechanically true, slightly too comforting: what stands between him and revenue is a partner bank's KYC decision and an unread employment contract, neither of which he controls.
- **The ₹28,694 credit** is correctly written off as non-runway — but the document never asks whether it can be extended, converted, or re-granted. Google Cloud credit extensions are sometimes granted on request. It spends two weeks of plan against a hard 16 November deadline without one email.

---

## 11. Smaller corrections, all verified

- `runner.py` + `assembler.py` = **871** lines (626 + 245), not 875.
- **`reaper.py` already has the refund fix.** `:56` is `refund = (video.credits_used or 0) if video else 0` and `:74` zeroes `credits_used`. The "also fix, cheap" item applies to `runner.py:618` only (`refund = video.credits_used or 1` — exact line, confirmed). The missing `revoke` in the reaper is real.
- **Strengthen the week-1 proof cap with the reason the document missed:** the rate limiter **fails open** — `rate_limit.py:5-6, 51-53`, "if Redis is down, requests pass." So `pipeline_proof: (20, 300)` isn't a ceiling, it's a ceiling-when-Redis-is-up. That is the single strongest argument for the DB-backed daily cap and it isn't in the document.
- **"Every signed-in user gets Pro" is right on features, wrong on credits.** `monthly_credits_for` is deliberately keyed on `user.plan`, not `effective_plan`, and `plans.py:83-88` says exactly why: "granting on that basis would hand every signed-up stranger 50 credits a month of real Vertex and Pexels spend." A stranger gets FREE's 3. The proof hole is real; the 50-credit arm isn't.
- **Flipping `PLAN_ENFORCEMENT_ENABLED = True` in week 2 does not close the autopilot lane.** `series_tasks.py:160` calls `generate_script(duration_seconds=series.duration_seconds or 60)` with **no plan clamp** — the clamp exists only at `scripts.py:174`. A Free standing order can still generate 300s against a 45s cap. Not in the document.
- **The grep evidence isn't reproducible as written.** `posthog|mixpanel|amplitude|plausible|gtag|segment` does *not* return nothing — `segment` matches heavily in `studio/page.tsx`. The conclusion (no product analytics) is correct.
- **`frontend/src/app/dashboard/analytics/page.tsx` ships and works**, computing output stats off `/videos?page_size=100` rather than the 501'd router. The document's "you cannot read it" is right about instrumentation but the frontend picture is more built than stated.
- **"The NextAuth session lives 30 days"** — `auth.ts:14` is `session: { strategy: "jwt" }` with no `maxAge`. 30 days is the framework default, not something the file says. Conclusion holds; cite it as a default.
- **`Pricing.md` already specifies the ₹149/10cr top-up** and already says "prepaid top-up preferred over postpaid metering — RBI e-mandate rules make variable recurring charges painful." The document presents both as grafts. Consistent, not wrong — but it means the Razorpay-Subscriptions question is already answered as "don't need it," which shortens week 2.
- **Scope actually skipped:** legal/compliance. `privacy/`, `terms/` and `refunds/` pages ship (231 lines total) and mention **no DPDP Act, no GST, no grievance officer, no registered entity** — while `Business Audit.md` flags DPDP explicitly. Razorpay's own activation review reads those pages. The plan takes money in week 3 and never checks them.
- Second scope waved at: the document names WhatsApp/Instagram webviews as the distribution channel and says Instagram has no exit at all, then defers Instagram to him with no analysis of what "no Instagram" costs the strategy.

---

## What you can lean on

Beyond §1's re-verification, these all came back **exact**: 299 tests collected (ran it) · 14 migrations 0001-0014 · the atomic claim (`pipeline.py:244-248`, `UPDATE … WHERE status NOT IN (…)`, rowcount→409, commit before `.delay()`) · the blank-scene pre-flight naming the scene number (`:111-123`) · `runner.py:204` and `:328` bypassing `_store_media` (called only at 142/379/588) and the production 404 that follows · `config.py:25` and `:33` · `auth.ts:13` Google sole provider · `costs.py:17` gemini at 0.0 · zero `track()` in `image_gen.py` · `premium_voice` tracked (`premium_voice.py:167`) and absent from `UNIT_COSTS_USD` · 9 formats all `available: True` with exactly one `language` override (shayari, `:197`, Hindi) · `footage_match.py:11` `re.compile(r"[a-z0-9']+")` and `MIN_SHARED_TOKENS = 3` · `priority` and `brand_kit` with zero consumers · `channels.py` with no count check · 55 frontend files, no download or share affordance, no smtp/waitlist/email capture anywhere · `test_montage.py:229-233` asserting a source string · `harvester.py:333` "moat" · `assembler.py:18-22` 16:9 · `series.py:99` permitting `ai_image` on autopilot against `SERIES_RENDER_COST = 1` (`series_tasks.py:28`) · `upload_tasks.py:27` local-disk read vs `DEPLOY-VPS.md:160-163` "nothing unique lives here" · 140 commits, Sun 36 / Wed 30 / Mon 27 / Tue 21 / Thu 16 / Sat 7 / Fri 3, 95/140 = 68% between 19:00-01:00.

**The one change I'd make to the plan:** move the vault's A1 (free, ten minutes) and A2+A3 (~1.5 days) ahead of the twenty DMs, not after them. The document's week 4-5 pre-sale sends hand-made videos built by a pipeline whose visual brief is knowingly broken, and its weeks 6-8 build a refusal on top of that same brief. Fixing `formats.py:245-246` first is what makes both worth doing — and it may substantially change the answer to "how do I make it unique."

---

Links: [[Pitch]] · [[Home]] · [[Visual Quality Diagnosis]] · [[Competitors]] · [[Pricing]] · [[Unit Economics]]
