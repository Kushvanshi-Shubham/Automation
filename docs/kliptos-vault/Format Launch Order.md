# Format Launch Order — one at a time, and why "easiest" is a trap

> 11 September 2026. Decided with the owner. Companion to [[Editing Grammar]].

## The decision

Launch formats **one at a time**, not all nine. First live: **fake_text**, then **shayari**. Gaming montage ships as **"coming soon"** and is built in the background.

Gaming being deferred is the owner's call and a good one — it is ~70% built, but it needs the user to *already have footage*, which is a cold start a brand-new user cannot clear.

## The word that decides everything

The owner's instinct was to start with whatever is **simplest to build**. Those are `reddit_story` and `viral_story`: no uploads, no beat grid, short script.

They are also the formats built **entirely on the scene → keyword → Pexels chain** — the exact thing that produced the GTA render he rejected. Easiest to build, worst output. Shipping those first means shipping the known bug in the formats where it is most visible.

So the ranking is by **exposure to the stock-footage lane**, not build effort:

| format | visuals from | risk |
|---|---|---|
| **fake_text** | its own renderer (`pipeline/fake_text.py`) | **none** — never fetches a clip |
| **shayari** | abstract / mood imagery | low — nothing literal to get wrong |
| motivational | generic gym / nature stock | medium |
| reddit_story · viral_story | literal scene matching | **high — this is the GTA failure** |
| breaking_news | literal + factual sourcing | high |

`fake_text` is the only format in the repo with its own renderer. It cannot fetch a wrong clip because it never fetches one — its quality is pure craft, entirely in the owner's control.

`shayari` is second because it is text-forward and slow, which means the 7.4-second average shot length that ruins every other format is **correct** there. And the owner can judge the output himself, which no metric replaces.

## Why one at a time, not all of them

Each format done *properly* is 2–4 evenings of ffmpeg work plus real taste in a culture you have to actually know. Nine of those is a quarter of a year of evenings around a job.

And the failure is not neutral: **eight mediocre formats are worse than two excellent ones.** A gamer who sees one clumsy phonk montage never comes back, tells people the tool is bad, and that judgement lands on all eight formats at once. Breadth looks like ambition and behaves like dilution.

## The half of the original concept that is weak

The owner's first vision had two halves. The second half — render each type in its own grammar — is the strong one ([[Editing Grammar]]).

The first half, **"user opens the app and sees all content: hot / viral / meme / song / shayari / news"**, is a discovery feed. It answers *"what should I make today?"* — a question most people opening a creation tool **do not have**. The gamer has a clip he is proud of. The shayari writer has a line in his head.

It is also the most expensive thing to maintain (trends rot in days, feeds break silently) and the least defensible (every competitor has one; nobody ever switched tools over a trending list).

Telling detail: the owner said trends *"came later on"* in his own thinking. His first instinct was format-first, and format-first is the stronger organising principle — trend-first makes you a commodity news feed, format-first makes you a specialist tool.

## Music

Free/royalty-free only for now, licence applied for in parallel. **Do not buy an ordinary Epidemic Sound / Artlist / Soundstripe subscription** — those license *your own channel*, not rendering into customers' videos. That is sublicensing and needs a negotiated platform/API licence. Buying the wrong one is wasted money that does not make the product legal.

Current library: 10 Kevin MacLeod CC-BY tracks (3 melancholy, 2 tender, 2 calm, 2 energetic, 1 uplifting). Legal, usable for a first shayari launch, **none of it sounds Indian**, no phonk at all. Phonk is the lucky exception — remix-native with a large genuinely free supply — so the gaming format is the one where the licensing wall is not in the way.

**Never ship an unrestricted music upload.** The server does the mixing, so "the user uploaded it" is not a defence — Content ID catches it and the strike lands on *their* channel.

## Next three

1. **Music for shayari** — research and downloads, not code.
2. **Render one shayari end to end and watch it.** The owner is the only person who can judge whether it *feels* like shayari.
3. **fake_text**, which carries no visual risk at all.
