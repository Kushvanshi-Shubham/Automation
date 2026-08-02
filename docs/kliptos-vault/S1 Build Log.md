# S1 Build Log

Running log of actual build work. Newest first.

## 2026-08-02 — 📐 Aspect ratios shipped: 9:16 / 1:1 / 16:9 (commit 942caf7)
- **Every render path is now format-aware**: narrated, visual, image posts, and creator clips take `aspect_ratio` ("9:16" default, "1:1" square, "16:9" widescreen) — stored in `script_data`, zero migrations
- **The plumbing**: `ASPECT_RATIOS` map in assembler (dimensions + Pexels orientation), parametrized ffmpeg crop filter, ASS caption resolution parametrized with styles scaled by height/1920 (captions keep the same relative size in any frame), Pexels searches by matching orientation with a graceful fallback (the crop filter covers any input)
- **API**: `GET /pipeline/aspect-ratios` catalog; `pipeline/start` + clip creation validate the value; videos API exposes it so the preview player frame adapts (16:9 gets a wider column)
- **UI**: 📐 Format picker in Create (📱 9:16 · ⬜ 1:1 · 🖥️ 16:9) shown for every renderable type
- Live E2E: same clean-source highlight rendered at 1920×1080 and 1080×1080, caption scaling frame-verified; live Pexels landscape search returned real 2732×1138 footage
- Observed during testing: Gemini `gemini-flash-latest` threw transient 503 "high demand" on large prompts (small prompts fine) — our Gemini→OpenAI fallback chain degraded cleanly to a 502; no code change needed
- Known polish item: media-swap thumbnails still search portrait-only (renders fine via crop)
- 98 backend tests green (new module leaves the shared test user pristine — it runs alphabetically first); CI green

