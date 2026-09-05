# Pitch — the story, the answers, the traps

> Working document. Edit it, argue with it, cut what doesn't sound like you.
> Last worked on: 2026-09-06, before the call with the judge/investor.

## The thesis, in one line

**People don't quit content creation because they're bad at it. They quit because it takes too long.**

Idea on Monday, editing on Thursday, nothing happens, and by week three the patience is gone. It isn't talent that runs out — it's stamina. Kliptos shortens the distance between "I have an idea" and "it's posted" enough that posting stays a habit instead of becoming a project.

## The line to lead with

> *"I cannot make anyone famous. I cannot make them an influencer. What I can do is make the path shorter and faster, so they're still around when it starts working."*

Every other AI video tool promises virality. Refusing to promise it is why the rest gets believed.

## Why it isn't ChatGPT

> *"Everyone making content with AI today starts by explaining themselves. Open Gemini or Claude and before you get anything you describe the format, the tone, the length, the captions — every time. Kliptos already knows the job."*

The model is **one step out of about eight**: trends → script → voice → visuals → captions → music → render → publish. A better Gemini makes the scripts better; it doesn't make the video.

## Three doors

| If you… | You start at |
|---|---|
| are new, no idea yet | **Trends** — pick one, it becomes a video |
| have the idea | **Studio** — shape it yourself |
| already shot footage | **Upload** — it builds the video from your clips |

Same product, three entry points by how far along the creator is.

## The north star

Trend → script → video → published to YouTube/Instagram/anywhere, **with as little human intervention as the creator wants**. Autopilot already does the loop; the goal is that it also *chooses well*.

## Features — one to three words

**Start from:** Trending topics · Any link · Your script · Your footage
**Formats (9):** Reddit story · Fake texts · Viral story · Breaking news · Motivational · Music visual · Shayari · Gaming update · Image carousel
**Control:** 11 moods · Length picker · Editable script · Reorder scenes · Rewrite scene · Free preview · Free restyles
**Voice:** AI narration · Hindi voices · Premium voices · Pace control · Voice preview
**Visuals:** Stock footage · Stock photos · AI images · Your footage · Auto-match footage · 4 looks
**Captions:** Burned-in · 5 animations · 6 fonts · Brand colour · Headline overlays · Hindi captions
**Sound:** Mood-matched music
**Publish:** YouTube upload · Scheduling
**Automation:** Standing orders · Auto-publish · Feedback memory · Teach-a-style
**Account:** Credit system · Plan tiers · Own API keys

## ⚠️ Built vs not built — read before the call

Overclaiming here is the fastest way to lose the room. If they probe one item and it isn't real, everything else gets doubted.

**Real and working in production:** everything in the feature list above.

**NOT built — say "next", never "has":**
- **Gaming montage** — no automatic highlight detection, no beat-syncing. Clip cutting from uploads exists; choosing the best moments and cutting to music does not.
- **Interface that adapts per video type** — same screen for every format today.
- **Trend mash-up** — combining four trending topics into one video.
- **Payments** — checkout returns 501. Razorpay KYC not started.
- **Instagram publishing**, AI presenter, email/password signup, onboarding.
- **Monthly credit grants** — nothing in the code gives subscribers their credits.

**Honest technical limit:** one render worker, on my laptop. A hundred simultaneous renders queue for hours — they don't crash, and a reaper refunds anything stuck over 30 minutes. Scaling is adding workers, a hosting decision, not an architecture change.

## Traction — say it flat

2 accounts (mine and a friend's). 6 videos created, 1 rendered. 0 paying customers, and zero revenue is structural rather than a sales failure — there is no code path that takes money yet.

> *"I built more than I sold. That's what I'm fixing now."*

Said plainly with no defensiveness, this does more good than any explanation. **Do not count the friend as a user.**

## Cross-questions, and how to answer

**"Nine formats, zero users — why not one format and a hundred users?"**
The hardest one, and it's coming. → *"Formats aren't nine products, they're one recipe system with nine presets — adding the tenth is a config entry, not a rebuild. But you're right that I've built more than I've sold."*

**"How is this different from Opus Clip / CapCut / InVideo / Canva?"**
Opus Clip cuts long videos into shorts. CapCut is a manual editor. InVideo is templates. Kliptos writes it from scratch and renders it, and you approve the script before spending anything. Also: nobody else renders Hindi properly — they translate into it.

**"If Gemini gets better, why doesn't it just do this?"**
→ The model is one step of eight. See above.

**"How does it make them money or fame?"**
Don't promise outcomes you can't demonstrate. → *"More videos published, more consistently."*

**"You're finishing your degree — what happens after?"**
Correct their premise: not a student with free time — **employed, and the degree completes 16 Sept 2026.**
→ *"I'm working a job and my degree finishes on the 16th. Everything you've seen was built in evenings and weekends. From late September that constraint loosens — `[X hours/week]`. I'd go full-time at `[the milestone that would justify it]`."*

This is stronger than a student answer. Shipping a nine-format pipeline while employed says more about execution than free time ever could. But be ready for the follow-up, because it always comes: **"Would you leave the job for this, and at what point?"** Have a real answer — revenue figure, user count, or funded runway. "When it makes sense" reads as no.

⚠️ **Check your employment contract before taking money or filing for the seed fund.** Indian employment agreements frequently assign IP created during employment — sometimes including work done on your own time and equipment. If your employer has any claim on Kliptos, that surfaces during diligence and kills the round, not before it. Worth reading the clause now while it costs nothing.

**"What's your unfair advantage?"**
→ Built the whole pipeline solo and understands every layer; India-first where competitors are translated-into-Hindi.

## Make it measurable

"Faster and easier" is abstract. Give it a target they can hold you to:

> *"Someone posting twice a month should be posting three times a week."*

Being holdable is what makes a claim credible.

## Order for the call

1. **The problem** — people quit because it's slow
2. **The honest limit** — I can't make you famous
3. **What I do instead** — three doors, idea to posted, fast
4. **What's next** — interface adapts to what you're making; gaming montages; trend mash-ups
5. **Traction, flat** — and what I'm fixing

## Ask them one thing

They rated the first write-up 1/10 without saying what was missing. Ask directly: **"What were you looking for that wasn't there?"** Costs nothing, and it's the most useful question available.

---

Links: [[Home]] · [[S1 Build Log]] · [[Pricing]] · [[Competitors]]
