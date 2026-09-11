# Where the novelty is — unsolved problems and what to build

> 11 September 2026. An 18-agent hunt: five independent sweeps for problems
> nothing currently solves (creator voices, distribution, the originality
> crunch, under-served languages, adjacent fields), five invention lenses each
> novelty-checked and feasibility-checked against this repo, then a ranking, a
> synthesis and a prior-art critic. 2.9M tokens, 795 tool calls.
>
> Money and revenue were deliberately excluded from scope.

---

# Where the novelty actually is

I checked the load-bearing claims against your own code before writing this. `services/youtube.py:22` is still two scopes. `pipeline/transcribe.py:39` still calls `.transcribe()` with no `language=`. There is no embedding call anywhere in `backend/app` (grep returns two hits, both the phrase "flat vector art"). And `script_data` is reassigned at 13 sites with no history table. Those four facts decide most of what follows.

---

## 1. THE BIGGEST UNSOLVED PROBLEMS

### P1. "I have the script and the voiceover. Finding pictures that fit it takes hours."

**Who:** everyone whose visuals are sourced rather than filmed — faceless, explainer, documentary, commentary, review. The largest population in the creator-tool market, and the one you already serve.

**Evidence it is real:** a professional editor for Geography by Geoff / MegaBuilds (r/editors, 57 upvotes) describing "The Hunt" — "spending half an hour scrolling through Storyblocks and Envato just to find a single 5 to 10-second clip… because of all the context switching I have practically zero personal life left." r/NewTubers, 76 upvotes: "even for a simple 1-minute section, finding footage that actually fits the narrative takes me hours." And the one that tells you money is not the fix — r/editors, 47 upvotes, about **Artlist**, a paid professional library: "If I type in Wisconsin flood or Wisconsin storm or even just Wisconsin itself I will get footage of just random countries like France or Australia or Thailand." InVideo sits at 1.9/5 across ~1,014 Trustpilot reviews with "the frames do not make sense" as the recurring line.

**Why it is still unsolved, and this is the surprise:** three separate walls. (a) Libraries are keyword-indexed and the query is a sentence, so precision makes retrieval *worse* — visible in your own code at `runner.py:159`, `query = background_query or visual_prompt or text` handed straight to a `per_page=10` relevance walk. The string that fixes scene-matching is the string that breaks search. (b) Generation does not rescue it — an editor testing Seedance 2.5 and MiniMax H3 on a paid job (70 upvotes) generated ~40 clips, kept 12, then spent two days cutting around bad frames. (c) **The stock corpus is contractually fenced.** Pexels' terms forbid bulk systematic copying and data mining "including machine learning purposes." So nobody — you included — can build the semantic index that would solve it. The ceiling is legal, not technical.

And the inversion underneath: stock-footage-over-TTS-narration *is* the templated form YouTube's "inauthentic content" language targets. Commentary, review and video-essay content is transformative by construction, is safe, and has **zero** AI tooling for its visual layer — because its visuals are specific copyrighted media, so every AI video company routed around it into stock. The pain that hurts most and the genre that survives are the same place, and the whole industry is pointed the other way.

### P2. "I can see the video died. I cannot see why."

**Who:** everyone below ~10k impressions (which is almost everyone), and separately everyone above it who has a retention curve and no explanation for it.

**Evidence:** "my latest video after 72 hours only has 10 impressions, 10!!!" (39 upvotes). YouTube's own Thumbnail Test & Compare returns inconclusive below roughly 10k impressions — the official learning tool is unavailable to exactly the people who need it. Two 2026 round-ups written by competitors — OpusClip's own "10 Best Retention Graph Analyzers" and OverseerOS's — between them cover about twenty tools and neither can name one that aligns retention to transcript, shot changes, or edit decisions.

**Why unsolved:** the two halves sit in different companies. Analytics vendors hold the OAuth and only ever see a finished mp4. Generators hold the edit decision list and throw it away at export. Nobody occupies both. There is also a statistical wall nobody addresses: at 300 views the difference between video A and video B is indistinguishable from a Tuesday, so creators learn superstitions.

### P3. "AI writes it, but it doesn't sound like me — so I rewrite half of it and save no time at all."

This is the problem that voids the entire category's value proposition. If you still rewrite half, the tool did nothing.

**Why unsolved:** style transfer is offered by everyone and **measured** by no one. Every tool will write in your voice; none will tell you how close it got or which tic it dropped. With no fidelity score there is no gradient, so every product plateaus at plausible-generic. Your own Teach-a-style has the same hole — it is a one-shot setting with no feedback.

