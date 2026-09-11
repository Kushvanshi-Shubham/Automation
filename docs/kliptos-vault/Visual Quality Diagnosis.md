# Visual quality: why the GTA render was wrong

> Produced 2026-09-10 by a 14-agent investigation into ONE rejected render —
> video `1bb26518-67bd-4110-a372-50a4b68ca825`, a gaming_update about GTA 5
> whose seven visuals were all generic gaming peripherals: 4 diagnostic lenses
> over the code, 3 adversarial refuters, 5 research streams, a synthesis and a
> completeness critic. 1.15M tokens, 363 tool calls.
>
> **Read the critique second section first.** All three refuters rejected the
> initial hypothesis (that our "no brand names" rule caused it), and the critic
> then overturned the synthesis's central evidence and found a defect larger
> than the one under investigation: on the trend route the script's facts were
> INVENTED, because no source text is ever passed.

---

## Synthesis

All file paths below are under `C:\Users\Administrator\Desktop\Handover\Automation`. I re-verified every load-bearing claim in the repo before writing; where the three passes disagreed I say which one the code supports. Line numbers drifted slightly from what the passes reported (the runner's branches are at 502/509/524/529, not 502/511/524/531) — the structure is exactly as described.

---

# 1. Root cause

## The instruction responsible

`C:\Users\Administrator\Desktop\Handover\Automation\backend\app\services\formats.py:245-246` — the last sentence of the `gaming_update` recipe:

> `visual_prompt = gaming setups, esports crowds, RGB keyboards, controller close-ups (no copyrighted game footage).`

That is an **assignment, not a constraint**. It tells the model "the value of this field is one of these four things." It is injected by prepending it to the creator instructions (`backend/app/routers/scripts.py:206-207`) and lands **last** in the user prompt, immediately before "Write the script now." (`backend/app/services/script_gen.py:186-194`). The base rules that could have argued with it sit far away in the system message.

All seven rejected visuals are that four-item list enumerated: RGB tower and dual-monitor desk = "gaming setups"; controller and mouse = "controller close-ups"; LAN party = "esports crowds"; streamer and headset = the same lifestyle bucket. 7/7 accounted for. Nothing about a vehicle patch suggests a LAN party or a USB cable — those are there because we listed them.

**The model did not fail. It obeyed.**

## The co-primary: the coupling clause is missing

Nothing in the path that generated this video tells the model that a segment's visual must depict *that segment's own text*. `script_gen.py:22-23` defines the field as "a concrete, filmable description for stock-footage search or AI video generation" — a function, with no stated relationship to the line beside it.

The missing clause **already exists in the repo**, exactly once. I grepped the whole backend:

- `backend/app/services/script_gen.py:136` — "concrete, filmable stock-footage description **matching that line**" — inside `CUSTOM_SCRIPT_PROMPT`, the bring-your-own-script path, which this render did not use.
- `backend/app/routers/scripts.py:34` — a weaker "for that slide", carousels only.

The narrated path has neither. So topic-blind visuals are the **default behaviour of this prompt for every format**, brands or no brands — the same defect is latent in `shayari` (`formats.py:192`) and `motivational` (`formats.py:133`), which carry the identical `visual_prompt = <fixed palette>` shape on topics with no brands in them at all.

## The three-way distinction you asked for

**(a) "Our prompt forbade it" — true, but contributing, not primary.** `script_gen.py:22-23` bans brand names and celebrity likenesses; the recipe bans "copyrighted game footage"; `backend/app/services/image_gen.py:67` bans logos. These are why no visual says the word GTA — and you can see one of them working: output 3 is an *anonymous* streamer where the subject named MRRAJAPLAY. But prohibitions subtract options, they don't supply "LAN party" or "USB cable". A compliant-and-faithful visual was fully available: "a matte-black armoured hover-bike with a roof-mounted missile pod over a neon coastal highway at night" names no brand and is still the Oppressor MK2.

**(b) "The model would have generalised anyway" — no, and this is the strongest evidence in the whole diagnosis.** The *same call, same completion* produced the Oppressor MK2 lock-on nerf, the Vigilante speed buff *and* its missile cooldown, MrRajaplay's live event, the Diamond Depot heist, and Rockstar. The JSON schema puts `text` before `visual_prompt` (`script_gen.py:31-33`), so every one of those facts was already in context when it wrote that segment's visual. Capability was present and was overridden by instruction.

There *is* one real generalisation pressure, and it is our fault too but a different line: `_BASE_RULES` calls the field a **"stock-footage search"** query. Tell a model its output is a library search and the winning move is a generic, well-indexed noun phrase — which is exactly why every output is shot-type-prefixed prose ("Extreme close-up shot of…"). This render used `ai_image`, where inventory is irrelevant and a faithful description is strictly better, and the script prompt cannot even see which engine was chosen (`backend/app/schemas/script.py` has no engine field; the engine is picked later at `backend/app/routers/pipeline.py:140`).

**(c) "The downstream engine could not have rendered it either" — largely true, and this is what changes the fix.** Three verified gates stand after the script:

1. `image_gen.py:66-67` rewraps every subject with the format's `visual_style` — `bold` = "Bold graphic poster art, high contrast, saturated colour blocking, **strong silhouettes, striking and simple**" — then appends "Absolutely no text, no words, no letters, no numbers, **no logos**, no watermarks, no borders." Even a perfect prompt renders as an abstracted, logo-free poster.
2. `image_gen.py:100` appends `STYLE_SUFFIX`, which re-specifies **"(4:5)"** after `scene_prompt` already said "(9:16)". Two contradictory composition instructions in one string. It is a carousel-era leftover — the module docstring (line 3) says the file is for image posts.
3. No recovery. `backend/app/pipeline/runner.py:514-515` passes only `seg.get("visual_prompt") or seg["text"]`; the `or` fires only if the prompt is empty, which it never was. `video.subject` is never referenced in `image_gen.py`. The word GTA never reaches the image model in any form.

And the sequencing killer: **making prompts specific today is unsafe.** The visuals loop (`runner.py:500-537`) has no try/except. Pexels raises on zero results (`backend/app/pipeline/visuals/pexels.py:84`, single search, `per_page=10`, portrait, `size=medium`). `image_gen.py:104` raises "likely filtered" and then retries two more Gemini models against the identical policy. Either exception reaches `runner.py:607`, which fails the video and refunds. Pexels is the **default** engine for narrated video, and it receives the full prose sentence verbatim as the search query. A specific prompt on the default lane trades a bad render for a dead render.

## Where the passes disagreed

- **One diagnostic pass ranked "no brand names" as a primary cause; all three adversarial passes ranked it contributing or a red herring.** The code supports the adversarial passes. The test is asymmetric: delete the ban and leave `formats.py:246` in place and nothing changes; delete the palette and add the coupling clause and you get hover-bike and vault imagery *under the existing ban*.
- **One adversarial pass says do not touch prompt specificity until fallbacks exist; the prompt-rules pass says ship the recipe rewrite now.** Both are right about different lanes. A described scene still generates on `ai_image`; on `pexels`, specificity means no inventory means a hard fail. Reconciliation: ship the recipe rewrite and the per-scene fallback **in the same change**, or gate the rewrite to `ai_image` only.
- **Veo pricing disagrees between passes.** The dedicated research pass has Veo 3.1 Lite at **$0.05/sec (720p)** from Google's own Gemini API pricing page; the competitor pass has $0.03/sec from a third-party blog. Use $0.05 and verify. Both agree Fast = $0.10/sec. Standard: $0.40/sec (Google page) vs "$0.20-0.60" (blog) — treat the blog as stale.

---

# 2. Your five questions

### a. Why no GTA imagery

Because we told it not to, twice, and then handed it a substitute list — and the list, not the ban, is what produced keyboards. Specifically: `formats.py:246` supplied the four-item palette as the definition of the field; nothing anywhere told it the visual must match its own line; the field was described as a stock-search query, which biases toward high-inventory phrasing; and the brand/likeness/logo bans closed the compliant-and-faithful path so substitution felt correct. Then downstream, `bold` poster-art styling plus a hardcoded "no logos" would have abstracted even a good prompt, and the narration never reaches the image model as a second chance.

The part that is **not** fixable by prompt work is in section 5: we cannot generate GTA, only something that reads as it.

### b. Why static images, and what real video would cost

Not a defect and not a degradation — `ai_image` has exactly one visual path, hardcoded: generate one still, then fake motion. `runner.py:509-523` calls `image_gen.generate_image` then `assembler.image_to_clip`, which is a `zoompan` from 1.0 to 1.18 (`backend/app/pipeline/assembler.py:147-182`). There is no video engine anywhere: `ENGINE_CREDIT_COST = {"pexels": 1, "stock": 1, "stock_image": 1, "ai_image": 2}` and `TYPE_ENGINES` gives narrated only `{pexels, stock, ai_image}`. A repo-wide grep for veo/generate_video/image_to_video across `backend/app` returns **one hit** — a price with no implementation, `backend/app/services/credits.py:30`: `"veo_fast": 8.50, # Veo Fast 60s`. `heygen.py` is a talking-head scaffold with zero references from the runner. There is no switch to flip.

Worth knowing: the default engine for narrated video is `pexels` (real video clips). You actively selected `ai_image` — `credits_used: 5` = `ceil(7 × 0.7)` confirms it. The picker copy does say "A generated scene per line with slow pan/zoom", so it was technically disclosed and far too quiet.

**Cost of real motion, for this exact video (7 scenes, 52.5s), converted with your own formula (cost × 2 at $0.10/credit):**

| Route | Per-second | 7×4s = 28s | 7×8s = 56s |
|---|---|---|---|
| Veo 3.1 Lite i2v, 720p | $0.05 (Google pricing page) | $1.40 → **28 credits** | $2.80 → 56 credits |
| Veo 3.1 Fast, 720p | $0.10 (Google page, corroborated by fal.ai) | $2.80 → 56 credits | $5.60 → 112 credits |
| Veo 3.1 Standard, 720p/1080p | $0.40 (Google page) | $11.20 → 224 credits | **$22.40 → 448 credits** |
| Kling 2.5 Turbo Standard (via fal) | $0.042 | 7×5s = $1.47 → 29 credits | — |
| Wan 2.2-5B (via fal) | $0.15 flat per ≤5s clip | 7 clips = $1.05 → 21 credits | — |
| MiniMax Hailuo-02 Fast, 512p (via fal) | ~$0.017 | 7×6s = $0.71 → 14 credits | — |

Today's same video: 7 stills at the assumed $0.035 each ≈ $0.27 ≈ **5 credits**.

**The recommendation is the hybrid**: animate the hook and maybe one payoff scene, keep Ken Burns on the rest. 3 scenes × 4s on Veo Lite = $0.60 plus $0.27 of stills ≈ $0.87 ≈ **17 credits**, up from 5. Viewers judge a Short on the first two seconds; scene 5 of 7 panning slowly costs nothing and nobody notices.

**Unknowns I am carrying forward rather than filling:** Vertex's own Veo SKU price could not be verified (that pricing page is JS-rendered and would not fetch — every number above is the Gemini API page). Whether `generateAudio=false` discounts on Vertex is **unknown**, and it matters — you already have TTS and should never pay for Veo audio. Whether Veo runs in `asia-south1` is **unknown**; every Google doc and SDK sample uses `us-central1`, which would mean your Malaysia VPS pulls multi-megabyte clips across the Pacific per scene. Whether Veo 3.1 Lite is GA or preview on Vertex is **unknown** (preview means low quota and no stability guarantee). Default per-project Veo quota is **unknown** — if it throttles, seven parallel clips could turn a 2-minute render into 15. `personGeneration` is an allowlist gate with documented rejections on image-to-video when the source still contains a realistic human, which is what many of your illustrated scenes look like. And your $0.035/image is still an **assumption** — the Cloud Billing API returns 403 for the service account, so per-render cost is not yet measurable. Finally, re-encoding seven downloaded 720p clips on 2 vCPU is meaningfully heavier than zoompan; not measured.

### c. "Do we lag in our AI / the LLM?"

**No.** The ground truth refutes it by itself: one call produced the Oppressor MK2 lock-on nerf, the Vigilante speed buff *and* missile cooldown, MrRajaplay, a Diamond Depot heist, and Rockstar. A model that lags cannot write that. The weak link is the **brief we hand it**, not the model.

Partial merit, stated honestly: `backend/app/services/llm.py:19` pins `gemini-flash-latest` (chosen for the free tier). Flash-tier models are more literal list-followers and less likely to resolve "the recipe says gaming setups" against "my own line says Oppressor MK2" in favour of relevance. So model tier affects *robustness to a bad prompt*, not the underlying ability. Upgrading the model would not reliably fix this while `formats.py:246` stands — and the recipe fix works on flash. Don't spend money here.

### d. Does this need auto-learning or a dataset?

**No dataset. This is a prompt-architecture problem, not a training-data problem.** A model that writes good shayari can obviously describe rain on a window; the joint call never asked it to.

Two things about the loop you already have:

- **The cheapest test available to you costs zero code.** Standing feedback notes are appended **last** (`backend/app/services/feedback.py`, wired at `routers/scripts.py:225-229`, with the wording "Apply ALL of it to this script") — after the recipe. That makes a creator note the single strongest position in the entire prompt. A note like "the visual_prompt must show the actual thing this line is talking about" should override `formats.py:246` today. Do that first, re-render the same subject, and you will know within ten minutes whether this whole diagnosis is right.
- **But feedback can never fix the look**, because nothing from feedback or `script_data` reaches `image_gen` beyond `visual_style`. Learned visual preferences have no path to the image prompt.

What "auto-learnable" should mean technically, in order:

1. **Two-stage generation** — one call writes the script, a second cheap call writes one frame per line, seeing that line plus minimal global context. Every published multi-scene pipeline does this (Free-Bloom, VideoDirectorGPT); a joint one-shot call treats the visual as an afterthought. About **$0.001-0.004 per video** on a Flash-Lite-class model. One caveat from the literature: a per-line pass must be told to resolve pronouns, or line 4 says "she looks out" with no idea who she is.
2. **An entity-overlap contract validated in Python, with one retry** — require the prompt to contain the line's concrete nouns, ban a vocabulary list ("abstract", "symbolising", "geometric shapes"), and reject-and-retry in code. This is the only part of the stack that cannot silently regress; a prompt instruction is advice, a validator is enforcement. Free.
3. **15-20 hand-written example pairs, keyed to the existing `visual_style` field.** In the npj AI study, structured prompting did the heavy lifting (+11-12% F1) and retrieved dynamic examples added only 5.6-7.3% on top. Cost is a few hours of your time, not a dataset.
4. **Then the real auto-learning**: log every visual a creator swaps or edits in the studio, and later retrieve the closest *accepted* pairs as few-shot examples. Nothing is trained. Start **logging** now (skipping it is irreversible); start **retrieving** in a month, once there are events. Gate what enters the bank on an explicit edit or a passing score — a bank fed by mere non-complaint learns laziness.

**Fine-tuning: reject for now.** GEPA reports beating RL by 10-20% with up to 35× fewer rollouts by evolving prompts instead of weights. And the two papers closest to this exact task (Prompt-A-Video, RAPO++) *do* end in a fine-tune — read carefully: in both, the dataset is **manufactured by the pipeline**, and the tune exists to make an already-working expensive loop cheap. It is distillation, not discovery. You don't have the working loop to distil yet. Third-party (unverified) figures also put tuned Gemini-3-era inference at a **1.5× multiplier, permanently** — a cost increase landing directly on a credit price derived from cost you cannot yet measure.

**One thing nobody has measured, and should:** whether your failures are prompt-side or retrieval-side. Take 20 recent segments, score each visual against its line, then hand-check the failures — did a good clip exist in the library and retrieval miss it, or does no such clip exist? Until that is done, the split is inference.

### e. The missing duration picker

You are right in effect, and the code says why in four separate places.

1. **Discover sends no duration at all.** `frontend/src/app/dashboard/topics/page.tsx:84-93` is the entire request body: `topic_id`, optional `mashup_topic_id`, and format. A grep for "duration" in that file returns **nothing**. So every trend-route video falls back to the pydantic default of 60s (`backend/app/schemas/script.py:31`).
2. **The studio's picker is behind a closed drawer.** `frontend/src/app/dashboard/studio/page.tsx:152` — `showAdvanced` defaults false; the Length select is inside that branch at :406-418, below the format grid, mood grid, prompt box, language and style pickers. Default 60 (:156).
3. **That untouched default set both the shape and the price.** `round(60 / 8.5) = 7` segments (`script_gen.py:16,175`) — exactly this render's 7 — and on `ai_image` 7 scenes = 5 credits. A number you never chose decided what the video was and what it cost.
4. **The requested length is never stored.** `routers/scripts.py` writes `script_data = {subject, tone, style, segments, total_duration}` — `duration_seconds` is used and dropped. So the editor has no length control and no "regenerate at 90s"; the only way to lengthen a script is `addSegment`, which inserts an empty scene for you to write by hand. That is what makes the missing picker unrecoverable rather than merely annoying.

Two correctness bugs sit behind the same complaint:

- **The pace constant lies.** `formats.py` comments that `words_per_second` "drives both the script budget and the TTS rate." It does not. `generate_script` has **no** `words_per_second` parameter (I checked the signature); the prompt hardcodes "~2.5 words/second" (`script_gen.py:24`) and `_finalize` divides by 2.5 (:152), while TTS speeds gaming_update up by +12% for its 2.8. 60s requested → 52.5s estimated (your stored `total_duration`) → roughly 47s spoken. Systematically short.
- **Duration choices are hardcoded in three unsynchronised places** (studio `DURATION_CHOICES` at page.tsx:93 with a plan filter; a bare `[15,30,...300]` array in the series page with **no** plan filter; `ge=15, le=300` asserted twice in the backend), and `SECONDS_PER_SEGMENT = 8.5` is duplicated across the language boundary with only a comment holding it equal (`studio/page.tsx:89-90`). Also the plan clamp exists only at `routers/scripts.py:173` — `backend/app/pipeline/series_tasks.py:160` calls `generate_script` directly with no clamp, so a Free standing order can generate 300s against a 45s cap (masked today only because plan enforcement is off).

On the control itself, the research is one-sided: **presets, not a slider** (NN/g: sliders are for approximate values with live feedback; here the value is load-bearing — it sets segment count and price, and there is no preview to scrub). And **per-format defaults, not one global number** — published per-type ranges disagree by 3× (quick tips 15-20s, tutorials 25-40s, narrative 30-45s+), and four of your recipes already hardcode contradictory counts (`formats.py:60` "10-16 messages", :130 "5-8 segments", :188 "2-4 couplets") while the prompt simultaneously demands "EXACTLY 7 segments".

Two data points worth putting on the chip labels, because they pull in opposite directions: engagement and completion peak **short** (TikTok engagement peaks at 15-30s; Reels watch-ratio 66.0% under 15s vs 16.4% over 60s) while views and reach peak **longer** (TikTok median views 1,000 at 15-30s rising to 11,136 at 120-180s). And 8.5s per segment is slower than every published pacing guideline (b-roll 3-5s max); at typical Hindi voiceover rates it holds ~15 words vs ~19-21 in English, so it should not be one constant. India-specific length data could **not** be established — the widely-quoted "18 seconds" and "Hindi gets 3.2× engagement" figures trace to unsourced blogs. Do not hardcode an India default on those.

---

# 3. Ranked plan

Ordered by impact ÷ effort. Given you are building around a job, take **A1 and A2+A3 first** and stop there for a cycle.

## Group A — free, do today (no per-render cost, no decision needed)

**A1. Prove the diagnosis with a standing feedback note. Zero code, minutes.**
Add a creator note: "The visual_prompt must show the actual thing this line is talking about." It lands after the recipe (`routers/scripts.py:225-229`), so it should beat `formats.py:246`. Re-render the same subject on `ai_image`. **Buys:** a same-day confirmation or refutation of everything above, for 5 credits. Do this before touching code.

**A2. Rewrite the palette clauses and add the coupling rule. ~1 hour + tests.**
Files: `backend/app/services/formats.py:245-246` (gaming_update), `:133` (motivational), `:192` (shayari) — leave `:60` (fake_text genuinely ignores the field). Plus `backend/app/services/script_gen.py:22-23` (`_BASE_RULES`), `:47-49` (`_POETIC_RULES`), and the schema hint at `:32`. Lift the wording that already exists at `script_gen.py:136`. Make the segment text the source and the palette an explicit *fallback* for lines with nothing depictable. **Buys:** the actual fix for complaint (a), across every format rather than just this one. **Must ship with A3.**

**A3. Make a per-scene visual failure non-fatal. ~half a day.**
File: `backend/app/pipeline/runner.py:500-537`. Wrap each branch. On failure: retry with a shortened/keyword query or a trademark-stripped prompt, then the format's `background_query`, then a neutral house query, then a single generic still — and surface "scene N used a fallback" in job progress rather than shipping it silently. Separately, in `backend/app/services/image_gen.py:96-115`, distinguish a real refusal (`finish_reason` / `prompt_feedback`) from a transport error before trying the next model; retrying two more Gemini models against the same policy is pointless. **Buys:** specificity becomes safe — and it fixes an existing latent bug where any one-background format past ~10 scenes fails outright (`pexels.py:64` `per_page=10` against a single `used_ids` set for the whole video; a 95s+ Reddit Story crosses that line).

**A4. Fix the pin-ignored bug. One line + a test.**
`runner.py` — move the `elif seg.get("media_id")` branch (line 524) **above** `elif ai_visuals` (line 509), matching how `asset_id` already behaves. Today a creator reacting to this exact render by hand-picking better clips for all 7 scenes sees 7 green "Visual pinned" confirmations (`studio/page.tsx:875-925`), spends 5 credits, and gets byte-identical AI stills. **Buys:** the recovery path works — and it removes a plausible reason you concluded "our AI lags" rather than "I picked the wrong lane."

**A5. Give the image model a second chance at the subject. ~1 hour.**
`runner.py:514-518` plus the `scene_prompt` signature — pass `seg["text"]` and `video.subject` as *context*, a hint not the subject. Route the carousel path (`runner.py:133-136`) through `scene_prompt` too; it currently skips `VISUAL_STYLES` entirely. **Buys:** the narration's nouns survive even when the script prompt was written for search.

**A6. Delete the carousel leftovers from the scene path. Minutes.**
`image_gen.py:100` — stop appending `STYLE_SUFFIX` (it re-specifies 4:5 against `scene_prompt`'s 9:16, and 4:5 isn't even in `_ASPECT_FRAMING`). Narrow `image_gen.py:67`'s negatives to "no captions, no subtitles, no watermark". **Buys:** removes a self-contradicting instruction and stops the wrapper fighting the subject. Related taste call for you: `bold` is deliberately abstract ("strong silhouettes, striking and simple"); `cinematic` may suit gaming_update better.

**A7. Promote Length, and add it to Discover. ~half a day.**
`studio/page.tsx` — move the Length block out of `{showAdvanced && …}` to sit next to the format grid (keep the `mode !== "own"` guard). `topics/page.tsx:84-93` — send `duration_seconds`. And define the choices **once** in the backend beside `NARRATION_PACES` in `formats.py`, served through the existing catalog call, consumed by studio + series + Discover; delete the frontend copies. Presets with labels ("30s — best completion", "60s — more views"), pre-selected per format. **Buys:** you stop getting a length you didn't choose, and the price stops being set by a hidden default.

**A8. Make duration actually bind. ~half a day, tests first.**
`script_gen.py` — add `words_per_second` to `generate_script`, interpolate it into the "~2.5 words/second" line (:24) and `_finalize`'s divisor (:152), and derive seconds-per-segment from it instead of the fixed 8.5. Feed it from `fmt["words_per_second"]` in `routers/scripts.py`. Store `duration_seconds` in `script_data` (JSON column, no migration) so the editor can later offer regenerate-at-length. Apply the plan clamp at `series_tasks.py:160`. Fix the `formats.py` comment that claims something the code doesn't do. **Buys:** 60s means 60s. **Warning:** this changes every format's output length at once — pin the format tests before shipping.

**A9. Two-stage visual pass + entity validator. 1-2 days.**
The durable fix (see 2d). Costs roughly $0.001-0.004 per video, so it sits at the boundary of "free" and "per-render". **Buys:** correct visuals by construction for every format, and it produces the scored signal any later learning loop needs.

## Group B — costs money per render (needs billing live first)

**B1. Hero-scene image-to-video.** Veo 3.1 Lite i2v behind a per-scene flag, hook only. ≈$0.60/video extra ≈ 17 credits total vs 5. Register as a new engine in `ENGINE_CREDIT_COST`/`TYPE_ENGINES` and price via `credits_for_cost`. Verify first: region, `personGeneration` gate, GA-vs-preview, quota, audio-off discount. **Do not** default it on while plan enforcement is off — that is uncapped spend on free users.

**B2. A TIFA-style verifier before render.** Ask a cheap vision model 3-5 atomic yes/no questions derived from the line, against the candidate visual, and re-generate once below threshold. ~$0.001-0.002 per video against ~$0.315 of image spend on a 9-image video. Matters most for **autopilot**, where nobody is watching. Do it after A9.

**B3. Match footage on vision, not speech.** `backend/app/services/footage_match.py` scores narration against **whisper transcripts**, and your own comments say why that fails: `backend/app/services/highlights.py:8-12` — "It finds nothing in gameplay. A montage of gunfights has almost no transcript to reason about." Caption sampled frames once at upload and score those against the visual prompt. Also stop muting pinned creator footage under narration — `assembler.cut_source` passes `-an`, so pinned gameplay plays silent while the clip and montage lanes keep original audio.

## Group C — needs your decision, not code

**C1. How close to the IP line do you want to sit?** Current setting is "not at all", and that is precisely what produced this render. The middle position — describe the thing physically, never name the trademark — is what I would change the rules to. Naming trademarks in image prompts is the far position and I do not recommend it.

**C2. Own-footage as the default lane for gameplay formats.** It is the only source that can actually show a Vigilante. The render path exists and takes priority (`runner.py:502`), but pinning 7 scenes costs roughly 32 interactions plus 7 timecodes you must source in another player, typed into a bare input with no preview — while the highlight list already computed at upload is never surfaced in that panel. Fixing that panel is a real piece of work; deciding it matters is yours.

**C3. Plan/duration policy.** 300s exceeds the Shorts and Reels 180s ceilings, so the top of Pro promises something two of three platforms cannot take. Free at 45s happens to cover the highest-engagement bands on both; 60s is a clean first Pro chip.

---

# 4. What we should NOT do

- **Do not ship "remove the brand-name ban" as the fix.** It is shared by six styles, does real safety work on celebrity likenesses, and alone changes nothing while `formats.py:246` stands — while on the *default* pexels engine it converts a bad render into a failed one.
- **Do not make prompts specific before A3 exists.** Verified: no try/except in the visuals loop; Pexels raises on zero results; the image path raises "likely filtered" then retries the same policy twice.
- **Do not upgrade the LLM to fix this.** The same call already wrote the specific narration.
- **Do not fine-tune and do not collect a dataset.** Wrong instrument, and it would bake a task-framing bug in at a reported (unverified) 1.5× inference multiplier, forever, on a cost you cannot yet measure.
- **Do not put Google Search grounding on the visual pass per segment.** $14 per 1,000 grounding requests on Gemini 3.x ≈ $0.126 per 9-segment video — about 40% on top of that video's entire image budget — and grounding fixes factual gaps, not visual vagueness. One grounded call per video at the topic level is ~$0.014 and fits inside the free monthly allowance.
- **Do not make Veo 3.1 Standard a default.** $22.40 for one 52-second render, 448 credits, roughly 83× the cost of the same short as stills. One runaway retry loop is a real financial event pre-revenue.
- **Do not build on Sora 2** (one source says API access ends 24 Sep 2026 — unverified, but reason enough not to depend on it), and **do not buy Veo through Runway** (identical $0.10/sec with an extra intermediary).
- **Do not abandon still-per-scene for text-to-video.** The still is an asset: a retry costs cents, the creator can approve a frame before you spend 20-80× animating it, and Teach-a-style works on images. Image-to-video is the better architecture, not the compromise.
- **Do not scrape web images, hotlink Steam capsule art, or clip official trailers.** Publisher-uploaded trailers are precisely what *is* in the Content ID reference database — we would be manufacturing claims for our own paying users. And "nobody complains about hotlinking capsules" is not a licence.
- **Do not host a shared gameplay B-roll library.** Publisher video policies cover the person who played the game posting their own footage; Valve's explicitly bars licensing your videos to others. A library turns Kliptos from a tool into a footage distributor, which is the one posture you cannot defend.
- **Do not treat IGDB / RAWG / Giant Bomb as a visual source.** They are metadata with cover art, they explicitly do not own the underlying copyright, Giant Bomb is non-commercial-only, and RAWG requires a live hyperlink on every page using its images while forbidding use "for the purposes of further distribution" — which is arguably exactly what baking them into an exported MP4 is. IGDB's commercial terms are **unknown** (contact-us, no published rate). Games Press Pro pricing is **unknown**.
- **Do not use a slider for duration, and do not pick one global default.**
- **Do not conclude you are behind the market.** AutoShorts.ai — the most-reviewed player — is explicitly stills-plus-transitions; Revid's visual layer is stock only, no AI video models; InVideo's $60/mo Max plan's 25 credits buy roughly 18.75 seconds of Pro-quality generation, under half a Short per month. Nobody in this price band does real AI video per scene, because $3-6 of generation against $0.60-1.30 of revenue per video does not close. **Caveat:** most of that came from rival-owned comparison blogs, several primary pricing pages returned 403, and no side-by-side output test was run — the cheapest real answer to "do we lag" is to run one script through one competitor and look.

---

# 5. What cannot be fixed, and must be said honestly to users

**Kliptos cannot generate GTA.** Not "hasn't yet". Image models either refuse named marks and key art outright, or silently drop the brand and hand back generic in-style imagery — which is exactly the failure you saw. Testing across generators found copyrighted-character refusal rates of roughly 42-92%; DALL-E 3 refused 78% of a 40-character set. And where models *did* comply, the outcome was cease-and-desist letters and an opt-in policy reversal. Take-Two is a notably litigious rightsholder. So for a video about a named game, product, film, or real person, there are exactly three honest options:

1. **The creator's own capture** — the only source that can actually show a Vigilante or the Diamond Depot.
2. **A described-not-branded scene** — "a matte-black armoured hover-bike with a roof-mounted missile pod banking over a neon coastal highway at night." Names nothing, reads as the thing, renders fine.
3. **A designed news-card / motion-typography treatment** that names the game *in text* — "GTA ONLINE / OPPRESSOR MK2 NERFED", patch-note styling, stat deltas. Nominative use in commentary, zero reproduction of anyone's artwork, cheap to render on your VPS, and it reads as intentional rather than as filler.

What must never happen again is option 4: unrelated generic imagery presented as if it were on-topic. That is the actual grievance — not "no gameplay footage" but "a gaming mouse pretending to be about a vehicle patch."

Three more things to state plainly rather than fix:

- **"AI illustrated" means stills with a slow zoom.** Rename the picker to say it — "AI still images with slow pan/zoom" vs "Stock video clips" — with the credit cost on both. There is no AI-video lane in the product today, and pretending otherwise is where "why not videos" came from.
- **Stock libraries structurally contain no branded game footage.** A contributor cannot license Rockstar's audiovisual work, so it is absent by construction, not merely sparse. What the library actually holds under "gaming" is the seven categories the model listed. No query improvement fixes that. For gaming subjects, the honest line is: bring your footage, or take the news-card treatment.
- **When a scene degrades, say which scene.** A silent fallback is how a recoverable bad render becomes lost trust.

**Legal caveats to carry, not resolve:** publisher video policies are unilateral, revocable licences with conditions — none read as permission for a SaaS to redistribute footage to paying subscribers. The fair-use reasoning in the research is US-shaped; India uses the narrower enumerated "fair dealing" under s.52 of the Copyright Act, which was **not** researched and should not be assumed to match. The primary policy pages for Rockstar, Nintendo, Valve and Riot were **not** read in full (timeouts and 403s) — those four should be read directly before anything ships that touches game footage. None of this is legal advice.

---

## Completeness critique — corrections to the synthesis

Verified against the repo. The diagnosis is structurally right — `formats.py:241-246` does contain the four-item palette, `_BASE_RULES` (`script_gen.py:21-22`) does define `visual_prompt` with no coupling to its own line, the coupling clause does exist only at `script_gen.py:136`, the runner's branch order is `asset_id` → `ai_visuals` → `media_id` → pexels (pin-ignored bug real), `pexels.fetch_clip` raises on zero results with no try/except above it, and `veo` appears exactly once in the backend (`credits.py:30`). Below are the gaps.

## 1. A sixth complaint was never answered, and it is the most serious one

"need a deeper reseacher to be honest" is treated as a request for a deeper analysis. In context it reads as a request for a **research step before scripting** — and the code shows he is right in a way the plan never notices.

`backend/app/routers/scripts.py:256-262`: on the **topic route** (the route this render used), the only things passed to the model are `topic.title` and `topic.hook_text`. `reference_text` stays `None` — it is populated **only** on the `source_url` branch (`:253`). So the model was handed the string `"GTA 5 LIVE | MRRAJAPLAY #gtalive #gtaonline..."` and nothing else, and produced the Oppressor MK2 lock-on nerf, the Vigilante missile cooldown and a "Diamond Depot" heist **from nothing**.

This inverts the plan's single strongest evidential claim. Section 1(b) and answer (c) both rest on "the same call produced those specifics, therefore capability was present and was overridden by instruction." What the code shows is that those specifics were **fabricated**. They are not proof the model can be faithful; they are proof it will invent patch notes when given a title. The owner's rejected video states false facts about a live game as news, under a real streamer's name. That is a larger defect than the visuals and the plan does not mention it once.

The "no visual matched the script" framing also softens: no stock library and no image model could have depicted a heist that does not exist.

Concrete corrections:
- Answer (c) needs rewriting. "Do we lag in our AI?" — the honest answer is "not the model tier; the model is being asked to write news from a headline with no source, and it complies by inventing." That is a brief problem *and* a grounding problem.
- Complaint 6 needs a Group A item: `generate_script` **already takes `reference_text`** (`script_gen.py:167`) and already injects it with "base the script on the FACTS in it (do not invent numbers or claims beyond it)" (`:186-190`). The wiring cost is one call on the topic route. This is the cheapest high-value fix in the whole review and the plan omits it.
- Related dead signal: `Topic.keywords` (`models/topic.py:18`) is written by the harvester (`services/harvester.py:103,161,200`), exposed in `schemas/topic.py:13` — and read **nowhere** in the backend (`grep -rn "keywords" backend/app` returns only those definitions). Those keywords would anchor both the script and the Pexels query.

## 2. Cheap fixes an experienced engineer would reach for first, missed entirely

**a. The per-scene visual prompt is already editable, and re-rendering is already free.** `frontend/src/app/dashboard/studio/page.tsx:897-903` renders a "Visual direction" input bound to `segment.visual_prompt`, shown whenever the format has the `scenes` control — which `gaming_update` does (`formats.py:254`). The `ai_image` branch reads exactly that field (`runner.py:513`). And `credits.is_free_restyle` makes a same-engine re-render free up to `FREE_RESTYLES_PER_VIDEO = 3` (`routers/pipeline.py:31`). **The owner could have fixed this exact rejected render by typing 7 prompts, for zero credits.** The plan never says this, and A1 routes the same-day test through the feedback API instead of the box that is already on screen. It should be: type the prompt into the existing field, re-render free, then decide.

**b. `headline` is fully wired end-to-end and never populated.** `ScriptSegment.headline` exists (`schemas/script.py:52`), `captions.py` carries a whole per-scene Headline style with fade (`:163-173, 274-293, 391-395`), and `runner.py:557` passes `segments[i].get("headline")` into it. But no prompt asks for it (`headline` appears nowhere in `script_gen.py` or `formats.py` except one unrelated word at `formats.py:104`), and `grep -rn headline frontend/src --include=*.tsx` returns **nothing**. Section 5's option 3 — "a designed news-card treatment that names the game in text" — is therefore one line in the recipe plus one JSON schema field plus one studio input, not new work. Presenting it as an aspiration while the render path sits finished and unused is the plan's biggest miss.

**c. Recipe overrides need no deploy.** `scripts.py:222` — `user_fmt.script_recipe` lets a user-defined format replace the recipe entirely. The owner can test A2's wording through the product before touching `formats.py`.

**d. The Pexels query is the entire prose sentence** (`runner.py:531`, into `pexels.py:64` `params={"query": query...}`). Sending `topic.keywords` or a trimmed noun phrase is a one-line search improvement that needs none of A3's fallback machinery.

## 3. Proposed fixes that break something

**A6 (stop appending `STYLE_SUFFIX`) breaks carousels.** `generate_image` is shared. The carousel path at `runner.py:133-136` passes `seg.get("visual_prompt") or seg["text"]` **raw** — it never calls `scene_prompt`. So `STYLE_SUFFIX` (`image_gen.py:22-25`) is the only styling *and the only "no text, no watermarks" ban* that carousel slides get. Delete it and every carousel slide starts generating misspelled lettering. A6 is listed as "minutes" and independent; it **cannot** ship before A5's carousel-through-`scene_prompt` routing.

**B3's `-an` item is a no-op as written.** `assembler.render_segment` maps `-map 0:v:0 -map 1:a:0` (`assembler.py:68`) — the clip's audio is discarded at assembly regardless of what `cut_source` did. Removing `-an` from `cut_source:197` changes nothing in the narrated lane. Keeping gameplay audio under narration requires an `amix` with ducking in `render_segment`, which is a different and much larger change. The claim that "the clip and montage lanes keep original audio" is about a separate feature, not this pipeline.

**A4 (move `media_id` above `ai_visuals`) creates a billing bug if shipped alone.** `routers/pipeline.py:145-146` prices `ai_image` as `engine_credit_cost("ai_image", scenes=len(all segments))` — every segment, pinned or not. Today the mispricing is hidden because every scene really is generated. Fix the ordering and a creator who pins all 7 scenes pays 5 credits for 0 generated images. The scene count must exclude pinned scenes in the same change.

**A8 has more blast radius than stated.** Three problems: (i) `_finalize` (`script_gen.py:152`) uses `seg.setdefault("duration_estimate", …/2.5)` — the divisor is a *fallback for when the model omits the field*. Your stored `total_duration: 52.5` is the sum of the model's own estimates, so "60s requested → 52.5s estimated" is not caused by the divisor and changing it will not fix it; the lever is the `~2.5 words/second` line in the rules and `SECONDS_PER_SEGMENT`. (ii) There are **two** rule blocks with hardcoded rates — `_BASE_RULES:23` says ~2.5 and `_POETIC_RULES:44-45` already says ~1.2 — plus `formats.py` recipes that restate rates in prose (`shayari` says "~1.2 words/second" again at `:192`). A single interpolation point will leave contradictions. (iii) `SECONDS_PER_SEGMENT = 8.5` in `studio/page.tsx:89` is not only duplicated, it converts **carousel slide counts into a duration** (`page.tsx:210`), so making it per-format silently changes how many slides an image post produces.

## 4. Numbers and evidence

- **Credit conversions are floored where the formula ceils.** `credits_for_cost` is `max(1, ceil(cost × 2 / price))` (`credits.py:33-36`). So Kling $1.47 → **30** credits not 29; Hailuo $0.71 → **15** not 14; and the headline hybrid recommendation $0.87 → **18** not 17. Small, but the plan claims to be using the repo's own formula.
- **`$0.035/image` is a repo constant, not an assumption the analysis introduced** — `credits.py:18 IMAGE_COST_USD = 0.035`. Worth saying so; "assumed" reads as if the analysis guessed. Whether it matches Google's real per-image price is genuinely unverified, and that framing is fine.
- **Every Veo/Kling/Wan/Hailuo price is unverifiable from inside the repo** and the plan carries them as single-source (one Google pricing page, one fal listing, one blog). It flags this honestly, but the Veo Lite $0.05 figure is load-bearing for B1's entire recommendation and rests on one page nobody in this review can open. Treat B1's cost table as a hypothesis to price-check with one real API call before it reaches a roadmap.
- **A7 overstates the work.** `DURATION_CHOICES` (`studio/page.tsx:93-101`) already has exactly the descriptive labels the plan proposes adding ("45s — standard Short", "90s — room to explain") and is already plan-filtered (`:412` filters on `maxSeconds` from `planData.features.max_duration_seconds`). The real A7 is two things only: move the block out of `{showAdvanced && …}` (opens at `:378`, the Length select sits at `:408-418`) and send `duration_seconds` from `topics/page.tsx:84-93`. The "define the choices once in the backend" part is nice-to-have, not the fix.
- `series_tasks.py:160` calling `generate_script(duration_seconds=series.duration_seconds or 60)` with no plan clamp — **confirmed**, the clamp exists only at `scripts.py:174`.
- The `used_ids` + `per_page=10` exhaustion bug on one-background formats past 10 scenes — **confirmed** (`pexels.py:64` single search, `runner.py:529-534` one `used_ids` for the whole video).
- C2's "the highlight list is never surfaced in that panel" — accurate but worth sharpening: highlights **are** surfaced, on the clips page (`frontend/src/app/dashboard/clips/page.tsx:290-346`). They are absent from the studio's per-scene picker. And `services/highlights.py` already exists specifically to solve the no-transcript gameplay case, so B3's premise is half-built already, not greenfield.

## 5. Honesty about what cannot be fixed

Section 5 is the strongest part and I would not soften it. Two additions:

- The honest-limits list needs a fourth entry: **the trend route writes from a headline with no source material, so factual specifics in a news-style format may be invented.** That is a "must be said to users" item at least as urgent as "AI illustrated means stills," and it is currently absent.
- "What must never happen again is option 4: unrelated generic imagery presented as if it were on-topic" is right, but for this render the deeper grievance is a fabricated patch note narrated as news over a stock gaming mouse. Naming only the imagery half understates it.

Nothing else in the plan overpromises. The "no AI-video lane exists" claim, the hardcoded `ai_image` → still → `zoompan` 1.0→1.18 path (`assembler.py:147-182`), and the absence of any switch to flip are all verified exactly as described.

---

Links: [[Pitch]] · [[Home]] · [[Competitors]] · [[Pricing]]

---

## EXPERIMENT RESULT — 2026-09-11, run against the live model

The diagnosis above was reasoning from code. This is measurement.
`backend/scripts/visual_relevance_experiment.py` runs the SAME subject
(the rejected GTA render's topic) through three prompt variants and counts how
many visual prompts name something from their own line.

| Variant | Scene-specific | Generic peripherals |
|---|---|---|
| **1. As shipped** | **0 / 7** | 6 / 7 |
| 2. Palette assignment removed only | 3 / 7 | 0 / 7 |
| **3. Palette removed + coupling clause** | **6 / 7** | 1 / 7 |

Variant 1 reproduced the original failure exactly — multi-monitor setups,
mechanical keyboards, gaming mice, an esports crowd — for a script about a
Terrorbyte buff and a Heavy Railgun.

Variant 3 produced, unprompted and naming no trademark:
- *"A player on a futuristic black hover-bike firing a missile that harmlessly
  veers off course from its target"* — the Oppressor MK2 nerf, described
  physically.
- *"A tropical island mansion vault door dramatically opening to reveal piles
  of gold bars and cash"* — the Cayo Perico payout.
- *"Extreme low-angle shot of a massive, chrome-plated, armored semi-truck"*.

That is precisely the "describe it, don't name it" output the synthesis
predicted was available under the existing brand ban.

**Conclusion: the script half of visual relevance was never an industry-hard
problem for us. It was four words in `formats.py` plus a missing clause.**
Removing the palette alone recovers half of it; adding the coupling clause
recovers nearly all of it. The model was never the limitation.

**What this does NOT prove, and must not be claimed:**
1. That the image model renders "futuristic black hover-bike" *well* — the
   `bold` visual_style wrapper ("strong silhouettes, striking and simple")
   still abstracts the subject, and `STYLE_SUFFIX` still contradicts the
   aspect ratio.
2. That Pexels can find these. It cannot; stock has no armoured hover-bikes.
   **Specific prompts on the default `pexels` engine will produce MORE zero-result
   failures, and `runner.py` has no try/except around that loop.** The fix must
   ship with the per-scene fallback or it converts bad renders into dead ones.
3. That competitors' failures share this cause. Unknown.

**Strategic consequence:** "nobody has solved visual relevance" is materially
weaker as a moat than the audit assumed — at least on the script side, we
simply had not tried. The genuinely hard half is the render side: getting an
engine to produce the described thing. Any positioning built on the refusal
should be built on that half, not this one.
