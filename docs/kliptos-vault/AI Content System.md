# AI Content System

Owner direction (2026-08-04): build the "personal AI reel factory" pattern (reference video: an agent + HeyGen + style-learning + feedback file) INTO Kliptos as product features. Trend discovery already beats his input step; these four close the rest of the loop.

## Shipped — commit `dfdb023` (2026-08-04)

### 1. Create from a link
- Paste a YouTube video / article / launch-post URL in Create → script is written from the page's extracted text. Optional "angle" field.
- `app/services/link_ingest.py`: SSRF-guarded (private/loopback IPs, weird ports, redirect hops re-validated), 2 MiB body cap, 6000-char reference cap. YouTube resolves via the official Data API (title/channel/description/tags). **No media is ever downloaded from third-party links** — the creator-owned-only rule (see [[Strategy - Intent Platform]]) holds.
- Scenes can pin the creator's own uploaded footage: `asset_id` + `asset_start` per segment; renderer cuts that piece (`assembler.cut_source`) instead of Pexels. Studio swap panel grew a "Your footage" section.

### 2. Feedback memory (self-improving loop)
- Preview page card "For next time": short standing notes, scoped to the video's format or to everything.
- Stored in `feedback_notes` (migration 0010), appended to EVERY future script generation — interactive and series autopilot both. `/feedback-notes` CRUD, 30 notes max, newest 8 reach the prompt.

## Shipped — commit `019819c` (2026-08-05)

### 3. Teach a style
Upload 2–20 of your reels (existing Footage flow — already Whisper-transcribed) → `style.learn` task mines pace/hooks/transcripts → one LLM pass produces a recipe + caption/music/tone defaults → appears in Create as a personal format (`user:<uuid>`). Table `user_formats` (migration 0011), `/styles` router (max 5 per user), `/dashboard/styles` page with Create bay tabs (Studio | Your styles). Upload-only by design: Kliptos never scrapes reels. ⚠️ Needs a live run with real reels — upload 2+ and teach one.

### 4. AI presenter (HeyGen) — scaffold shipped, lane pending
"heygen" is now a BYO-key provider (encrypted like the rest, live-validated against the HeyGen API) and `services/heygen.py` carries the generate→poll→download client. ⚠️ OWNER: get a HeyGen account (avatar + voice clone) — then the presenter option lands in the studio rail with credit pricing above stock renders (see [[Pricing]]).

## Design constraints that shaped this
- Legal: reference TEXT extraction is fine; downloading third-party video is not. User-supplied uploads are the only media ingest.
- All prompt guidance funnels through `custom_instructions` — link text, format recipes, and feedback notes stack in one place.
- Segment schema is a whitelist: any new per-scene field must be added to `ScriptSegment` or it silently drops on save.