## 2026-08-02 — ✂️ Creator-clip Phase B shipped: highlight → 9:16 short (commit 09d91f1)
- **New output type "clip"**: `assembler.render_clip` = single-pass ffmpeg trim + center-crop 1080×1920 + caption burn, **original audio kept** (the whole point — the creator's own voice)
- **Word-synced captions from whisper**: `transcribe.words_in_range` slices the transcript's word events to the clip range and shifts times to 0 → same cue grouping/style packs as narrated shorts
- **`POST /media-assets/{id}/clips`**: 1 credit, bounds validated (5–90s, within duration), caption_style optional; video row is BORN in "rendering" (fresh row = no claim race), ledger debit + commit-before-enqueue like pipeline/start; audio-only assets 422 for now (audiograms later)
- **Clips page live**: "Create clip · 1cr" renders and lands on the existing preview page (WS progress, publish panel — clips can go straight to YouTube)
- **Two real bugs found by live E2E**: `asset.path` and `OUTPUT_DIR` are relative but ffmpeg runs with cwd = ASS workdir → `.resolve()` both. **One false alarm**: "double captions" in frame checks = the test source was our own earlier render with captions already baked into pixels; re-ran on a caption-free source (same audio over plain color) → clean single-layer word-synced captions, frame-verified at 4 timestamps
- Full-flow E2E green: upload → whisper → Gemini highlight → clip render 24s → 1080×1920 + audio, 1 credit deducted (and auto-refund confirmed working on the failed attempts)
- 93 backend tests green (clip endpoint validations, credits, words_in_range, isolation cleanup); lint + tsc clean
- Next per owner sequence: aspect ratios → format templates (S3)

## 2026-08-02 — 🎤 Creator-clip recipe Phase A shipped (upload → transcribe → highlights)
- **assets table** (migration 0008) — the strategy's Asset primitive, rights-cleared rail (creator-owned uploads only)
- **Upload API** `/media-assets`: multipart streaming w/ 500MB cap, ext whitelist (mp4/mov/webm/mkv/mp3/m4a/wav), 10-upload limit, ownership everywhere
- **Processing task** (`asset.process`): ffprobe → audio extract → **faster-whisper (base, int8, WORD timestamps — works on py3.14!)** → Gemini clip-producer prompt picks 3-6 highlights (15-90s, validated bounds), BYO-key aware
- **Clips page** + nav: dashed upload zone, live analyzing status, highlight rows w/ timestamps + reasons; "Create clip" button stubbed for Phase B
- **Live E2E**: uploaded the 64s Apex short as source → Whisper transcribed real narration → highlights referenced actual content ("Skull Town", "Vantage bat radar") with correct timestamps
- Phase B next: render pinned highlight → 9:16 crop + word-synced captions from the transcript (1 credit)
- Also: CI unblocked (owner fixed GitHub billing) + lockfile sync commit; **owner bought kliptos.app** 🎉
- 89 backend tests green; build + lint clean

## 2026-08-02 — ✨ "Right trend → right Short" shipped (the moat move from the brainstorm)
- **Best-format recommendation per trend**: `topics.best_format/format_reason` (migration 0007); harvest-time LLM strategist recommends narrated/visual/image per topic with an 8-word why; failure-safe (fields empty without LLM). 265 existing topics backfilled.
- **Live-verified intelligence**: ALL music topics → visual ("KATSEYE Animal" → 🎵, exactly the owner's brainstorm case); news → narrated ("iran news: context matters"); maps/lists → image
- Topics toolbar defaults to **✨ Best format (auto)** — Create button adapts per card and shows the recommendation chip + reason
- **Reframing**: Script Studio → **Create** (nav + headers); source badges → "YouTube signal"/"Trends signal" with rights tooltip; landing hero → **"The right trend, into the right Short."** + format-aware subcopy
- 85 backend tests green; build + lint clean

## 2026-08-02 — 🔒 GATE 0 shipped: security P0s + CI (Codex audit findings fixed)
- **OAuth state hijack fixed**: reusable signed-JWT state replaced with single-use Redis-stored nonces (`services/oauth_state.py`, atomic Lua get+del, 10-min TTL, purpose-bound) for both YouTube and Instagram connect flows; replay test proves second use is rejected
- **Dispatch race + idempotency fixed**: atomic status CLAIM (`UPDATE … WHERE status NOT IN (…)`, rowcount check) on render start and YT publish/schedule; job committed BEFORE Celery enqueue (task id recorded in follow-up write); IG publish guarded against concurrent duplicates
- **WebSocket progress authenticated**: `?token=` JWT + job-ownership check, 4401/4403 closes; frontend hook passes session token; tests cover no-token, bad-token, foreign-job, and happy path
- **Build hygiene**: stale pre-monorepo `Desktop\Handover\frontend` deleted (owner-approved); `turbopack.root` pinned (ancestor lockfile confusion); studio lint error fixed with derive-during-render pattern; lint + tsc clean
- **CI added**: GitHub Actions — backend (py3.12 + Redis service + ffmpeg, pytest) and frontend (npm ci, lint, tsc, build) on every push/PR
- 83 backend tests green
- Deferred (documented): backend-token-in-session proxying → deploy milestone; renamed studio/"best format" product moves → next

## 2026-08-02 — Per-scene media swap shipped + Founder Pack delivered
- **Media swap**: every scene card in the studio gets "🖼 Swap visuals" → thumbnail grid of 8 portrait Pexels candidates for that scene's visual prompt (photos for image posts, clips for videos, durations + photographer credits) → click pins `media_id`/`media_thumb` into the segment (persisted via script save, unpin supported) → runner downloads the EXACT pinned clip/photo at render (`fetch_clip_by_id`/`fetch_photo_by_id`)
- Endpoint: `GET /scripts/{id}/segments/{i}/media-options` (ownership-checked; 422 on bad index)
- Live-verified: real segment returned 8 candidates (Ron Lach 32s, etc.)
- **Founder Pack** (`docs/FOUNDER_PACK.md`): MVP one-pager, Veo3 logo prompts (static + animated reveal), 4-scene 30s promo prompts, trademark guide (skip patent — S.3(k); file TM classes 9/41/42 at ipindia; grab handles/domain NOW), investor list (100X.VC/Antler/YC/creator funds), influencer channels (PH, r/NewTubers, mid-size faceless-channel YouTubers), 12-item manual task table
- 81 backend tests green; frontend build green
- Note: dev.ps1 spawned windows died silently once — services run reliably as session background processes; investigate window-spawn env later

## 2026-08-01 — Caption style packs shipped (Crayo gap closed)
- 5 packs in `captions.py`: **Classic Bold** (default) · **Neon Pop** (electric yellow) · **Center Impact** (huge, violet outline, mid-screen) · **Minimal Box** (sentence case on soft box) · **Karaoke Highlight** (each word lights yellow AS SPOKEN via \\k tags — possible because we keep per-word edge-tts timings; competitors mostly can't)
- `caption_style` flows: pipeline start (validated) → script_data → runner → per-segment ASS; `GET /pipeline/caption-styles` for the UI; studio picker (narrated + visual)
- Frame-verified: karaoke mid-word state (spoken words yellow, unspoken white) + impact violet outline
- 78 backend tests green; frontend build green

## 2026-08-01 — 🤖 SERIES AUTOPILOT SHIPPED (the AutoShorts headline feature, done our way)
- `series` table + `videos.series_id` (migration 0006): niche OR fixed-theme source, style/output-type/language/voice, cadence (daily/2-day/weekly), **auto-publish to a channel OR review-first (default)**, max 3 active per user until billing
- **Celery beat** ticks `series.tick` every 15 min → advances next_run_at IMMEDIATELY (no double-fire) → dispatches `series.run_one`: credit check (skips safely, surfaces "not enough credits") → topic pick (top fresh trend in niche, dedupes against the series' previous subjects) → script with variety guard ("avoid repeating: …") → video + credit ledger + render; auto-publish chains `run_pipeline → upload_video_task` (chain stops on render failure)
- CRUD API + `POST /series/{id}/run-now`; Series page UI (create form w/ trends-vs-theme toggle, run-now, pause/resume, next-run display, error surfacing) + nav entry
- **Windows gotcha:** `-B` embedded beat is rejected on Windows — beat runs as a SEPARATE process (dev.ps1 + runbook updated; deploy = its own service)
- **Live E2E verified:** series "Space Wonders Daily" → run-now → autonomously wrote and rendered "3 Mind-Blowing Space Facts You've Never Heard" (visual short, ready) with exactly 1 credit deducted
- 76 backend tests green; frontend build green

## 2026-07-30 — Voices + languages shipped (AutoShorts gap analysis)
- Owner benchmarked AutoShorts (screenshots): gaps = series autopilot, voice picker, languages, art styles, aspect ratios, per-scene media swap. Quick wins built same-session:
- **14-voice curated catalog** (`services/voices.py`): US/UK/AU/Indian English + **Hindi (Madhur/Swara)** + Spanish/Portuguese, each with gender + vibe; `GET /scripts/voices`; **cached previews** (`/scripts/voices/{id}/preview` → mp3 under /media, localized preview text)
- **voice_id threading**: pipeline start validates + stores it → runner narrates with the chosen voice; studio editor gets voice select + ▶ Preview (narrated type only)
- **Script language** param → Gemini writes narration in the target language (title/tags stay English for SEO); language select in studio form
- Live-verified: Hindi preview mp3 served (200), Hindi script generated in Devanagari
- Remaining gaps queued: **series autopilot (next major)**, art styles (needs paid image key), aspect ratios, media swap UI
- 70 backend tests green; frontend build green

## 2026-07-30 — UI revamp phase 1 + full SEO infrastructure
- **Landing page redesigned** (premium dark violet/blue): sticky glass nav, animated 9:16 phone mockup hero, honest capability strip (no fake stats), 4-step how-it-works, 6 real feature cards, **truthful pricing** (Free live / Pro+Studio "coming at launch" with real feature lists + INR), FAQ accordion, CTA block. The old page's fabricated claims (4K, voice cloning, API access, fake user counts) are gone.
- **SEO**: metadataBase + title template + OG/Twitter cards (branded og.png generated via Pillow), `sitemap.ts`, `robots.ts` (dashboard/api disallowed), JSON-LD `SoftwareApplication` + `FAQPage` — all verified serving on the live dev server. `NEXT_PUBLIC_SITE_URL` drives canonical URLs at deploy.
- Dashboard revamp = phase 2, waiting on owner's logo.
- Billing + deploy: waiting on owner accounts (Stripe/Razorpay test keys; Render-or-Railway + Vercel).

## 2026-07-30 — Workflow v2 #4 shipped: 🖼️ image posts (carousels)
- **Key finding**: Gemini image models are NOT in the free tier (all return 429 limit:0). Product answer consistent with our economics: **stock photos (Pexels /v1/search, portrait) = default engine (1 cr, works today)**; AI images (`services/image_gen.py`, model-fallback list, BYO-aware) = 2 cr, activates with any billed Gemini key.
- New output type `image`: LLM writes 3-6 slide captions + image prompts (carousel instruction) → pipeline image branch (no ffmpeg) saves slides to /media → `script_data.images` + thumbnail_url; engine/type matching validated (`TYPE_ENGINES`)
- UI: 🖼️ card in studio, "Generate Images · 1 credit", preview shows slide grid w/ full-size links; video-publish panels hidden for image posts (IG carousel publishing comes with Meta app)
- Live E2E: 3-slide coffee carousel from real Pexels photos, verified visually
- Also saved: `docs/INSTAGRAM_SETUP.md` — exact top-to-bottom Meta setup steps for owner
- 66 backend tests green; frontend build green

## 2026-07-30 — Workflow v2 #3 shipped: Instagram Reels publishing (behind flag)
- **Official Graph API flow**: FB Login OAuth (signed-state JWT) → long-lived token (~60d, Fernet-encrypted) → auto-discovers the IG Business account behind the user's Page → REELS container (Meta fetches video from public URL) → poll FINISHED → publish
- **New `publishes` table** (migration 0005) — the multi-platform publish ledger (per video × platform attempt w/ status/external_id/error); `ig_accounts` table for connections
- Endpoints: `/instagram/{status,connect,callback}`, list/disconnect; `POST /uploads/{id}/publish-instagram`; `GET /uploads/publishes/{id}`
- UI: Instagram section in Settings (disabled state explains Meta app pending), Reel publish panel on preview w/ caption + live status
- **Feature-flagged on META_APP_ID/SECRET** — everything testable except the final Meta fetch, which needs a PUBLIC media URL (deploy/tunnel). Works in Meta Dev Mode for owner/testers pre-review.
- ⚠️ Owner actions: create Meta app (developers.facebook.com) + start App Review for `instagram_content_publish`; IG account must be Business/Creator linked to a FB Page
- 64 backend tests green; frontend build green

## 2026-07-30 — Workflow v2 features 1+2 shipped: output types (script-only + visual short)
- `videos.output_type` (migration 0004): **script** (free, 5/day rate limit, no render — Copy Script button) · **narrated** (current) · **visual** (no narration: on-screen text lines, music as THE soundtrack at 0.85 vol, LLM told to keep segments <12 words)
- Pipeline: visual branch skips TTS, durations clamped 2.2–10s from estimates, `render_segment_silent` + `add_music_track` in assembler; pipeline/start rejects script-only (422)
- UI: "What do you want to make?" cards in Studio creation form; type+style selects on Topics toolbar; type badge in editor; visual-type tip about attaching trending audio natively when posting
- **Live E2E verified**: Gemini wrote a 5-segment visual script ("These three nature moments look completely fake") → rendered 25.0s, music-only audio, on-screen text — frame-checked visually
- **Caption bug found & fixed via frame check**: ASS WrapStyle 2 clipped long lines at frame edges → WrapStyle 0 (smart wrap), verified wrapped 2-line render
- 60 backend tests green; frontend build green

## 2026-07-30 — S2 #5 shipped: BYO API keys
- `user_api_keys` table (migration 0003), Fernet-encrypted, unique per user+provider
- `PUT/GET/DELETE /settings/api-keys`: keys are **live-validated against the provider before saving** (bogus key → 422 with friendly message), listed masked only — plaintext never returned
- Generation path: user's own key takes precedence over platform key per provider; a user key makes a provider available even when the platform has none; `GET /scripts/models` marks BYO entries "— your key" (`own: true`)
- Settings UI: "Your AI API Keys" section (password input, save w/ validation, masked chip, remove)
- Platform-fee-per-BYO-render: deferred to the billing milestone (needs credit pricing hooks)
- Live-verified E2E: real key saved via API → models showed "your key" → generation ran on the user key (one Google-side 503 transient mid-test, succeeded on retry)
- 55 backend tests green; frontend build green

## 2026-07-29 — S2 #4 shipped: publish metadata editor
- Preview publish panel is now a full editor: **title (95-char counter) · description · tags (comma-separated, max 30) · YouTube category (11 assignable categories via `GET /uploads/categories`) · privacy · schedule** — all prefilled from AI values, saved via PUT metadata then dispatched to upload in one click
- Backend: `category_id` flows through publish/schedule → Celery task → YouTube snippet (validated against assignable list, safe fallback to Entertainment)
- 48 backend tests green; frontend build green

## 2026-07-29 — S2 #3 shipped: studio power features
- **Model selection**: `model` param end-to-end (`auto`/`gemini`/`openai`); `GET /scripts/models` returns server-configured choices for the UI picker; explicit-but-unconfigured model → clean 503
- **Custom instructions** (≤600 chars) appended to the generation prompt — live-verified: "End with exactly: follow Kliptos for part two" produced exactly that
- **Tone presets** in UI (engaging/hype/dramatic/funny/calm + custom free-text)
- Studio creation form gained a collapsible ⚙️ Advanced panel (model, tone, instructions)
- 45 backend tests green; frontend build green

## 2026-07-29 — S2 #2 shipped: niche clustering for trends
- `Topic.category` (migration 0002, indexed) + shared niche registry (`services/niches.py`): gaming, entertainment, music, sports, tech, education, news, comedy
- YouTube harvest now pulls the overall chart + one chart PER NICHE via native `videoCategoryId` (1 quota unit each; niche-first ordering so dedupe keeps the specific niche; unsupported categories skipped gracefully)
- Google Trends items are LLM-classified into niches at harvest time (temperature 0, defensive pad/trim, `general` fallback when no LLM)
- `GET /topics?category=x` + `GET /topics/niches` (server-driven chips); Topics page: niche chip row + category badge on cards
- Live-verified: 79 fetched / 56 added, zero errors; distribution across 8 niches; gaming filter returns only gaming; 38 pre-migration topics backfilled
- 40 backend tests green; frontend build green

## 2026-07-29 — S2 #1 shipped: script creation modes + bring-your-own-script
- **4 styles**: Viral Story (default) · News/Update (facts-first, uncertainty phrased as reported) · Educational (one concept + analogy) · Commentary (opinionated, invites comments). Style picker on Topics toolbar + Studio creation form.
- **BYO script**: paste your own narration — LLM ONLY segments it + adds visual prompts; wording preserved exactly (live-verified word-for-word).
- Studio empty state is now a full creation form (AI-writes-it vs I-have-my-own toggle, style cards).
- Live-tested: news_update produced a proper patch-notes-style hook for Apex S27.
- 36 backend tests green; frontend build green.
- Foundation noted for later: story SERIES (episode catalog, "continue the story") builds on the style system.

## 2026-07-29 — 🚀 FIRST REAL YOUTUBE PUBLISH (owner's channel)
- Owner's Apex Legends short published (unlisted): youtube.com/watch?v=-k8I2BSiPwQ — the complete product loop (trend → script → render → YouTube) is proven live.
- **Bug fixed**: owner's first Publish click silently died — Windows/asyncpg event-loop bug (Celery reuses the module-level engine's pooled connections across asyncio.run loops; 2nd task in a worker got a dead socket). Fix: `engine.dispose(close=False)` at every task start.
- Feedback UX: preview now shows "Watch on YouTube →" link (youtube_video_id added to VideoResponse).
- S2 roadmap addition (owner): publish metadata editor — title/description/hashtags/category/quality/thumbnail before upload.

## 2026-07-29 — 🏁 S1 CLOSED (owner approved: "loved it")
- Owner rendered a real Apex Legends short and approved the product. **Bug found & fixed at close:** dashboard home was still mock data, so rendered videos looked "lost" (they were persisted — just undiscoverable). Dashboard now shows real stats + the full video library (every video links to Studio or Preview by status; live-polls while rendering/uploading).
- S2+ backlog captured in [[Roadmap]] (owner review): categorized/region trends + Twitter/Snapchat/Insta sources · multi-platform posting · BYO API keys w/ platform fee · model choice + prompt refinement · UI revamp (owner designing logo).
- Next phase: **deploy for friend-testing** (Railway + Vercel), then billing.

## 2026-07-29 — YouTube upload & scheduling built
- **Channel connect**: `GET /channels/connect` → Google consent (youtube.upload + readonly, offline, prompt=consent) → `GET /channels/callback` (identity via 10-min signed-state JWT) → tokens **Fernet-encrypted at rest** (test proves ciphertext ≠ plaintext), channel row upserted, redirect to Settings with success/error param
- **Upload**: Celery task `youtube.upload` — resumable insert via google-api-python-client, auto token refresh from encrypted refresh token; statuses ready→publishing→published/scheduled/upload_failed. Scheduling = privacy:private + status.publishAt (YouTube flips it public itself)
- **UI**: Settings page (connect/disconnect channels, callback banners), Preview publish panel (channel + privacy + optional schedule datetime; polls while publishing), Upload Manager page (lifecycle list)
- lucide-react dropped brand icons — no `Youtube` icon; using `Tv`
- 32 backend tests green; frontend build green
- ⚠️ **Owner action to test**: add `http://localhost:8000/api/channels/callback` to the OAuth client's Authorized redirect URIs in Google Cloud Console, then Settings → Connect Channel. Upload works for your own account (test-user) even before scope verification.

## 2026-07-29 — Captions + background music shipped
- **Word-timed burned-in captions**: edge-tts word boundaries (requires explicit `boundary="WordBoundary"` in v7 — root cause of the earlier zero-duration bug) → 2-3 word cues breaking on punctuation, stretched to eliminate flicker → ASS subtitles burned per segment via ffmpeg (cwd trick avoids Windows path escaping). Visually verified via extracted frames: bold white uppercase w/ outline, lower-middle, correct sync.
- **Background music**: `backend/assets/music/` library (mp3s gitignored — each env seeds its own), random track mixed at 12% under narration, `-shortest` mux. CC-BY tracks auto-append attribution to the video description (verified in DB). FreePD is dead (site closed) — seeded with 2 Kevin MacLeod CC-BY tracks from incompetech.
- Tests isolated from real API keys in backend/.env (conftest clears them); 26 tests green.
- Next: YouTube upload & scheduling.

## 2026-07-29 — YouTube Trending source live
- YOUTUBE_API_KEY wired; live harvest: 24 topics (14 YouTube trending + 10 Google Trends), zero errors. Both S1 trend sources operational.
- All S1 keys now in place except billing (Stripe/Razorpay). Remaining owner action: youtube.upload OAuth verification.

## 2026-07-29 — Gemini live: full creator flow unlocked in browser
- GEMINI_API_KEY wired and verified end-to-end through the API (8-segment script generated live). Model pinned to `gemini-flash-latest` rolling alias — `gemini-2.5-flash` is retired for new users (July 2026).
- Complete flow now works in the browser: Topics → Create Short (Gemini writes script, free tier) → Studio edit → Generate Video (1 credit) → live progress → 9:16 preview player.
- Pending keys: YOUTUBE_API_KEY (trending source). Pending owner: youtube.upload OAuth verification application.

## 2026-07-29 — 🎬 VIDEO PIPELINE LIVE (the core product works)
- **Full render verified E2E through the production path**: `POST /pipeline/start` → 1 credit deducted via ledger (3→2) → Celery worker (solo pool on Windows) → edge-tts narration → real Pexels portrait clips → FFmpeg 1080×1920@30fps h264+aac → `/media/{id}/final.mp4` served over HTTP (verified 200)
- Components: `pipeline/tts.py` (edge-tts, ffprobe-measured durations — TTS word-boundary events proved unreliable), `visuals/pexels.py` (portrait rendition picker, no-repeat clip ids), `assembler.py` (raw ffmpeg subprocess — **moviepy/pydub/whisper removed from requirements**, decision: leaner + faster), `runner.py` (stage orchestration, Redis progress, **auto-refund on failure**), credit costs per engine in `routers/pipeline.py`
- UI loop closed: Studio "Generate Video · 1 credit" → Preview page with live WS progress bar → 9:16 player
- **Gemini added as primary LLM** (free tier) with OpenAI fallback (`services/llm.py`); script_gen now provider-agnostic. Awaiting GEMINI_API_KEY from owner.
- **YouTube Trending source added** to harvester (needs YOUTUBE_API_KEY). Instagram trends rejected (no public API; ToS) — Insta returns later as a *posting* target via Graph API.
- Gotchas: celery_app needs `include=["app.pipeline.tasks"]` or tasks silently discard; ffmpeg PATH requires new shell after winget install; Windows Celery needs `--pool=solo`
- 22 backend tests green; frontend build green

## 2026-07-28 — Script Studio shipped (GPT-4o)
- `app/services/script_gen.py`: GPT-4o JSON-mode script generation (hook-first segments with visual prompts, ~2.5 wps duration model) + per-segment regeneration with feedback
- Endpoints: POST `/scripts/generate` (topic_id or custom_prompt → creates `script_ready` Video), GET/PUT `/scripts/{id}`, POST `/scripts/{id}/regenerate-segment` — all ownership-checked; 20 tests green
- Studio page: segment editor (narration + visual prompt), save, per-segment AI regenerate with feedback input; Topics "Create Short" → generates → routes to studio
- OPENAI + PEXELS keys wired. ⚠️ Live GPT-4o call blocked: OpenAI account has `insufficient_quota` — owner must add billing credits. Error path verified graceful (502 + log).
- **Decision: Reddit source stays OFF** — Reddit's Data API policy requires written approval for commercial use; Kliptos is commercial. Alternative: YouTube Trending as second source once YouTube API key exists. Code stays dormant behind missing creds.

## 2026-07-28 — Topic Harvester live (first pipeline feature)
- `app/services/harvester.py`: Google Trends RSS (no key needed, **live-verified: 10 real topics harvested**) + Reddit via app-only OAuth (skips cleanly until `REDDIT_CLIENT_ID/SECRET` provided — Reddit 403-blocks unauthenticated server calls since the 2023 API lockdown)
- Dedupe by sha256 content hash (cross-run and within-run); log-scaled 0–100 scores; template hooks (LLM hooks come with script studio)
- `POST /topics/refresh` implemented; Topics page rewritten: react-query on real API, loading skeletons, empty state, live Refresh button — MOCK_TOPICS deleted
- 16 backend tests green; frontend build green

## 2026-07-28 — ✅ AUTH CONFIRMED WORKING (owner browser test)
Owner signed in with Google end-to-end: dashboard shows real user + 3 signup credits. First fully-working user-facing feature. Next: topic harvester (key-free via Google Trends RSS + Reddit public JSON), then script studio (awaits OPENAI_API_KEY) and pipeline (awaits PEXELS_API_KEY).

## 2026-07-28 — OAuth live + pub/sub bridge + typed API client
- Google OAuth creds wired (backend `.env` + frontend `.env.local`); NextAuth providers endpoint confirms google/OIDC with correct callback; `/dashboard` unauthed → 307 to `/sign-in`. **Interactive browser sign-in test pending owner.**
- **Redis pub/sub progress bridge shipped** (audit §3.2 closed): workers publish via `app/services/progress.py`, WS endpoint is a pure subscriber. Dead in-memory `ConnectionManager` deleted. Integration test proves worker→Redis→WS delivery (12 tests green). redis-py pinned to RESP2 (`protocol=2`) for the Redis 5.0 Windows port.
- **OpenAPI-typed client**: spec exported (25 paths) → `frontend/src/lib/api-types.ts` via `npm run gen:api`. `use-pipeline` WS URL now derived from `NEXT_PUBLIC_API_URL`.
- Both dev servers running: API :8000, Next.js :3000.

## 2026-07-28 — Repo consolidation + local infra live
- **Monorepo pushed to GitHub** (`Kushvanshi-Shubham/Automation`) incl. docs + this vault; old `frontend` repo **archived** (delete pending `delete_repo` scope from owner)
- **Local stack installed and verified on this machine:**
  - FFmpeg 8.1 (winget) ✅
  - PostgreSQL 16.14 as Windows service, `kliptos` DB created, **Alembic migration applied — 6 tables live** ✅
  - Redis 5.0.14 (tporadowski Windows port) as service `Redis`, PONG ✅ — Memurai MSI failed twice (SFXCA temp-dir bug, error 1603)
  - Live API smoke test on real Postgres: `/api/health` OK; 401s enforced with no token; authed `/auth/me`, `/billing/credits`, `/videos` all return real DB data ✅
- Config fix: `CORS_ORIGINS` now `NoDecode` + validator (accepts comma-separated env values); `.env` files must be BOM-free (PowerShell `Out-File` gotcha)
- Server start: `cd backend; .venv\Scripts\python -m uvicorn app.main:app --port 8000`

## 2026-07-28 — Auth milestone shipped (commits 3da7243, 73090f1)
**Backend** (11 tests green):
- Monorepo merge done; hardened config (SECRET_KEY required + placeholder rejection, Fernet TOKEN_ENCRYPTION_KEY)
- Real Google ID-token verification → JWT → `get_current_user` from DB; signup grants 3 credits via ledger; idempotent login
- All routers auth-required; unbuilt features return **501**, never fake data; videos/topics/billing wired to real DB queries
- Alembic initialized with initial migration; startup `create_all` deleted; `User.role` + `country` added

**Frontend** (`next build` green):
- NextAuth v5: Google sign-in → backend token exchange in jwt callback; httpOnly session (localStorage token removed)
- Dashboard gated by server-component layout; shell shows real user + live credits
- Correction: `shadcn` v4 IS a runtime dep (`shadcn/tailwind.css`) — restored; only Prisma was unused
- Gotcha fixed: first commit recorded `frontend/` as a gitlink (submodule) — replaced with tracked files

**Environment notes:** no Docker/FFmpeg on this machine — Postgres/Redis and the render pipeline need infra decisions; tests run on SQLite meanwhile. Python 3.14, Node 24.

**Next up:** OpenAPI-generated TS client → Redis pub/sub progress bridge → topic harvester → script studio (GPT-4o) → Pexels+edge-tts pipeline.
**Blocked on owner:** Google OAuth client credentials (`AUTH_GOOGLE_ID/SECRET` + backend `GOOGLE_CLIENT_ID`) and starting the `youtube.upload` verification application.

## 2026-07-28 — Kickoff
- Audits complete ([[Project Audit]], [[Business Audit]]), scope approved, vault created
- Starting: monorepo merge → backend foundation (config hardening, Alembic, real auth) → frontend auth wiring
- ⚠️ Owner action item: start Google Cloud OAuth consent-screen verification for `youtube.upload` scope (longest external lead time)

Links: [[Home]] · [[Roadmap]]
