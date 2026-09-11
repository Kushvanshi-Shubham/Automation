# Three questions: more inputs, optional voice, our own library

> 11 September 2026. Each proposal argued FOR and AGAINST by independent
> agents, then judged. Written in plain language at the founder's request.

---

Three answers, then the build order.

**Short version:** (1) Yes to more inputs, but you already own most of it — only images are truly missing. (2) Yes to optional voice, but only at the end, and do not build a clone button. (3) Yes to your own media, but per-user private only — never pooled — and "trainable" is the wrong word; I explain why.

---

# 1. "Input should not be limited to voice"

**What you said:** people may have an image, a poster, an essay, a pitch — not only a voice note. And there are two users: one with no idea, one who already has one.

### The good side

- **Kliptos is already a multi-input app.** `POST /scripts/generate` branches four ways: a trend, a rough idea, a link, or your own typed script. The studio already shows three tabs — Idea / Link / Own script (`frontend/src/app/dashboard/studio/page.tsx:145`). Voice-only would be going backwards.
- **All inputs already pour into one variable.** It is called `reference_text`. The link path fills it. The script writer is the only thing that reads it. So "read a poster" is not a new pipeline — it is one more thing that fills the same variable. Nothing after that point changes.
- **Reading a picture is cheap.** Google's docs price one small image at about the same as a short paragraph of text. You already send up to 6000 characters of article text on the link path.
- **Turning a picture into a scene is already built.** `assembler.image_to_clip` (`backend/app/pipeline/assembler.py:155`) takes a still and makes a slow pan/zoom shot. You use it for AI images today. A creator's own poster would use the same function. And `.jpg`/`.png` are already in your R2 content-type map.
- **One shipped feature is visibly broken here.** I read `_run_image_post` in `backend/app/pipeline/runner.py`. Every carousel slide is an AI image, a Pexels photo by id, or a Pexels search. There is no path for the creator's own picture. A designer who already made the poster cannot put it into their own carousel.
- **An image carries things a voice note physically cannot.** Exact spellings, prices, dates, names. Whisper on an Indian accent will mangle a product name; a screenshot will not. And some things must literally appear on screen.

### The bad side

- **Two of the three things you named already ship.** `custom_script` is your essay and your pitch. `source_url` is your link. Both are in `backend/app/schemas/script.py` today. They are not missing. They are unlabelled. Building them again builds nothing.
- **Nobody has walked through the doors you have.** Your own audit says 3 accounts, 6 videos, 1 render. And `backend/app/routers/analytics.py` returns 501 on every route — there is no event tracking anywhere. So you cannot see which door gets used. Adding four more doors to a funnel you cannot see is guessing louder.
- **The door you already have is quietly broken.** This is the thing I most want you to see. In `backend/app/routers/scripts.py`, lines 201-229 build a variable called `instructions`. It collects your own typed custom instructions, the format recipe, the mood prompt, your Teach-a-style recipe, and your feedback memory. Line 314 passes it to `generate_script`. But line 243 — the bring-your-own-script path — calls `script_gen.format_custom_script(req.custom_script, model=..., user_keys=...)`, and that function at `backend/app/services/script_gen.py:224` **has no `instructions` parameter at all**. I read both. So on the "I already have a script" path, your self-improving feedback loop, your Teach-a-style recipe, the format recipe and the user's own instructions are all thrown away with no error. That is the exact user you are worried about, being served by a broken door.
- **Doors multiply bugs, they don't add up.** `scripts.py:300-306` exists only to block input types that cannot combine, and `prompt_subject` exists only because combining two inputs once put the same trend into the prompt twice.
- **The important one: a poster makes the script ACCURATE. It does not make the script SOUND LIKE YOU.** If you build the easy input work instead of the voice work, the product gets wider and stays bland — and bland is what the platforms now punish. Accuracy is the floor. Sounding like you is the only thing that is yours.

### The best version

**Step 0 — fix the broken door (half an evening).** Pass `instructions` into `format_custom_script`. Keep the "do not change their wording" rule for the text itself; apply the recipe to `visual_prompt`, captions and music only.

**Step 1 — let people type the Hot Mic answers (one evening).** Under the record button, a small "type it instead" link that opens a text box. Same three questions, same thesis, same constrained script. Whisper only turns speech into text anyway, so nothing downstream changes. Cost: one textarea and one `if`. This also solves your shy-user worry for free, and it answers a question you cannot answer yet — is it the QUESTIONS that make the script better, or the VOICE? Run the same trend three ways and look at them side by side.

