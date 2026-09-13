# Editing Grammar — making a format actually look like its format

> 11 September 2026. The layer under [[Creation Workflow v2]]. Shipped as `72bc642`.

## The problem, in one line

Every format rendered **identically**. Hard cuts, one Ken Burns speed, three-word captions. Only the palette, the caption style and the music mood changed.

A shayari and a breaking-news update went through the *same ffmpeg filtergraph*. That is the real reason output felt machine-made regardless of which of the nine formats you picked — and no amount of better script writing was ever going to fix it, because the problem was downstream of the words.

## The owner's thesis, which this implements

> "the next part was to make sure that content type totally in that way — like montage gaming video contains phonk music with their headshot or best moments on beat and video editing. for shayari it totally different. slow down, speed, bg, music."

He is right, and this is the strongest idea in the project. **A gaming montage and a shayari reel are not the same video in different colours.** They differ in:

| | shayari | gaming montage |
|---|---|---|
| shot length | 6s, held | 0.4s, on the beat |
| who leads the audio | the voice | the music |
| captions | a line held still | words popping |
| motion | almost none | hard push |
| footage | sourced | the creator's own |

Those are five different machines, not five colour presets.

**Why it is defensible:** this is not a model capability. A smarter LLM does not hand you *"cut on the 2nd and 4th beat with a 120ms whip."* It is craft knowledge from someone who watches this stuff. Models improve every six months; taste does not arrive in an update.

**What nobody else does:** invideo, Pictory, Fliki, Klap and Opus all produce exactly one video — stock footage, slow zoom, captions in the middle, generic bed. Ask any of them for a montage, a poem, or a news update and the *editing* never changes.

## What shipped

A format carries an `editing` recipe, travelling the same `render_defaults()` → `script_data` road as `visual_style` and `words_per_second`:

- **`motion`** — `kenburns` (the untouched default) · `drift` · `punch` · `still`
- **`transition`** — `cut`, or `soft` with a `fade` size
- **`words_per_cue`** — how much of a line a caption holds

Recipes so far:

| format | motion | transition | words/cue |
|---|---|---|---|
| **shayari** | drift | soft 0.3s | 7 |
| **motivational** | drift | soft 0.2s | 4 |
| **breaking_news** | punch | cut | 3 |
| **gaming_update** | punch | cut | 3 |
| *everything else* | kenburns | cut | 3 |

Shayari holds seven words because **three-word chunks destroy a couplet's shape** — a *sher* is read a line at a time, and chopping it is the same class of mistake as narrating poetry at news pace.

## Three decisions worth not re-litigating

**1. The defaults ARE the old behaviour, byte for byte.** A `cut` format emits *no fade filter at all* — not a zero-length one. Videos made before this feature have no `editing` key and render exactly as they did. Test-pinned, including the original Ken Burns numbers (`0.0009`/frame, ceiling `1.18`).

**2. `soft` is a per-shot fade, deliberately not an xfade chain.** A true cross-dissolve shortens the video by `(n-1) × d` while the narration keeps its full length, and nothing downstream would re-sync them. Per-shot fades cost no duration and cannot desync. Verified: a soft shot and a hard cut are the same length to within 0.1s.

**3. Two dicts, two files, same keys.** `formats.MOTIONS` holds the human labels; `assembler.MOTION_CURVES` holds the numbers. A motion offered in the UI with no curve behind it falls back to kenburns **silently**. A test keeps the key sets equal.

## The mistake, recorded on purpose

The first version of the tests **passed completely while two of the four settings reached nothing.** The recipe existed, the functions accepted the argument, and the runner never passed it.

That is the *identical* failure to the bring-your-own-script bug fixed the same night, four hours earlier — settings computed correctly, receiver ready, no wire between them.

The fix: extract `runner._assemble_segment()` so each setting is driven through its real call site, then reintroduce every break one at a time and confirm the test fails. Six of six now do.

**The lesson, which generalises:** a test that checks both ends of a wire proves nothing about the wire.

## Why this matters more than shayari

The point is not that shayari now drifts. It is that **the next format is a dict entry plus taste, rather than new code.** That is what makes the one-format-at-a-time plan affordable on 4–5 evening hours — see [[Format Launch Order]].

## Not done

- **Visuals are unchanged.** Shayari still draws from the same lane it always did. If the pictures are the weak part they are still the weak part — a separate problem from how the video is *cut*, and the one after music.
- **No per-scene retiming.** Shot length is still driven by narration length, so "0.4s cuts on the beat" exists only in the montage lane.
- **No render has gone end to end through this yet.** Everything above is the pipeline being correct in isolation.
