# KLIPTOS REDESIGN — PHASE 0, PART 2: PHILOSOPHY, CONCEPTS, DIRECTION

> Deliverables 5–15 of the brief: product philosophy, IA, navigation, per-surface concepts (3 each,
> scored), motion system, design language, tokens, journeys, phasing. **No code until approval.**

---

## 1. New product philosophy — first principles

The question is not "how should this page look." It is:

> **What is the fastest possible way for a creator to make a viral short?**

Answer, from our own data: *see the right signal → commit to it → amend what the machine drafted → approve → it airs.* Five verbs. Everything else is furniture.

The second question decides the identity:

> **What IS Kliptos, physically?**

It is a **production line**. Real stations, real telemetry, real objects (scripts, reels, clips) that move through it. Today we hide the line behind forms. The redesign exposes it.

**Philosophy: THE INTERFACE IS THE FACTORY FLOOR.**
Not a website about a studio — the studio. Users don't navigate pages; they move along a line. Work doesn't "load"; it **travels**. The brand is the motion of things being made.

---

## 2. The core metaphor — three candidates, scored

### Candidate A — "MISSION CONTROL" (broadcast control room)
One dense fixed screen: monitor wall, signal feeds, status boards, everything visible at once.
- Originality ◐ (mission-control dashboards exist in dev-tools) · Learnability ◐ (dense) · Speed ● · Scalability ◐ (fixed screen fights growth) · Brand ◐

### Candidate B — "THE LINE" (spatial production pipeline) ⭐ RECOMMENDED
The entire app is **one continuous horizontal space** with five fixed stations. A short is a physical object that visibly travels left→right through them. Navigation is *moving along the line* (keys 1–5, transport bar, or lateral travel). There are no pages — there are places.
- Originality ● (no shorts tool, and few apps anywhere, are built this way) · Learnability ● (the metaphor teaches itself: things move rightward) · Speed ● (five keys, one axis) · Accessibility ● (stations are still linear DOM regions; motion-reduced = station cuts) · Scalability ● (new capability = new bay on an existing station, or a new station) · Brand ● (a screenshot of an object mid-conveyor is unmistakable)

### Candidate C — "THE RADAR" (signal instrument as the whole app)
Everything orbits a live trend radar; production states are satellites around it.
- Originality ● · Learnability ◐ · Speed ◐ (spatial hunting beats lists only for discovery, hurts everything else) · Scalability ○ (editor/billing/settings strain the metaphor) · Brand ●

**Decision: B is the spine; C is absorbed as the instrument inside Station 1** (discovery deserves the radical treatment — it's our differentiator — but the whole app shouldn't be a radar).

---

## 3. Information architecture — THE LINE

Five stations plus two overlays. **Every existing route maps here; nothing is removed** (§8 table).

```
①SIGNAL──────②DESK──────③STAGE──────④RAIL──────⑤AIR            overlays: ⌘K CONSOLE · VAULT
 the radar    the script  the scene    the moving   published +
 field where  bench where  bay where    conveyor —   on-air board:
 trends       drafts are   footage,     renders      channel state,
 appear as    amended      voice,       visibly      publish record,
 live blips   line by      captions &   travel the   analytics
 with an      line         recipe are   5 real       instruments,
 opinion                   staged       stages       the archive shelf
```