**Step 2 — one line of copy (thirty minutes, no code).** Under the "I have my own script" tab write: "Paste your essay, your pitch, your notes — anything you already wrote." Your essay and pitch cases are then closed.

**Step 3 — images only, later, and only when a real person asks (2-3 evenings).** Start with the carousel hole, not a generic dropzone. Then add the same branch to `_visual_for_scene` using `image_to_clip`. Rule: an uploaded image must do BOTH jobs — it is reference text AND it is the scene visual.

Three guardrails I checked in your code:
1. Count image uploads separately. `MAX_ASSETS_PER_USER = 10` is sized for 500MB videos. Ten posters is nothing. If images eat those slots, clip mining starts telling people "Upload limit reached."
2. Guard `backend/app/pipeline/asset_tasks.py`. It runs ffprobe then Whisper on every asset. An image would go straight to status "failed".
3. **No migration needed.** `backend/app/models/asset.py:15` is `kind = Column(String, default="video")` — a plain string, no enum, no check constraint. `kind="image"` is free.

### The worst version

**"Upload anything."** A box that takes .docx, .pptx, .xlsx, .zip, 40-page PDFs, links, images. Each needs its own parser and its own failure message. Six evenings becomes six weeks. You have seen how this goes: the link feature was 21 files and about 1190 lines added, and most of `link_ingest.py` is handling the ways it fails, not the way it works.

**And the quiet version of the same mistake:** building this instead of the voice work, because this is easier. The funnel gets wider, and every video out the other end is still an AI voice over stock footage.

**The small absurd version:** reading someone's poster for its text, then illustrating their video with AI art of a different poster. They uploaded the thing. Put the thing in the video.

### My answer

**Yes, in a small form. About 4-5 evenings total** — and Steps 0-2 are under two evenings and carry most of the value. Do not build PDF, .docx, .pptx or decks. That road ends in business marketing videos, which is a different buyer and a different competitor set.

---

# 2. "Using your own voice should be optional"

**What you said:** real voice, AI voice, or their voice cloned — the user picks, because some people are shy or do not speak clearly.

### The good side

- **Your app already makes videos with no voice at all.** `backend/app/pipeline/runner.py:553-562` sets `audio_path: None` for every segment on a "visual" short. Your studio calls it "Visual short — On-screen text + music, no voice."
- **Your landing page already promises faceless.** "Kliptos builds fully faceless shorts," and "faceless YouTube channel" is one of your SEO keywords. If one screen demands a voice while the home page promises none, the product is arguing with itself.
- **The reasons are real, not excuses.** Shy. Sharing a room. Recording at 1am. Anonymous on purpose. Your own research found creators renting hosts on Fiverr rather than appear — people will pay money to avoid performing.
- **The clone option is already mostly built.** `backend/app/services/premium_voice.py` marks cloned voices with a `cloned` flag and sorts them to the top; the studio shows them with a star. Your settings page already stores an encrypted ElevenLabs or Cartesia key. So a user who makes a clone on their own ElevenLabs account **can already pick it inside Kliptos today.**
- **A 60-second take is exactly what a clone needs.** Cartesia's docs say 10 seconds is enough and up to 60 seconds keeps the accent better; ElevenLabs says instant clones come from samples under two minutes. So the recording you are already asking for would do double duty.

### The bad side

- **If your real voice never reaches the video, nothing in that video is uncopyable.** A thesis is text. Text was always the easy part to fake. Your own notes say everyone claims style transfer and nobody can measure it.
- **Notice what the against side proved by being fair:** cloning your own voice is fully legal, fully allowed, and YouTube does not even require an AI label for it. That is not a win — that is the problem. It changes nothing a viewer hears, nothing a platform can see, and nothing a competitor cannot do from the same 60 seconds.
- **The clone may sound worse for your users, not better.** ElevenLabs' own docs say quick clones struggle with uncommon accents and unusual voices. Your users are Indian English, Hindi and Hinglish. So the clone can land in the bad middle — not clearly you, and less clean than the free voice you already ship. **I did not read that page myself**, which is exactly why my answer below is "test it, don't argue about it."
- **The clone is the cheap build, and that is the trap.** `premium_voice.py` is already generic across providers, so bolting on a clone call is small. The real-voice cut is the hard one: `tts.py` always synthesizes — there is no way today to drop a slice of the user's own recording into a segment — and `assembler.py` mixes music flat with no ducking. If both ship as "options," the easy one ships, the box marked "voice" gets ticked, and the hard one becomes permanent phase 2.
- **Do not put your own provider key on the server for this.** I checked. Your paid render charges credits, which is fine. But your free one-scene preview accepts `voice_provider`, has no daily cap (only AI images have one), and plan checks are off — so every signed-in stranger counts as PRO. That is free previews on your card. And you would not see the bill: `track("premium_voice")` writes a counter, but `premium_voice` is not a key in `UNIT_COSTS_USD` in `backend/app/services/costs.py`, and `SERVICES = list(UNIT_COSTS_USD)` — so it always reports as zero. I confirmed both.

