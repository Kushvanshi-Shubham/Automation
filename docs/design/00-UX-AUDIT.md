# KLIPTOS REDESIGN — PHASE 0, PART 1: THE HONEST AUDIT

> Rule of this document: if a pattern exists because "most websites do it like this," it gets named.
> The author built every screen below. Nothing here is diplomatic.

---

## 1. Page inventory (everything that exists — nothing may be removed)

| Route | What it does | Functional inventory that must survive |
|---|---|---|
| `/` | Landing | positioning, demo videos, pricing, FAQ, legal links, sign-in entry |
| `/sign-in` | Auth | Google OAuth |
| `/terms` `/privacy` `/refunds` | Legal | full policy content (Razorpay + Google verification depend on these URLs) |
| `/dashboard` | Home/library | real video library, statuses, links into preview |
| `/dashboard/topics` | Trend discovery | niche chips, source filters, score, ✨best-format chip + reason, per-topic Create (with format), refresh/harvest, script-only mode |
| `/dashboard/studio` | Create + editor | format grid (9 + custom), BYO-script mode, language/tone/model/instructions, segment editing, per-segment regenerate w/ feedback, media swap (real Pexels), voice picker + preview, caption styles, aspect ratios, render |
| `/dashboard/preview/[id]` | Review + publish | player (aspect-aware), live WS progress, metadata editor, YT categories, publish/schedule, IG (flag-gated), publish record |
| `/dashboard/clips` | Repurposing | 500MB upload, transcription status, highlights w/ reasons, caption+aspect pickers, cut to clip |
| `/dashboard/series` | Autopilot | format-aware creation, niche/theme, cadence, review/auto, channel, pause/run-now/delete, error surfacing |
| `/dashboard/uploads` | Upload manager | list of publishable/published videos |
| `/dashboard/analytics` | Analytics | overview + per-video (stub-level today) |
| `/dashboard/billing` | Credits | balance, ledger, owner economics panel |
| `/dashboard/settings` | Settings | BYO keys (3 providers, live validation), channel connect/disconnect, IG connect |
| WS `/ws/pipeline/{job}` | Live progress | 5-stage render telemetry — **our most under-used asset** |

Components: sidebar (9 items), topbar, ~30 card surfaces, chips, selects, segmented pills, upload zone, thumbnail grids, progress bar, WS hook, toasts (none — gaps), spinners (generic), skeletons (pulsing rectangles).

## 2. What is generic — named without mercy

Judged against the 50-most-popular-AI-products test:

1. **Left sidebar + topbar + content well** — indistinguishable from ChatGPT/Notion/Linear/every admin template. Guilty.
2. **Landing = sticky nav + hero + gradient headline + stat strip + pricing cards + FAQ accordion** — the exact skeleton of every AI SaaS launched since 2023. The *content* (real renders) is differentiated; the *form* is a template. Guilty.
3. **Glassmorphism + violet/blue gradients + ambient blobs** — we shipped this *last week*; the brief correctly identifies it as the 2024–26 AI-default skin. Guilty, recently and enthusiastically.
4. **`rounded-2xl bg-zinc-900 border-white/5` cards, everywhere, all identical** — Tailwind-demo rhythm. ~30 instances. Guilty.
5. **Topics = filterable card grid** — a list wearing a grid costume. Our single biggest differentiator (trend intelligence with an opinion) rendered as the single most generic pattern in software. Most-wanted criminal.
6. **Create = a form** (pick options → textarea → submit button). The most magical moment of the product — "the machine writes and directs a film" — presented as a settings form.
7. **Progress = a horizontal bar with %**. We have *live five-stage production telemetry over a socket* and we draw… a loading bar. Under-exploitation of the century.
8. **KPI stat cards** on billing/analytics — explicitly banned by the brief; present today. Guilty.
9. **Emoji as chrome** (🎙️🎵🖼️✨📐💬) — charming in year one, incoherent as identity. Guilty.
10. **Settings = vertical page of cards** — the pattern the brief says to dissolve into context. Guilty.
11. **Motion = framer fade-up on scroll** — decorative, communicates nothing. Guilty.
12. **Empty states = grey icon + "nothing yet" + button** — teaches nothing. Guilty.

**Verdict: 100% of chrome is convention. 0% of chrome is Kliptos.** Everything distinctive about the product currently lives in the *data* (real renders, format reasons, stage names) and nothing in the *interface*.

## 3. What is genuinely ours (assets to amplify, not invent)

These already exist in the backend and are the raw material of a signature interface:

- **A production pipeline with real stages** (QUEUED→VOICE→VISUALS→ASSEMBLY→MUSIC→READY) broadcasting live telemetry. Most competitors fake progress; ours is real.
- **An opinion per trend** (best format + an 8-word why). Nobody else's discovery has a point of view.
- **Formats as full recipes** — 9 named pipelines, each changing script/footage/captions/pacing/music.
- **Scene-level structure** with durations, visual prompts, pinnable real footage.
- **Credits with honest semantics** (auto-refund, price-before-action).
- **The autopilot** (standing production that works while you sleep).
- **Creator-owned footage mining** (transcripts, moments, reasons).
- **India-first reality** (Hindi as first-class, shayari as a format).

The redesign thesis follows directly: **stop describing the production studio with SaaS furniture; let the interface BE the production studio.**

## 4. Competitive teardown (what everyone else looks like)

| Product | Skeleton | Where they're generic |
|---|---|---|
| AutoShorts | wizard form → queue table → grid library | pure CRUD skin over a render farm |
| Crayo | template gallery → 3-step wizard | Canva-flavored SaaS |
| Vadoo / Nullface / InVideo AI | prompt box → progress bar → download card | ChatGPT-with-a-render-button |
| Opus/Klap (clips) | upload → list of clips w/ scores | table of results |
| Every AI SaaS (meta) | sidebar, hero, cards, purple, "Generate" | the sea we must not swim in |

Nobody in this market has an interface with a *metaphor*. Every one of them is a form in front of a queue. The category identity is unclaimed. That is the opportunity: the first shorts tool that feels like **a place**, not a form.

## 5. What "feels AI-generated" about our current UI, specifically

- Interchangeable card grids where hierarchy should be
- Gradient-text headline (the single most cloned element in AI startups)
- Purple glow shadows on CTAs
- Uniform border-radius everywhere (nothing is sharp, nothing is round — everything is 16px)
- Icon+label sidebar items with a violet active pill
- The word "Dashboard" as a page title
- Fade-up-on-scroll storytelling
- Pricing table with a highlighted middle column

Every one of these dies in Phase 1.
