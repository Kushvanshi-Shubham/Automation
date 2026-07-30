# Creation Workflow v2 — "Not everyone wants a narrated story"

> Owner insight (2026-07-30): a music trend shouldn't force a narration video. AutoShorts only
> does stories — that's their ceiling, and our opening. Users must choose WHAT they're making
> before we decide HOW to make it.

## The core change: an OUTPUT TYPE step

```
ENTRY                    OUTPUT TYPE              SCRIPT STAGE           ASSET/RENDER STAGE        PUBLISH
─────                    ───────────              ────────────           ──────────────────        ───────
Trending topic     ┌──▶  📝 Script only     ───▶  Studio (edit) ───────▶ (none — copy/export) ───▶ n/a
Custom idea        │                                                     
Own script    ─────┼──▶  🎙️ Narrated short  ───▶  Studio (edit) ───────▶ TTS+visuals+captions ───▶ YT now, IG next
                   │         (today's flow)                              +music → mp4
                   │
                   ├──▶  🎵 Visual short    ───▶  Studio (text-on-     ─▶ visuals+captions,     ───▶ YT/IG
                   │         (no narration)       screen lines)          NO voice, music-forward
                   │                                                     (user adds trending audio
                   │                                                      natively in YT/IG editor*)
                   ├──▶  🖼️ Image post      ───▶  caption text     ────▶ AI images (Gemini      ───▶ IG-first
                   │         (carousel)                                  image models)
                   │
                   └──▶  🎬 Premium AI video ──▶  Studio (edit,    ────▶ Veo/HiggsField/Flow   ───▶ YT/IG
                             (Pro)                per-segment            per segment, variable
                                                  engine choice)         credits
```

\* Licensing reality: we can never bake trending copyrighted music into rendered files server-side.
The compliant (and actually algorithm-preferred) path: render the visual short silent/with our CC
music, user attaches the trending sound inside the YouTube/Instagram editor at post time. UI copy
must explain this.

## Where the script is written / edited (answers the "confusing part")
- The script stage stays EXACTLY where it is (Studio) for every output type — it's the spine.
  What changes per type is what the script BECOMES: narration audio (narrated), on-screen text
  (visual short), image prompts (image post), or plain deliverable text (script-only).
- Video EDITING is not a timeline editor (we are not CapCut). Editing in Kliptos =
  (a) edit segment text, (b) edit visual prompt, (c) regenerate segment, and — future —
  (d) per-segment ENGINE choice (stock / AI image / AI video via Veo/HiggsField/Flow labs)
  with per-segment re-render. That's the "mixed class of collections" the owner described.

## Credit matrix (draft — final at billing milestone)
| Output type | Engine | Credits | Notes |
|:---|:---|:---|:---|
| Script only | LLM | **0** (rate-limited on Free: 5/day) | Costs ~$0; acquisition hook |
| Narrated short | Pexels | 1 | today's product |
| Visual short (no voice) | Pexels | 1 | same infra minus TTS |
| Image post (4 images) | Gemini image | 1 | on BYO key: fee-discounted at billing |
| Narrated/visual short | hybrid Veo | 8–10 | S3, needs Veo integration |
| Premium AI video | full Veo / HiggsField | 25–30 | S3, Pro-gated |
- BYO-key renders: platform fee model (reduced credits) — defined at billing milestone.

## BRD alignment check (owner asked)
Master Plan v3 spine: trends → script → render → publish → monetize. **Unchanged.**
V2 generalizes ONE box (render) into output types — an extension, not a pivot. OneFlancer
(S3/S4) untouched. The plan's "Veo/HiggsField engines" phase maps 1:1 to the Premium type here.

## Priority order (owner-set, 2026-07-30)
1. **Output-type step + Script-only mode** — small build, immediately widens the product
2. **Visual short (no narration)** — pipeline variant: skip TTS, script lines become timed
   on-screen text, music at full presence
3. **Instagram** — owner: "Instagram is the basis for connecting/posting."
   Reality: official Graph API Reels publishing requires IG Business/Creator account linked to a
   FB Page + Meta app with `instagram_content_publish` + **App Review (weeks)**.
   → ACTION NOW: create Meta developer app + submit review in parallel (same playbook as the
   still-pending `youtube.upload` verification). Build the publish code behind a flag meanwhile.
4. **Image generation** (Gemini image models — also powers thumbnails later)
5. **Premium engines** (Veo/HiggsField/Flow labs) with variable credits — Pro-gated
6. **Billing** (credits purchase + BYO platform fee) — after free-version flows are proven

## Explicitly deferred
- Thumbnails (folds into #4 image generation)
- Timeline-style editing (not our product)
- Trending-audio ingestion (licensing; solved by native-editor attach flow)