### The best version

**Two things are being made optional. You are right about one and wrong about the other.**

- Right: optional at the END — whose voice narrates.
- Wrong: optional at the START — skipping the 60-second recording. Never make that optional. The recording is where the idea comes from.

Say it in the product like this: **"You talk for 60 seconds. You choose whether your voice ships."**

So the three options are already two-and-a-half built:
1. **AI voice** — shipped. It is the default. Leave it.
2. **My cloned voice** — already works with the user's own key. Build **nothing**. Write one help line: "Made a clone on ElevenLabs? Add your key in Settings and it shows up here."
3. **My real voice** — not built. This is Hot Mic. This is where the evenings go.

**Do this before anything else, and it takes 10 minutes and no code:** clone your own voice on your own ElevenLabs account, add the key in Settings, render one video, and play it to someone who knows your voice and does not know what you did. If they say "that's you," a clone button may be worth 3 evenings later. If they say "that's a robot with your accent," the question is closed forever and you saved a week.

Three fixes that are wrong today no matter what you decide (about one evening):
- Add `"premium_voice"` to `UNIT_COSTS_USD` in `costs.py`. The number already exists — `credits.py` records `premium_voice: 0.15` in `ENGINE_REAL_COST_USD`. Copy it.
- Add Cartesia and ElevenLabs to the processor list on `frontend/src/app/privacy/page.tsx`. It names Google, OpenAI, Hugging Face, Pexels and Microsoft. You already send Cartesia and ElevenLabs text today.
- Pass `language=` in `backend/app/pipeline/transcribe.py`. Line 39 calls `transcribe(str(wav), word_timestamps=True)` with no language, so Whisper guesses. Both advocates agree this hurts Hindi and Hinglish.

### The worst version

**Three radio buttons — Real voice / AI voice / My cloned voice — with "AI voice" preselected, shipped before Hot Mic exists, on your own API key.**

It looks sensible. Here is the order it goes wrong. The clone ships first because it is genuinely small. It demos beautifully to you, because you have a good mic and a quiet room. The box marked "voice" gets ticked. "Real voice" has nothing to play, because `synth_script` cannot insert a ready-made audio file. Users clone on your key because most have none, so strangers' voiceprints sit on your personal account with no consent record and no delete path — that is the one mistake here that is hard to undo. The spend is invisible because `premium_voice` is not in `UNIT_COSTS_USD`. Six months later you are a wrapper with a three-question form in front of it, and your landing page says "voice cloning" again — the exact claim you already deleted once as fake.

### My answer

**Yes — but "optional" means optional at the end only, and you build zero evenings of clone work.**
- Clone option: **0 evenings.** It already works with the user's own key. One help sentence.
- The three fixes above: **about 1 evening.**
- The listening test: **10 minutes.**
- Everything else goes to the real-voice cut: **6-10 evenings.** Span selection on word boundaries against each format's `words_per_second`, room tone from the quietest part of their own recording, and ducking music under it in `assembler.py`, which mixes flat today.

Voting against the clone button costs you no time at all. It moves 3-4 evenings from the part with no advantage to the part that has one.

---

# 3. "Grow our own media library from user uploads"

**What you said:** Pexels-type sites are a problem; as users upload, our own database grows, we prioritise their images and videos, and the AI gets more trainable.

### First, the one thing you have wrong — and it is worth being clear about

**You cannot train the model, and you would not want to.**

You do not own a model. You call Gemini through Vertex. The only thing you can do is put text into the prompt.

Even if you could train it: training teaches a model to *sound* a certain way — tone, rhythm, phrasing. It does not teach it *facts about your files*. A model trained on your users' transcripts would never learn "second 42 of file X shows a red car." That is not what training does.

And the model never sees the video anyway. It only ever sees the Whisper text. So "training on footage" really means "training on rough speech-to-text of footage."