The 2026 context makes it existential rather than cosmetic: consumer enthusiasm for AI-generated creator work reportedly fell 60% → 26%, and 83% say human-made sound builds stronger emotional connection. (Vendor surveys — directional, not gospel. Flagged again in §6.)

### P4. The originality black box, and the fact that every tool destroys the evidence

The policy's operative tests are properties of a **corpus**, not a file: "templated videos with little to no variation from one upload to the next," "may feel repetitive to viewers after watching several videos in a row," "videos feel interchangeable." Nothing measures a creator's self-similarity — ChannelGrade compares you to a *competitor*, TubeBuddy's demonetization audit greps titles for advertiser-unfriendly words.

When enforcement lands it is channel-level and unexplained: YouTube Support, verbatim, "cannot manually look up or provide specific video URLs for these automated policy decisions." The appeal asks for script drafts and project files. No AI video tool keeps them — and neither do you: `routers/scripts.py:418` does `video.script_data = {**(video.script_data or {}), "segments": segments, ...}`, so the single best proof of human judgement is overwritten at the instant it is created, at 13 sites.

The second half of this is the strangest finding in the research: every "human-made" product shipped in 2026 is a **public badge** (The Human Made Mark, Verified Human, HUMA), and the evidence says that is backwards. AI-disclosed TikTok posts take roughly 7–8% fewer likes; Schilke & Reimann's 13 preregistered experiments (>3,000 participants) found disclosure erodes trust whether voluntary or required — while YouTube states its own synthetic-content label carries no ranking or monetisation penalty. **The penalty for honesty is entirely human, never machine.** The party that wants evidence of human involvement is a reviewer, in private, during an appeal. Nobody serves that party.

### P5 (smaller, but structurally yours). Code-switched and Indic text

Every tool competing on Hinglish captions is an ASR company — Kapwing, Submagic, CapCut, Captik all start from someone else's audio, so their ceiling is code-switched ASR at 14–16% WER in real conditions. You *generate the text*, and `edge-tts` hands back exact word boundaries. The problem collapses from "transcribe mixed-language audio and guess the script" to "choose a script per word on known text." Same asymmetry on the other eight Indic scripts, where the burned-in caption failures (dotted circles, split conjuncts) only exist in rendered pixels — which is why nobody funded grinds it, and why your Spacing=0 fix was a real discovery. Caveat: at least one founder is already shipping directly at the Hinglish wedge, and the 3–5x CPM gap makes this audience structurally the least able to fund engineering.

---

## 2. WHERE THE ACTUAL NOVELTY IS

Three different things get called novel. They are not interchangeable.

**(a) Nobody has built this.** Scarce, and worth the most. Verified empty in this research: measuring how much of your script *any* model would have written from the same brief; logging the alternatives a creator **rejected**; a pre-registered "what result would make me stop" with a minimum-detectable-effect calculated against the creator's own variance; matching comment n-grams back to the authored line to find which of your sentences humans retyped; extracting the creator's own forward promises ("part 2 next week") out of their scripts; library-minus-forward-plan as a shot list.

**(b) Built, badly, and the gap is real.** Stock retrieval. Visual coherence. Hinglish captions. Indic caption shaping under animation. Audio ducking. These are not novelty — they are craft gaps where you are better equipped than the incumbents. Worth building, worth nothing as a pitch.

**(c) Novel only in combination.** Audio-only ingest **+** format-as-editing-grammar **+** the creator's own larynx surviving into the render. Or: generator **+** publish credential **+** analytics scope. Each component is commodity; holding all three simultaneously is not, and no incumbent does.

**(d) The fourth category, which is not technical at all: things everyone's incentives forbid.** A generator that blocks a render. An analytics tool that says "this difference is noise." A volume tool that says "make fewer videos." These are copyable in a week and will not be copied, because they suppress the headline metric every competitor is priced on. That is a real moat and a soft one. It holds until someone decides the positioning is worth more than the volume — so treat it as a head start, never as a fortress.

