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
| **shayari** | drift | cut (see below) | 7 |
| **motivational** | drift | cut | 4 |
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

## The pause was in the wrong place — and then the wrong shape

Two owner verdicts, two days apart, both correct, both about the same thing.

**First: "too slow, the gap is weird — if you download audio of shayari you will understand it."**

Both halves were one mistake. `words_per_second: 1.2` asked edge-tts for −52% and got clamped to its **−45% floor** — the maximum slowdown the engine allows, on every shayari ever rendered. That is a slowed recording, not a recitation. Then the gap went into the *picture* as a fade, where it reads as a glitch because the voice never actually stops.

Real shayari is spoken near normal speed and the poetry lives in the **silence**. So the script budget (how many words fit) was split from `speech_wps` (how fast they are spoken, 2.2 → −12%), and the silence moved into the audio while the picture just holds. The rejected dip-to-black was pulled from every format.

**Then: "every shayari are never same — sometimes long gap sometimes short, the deep breath, heavy hearts."**

Also right, and measurable. 831 pauses across 37 minutes of Creative-Commons live mushaira from archive.org, measured with ffmpeg `silencedetect`:

```
min    p25    median   p75    p90    max
0.25   0.38   0.53     0.86   1.26   7.85   seconds
```

**The spread is 3.3×.** A fixed 0.55s is not a rough approximation of that — it has zero spread, the one property the real thing most obviously has. And **a pause longer than twice the median lands about every third pause** (15% and 12%, found independently in both usable recordings), which with one couplet per segment falls exactly where a sher ends.

Crucially there is **no metronome** — autocorrelation is weak at every lag (0.06–0.31), so a rigid short-short-LONG would have been wrong. `services/rhythm.py` therefore scales each silence by how the line ends (a danda is held, a comma runs on), its length, its position (the run-up to the closing sher is the longest in the piece; nothing follows the final line) and the mood — which was already stored on the video and had never reached the narration.

Variation is hashed from the line, not random, so a re-render is identical. Full numbers in the `kliptos-recitation-rhythm` memory.

**What the measurement does not give us:** *why* any individual pause was long. That needs the audio aligned to its text. The four factors are judgement checked against the overall shape — retune by listening, not by reading numbers.

## Why this matters more than shayari

The point is not that shayari now drifts. It is that **the next format is a dict entry plus taste, rather than new code.** That is what makes the one-format-at-a-time plan affordable on 4–5 evening hours — see [[Format Launch Order]].

## Not done

- **Visuals are unchanged.** Shayari still draws from the same lane it always did. If the pictures are the weak part they are still the weak part — a separate problem from how the video is *cut*, and the one after music.
- **No per-scene retiming.** Shot length is still driven by narration length, so "0.4s cuts on the beat" exists only in the montage lane.
- **No render has gone end to end through this yet.** Everything above is the pipeline being correct in isolation.