What you actually want is **labelling so the app can find the right second**. That is a search job, not a learning job. Labelling is cheap, instant, private, and you can delete it. Training costs real money, needs consent you never collected, takes weeks, and you can never un-train a model after a user asks you to delete their data.

The good news: **you already do the correct version of this.** Feedback memory, Teach-a-style and `custom_script` all put the user's own material into the prompt at the moment of writing. Delete the row, the effect is gone. That is the right mechanism. Same instinct, completely different build.

### The good side

- **The per-user half is not a plan. It is shipped code that already wins.** I read `_visual_for_scene` in `backend/app/pipeline/runner.py`: the `asset_id` branch runs **first** — before the pinned stock clip, before the AI image, before Pexels. The comment above it even records that this ordering was once wrong and got fixed. Storage on R2, Whisper transcription, highlight detection, the auto-matcher (`footage_match.py`) and the render path all exist and are tested.
- **The creator's own capture is the only source that CAN show a named game, product or place.** A Pexels contributor cannot license Rockstar's work, so it is not "rare" there, it is absent. Better search queries can never fix that. Your own diagnosis named this exactly: not "no gameplay footage" but "a gaming mouse pretending to be about a vehicle patch."
- **It is the cheapest honest answer to platforms punishing sameness.** One person's own footage is different from everyone else's without any effort.
- **Storage is not a reason to say no.** R2 is cheap and your own cap comment says "until object storage exists" — object storage now exists, so that comment is stale.

### The bad side

- **The shared pool is the one mistake a solo founder cannot survive.** Valve's video policy says in plain words: "You also can't sell or license your videos to others for a payment of any kind." A private library is fine — the person who played the game uses their own recording. A pool is exactly licensing one person's video to others, and your subscription is the payment. Your own vault already ruled this out.
- **Your own UI already promises the opposite.** The Footage page says "Your footage, your rights." The upload docstring calls it "the rights-cleared rail." I read it. Pooling breaks a sentence that is already on the screen.
- **Privacy has no undo.** Living rooms, children, a password on screen. If any setting means a stranger's monetised Short contains eight seconds of someone's home, you do not get an email. You get a screenshot on Twitter.
- **You have zero moderation code.** A grep for moderation, nsfw, dmca, takedown, flag finds nothing relevant. A pool needs screening, a named takedown contact, an appeals path and an audit log on day one. That is a desk job, not a feature.
- **The pool would be tiny.** 3 accounts, 10 files each. Even at a thousand maxed-out users that is random phone video against Pexels' millions of graded, tagged, cleared clips.
- **The matcher only reads what was SAID, never what the clip LOOKS like.** I read `footage_match.py` line by line: it builds windows from `transcript["segments"]` and scores them against `seg["text"]` — the narration. So gameplay, drone shots, your shop front, a silent screen recording can never be matched. There is no embedding or vector search anywhere in the backend; I grepped.
- **Uploads block paid renders.** `celery_app.py` has no task routes, and production runs `--concurrency=1` on 2 vCPU. So transcribing someone's free 40-minute upload sits in the same queue as a paying customer's render.
- **Deleting a file has no guard.** `delete_asset` in `backend/app/routers/media.py` deletes the row and the object with no check for videos that pinned it. The render then dies with "pinned footage no longer exists." Today almost nobody hits it. Lift the cap and they will.

### The best version

**Per-user only, forever. Do not call it a library — call it "Your footage." The word "library" is what pulls you toward sharing.** Then build in this order:

1. **Delete guard (1 evening).** Block or warn on delete when a video still points at that clip. Do this **before** raising the 10-file cap.
2. **Fix the studio panel (2 evenings). This is the highest-value item in the whole proposal.** I read it. Today it shows a filename, a duration number, a "Use" button, and one shared "Start at second" text box for the entire panel. So the creator opens the file in another player, finds the moment, and types the number. Meanwhile you already compute a highlight list at upload — and you only show it on the clips page, not here. Fix: six thumbnails per clip, click one to set the start second, and show the highlights you already paid for. You are not building a feature. You are switching one on.
3. **Accept images (2 evenings).** Add `.jpg/.png/.webp`, set `kind="image"`, skip Whisper for them, send them down the still-with-slow-zoom lane. Same work as Question 1, Step 3 — do it once.
4. **Split the queue (1-2 evenings).** Put `process_asset` on its own low-priority route before you invite more uploads.
5. **Then label what the clip LOOKS like (2-3 evenings).** At upload: ffmpeg one frame every 5 seconds, shrink to 384px, ask the cheap Gemini vision model for a ten-word description, store it as a new JSON column (this one does need a migration — 0015; you have 14, it is routine). Then in `footage_match.py` score against those captions AND against `seg["visual_prompt"]`, not just `seg["text"]`. Keep your existing score floor and spacing rule. No vector database, no embeddings. The price I have works out to a few US cents per hour of footage, paid once — **but that is Google's Developer API list price and your calls go through Vertex. Confirm the Vertex number before you build.**
6. **Only then** raise the 10-file cap.