What is **not** novel, and you should stop saying so: reordering non-contiguous speech into a short (OpusClip's own engineering page: "we find gold nuggets from different parts of your video and seamlessly combine them"), audio-only ingest (OpusClip's podcast tool takes an MP3), an LLM arranging spoken segments against a narrative framework (Eddie AI's Rough Cut Frameworks), and per-scene visual alternatives (you already ship it at `/segments/{i}/media-options`).

---

## 3. THE IDEAS

### Idea 1 — Hot Mic

**One sentence:** Before it writes anything, the tool asks you three questions about the topic, you talk into your phone for sixty seconds, and the video is built to argue *your* take — with your actual voice audibly in the cut.

**Mechanism:**
1. Trend → three provocations from Gemini, each aimed at what cannot be scraped: friction ("what part of this annoys you?"), private knowledge ("what do you know here a stranger wouldn't?"), stake ("what would you bet happens next?").
2. Record 60–90s. `routers/media.py:26` already whitelists `.mp3/.m4a/.wav`; a 16kHz mono downmix is ~2MB against ~300MB of video, so this works on 6 Mbps 4G with no video upload at all.
3. `transcribe.py` returns per-word timings. **Fix while you are in there:** line 39 passes no `language=`, so Hindi and Hinglish auto-detect and flip-flop. This is a prerequisite, not a detail.
4. One structured LLM pass extracts a **thesis object**: `{claim, the one specific detail, the stake, quotable_spans}` — each span a word-timed range in the raw audio.
5. Script generation is constrained to *argue that thesis* and forbidden from adding checkable claims not in it. Reuse `UNSOURCED_RULES` in `script_gen.py:75`, which exists because an unattended standing order once invented a patch note and a heist.
6. Render: at least one segment plays the creator's **raw audio**, cut on word boundaries. `runner.py::_run_clip` already cuts a range from an upload and uses original audio as the soundtrack, so mixed own-audio + TTS is an extension of a branch that exists, not a new lane. Pad joins with **room tone sampled from the recording's own quietest 500ms**, not digital silence — that one detail is what separates "a person talking" from "a ransom note." Duck the bed with `sidechaincompress`; `assembler.py` currently mixes flat at `volume=0.12` with no ducking anywhere in the file.
7. Optional and unclaimed: select spans to hit the format's declared `words_per_second` (1.2 shayari → 2.8 gaming news) by choosing denser or sparser spans and sizing the gaps, rather than resampling audio.

**Attacks:** P3 directly. P4 sideways (a video containing one specific person's opinion is not "easily replicable at scale"). And YouTube's crude face-on-screen proxy for human involvement, which currently has faceless creators renting hosts on Fiverr.

**Novelty, and who I checked:** Voice-note-to-video is taken — Pictory ("Voice to Video AI") and Mootion both ship it, and both are **narration-first**: you supply the complete narration and they decorate it, which costs you the same time as writing. OpusClip and Eddie AI both do extractive selection from your own speech. What none of them do: extract a thesis from a short take and generate *new* script around it, keep the creator's larynx word-aligned in the output, or generate the elicitation questions from trend discovery plus a format recommendation — which requires the front half of your product.

**Reuses:** `routers/media.py` audio path; `transcribe.py` (`word_timestamps=True`, `words_in_range`); `runner.py::_run_clip`; `tts.synth_script`'s return shape `[{index, audio_path, duration, words}]` at `tts.py:109`, which is the seam — return the same shape and captions, visuals, music and publish all work unchanged; `formats.py` pace; `feedback_notes`; Teach-a-style, which gets better with every take.

**What stops a copy:** honestly, not much for six weeks — the concept is simple. Three things slow it: the seam quality lives in join scoring and room tone, which is ffmpeg/DSP craft and exactly not a JS shop's; the per-creator archive of their own spoken phrasings is unbuyable and worthless to anyone else; and a company whose landing page says "batch 30 videos while you sleep" cannot ask for sixty seconds of talking per video without contradicting itself.

**First version:** one weekend. One endpoint: audio + topic → transcribe → thesis → script that must quote one verbatim span → render with that span as real audio in scene 1. Skip question generation. Render the same topic both ways and look at them side by side. If the human-seeded one is not obviously more *yours*, it dies for two days.

### Idea 2 — The Ledger (log first, fork later)

**One sentence:** An append-only record of every human decision that shaped a video — including the options rejected — which doubles as the appeal evidence and as conditioning for future generations.

**Mechanism:** one table, `decisions(id, user_id, video_id, axis, candidates, chosen_index, rejected, source, latency_ms, created_at)`, hash-chained if you want tamper-evidence (say tamper-*evident*, never tamper-proof — a Postgres chain with no external anchor only makes edits detectable). Wire `record_event()` into the mutation sites that already exist: `routers/scripts.py:418, 447, 497`, `routers/pipeline.py:231–503`, `proof.py:164`. Also log the `feedback` string on `regenerate_segment` — it is a labelled human correction and it is currently discarded. Then, later, the fork: sample 5 hooks, pick the 3 furthest apart, show them, let the creator tap one in eight seconds, condition the rest on the choice. Then retrieve their nearest past decisions by topic embedding as few-shot. Then `GET /videos/{id}/dossier`.

**Attacks:** P4. Also, quietly, P3 — accept/reject pairs are the only labelled data that could ever give Teach-a-style a gradient.

**Novelty, and who I checked:** provenance-as-evidence is shipped for **text** — Grammarly Authorship colour-codes each sentence by typed/pasted/AI-assisted and replays the writing process; Originality.ai's Writing Replay does keystroke-level authorship. Neither records **rejections**, both are text-only, and neither reuses the record to change future output. Nothing in AI video keeps anything.

**Reuses:** `alembic/versions/0010_feedback_notes.py` is 30 lines — the migration is a copy-paste. `services/feedback.py` already proves standing context reaches every generation. `series_tasks.py:251`, `if series.auto_publish and series.channel_id:` — the only place unattended publishing happens in the entire codebase, and therefore the one line where a human-contribution floor goes.

**What stops a copy:** nothing technical. The moat is that **the evidence cannot be backfilled** — only the tool that was in the room can produce it. Which means the value is time-in-position, which means the table ships before the UI, before anyone has decided the product is real.

**First version:** one evening. Migration plus logging on three endpoints, zero user-visible change.

### Idea 3 — Own Share

**One sentence:** After the script is written, generate the same brief four more times in the shadows and measure what share of the runtime any competent model would have produced unprompted.

**Mechanism:** `asyncio.gather` four more `generate_json` calls at temperature 1.0 through `services/llm.py` — these are never shown to anyone. Embed every sentence of the chosen script and of the four shadows. For each chosen sentence, take max cosine against all shadow sentences; above τ it is machine-reproducible. Score = share of **runtime** (weight by `duration_estimate`, which `_finalize` already guarantees) that is *not* reproducible. Cost: five Flash generations plus embeddings. Fractions of a cent.

**Attacks:** P4's measurement gap, and it is the only honest instrument for P3.

**Novelty, and who I checked:** every detector in the market answers "was a machine involved" — Originality.ai, GPTZero, Copyleaks, Pangram — which is the wrong question now that YouTube auto-applies labels from SynthID and C2PA with no ranking penalty. The right question is "could a machine have produced this," and using the model itself as the null hypothesis is unclaimed in any medium I could reach. PrePublish.ai ships a "YouTube Inauthentic Content Script-Risk Checker" from $19/mo, but it scores one pasted script against policy language in isolation and never touches generation. Sampling k generations and measuring self-consistency is established in the hallucination-detection literature; nobody has pointed it at creative output.

**What stops a copy:** the metric, a week. The calibration, longer. The willingness to gate a render, indefinitely — see §2(d).

**First version:** two evenings, entirely offline, no UI, no gate. Pull your last N scripts from Neon, regenerate each brief four times, embed with numpy cosine in a scratchpad, print the Own Share distribution by format. **You will need `embed_texts()` first** — there is no embedding call in the repo, and note `config.py:66` hard-sets `GOOGLE_VERTEX_LOCATION="global"` while embedding models are served regionally, so you need a second client pinned to a region or you will get a confusing 404.

### Idea 4 (cheap, optional) — the serial

Autopilot stops emitting episodes and starts running a show: a bible, a running counter, an open loop left hanging at the end of every upload, a payoff scheduled five videos out. It resolves the apparent contradiction between "vary everything or get demonetised" and "be consistent or nobody returns" — a serial is maximally varied episode-to-episode and maximally consistent as a show.

Do not call it Showrunner: **Fable Studio ships Showrunner Studio**, explicitly "built for serialized stories" with persistent worlds and canon across episodes. The mechanism and the name are taken. What is unclaimed is pointing it at an autopilot on a creator's own channel, driven by their own trends, bound to a format recipe — and enforcing "open by paying off a named prior episode, close by opening a loop" the same way `formats.py:189` already bans hooks and CTAs in shayari.

Why it is worth naming at all: zero migrations (the bible fits in `series.topic_prompt`), zero new scopes, six credits, six evenings — and **you are the test subject**, which no other idea on the distribution side can say. It also converts your weakest shipped feature into your strongest: `series_tasks.py` currently pins format, style, mood, voice and engine and repeats them forever. One free bonus you already own: `ScriptSegment.headline` exists, `captions.py` has a complete ASS style block for it, both `runner.py` and `proof.py` pass it through — and per your own audit no prompt has ever asked for it. A running counter is a fully-plumbed render path you can switch on from the prompt alone.

---

## 4. THE ONE I WOULD BUILD

**Hot Mic.** And the thing that makes it work is a move none of the source material proposed: **use Own Share as its evaluation harness, not as a product surface.**

Run the same topic through both arms — normal generation, and human-seeded — and measure Own Share on each. If the thesis-seeded script does not measurably contain more that a model would not have written, the premise is wrong and you found out in a weekend with a number instead of a feeling. This also kills Own Share's one real risk: as an absolute gate you have to calibrate τ against enforcement labels you do not have, but as a **paired comparison between two arms** you only need τ to be consistent, not correct. You get a gradient to iterate against — the exact thing P3 says the whole category lacks — without needing users, traffic, or a single new OAuth scope.

Why it beat the others:

- **It is startable.** Your own audit says 3 accounts, 6 videos, 1 render. Every idea whose signal is views, comments or retention curves — the retention join, comment mining, matched-pair re-publishing, cross-creator priors — is not wrong, it is **not startable**. Seven of nineteen die on one line of your own documentation. Hot Mic needs no users, no scopes, no verification wait.
- **It attacks the problem that voids the category.** P1 is bigger by headcount, but its ceiling is contractual and half its tooling went commodity this year. P3 is the one where the promise itself is broken, and where a genuine inversion is still available.
- **It is the only defence against the originality crunch that does not depend on measurement you cannot calibrate.** You do not have to detect templating if the video contains sixty seconds of a specific human being having an opinion.
- **It is true to your own line.** "I cannot make them famous, but I could pave an easier and faster path." Sixty seconds of talking replacing an hour of writing-then-rewriting is a faster path that keeps the person in their own work. A tool that removes them entirely is what the platforms are now terminating and what audiences are now discounting.

**The Saturday list, in order, regardless:**

1. **`decisions` table + logging on three endpoints.** One evening. Zero user-visible change. It is the only item here whose cost rises every week you wait.
2. **`language=` in `transcribe.py:39`.** Free, and Hot Mic is unshippable in India without it.
3. **Enforce the constraint you already half-promise.** `script_gen.py:160` tells the model "fix nothing, not even typos" at temperature 0.2 with no server-side check that it obeyed. Token-by-token verification is one evening and makes an existing claim true.
4. **Split `visual_prompt` into `visual_intent` and `retrieval_key`.** No migration — `script_data` is JSONB. Your scene-matching rules now make prompts deliberately specific ("a matte-black armoured hover-bike with a roof-mounted missile pod"), and `runner.py:159` hands that same string to a keyword endpoint. On the `ai_image` lane specificity helps; on the Pexels lane it actively hurts. Same string, two opposite requirements.
5. **Stop discarding the render timeline.** `pexels.fetch_clip` returns `video["id"]` at `pexels.py:82` and `runner.py:160/188/471` throw it away; `used_ids` is a local set destroyed at the end of `run()`. About 40 lines. Four different future ideas need it and the data is unrecoverable once a render ends.

---

## 5. WHAT I REJECTED, AND WHO ALREADY BUILDS IT

**Anything gated on an audience you do not have.** The retention-curve join, comment mining, matched-pair re-publishing, pooled cross-creator priors, comment-quotation-as-label. Good ideas. Build them the month you have users, not now.

**Matched-pair re-publishing specifically, and loudly.** Its own safety cap — make the original private so it does not compete with its variant — needs `videos.update`, i.e. `youtube` or `force-ssl`, the broadest scope you do not hold, on an app whose `youtube.upload` verification is still outstanding. And `runner.py:734` is `shutil.rmtree(workdir)`, so the per-segment files that make the cheap re-render possible are destroyed after every render. Without the cap the failure mode is a re-upload farm. Worst risk/reward here.

**Voice-memo-to-short as a standalone.** OpusClip's own page says it "finds gold nuggets from different parts of your video and seamlessly combines them" and its podcast tool accepts audio-only MP3; **Eddie AI** ships Rough Cut Frameworks where an LLM arranges spoken segments per narrative beat and explicitly does not generate dialogue. Non-contiguous reordering and audio ingest are both shipped, free tier included. Fold the engineering into Hot Mic; drop the claim.

**The owned-footage index.** Went commodity this year: **Video Asset Manager** ($99 one-time) has a "Video Director" where you paste your script and get AI-ranked clips from your own library; **Jumper** does on-device semantic search for creators; Adobe shipped **Media Intelligence** into Premiere; **TwelveLabs** launched Rodeo. The back-catalogue premise is also not real — there is no API to download your own uploads, and `media.py:27-28` caps you at 500MB and 10 assets per user "until object storage exists." It is a storage project before it is a retrieval project. The one unclaimed piece is the reversed arrow: library minus forward plan equals a shot list. Keep that in a drawer.

**The EU enforcement corpus.** The day-zero check was already run against live dumps: `content_id_ean` is empty in 100% of 181,142 rows, so a statement can never be joined to a video; category is 100% `OTHER_VIOLATION_TC` with empty language, so there is no slicing signal; the archive paginates across ~1,082 dates and is fully backfillable, so there is no history moat; TikTok files zero monetary decisions. What survives is a public chart and a DSA Article 17 letter generator — a marketing asset, not an answer to your question.

**Content decay.** **ContentRefreshAI** already scans posts for outdated facts and prices, verifies with live search, and saves as drafts until approved — for WordPress text. **VideoVFY** and **VerifyReels** already extract and check claims from arbitrary videos, which undercuts the cost-asymmetry argument. And the headline action is impossible: you cannot replace a published YouTube file.

**Self-similarity scoring as a standalone.** Overlaps Own Share, and **PrePublish.ai** is already shipped and indexed in that slot.

**Comment-derived topic queues.** At least seven shipped products, several free — CommentShark ("How to Find Unanswered Questions in Your YouTube Comments"), BeyondComments, Creator Brief, CreatorBlade, ReplyTide, TubeAnalytics, CreatorComment. The one unclaimed half is mining your *own* forward promises out of your own scripts, which needs zero API calls. Cheap, keep it.

**The closed generate-measure-learn loop.** **Creatify** ships exactly this architecture — generate at volume, tag, A/B, "Performance Agent" — for paid ads. Same machine, different metric. Nobody does it for organic retention, but do not present it as an unclaimed invention.

**Thumbnails.** You asked for novelty defensible by something other than taste; thumbnails are defensible by nothing else, and the space is crowded. The adjacent half of that same quote — fact-checking anything with a number — is the interesting one.

**Cross-posting, scheduling, hashtags, best-time-to-post, DM auto-reply.** Commodity, no data asset, no structural advantage. The APIs are open to everyone equally. And comment/DM automation is the literal "minimal human input" signature platforms are now punishing.

---

## 6. THE HONEST CAVEAT

**Two premises in the source material could not be verified and should stop being repeated.** YouTube's A/B-testing-excludes-Shorts claim (the help URL 404'd on two attempts) and the "~99.9% of Shorts views never render a thumbnail" figure (no reachable source). Both are load-bearing for the "distribution *is* the edit" argument. Verify before building on them.

**Your own audit already flagged the enforcement numbers.** The "16 channels / 4.7 billion views" figure traces to SEO content-marketing blogs, several misdating the policy by a year. The *policy language* is verified from YouTube and Tubefilter and does support the argument. The magnitude does not. Do not repeat it.

**One research lens ran with an exhausted search budget** and relied on direct page fetches rather than keyword sweeps. Absence of evidence there is weaker than elsewhere — that is where I would expect a missed competitor.

**The consumer-sentiment numbers** (60%→26%, 83%, 75%) each come from a single vendor survey. Directional. Do not build a pitch on them.

**Reddit evidence is self-selected complaint data.** People who solved the problem do not post about it. Volume of complaint is not proof of unmet demand.

**Nobody outside YouTube can confirm a dossier improves appeal odds.** The Ledger must be sold as "the evidence they ask for, assembled," never as an outcome.

**Three things could make the Hot Mic recommendation wrong:**

1. **The seam.** Phone audio in a real room spliced against studio-clean TTS is fiddly — noise floor, EQ, level, and worse, *prosodic* discontinuity, which a listener notices instantly without being able to name it. If it cannot be made inaudible at phone quality, this is a demo and not a product. Budget the f0 continuity scorer as open-ended work, not a weekend; `beats.py` proves you can do it, not that it is quick.
2. **The premise inverts if your own takes are worse than the draft.** Plenty of people genuinely write better than they speak. Test it on twenty of your own recordings and be willing to read the answer.
3. **It shrinks the addressable user** from "anyone who wants volume" to "anyone willing to have an opinion." That is a smaller market. It is also the entire point, and it is the half of the market platforms are not currently terminating.

**And the structural caveat over everything:** this ranking is a function of one fact — you have almost no users. If you had 200 next month, it inverts. The retention join and the analytics loop become the right build, the pooled priors become computable, and Hot Mic becomes a feature inside them. Re-run this decision the day that changes, and do not let a plan written for a zero-user constraint outlive the constraint.

---

## Prior-art critic

## The fact that reorders the list

Three verified constraints collapse 19 ideas to about 6 real ones:

1. **3 accounts, 6 videos, 1 render** (his own audit, `docs/kliptos-vault/Full Audit 2026-09-10.md:60`). Every idea whose signal comes from views, comments, or retention curves is not wrong — it is **not startable**. That is Jitter, Backtalk, Second Cut, Retype, Hindsight, Called Shot's pooled prior, and Owed's comment half. Seven of nineteen, gone on one line of his own documentation.
2. **No embedding infrastructure exists.** I grepped `backend/app` for embed/pgvector/cosine/text-embedding: three hits, all false positives in `link_ingest.py`. Nothing New, The Fork's divergence step, Divergence, Larder and Owed all silently assume it. It is one shared ~30-line helper (needs a second `genai.Client` pinned to a region — `config.py:66` hard-sets `GOOGLE_VERTEX_LOCATION="global"` and embedding models are served regionally). Build it once, first.
3. **Every new OAuth scope costs an owner action he has not yet spent.** `services/youtube.py:22` is still `[youtube.upload, youtube.readonly]`, and `youtube.upload` verification is still listed as outstanding. Adding a scope after submission restarts review. Any idea needing `yt-analytics.readonly`, `youtube`, or `force-ssl` is gated behind a weeks-long wait he has not started.

---

## The three to put in front of him

They are not three bets. They are **one product with three independently killable parts**: the human supplies something only they have (Hot Mic), the system measures whether it mattered (Nothing New), and the record of it survives (The Fork). This interlock is in the source material, not invented — Chain of Custody names Hot Mic's output as its strongest artefact, and Nothing New's gate names voice as the answer channel. Pitch it as one thesis: **the product's job is to extract and preserve the part of a video only you could have made.** That is the only positioning in this whole set that the 2026 crunch makes stronger rather than weaker.

### 1. Hot Mic — human input as the seed, not the correction

- **Novelty: real, but narrower than pitched.** Voice-note-to-video is taken (Pictory, Mootion) and they are narration-first. What is unclaimed: extracting a *thesis object* from a 60-second take and constraining generation to argue it; the creator's actual larynx surviving word-aligned into the render; and provocation questions drawn from trend discovery plus a format recommendation — which only he has. Two of three survive scrutiny; say so.
- **Pain: blocking.** "AI writes it but it doesn't sound like me, so I rewrite half and save no time" is the reason the entire style-transfer category plateaus. It also hits the trust collapse (60% to 26%) and the templating test in the same move.
- **Compounds: yes, quietly.** Every take is a corpus of one person's actual spoken phrasings. Worthless to a competitor, unbuyable, feeds Teach-a-style. Modest but real.
- **Kill test: one weekend.** Same topic rendered both ways, side by side. If the human-seeded one isn't obviously more his, it dies.
- **The gate he must clear first:** `transcribe.py:20` runs `WhisperModel("base", device="cpu", compute_type="int8")` and never passes `language=` — it only reads `info.language` back from auto-detect. Unusable for Hindi, worse for Hinglish. For an India-first product this is a prerequisite, not a detail. Forcing the language hint is free; anything above `base` on that VPS is not.

### 2. The Fork — log the decisions before building the UI

- **Novelty: real on one axis only.** Grammarly Authorship and Originality.ai Writer Replay already ship provenance-as-evidence for text. Recording **rejected alternatives** is unclaimed in any medium, and reusing them as generation conditioning is unclaimed in this category.
- **Pain: blocking, and currently self-inflicted.** I confirmed 13 sites doing `video.script_data = {**(video.script_data or {}), ...}` with no history table anywhere (`routers/scripts.py:418, 447, 497`; `routers/pipeline.py:231-503`; `proof.py:164`). The single best proof of human judgement is overwritten at the instant it is created. `regenerate_segment` receives a labelled free-text correction and discards it.
- **Compounds: strongest structural position in the set.** A competitor can add the table next quarter; they cannot have eighteen months of it. Only the tool that was in the room can produce the evidence — which means the value is *time in position*, which means the table ships before anything else.
- **Kill test: none needed for the first half.** One evening, one migration (copy `alembic/versions/0010_feedback_notes.py`, 30 lines), logging on three endpoints, zero user-visible change. **This is the first commit regardless of which bet he picks**, because it is the only item on the list whose cost rises every week he waits.
- Fold Chain of Custody's `auto_publish` gate in — it is one line at `series_tasks.py:251` and it is the same idea.

### 3. Nothing New, No Render — measure what a machine would have written

- **Novelty: genuinely real, and the most novel mechanism in the whole exercise.** Every detector asks "was a machine involved" — the wrong question once platforms auto-label with no ranking penalty. Using the model itself as the null hypothesis, k shadow generations of the same brief, and scoring the share of *runtime* a machine would have reached for unprompted, is unclaimed in any medium. Shipping it as a **gate on the render button** is the part no volume-priced competitor will ever copy.
- **Pain: painful, not yet blocking** — and it is the instrument for the thing the crunch is actually about.
- **Compounds: weakly on its own**, strongly once joined to the Fork ledger and any retention data he eventually gets. Be honest: the metric is copyable in a week; the calibration is not.
- **Kill test: two evenings, entirely offline, no UI, no gate.** Best kill-to-cost ratio here — and unlike almost everything else on the list, the *mechanism* test does not need users. Only the per-format thresholds do.
- **Real risk, correctly identified:** τ. Sentence cosine will not separate "same claim" from "same shape, different claim." Budget for claim extraction as the honest fix; that is research-shaped.

---

## Reject, and why

**Everything gated on an audience he does not have** — Jitter, Backtalk, Second Cut, Retype, Hindsight, Called Shot. Good ideas, unstartable. Jitter and Hindsight are what he builds the month he has users; they are not answers to "where is novelty available now."

**Second Cut specifically, and loudly.** Its own safety cap (make the original private so it does not compete with its variant) needs `videos.update`, i.e. the broadest scope he does not hold, on an app not yet verified for the one he does. `runner.py:734` is `shutil.rmtree(workdir)` — the per-segment files the cheap re-render depends on are destroyed after every render. Without the cap the failure mode is a re-upload farm, which is exactly what platforms punish. Worst risk/reward on the list.

**Enforcement Weather.** The day-zero check was already run against live data and two of its four promises are dead: `content_id_ean` is empty in 100% of 181,142 rows so a statement can never be joined to a video, and category is 100% `OTHER_VIOLATION_TC` with empty language so there is no slicing signal. The history moat is confirmed backfillable (1,082 dates downloadable today). TikTok files zero monetary decisions. What survives is a public chart page and a letter generator — a marketing asset, not an answer to his question.

**Larder.** The librarian half went commodity this year (Video Asset Manager ranks your own clips against a pasted script, $99 one-time). The back-catalogue story is not real — there is no API to download your own uploads, so it means manual re-upload into a rail capped at `MAX_SIZE_BYTES = 500MB` and `MAX_ASSETS_PER_USER = 10` ("until object storage exists"). It is a storage project before it is a retrieval project.

**Tape and Say It Once.** Collapse both into Hot Mic. OpusClip's own engineering page says it finds gold nuggets from different parts of your video and combines them, and its podcast tool accepts audio-only — so non-contiguous reordering and audio ingest are both shipped, free tier included. The demo is not novel to anyone who has seen it, and the remaining engineering risk (prosodic discontinuity at seams) is unbounded.

**Half-Life, Shift, Divergence, Owed.** Half-Life needs a back catalogue he doesn't have and its headline action (re-cut the bad scene) is impossible — you cannot replace a published file. Shift is a retention mechanic that needs a dense queue. Divergence overlaps Nothing New and lost ground to PrePublish.ai. Owed's comment half is shipped by seven free tools.

**Showrunner is the one runner-up worth naming.** The mechanism and the name are taken (Fable's Showrunner Studio), so the novelty is positional — but it is six evenings, zero migrations, zero new scopes, six credits, and **he is the test subject**, which no other distribution idea can say. It converts his weakest shipped feature (autopilot, which currently emits exactly the pattern YouTube terminates) into his strongest. If the top three stall, this is the cheapest real move on the board. Rename it.

---

## Four free wins to take regardless of which bet he picks

1. **Enforce the no-writing constraint he already half-promises.** `script_gen.py:157` tells the model "fix nothing, not even typos" at temperature 0.2 with zero server-side check that it obeyed. Token-by-token verification is one evening and makes an existing marketing claim true.
2. **The decisions table** (one evening, above). The asset only accrues with calendar time.
3. **Split `visual_prompt` into `visual_intent` and `retrieval_key`.** His scene-matching fix now makes prompts deliberately specific, and `runner.py::_visual_for_scene` hands that same string straight to Pexels as a keyword query. The fix for coherence is actively degrading retrieval, in the code, today. No migration — `script_data` is JSONB.
4. **Stop discarding the render timeline.** `pexels.fetch_clip` returns the id and `runner.py:160/188/471` throw it away. ~40 lines. Jitter, Second Cut, Divergence and Larder all need it, and the data is unrecoverable once a render ends.

---

Links: [[Is The Idea Worth It]] · [[Full Audit 2026-09-10]] · [[Visual Quality Diagnosis]] · [[Pitch]]
