# Strategy: Intent Platform (Codex brainstorm synthesis, 2026-08-02)

Owner brainstormed with Codex (thread 019fbd54): "why narration-only? build for many content
categories (anime/AMV/memes/shayari/podcast/gaming/sports), AI does 90%, Canva for AI shorts."
Codex audited the repo + recommended an "AI Creative Director" architecture. This note is the
adopted position after three-way comparison.

## Verdict (one line each)
- **Owner's instinct**: RIGHT direction (multi-format, intent-first), wrong granularity — genres
  are UX labels, not backend primitives; and anime/movie/sports scraping is a rights minefield.
- **Codex's recommendation**: right architecture framing (intent → rights-aware assets → recipe →
  editable plan), but over-engineered for current stage (full RightsManifest ledger, 9 services).
- **Current Kliptos**: already ~60% of the recommended shape — output types + styles + per-scene
  pinning + review-first series ARE proto-recipes. Evolution, not rebuild.

## Security P0s from Codex audit (VALIDATED as real — fix before any friend-testing)
1. **OAuth state not session-bound** (youtube.py / instagram.py): signed JWT state is reusable
   for 10 min and not tied to the initiating browser → account-linking attack (victim's channel
   lands in attacker's Kliptos account). Fix: single-use server-stored nonce, consumed at callback.
2. **Dispatch race** (pipeline start + series): `delay()` fires BEFORE commit → worker can see a
   missing job; no idempotency on double-click. Fix: commit first, then enqueue; status-transition
   guard (`ready→rendering` atomic update).
3. **Unauthenticated WS progress**: any job UUID can be subscribed. Fix: token on WS connect +
   ownership check.
- High (accepted tradeoff, fix at deploy): backend bearer token readable in client session →
  proxy via Next route handlers later.
- Build hygiene: stale duplicate `Desktop\Handover\frontend` (pre-monorepo copy) + stray
  `C:\Users\Administrator\package-lock.json` confuse Turbopack root → set `turbopack.root`,
  remove duplicates; add CI (GitHub Actions: pytest + lint + typecheck + build).

## Adopted product moves (cheap → big)
1. **"Best format" recommendation per trend** — classify at harvest (LLM): each topic card says
   "Best format: Music-led visual / Story explainer / Image post + why". THIS is the moat move:
   trend intelligence → format intelligence. (AutoShorts differentiator.)
2. **Reframe, don't rebuild**: rename Script Studio → "Create"; "What do you want to make?" →
   format cards presented as recipes; landing line → **"Turn the right trend into the right Short."**
3. **"Signal, not source" labels**: YouTube-source topics say "Trending on YouTube (signal)" +
   "uses original/licensed visuals" — kills the impression we lift copyrighted footage.
4. **Dashboard "Your next best Short" panel** (trend-fit + recommended format + 1-click draft).
5. **Next big recipe: Podcast/creator-clip highlights** (user uploads own video → ASR → highlight
   ranking → captions/crops). Creator-owned = zero rights ambiguity, huge authenticity win.
6. **Asset-rail badge** (green rights-cleared / amber BYO-attested) — the label system now, the
   full provenance ledger later.

## Explicitly deferred / rejected
- Anime/movie/sports auto-discovery editing: BYO-rights-upload-only, much later, legal review first.
- Pinterest as footage source: inspiration-only (mood/style), never ingestion.
- Full NLE/timeline editor: not our wedge (CapCut exists).
- "Fair use automation" promises: never.

## Sequence
Gate 0: security P0s + CI + build hygiene → cheap product moves (1–4) → billing/deploy (owner
keys pending) → podcast recipe (S3 headline) → creator memory/channel-fit scoring.