### The worst version

**"Opt-in sharing. Users tick a box saying they own the footage and agree to let it help other creators."**

This is the trap because it looks responsible. The tick box transfers nothing — a streamer cannot grant you rights to Valve's game, to the song in the background, or to his friend's face on the Discord call. When the notice arrives, "the user said he owned it" is not a defence. One tick also changes what the company is: from a tool that makes your video into a service that distributes other people's footage. Permanently, from the first shared file. And it is irreversible in the way that matters — once a stranger's published Short contains user A's living room, un-ticking the box does nothing.

**Runner-up worst version:** building a proper vector search index over 30 files, on a 2 vCPU box, while pinning a scene still needs a stopwatch and a text box. An excellent engine in a car with no steering wheel.

### My answer

**Yes to per-user. Absolute no to pooling, forever. And "trainable" becomes "labelled."**

About **8-10 evenings** total, so roughly three weeks at your pace. But **steps 1 and 2 are three evenings and carry most of the value.**

Not counted, because they are separate decisions: making pinned footage keep its own sound (`assembler.py` strips audio with `-an` and `render_segment` maps only narration — fixing it means mixing and ducking two tracks), and resumable chunked upload to R2 (3-4 evenings, worth it when files get bigger or more frequent).

---

# Putting all three together

### The build order

1. **Fix the custom-script bug.** Half an evening. (Question 1, Step 0.)
2. **The listening test.** 10 minutes, no code, any time you can make a clone on your own ElevenLabs account. It closes Question 2's clone branch permanently, either way.
3. **The bug-fix evening.** One evening: `premium_voice` into `UNIT_COSTS_USD`, Cartesia + ElevenLabs onto the privacy page, `language=` in `transcribe.py`, and the asset delete guard. All four are wrong today no matter what you decide.
4. **The studio footage panel.** Two evenings. Thumbnails, click-to-set-start, show the highlights you already compute. This switches on a feature you already built and paid for.
5. **Hot Mic, with typed answers from day one.** One evening for the text box, plus thirty minutes of copy on the "own script" tab. Then the real-voice cut — 6-10 evenings — which is the main event and the only part nobody can copy.
6. **Then, only if you see the need:** images in (2-3 evenings, covers both Question 1 and Question 3), queue split (1-2 evenings), frame captions for silent clips (2-3 evenings).
7. **Never:** a shared pool, training on user media, an "upload anything" box, or a clone button before the listening test passes.

### The ONE thing to do first

**Fix the bring-your-own-script path in `backend/app/routers/scripts.py:243` so it passes `instructions` through.**

Half an evening. It is a real bug, not a feature. It serves the exact user you named in Proposal 1 — the one who already has a script. And right now that user silently loses your feedback memory, your Teach-a-style recipe, the format recipe, and their own typed instructions. You built all four. On that path, none of them run.

---

### Where I had to choose, and what I could not find

- **Migration or not for a new asset kind.** One advocate said you need migration 15; the other said zero. I checked `backend/app/models/asset.py:15` myself: `kind = Column(String, default="video")` — plain string, no enum, no check constraint. So `kind="image"` needs **no migration**. The advocate who said otherwise was wrong. (The frame-caption column in Question 3 is a genuinely new column and does need one.)
- **Whether a clone sounds like you.** One side said a 60-second clone carries the person; the other said quick clones struggle with unusual accents. Neither of us listened to one. I chose "test it, don't argue about it" — that is why the 10-minute listening test is in the answer instead of a verdict.
- **The cost of captioning frames.** The number I have is Google's Developer API list price. Your calls bill through Vertex. I could not confirm the Vertex figure — check it before you build on it.
- **Whether users are actually asking for any of this: I could not find anything.** No input analytics anywhere in the repo, no user quotes, no waitlist notes. Your analytics router returns 501 on every route. So every "users want X" claim in this answer — mine included — is reasoning, not measurement. That is itself an argument for shipping the smallest version of each thing and watching.

---

Links: [[Where The Novelty Is]] · [[Is The Idea Worth It]] · [[Pitch]]