- **①SIGNAL** = today's Topics (+ harvest, niches, sources, script-only, own-idea intake)
- **②DESK** = Studio's script half (segments, regenerate, BYO script, language/tone/model/instructions)
- **③STAGE** = Studio's production half (formats, media pinning, voice, captions, aspect) + Clips staging
- **④RAIL** = live render conveyor (all in-flight work incl. autopilot + clip cuts + publishing) — the WS telemetry finally gets the starring role
- **⑤AIR** = library + uploads + analytics + publish record; the archive shelf lives at its far end
- **CONSOLE (⌘K-first overlay)** = settings, keys, channels, billing/ledger, profile, series management — *summoned, not visited*; also fully reachable as a drawer for non-keyboard users
- **VAULT (overlay shelf)** = source footage + highlights (Clips' asset side), pull-down into ③

The landing page becomes **the factory with the lights on**: not a hero — a live, slowly-operating miniature of the line itself, with real renders riding it. Marketing = watching the machine.

---

## 4. Per-surface concepts — three fundamentally different models each

*(chosen concept marked ⭐; scoring axes: Originality/Learnability/Speed/A11y/Scale/Brand)*

**NAVIGATION**
1. ⭐ **The Transport Bar** — a fixed bottom strip styled like an editing console's transport: five station segments with live counts and stage-glow, a playhead marking where you are; click/scrub/keys 1–5 to travel; doubles as global status. Nothing like a navbar; it is simultaneously nav + system state. (●●●●●●)
2. Radial command ring on long-press (○ learnability, mobile-hostile)
3. Zoomable infinite canvas (● originality, ○ a11y/scale — rejected as gimmick)

**DISCOVERY (Station ①) — the differentiator gets the radical treatment**
1. ⭐ **The Signal Field** — a dark scope where each trend is a **blip**: angle = niche sector, radius = freshness (hot drifts toward center), size = score, tint = recommended-format family; blips *breathe*; hover = dossier (title, why, format opinion, cost); **pull a blip onto the intake rail** to commit it to the line. A parallel "wire" list (toggle: `FIELD / WIRE`) preserves the fast scanning path and accessibility. (●◐●●●●)
2. Idea River — trends float past on a slow current, grab as they pass (memorable, but punishes slow readers)
3. Heat matrix — niches × momentum grid (fast, but still a table wearing paint)

**DASHBOARD**
1. ⭐ **There is no dashboard.** You arrive standing at the station where your attention is owed (something READY → arrive at ④/⑤; otherwise → ①). The transport bar is the overview. "Dashboard" was a symptom of pages; the line replaces it. (●●●●●●)
2. Mission wall (fixed monitor grid) — rejected: reintroduces mission-control staleness
3. Activity map — rejected: reporting, not doing

**EDITOR (②DESK + ③STAGE)**
1. ⭐ **The Light Table** — scenes are **film frames on an illuminated strip** (width = duration, thumbnail = pinned/auto footage, caption preview burned onto the frame); select a frame and the bench beneath it opens: the line of script, its visual direction, its footage tray, its timing. Recipe (format/voice/captions/aspect) is a **rack of physical toggles** on the bay wall, not dropdowns. BYO-script = feeding pages into the bench. (●●●●●●)
2. Node graph editor — over-powered for linear shorts; learnability ○
3. Teleprompter-first (script scrolls, visuals attach in margins) — beautiful for writing, weak for footage work; absorbed as DESK's *focus mode*

**RENDER / PROGRESS (④RAIL) — the signature moment**
1. ⭐ **The Conveyor** — each in-flight short is a **reel object on a rail** passing five physical gates (VOICE, VISUALS, ASSEMBLY, MUSIC, READY); the WS telemetry drives its actual position; gates light as the reel passes; failure = the reel is shunted to a **refund siding** (credit visibly returns). Multiple reels queue on parallel rails; autopilot reels arrive wearing a series tag. *This animation is the brand.* (●●●●●●)
2. Percentage instrument cluster — gauges are pretty but static
3. Log-stream terminal — honest but joyless

**LIBRARY (⑤AIR archive)**
1. ⭐ **The Shelf** — published work as **spines on a shelf** (spine height = duration, spine color = format family, LIVE spines glow faintly); pull one out to face it (player + record + metadata). Dense, scannable, zero-card. (●●◐●●●)
2. Film-strip timeline wall (chronological strip) — beautiful, weak at scale
3. Drawer archive (labeled pull-out drawers per format/series) — good, slower

**ANALYTICS (⑤AIR instruments)**
1. ⭐ **The Accuracy Scope** — analytics framed as *did the machine's opinions work?*: signal→outcome traces (this trend, this format, this result), a format leaderboard drawn as ranked horizontal signal strengths, honest "—" where the reporting scope isn't granted yet. Story instruments, not KPI cards. (●●◐●●●)
2. Broadcast ratings board — fun, thin
3. Report narrative (auto-written weekly memo) — strong future addition, kept in backlog

**SETTINGS / PROFILE / BILLING (CONSOLE)**
1. ⭐ **The Console** — no settings *page*: `⌘K` (and a persistent console handle for discoverability/a11y) opens a **service panel** that slides over the current station: searchable, sectioned (Identity/Keys/Channels/Ledger/Plan/Defaults), every control inline-editable, deep-linkable. Contextual summons everywhere: out of credits → console opens at Ledger; publishing without a channel → console opens at Channels. (●●●●●●)
2. Zones on the floor (walk to a "back office" station) — cute, slow
3. Traditional page, restyled — banned by brief

**LOADING / EMPTY / ERROR STATES**
- Loading = **things travel** (skeletons slide in along the line axis; never spinners; the conveyor IS the loading experience for renders)
- Empty ① = "the field is quiet — the harvester sweeps at :00" with the next sweep countdown; empty ④ = "the line is clear," gates idle-breathing; empty ⑤ = an empty shelf with one dusty outline
- Errors = the **siding**: failed work is never a red toast; it's an object moved to a visible siding with its refund receipt attached

---

## 5. Signature design language

**Space** — near-black floor `#0B0C0E`, but *not* flat: stations have faint floor markings (hairline lane rules, station numerals as painted floor type). Panels are **benches** (matte, hairline-edged, square-cornered) — no glass, no blur, no glow, radius scale 0/2/4 only.

**The one accent** — logo violet `#8B5CF6` appears **only on the object being made** (the reel, the pulled blip, the committed action). Everything else speaks in **work-light tones**: signal-green `#3FBF7F` (ready/live), tungsten `#D9A353` (working), cold-white `#E8EAED` (text), ash `#8A8F98` (secondary), alarm `#D25353` (refused). Color = state, never decoration.

**Type** — one grotesque for statements (Archivo or Söhne-class), one instrument mono (JetBrains) for telemetry/labels. Painted-floor typography (oversized station numerals, rotated rail labels) is a signature element.

**Iconography** — no emoji anywhere in chrome. One custom pictogram set, single style: **1.5px technical line, square joints** — drawn like equipment stencils (reel, gate, blip, shelf, siding). Format families get stencil marks, not emoji.

**Motion (one law)** — *everything meaningful moves along the line axis; nothing fades.* Arrive = slide in from the station you came from. Commit = the object departs rightward. Progress = physical travel. Failure = lateral shunt to the siding. Duration scale: 120ms (feedback) / 240ms (travel) / 480ms (station change), single easing family. `prefers-reduced-motion` = hard cuts, zero travel, full function.

**The screenshot test** — transport bar + film-frame strip + a reel on the conveyor + painted station numerals: no logo needed.

---

## 6. User journeys (the five verbs)

1. **Morning approve** — open → arrive at ④ (a reel waits at READY) → space = face it → ⌘⏎ approve → publish panel (channel, visibility, hold) → the reel departs to ⑤ and slots into the shelf. *~40 seconds, two keys.*
2. **See → make** — ① field: a fat blip pulses in GAMING → hover: "Gaming Update — covers patches, 1 CR" → pull to intake → ② bench opens with the draft → amend two lines, ↹ to ③, flip the caption toggle → SEND → watch it enter ④. *~6 minutes.*
3. **Own footage** — VAULT overlay → episode's moment strip → CUT → a clip-reel joins ④ directly.
4. **Autopilot** — console → Standing Orders → new order; its future reels arrive on ④ wearing the series tag; review-first reels park at the READY gate.
5. **Refused render** — reel shunts to the siding, refund receipt attached, one action: `RETRY (1 CR)`.

## 7. Tokens (foundation)

```
--floor #0B0C0E   --bench #131519   --bench-raised #1A1D22   --rule #2A2E35
--ink #E8EAED     --ash #8A8F98     --dust #565B64
--make #8B5CF6 (the object/commit only)
--ready #3FBF7F   --working #D9A353   --live #58A6FF   --refused #D25353
radius: 0 / 2 / 4      motion: 120 / 240 / 480ms, one easing
type: grotesque (display/body) + mono (telemetry) — weights 400/600/700 only
grid: 8px base; station gutter 64px; bench padding 16/20
```

## 8. Functional preservation map (nothing removed)

| Today | Lives at |
|---|---|
| Topics (all filters, harvest, best-format, script-only) | ① SIGNAL (field + wire toggle) |
| Studio: formats, BYO, language/tone/model/instructions | ② DESK bench + intake |
| Studio: segments, regenerate, media swap, voice, captions, aspect | ② frames + ③ STAGE racks |
| Preview player + WS progress | ④ RAIL (reel + gates) |
| Publish/schedule/metadata/categories/IG | ⑤ AIR publish panel |
| Dashboard library + uploads | ⑤ AIR shelf |
| Analytics | ⑤ AIR instruments |
| Clips (upload, transcribe, highlights, cut) | VAULT overlay + ③/④ |
| Series (all controls) | CONSOLE › Standing Orders + tagged reels on ④ |
| Settings/keys/channels, Billing/ledger/economics, Profile | CONSOLE (searchable, contextual, deep-linkable) |
| Legal, sign-in | front-of-house (restyled to the language, content intact) |

## 9. Implementation phasing (after approval only)

- **P1 Foundation** — tokens, type, stencil icons, transport bar, station shell + travel motion (old routes still render inside; zero functional risk)
- **P2 The Rail** — conveyor + reel from live WS (the brand moment, and the least entangled)
- **P3 Signal** — field + wire, intake pull
- **P4 Desk + Stage** — light table, benches, racks
- **P5 Air** — shelf, publish panel, instruments
- **P6 Console + Vault** — command-first services, footage shelf
- **P7 Front-of-house** — landing as the living factory; legal restyle
- **P8 Mobile** — designed as its own product: the line runs **vertically** (downward = forward); transport bar becomes a thumb dock
- Each phase: commit → functionality parity test → your review. Old UI remains reachable until P5 completes.

## 10. The final test (self-imposed)

Before calling any phase done: place its screenshot beside ChatGPT, Notion, Linear, Vercel, AutoShorts, Crayo. If a stranger could mistake it for any of them, it does not ship.

