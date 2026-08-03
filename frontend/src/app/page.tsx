"use client"

// Kliptos Front Door — implemented from the Claude Design handoff
// (Kliptos Front Door.dc.html). Landing + sign-in for the assignment desk.
import Link from "next/link"
import { signIn } from "next-auth/react"
import { useState } from "react"
import { T, mono } from "@/components/desk/tokens"

const FORMATS = [
  { label: "Reddit Story", code: "NR", desc: "First-person storytime over immersive background footage", when: "personal drama, confessions, wild it-happened-to-me stories" },
  { label: "Fake Text Convo", code: "TX", desc: "A chat conversation plays out in text bubbles with typing beats", when: "two-person drama or twists that land as a chat screenshot" },
  { label: "Viral Story", code: "NR", desc: "“You missed this” — hook-driven narrated storytelling", when: "surprising facts, hidden details, stories where context matters" },
  { label: "Breaking-News Explainer", code: "NR", desc: "Urgent, factual — what happened and why it matters", when: "news, world events, releases, results — anything time-sensitive" },
  { label: "Motivational Quote", code: "VS", desc: "Big on-screen lines over cinematic footage — no narration", when: "mindset, discipline, self-improvement, inspirational themes" },
  { label: "Music / Trend Visual", code: "VS", desc: "On-screen text + vibe footage — attach the trending sound when posting", when: "music releases, aesthetic moments, hype trends where vibe beats narration" },
  { label: "Shayari / Poetry", code: "NR", desc: "Original Hindi shayari, slow narration over aesthetic footage", when: "poetry, romance, melancholy, Hindi-audience emotional topics" },
  { label: "Gaming Update", code: "NR", desc: "Patch notes and game news with hype pacing", when: "game patches, esports, gaming culture and releases" },
  { label: "Image Carousel", code: "IM", desc: "3–6 slide photo post with punchy captions", when: "lists, tips, rankings, facts that work as swipeable slides" },
]
const CODE_COLORS: Record<string, string> = { NR: T.body, VS: T.live, TX: T.working, IM: T.signal }

const DEMOS = [
  { key: "reddit", src: "/demos/demo-reddit.mp4", code: "NR · REDDIT STORY", label: "Reddit Story", desc: "First-person storytime over satisfying footage" },
  { key: "chat", src: "/demos/demo-chat.mp4", code: "TX · FAKE TEXT CONVO", label: "Fake Text Convo", desc: "A chat escalates in bubbles with typing beats" },
  { key: "story", src: "/demos/demo-story.mp4", code: "NR · VIRAL STORY", label: "Viral Story", desc: "Hook-driven narration with word-synced captions" },
]

const STAGES = [
  { name: "QUEUED", at: "0%", note: "Credit reserved, job durable before a worker touches it.", color: T.text },
  { name: "VOICE", at: "10%", note: "14 curated neural voices across English, Hindi, Spanish, Portuguese.", color: T.text },
  { name: "VISUALS", at: "35%", note: "Licensed stock per scene, or the exact clip you pinned.", color: T.text },
  { name: "ASSEMBLY", at: "65%", note: "Captions burned in — five styles, word-timed from the voice.", color: T.text },
  { name: "MUSIC", at: "90%", note: "Creative-Commons bed, mood-matched, credit written into your description.", color: T.text },
  { name: "READY", at: "100%", note: "Nothing publishes until you approve it. A failed render refunds the credit.", color: T.ready },
]

const NOTS = [
  { t: "Not a timeline editor", d: "Editing here means: change the line, change the visual, regenerate the scene. If you want keyframes, use CapCut — we are the other half of that workflow." },
  { t: "Not a spam machine", d: "Review-before-publish is the default, and it stays. Autopilot exists so you skip the work, not so you skip the judgement." },
  { t: "Not trending audio, baked in", d: "Nobody can license that server-side. Visual shorts render clean so you attach the trending sound in the YouTube or Instagram editor — which the algorithm prefers anyway." },
  { t: "Not other people's footage", d: "Trends are a signal, not a source. Every render uses licensed stock, generated images, or your own uploads." },
]

const micro = (color: string = T.dim, ls = "0.1em"): React.CSSProperties => ({ fontFamily: mono, fontSize: 10, letterSpacing: ls, color })
const panel: React.CSSProperties = { border: `1px solid ${T.rule}`, borderRadius: 8, background: T.panel }

export default function FrontDoor() {
  const [signInOpen, setSignInOpen] = useState(false)
  const [signingIn, setSigningIn] = useState(false)
  const [inr, setInr] = useState(true)
  const [unmuted, setUnmuted] = useState<string | null>(null)

  const doSignIn = () => {
    setSigningIn(true)
    signIn("google", { callbackUrl: "/dashboard" })
  }
  const pill = (on: boolean): React.CSSProperties => ({
    background: on ? T.signal : "transparent", border: `1px solid ${on ? T.signal : T.strong}`,
    color: on ? T.bg : T.dim, fontSize: 12.5, padding: "9px 14px", cursor: "pointer", borderRadius: 6,
  })
  const monoBtn = (primary: boolean): React.CSSProperties => ({
    background: primary ? T.signal : "transparent", border: primary ? "none" : `1px solid ${T.strong}`,
    color: primary ? T.bg : T.body, fontFamily: mono, fontSize: 12, letterSpacing: "0.06em",
    padding: primary ? "15px 22px" : "14px 20px", cursor: "pointer", borderRadius: 6,
  })

  const plans = [
    { name: "Free", price: inr ? "₹0" : "$0", credits: "3 RENDERS / MONTH", includes: "Stock footage and edge-tts voices, watermarked. Script-only mode is unlimited-ish at five a day and costs nothing.", hot: false, cta: "START HERE" },
    { name: "Pro", price: inr ? "₹499" : "$19", credits: "50 RENDERS / MONTH", includes: "No watermark, every engine, standing orders, all nine formats, caption styles and aspect ratios.", hot: true, cta: "MOST CHANNELS PICK THIS" },
    { name: "Studio", price: inr ? "₹1,299" : "$49", credits: "150 RENDERS / MONTH", includes: "Priority render queue, bulk queueing, media kit — for multiple channels or a small team.", hot: false, cta: "FOR SEVERAL CHANNELS" },
  ]

  return (
    <div style={{ background: T.bg, color: T.text, fontFamily: "var(--font-archivo), Archivo, system-ui, sans-serif", minHeight: "100vh" }}>
      {/* Top strip */}
      <div className="sticky top-0 z-50 flex h-[34px] items-center justify-between px-4 sm:px-6" style={{ background: T.panel, borderBottom: `1px solid ${T.rule}`, ...micro() }}>
        <div className="flex items-center gap-3 sm:gap-[18px] min-w-0">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/brand/kliptos-logo-2k.jpeg" alt="Kliptos" style={{ width: 20, height: 20, borderRadius: 5, objectFit: "cover", flexShrink: 0 }} />
          <span style={{ color: T.text }}>KLIPTOS</span>
          <span className="hidden md:inline" style={{ color: "#474E5E" }}>|</span>
          <span className="hidden md:inline truncate">THE ASSIGNMENT DESK FOR SHORT VIDEO</span>
        </div>
        <div className="flex items-center gap-3 sm:gap-[18px]">
          <span className="hidden lg:inline" style={{ color: T.ready }}>FREE PLAN · 3 RENDERS / MONTH</span>
          <span className="hidden sm:inline">SCRIPT-ONLY IS FREE</span>
          <button onClick={() => setSignInOpen(true)} style={{ background: T.signal, border: "none", color: T.bg, fontFamily: mono, fontSize: 10, letterSpacing: "0.06em", padding: "6px 12px", cursor: "pointer", borderRadius: 6 }}>SIGN IN</button>
        </div>
      </div>

      <div className="mx-auto max-w-[1240px] px-4 sm:px-6">
        {/* Hero */}
        <div className="grid items-start gap-10 py-16 lg:grid-cols-[1.05fr_0.95fr] lg:gap-14 lg:py-[88px]">
          <div>
            <div className="mb-6 flex items-center gap-3.5">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/brand/kliptos-logo-2k.jpeg" alt="Kliptos" style={{ width: 54, height: 54, borderRadius: 12, objectFit: "cover" }} />
              <p style={{ ...micro(T.signal, "0.14em"), fontSize: 11, margin: 0 }}>TRENDS IN · SHORTS OUT</p>
            </div>
            <h1 className="text-[42px] leading-[1.02] sm:text-[56px] lg:text-[68px] lg:leading-[0.98]" style={{ margin: 0, letterSpacing: "-0.035em", fontWeight: 700, maxWidth: "19ch", textWrap: "balance" }}>
              Every other tool starts with a blank prompt. Kliptos starts with an opinion.
            </h1>
            <p style={{ margin: "28px 0 0", maxWidth: "56ch", fontSize: 18, lineHeight: 1.55, color: T.body, textWrap: "pretty" }}>
              It reads what is trending in your niche, tells you which format that topic deserves, writes the script,
              voices it, sources the footage, burns the captions, mixes the music and publishes it to your channel.
              You assign, amend, approve. One credit, about six minutes.
            </p>
            <div className="mt-[34px] flex flex-wrap items-center gap-3">
              <button onClick={() => setSignInOpen(true)} style={monoBtn(true)}>START FREE · 3 RENDERS</button>
              <a href="#formats" style={{ ...monoBtn(false), display: "inline-block", textDecoration: "none", color: T.body }}>SEE THE NINE FORMATS</a>
            </div>
            <p style={{ ...micro(T.faint, "0.06em"), fontSize: 11, margin: "18px 0 0" }}>NO CARD · GOOGLE SIGN-IN · SCRIPT-ONLY MODE COSTS NOTHING</p>
          </div>

          {/* Desk preview */}
          <div style={{ ...panel, borderRadius: 10, overflow: "hidden" }}>
            <div style={{ height: 30, background: T.head, borderBottom: `1px solid ${T.rule}`, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 12px", ...micro(T.dim, "0.1em"), fontSize: 9 }}>
              <span style={{ display: "flex", gap: 14 }}><span style={{ color: T.text }}>DESK</span><span>LINE 2</span><span>VAULT</span></span>
              <span style={{ display: "flex", gap: 14 }}><span style={{ color: T.working }}>1 WORKING</span><span style={{ color: T.ready }}>1 AWAITING YOU</span><span style={{ color: T.text }}>14 CR</span></span>
            </div>
            <div style={{ padding: 18 }}>
              <p style={{ margin: "0 0 3px", fontSize: 20, fontWeight: 600, letterSpacing: "-0.02em" }}>Five bets for Monday</p>
              <p style={{ ...micro(T.dim, "0.08em"), fontSize: 9, margin: "0 0 16px" }}>GAMING · TECH &amp; SCIENCE · HARVESTED 08:12 · GOOGLE TRENDS + YOUTUBE</p>
              <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
                {[
                  { n: "01", t: "Apex Legends patch notes revealed", r: "Best format: Gaming Update — covers game patches", s: "▁▂▃▅▇█ +41%", sc: T.ready, hot: true },
                  { n: "02", t: "Why sleep debt never repays itself", r: "", s: "▁▂▄▅▅▄ +12%", sc: T.dim, hot: false },
                  { n: "03", t: "शायरी: बारिश और पुरानी यादें", r: "", s: "▁▁▂▄▆▆ +9%", sc: T.dim, hot: false },
                ].map(b => (
                  <div key={b.n} style={{ border: `1px solid ${T.rule}`, borderLeft: b.hot ? `2px solid ${T.signal}` : `1px solid ${T.rule}`, borderRadius: 7, background: T.bg, padding: b.hot ? "12px 14px" : "11px 14px", display: "grid", gridTemplateColumns: "22px 1fr 96px 78px", gap: 12, alignItems: "center" }}>
                    <span style={{ fontFamily: mono, fontSize: b.hot ? 13 : 11, color: b.hot ? T.signal : T.faint }}>{b.n}</span>
                    <span style={{ minWidth: 0 }}>
                      <span style={{ display: "block", fontSize: b.hot ? 15 : 14, fontWeight: b.hot ? 600 : 400 }}>{b.t}</span>
                      {b.r && <span style={{ display: "block", marginTop: 3, fontSize: 11.5, color: T.dim }}>{b.r}</span>}
                    </span>
                    <span className="hidden sm:block" style={{ fontFamily: mono, fontSize: 10, color: b.sc }}>{b.s}</span>
                    <span style={{ fontFamily: mono, fontSize: 9, letterSpacing: "0.06em", background: b.hot ? T.signal : "transparent", color: b.hot ? T.bg : T.dim, border: b.hot ? "none" : `1px solid ${T.strong}`, padding: b.hot ? "6px 8px" : "5px 8px", textAlign: "center", borderRadius: 5 }}>ASSIGN</span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 14, borderTop: `1px solid ${T.rule}`, paddingTop: 14 }}>
                <p style={{ ...micro(T.dim, "0.1em"), fontSize: 9, margin: "0 0 8px" }}>THE LINE</p>
                <div style={{ border: `1px solid ${T.rule}`, borderLeft: `2px solid ${T.working}`, borderRadius: 7, background: T.bg, padding: "10px 12px" }}>
                  <p style={{ margin: "0 0 5px", fontSize: 12.5, fontWeight: 500 }}>Apex Legends patch notes</p>
                  <p style={{ ...micro(T.working, "0.06em"), fontSize: 9, margin: "0 0 7px" }}>VISUALS · 47%</p>
                  <span style={{ display: "flex", gap: 2 }}>
                    {[T.ready, T.ready, T.working, T.rule, T.rule, T.rule].map((c, i) => (
                      <span key={i} style={{ flex: 1, height: 3, display: "block", background: c }} />
                    ))}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Demo reels — real renders */}
        <div style={{ borderTop: `1px solid ${T.rule}` }} className="py-12 lg:py-14">
          <div className="mb-6 flex flex-wrap items-end justify-between gap-6">
            <div>
              <h2 style={{ margin: "0 0 8px", fontSize: 40, letterSpacing: "-0.028em", fontWeight: 600 }} className="!text-3xl sm:!text-[40px]">Every short here was made by Kliptos.</h2>
              <p style={{ margin: 0, maxWidth: "64ch", fontSize: 16, lineHeight: 1.55, color: T.dim }}>Same pipeline, three different formats. Nothing was touched in an editor afterwards.</p>
            </div>
            <p style={{ ...micro(T.faint), margin: 0, flexShrink: 0 }}>UNMUTE TO HEAR THE VOICE</p>
          </div>
          <div className="grid gap-3.5 sm:grid-cols-3">
            {DEMOS.map(d => (
              <div key={d.key} style={{ ...panel, borderRadius: 10, overflow: "hidden" }}>
                <div style={{ position: "relative", width: "100%", aspectRatio: "9/16", background: T.head }}>
                  <video key={`${d.key}-${unmuted === d.key}`} src={d.src} autoPlay muted={unmuted !== d.key} loop playsInline style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
                  <span style={{ position: "absolute", left: 10, top: 10, ...micro(T.body, "0.08em"), fontSize: 9, background: "#0A0B10b3", padding: "4px 7px", borderRadius: 4 }}>{d.code}</span>
                  <button onClick={() => setUnmuted(unmuted === d.key ? null : d.key)} style={{ position: "absolute", right: 10, bottom: 10, background: "#0A0B10cc", border: `1px solid ${T.strong}`, color: T.body, fontFamily: mono, fontSize: 9, letterSpacing: "0.06em", padding: "6px 9px", cursor: "pointer", borderRadius: 6 }}>
                    {unmuted === d.key ? "MUTE" : "UNMUTE"}
                  </button>
                </div>
                <div style={{ padding: "14px 16px" }}>
                  <p style={{ margin: "0 0 4px", fontSize: 15.5, fontWeight: 600 }}>{d.label}</p>
                  <p style={{ margin: 0, fontSize: 13, lineHeight: 1.5, color: T.dim }}>{d.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Pipeline stages */}
        <div style={{ borderTop: `1px solid ${T.rule}` }} className="py-12">
          <p style={{ ...micro(T.dim, "0.14em"), margin: "0 0 22px" }}>WHAT THE MACHINE ACTUALLY DOES, AND WHAT IT REPORTS WHILE DOING IT</p>
          <div className="grid grid-cols-2 gap-2 md:grid-cols-3 xl:grid-cols-6">
            {STAGES.map(s => (
              <div key={s.name} style={{ ...panel, padding: "16px 15px" }}>
                <p style={{ ...micro(s.name === "READY" ? T.ready : T.dim), margin: "0 0 10px" }}>{s.name}</p>
                <p style={{ margin: "0 0 8px", fontFamily: mono, fontSize: 15, color: s.name === "READY" ? T.ready : T.text }}>{s.at}</p>
                <p style={{ margin: 0, fontSize: 12.5, lineHeight: 1.5, color: T.dim }}>{s.note}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Formats */}
        <div id="formats" style={{ borderTop: `1px solid ${T.rule}` }} className="scroll-mt-10 py-14">
          <div className="mb-[26px]">
            <h2 style={{ margin: "0 0 8px", letterSpacing: "-0.028em", fontWeight: 600 }} className="text-3xl sm:text-[40px]">Nine formats. A format is a recipe, not a filter.</h2>
            <p style={{ margin: 0, maxWidth: "72ch", fontSize: 16, lineHeight: 1.55, color: T.dim }}>
              Each one changes the script rules, the footage rules, the caption look, the pacing and the music — because a
              patch-notes short and a shayari are not the same film with a different font. The trend picks the format for
              you; you can override it.
            </p>
          </div>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {FORMATS.map(f => (
              <div key={f.label} style={{ ...panel, padding: "18px 20px" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 10 }}>
                  <p style={{ margin: 0, fontSize: 17, fontWeight: 600, letterSpacing: "-0.015em" }}>{f.label}</p>
                  <p style={{ margin: 0, ...micro(CODE_COLORS[f.code], "0.08em"), fontSize: 9, border: `1px solid ${CODE_COLORS[f.code]}55`, borderRadius: 5, padding: "4px 6px" }}>{f.code}</p>
                </div>
                <p style={{ margin: "0 0 10px", fontSize: 13.5, lineHeight: 1.5, color: T.body }}>{f.desc}</p>
                <p style={{ margin: 0, fontFamily: mono, fontSize: 10.5, lineHeight: 1.6, letterSpacing: "0.02em", color: T.faint }}>USE FOR {f.when.toUpperCase()}</p>
              </div>
            ))}
          </div>
          <p style={{ ...micro(T.faint, "0.06em"), fontSize: 10.5, margin: "16px 0 0" }}>NR NARRATED · VS ON-SCREEN TEXT, NO VOICE · TX CHAT BUBBLES · IM PHOTO CAROUSEL — ALL EDITABLE BEFORE RENDER</p>
        </div>

        {/* Clips + India-first */}
        <div style={{ borderTop: `1px solid ${T.rule}` }} className="grid gap-12 py-14 lg:grid-cols-2">
          <div>
            <p style={{ ...micro(T.signal, "0.14em"), margin: "0 0 16px" }}>IF YOU ALREADY RECORD</p>
            <h2 style={{ margin: "0 0 14px", fontSize: 34, letterSpacing: "-0.025em", fontWeight: 600, maxWidth: "22ch" }}>Drop the episode. It finds the moments.</h2>
            <p style={{ margin: "0 0 18px", maxWidth: "56ch", fontSize: 15.5, lineHeight: 1.6, color: T.body }}>
              Upload a podcast, stream or talking-head video up to 500MB. It transcribes the whole thing, mines the
              moments that stand alone, and tells you why each one works. Pick one and it renders a captioned vertical
              cut from your own footage — zero rights ambiguity.
            </p>
            <div style={{ ...panel, padding: "16px 18px" }}>
              <p style={{ ...micro(T.dim, "0.08em"), margin: "0 0 12px" }}>EP-14-HIRING-RANT.MP4 · 48:12 · 4 MOMENTS FOUND</p>
              <div style={{ position: "relative", height: 34, border: `1px solid ${T.rule}`, borderRadius: 6, background: T.bg, backgroundImage: `repeating-linear-gradient(90deg, ${T.head} 0 1px, transparent 1px 7px)`, marginBottom: 12 }}>
                {[["8%", "9%"], ["31%", "7%"], ["56%", "11%"], ["81%", "6%"]].map(([l, w]) => (
                  <span key={l} style={{ position: "absolute", left: l, top: 0, bottom: 0, width: w, background: `${T.signal}33`, borderLeft: `2px solid ${T.signal}`, display: "block" }} />
                ))}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "92px 1fr", gap: 12, alignItems: "center" }}>
                <span style={{ fontFamily: mono, fontSize: 11, color: T.signal }}>04:02–04:38</span>
                <span style={{ fontSize: 13, color: T.body }}>“Nobody reads the résumé” — strong hook, complete thought</span>
              </div>
            </div>
          </div>
          <div>
            <p style={{ ...micro(T.signal, "0.14em"), margin: "0 0 16px" }}>भारत पहले</p>
            <h2 style={{ margin: "0 0 14px", fontSize: 34, letterSpacing: "-0.025em", fontWeight: 600, maxWidth: "24ch" }}>Hindi is a first-class language here, not a caption setting.</h2>
            <p style={{ margin: "0 0 18px", maxWidth: "56ch", fontSize: 15.5, lineHeight: 1.6, color: T.body }}>
              Madhur and Swara narrate in Hindi. Scripts are written in Hindi, not translated into it. Shayari is a real
              format with its own pacing — roughly 1.2 words a second, so the couplets breathe. Pricing is in rupees, with UPI.
            </p>
            <div style={{ ...panel, padding: "18px 20px" }}>
              <p style={{ margin: "0 0 12px", fontSize: 19, lineHeight: 1.7, color: T.text }}>बारिश की हर बूँद में<br />एक पुरानी याद है…</p>
              <p style={{ ...micro(T.faint, "0.06em"), margin: 0 }}>SHAYARI / POETRY · MADHUR · MINIMAL BOX CAPTIONS · SLOW PACING</p>
            </div>
          </div>
        </div>

        {/* Pricing */}
        <div style={{ borderTop: `1px solid ${T.rule}` }} className="py-14">
          <div className="mb-6 flex flex-wrap items-end justify-between gap-6">
            <div>
              <h2 style={{ margin: "0 0 8px", letterSpacing: "-0.028em", fontWeight: 600 }} className="text-3xl sm:text-[40px]">One credit is one short.</h2>
              <p style={{ margin: 0, maxWidth: "64ch", fontSize: 16, lineHeight: 1.55, color: T.dim }}>
                Failed renders are refunded automatically. Script-only mode never costs a credit. Bring your own OpenAI
                or Gemini key and pay a reduced platform fee instead.
              </p>
            </div>
            <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
              <button onClick={() => setInr(true)} style={pill(inr)}>₹ India</button>
              <button onClick={() => setInr(false)} style={pill(!inr)}>$ Global</button>
            </div>
          </div>
          <div className="grid gap-2 md:grid-cols-3">
            {plans.map(p => (
              <div key={p.name} style={{ border: `1px solid ${p.hot ? T.signal : T.rule}`, borderRadius: 9, background: T.panel, padding: "22px 24px" }}>
                <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 12, marginBottom: 6 }}>
                  <p style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{p.name}</p>
                  <p style={{ margin: 0, fontFamily: mono, fontSize: 22, color: p.hot ? T.signal : T.body }}>{p.price}</p>
                </div>
                <p style={{ ...micro(T.dim, "0.06em"), fontSize: 11, margin: "0 0 16px" }}>{p.credits}</p>
                <p style={{ margin: "0 0 18px", fontSize: 13.5, lineHeight: 1.6, color: T.body }}>{p.includes}</p>
                <button onClick={() => setSignInOpen(true)} style={{ width: "100%", background: p.hot ? T.signal : "transparent", border: `1px solid ${p.hot ? T.signal : T.strong}`, color: p.hot ? T.bg : T.body, fontFamily: mono, fontSize: 10.5, letterSpacing: "0.06em", padding: 11, cursor: "pointer", borderRadius: 6 }}>{p.cta}</button>
              </div>
            ))}
          </div>
          <p style={{ ...micro(T.faint, "0.06em"), fontSize: 10.5, margin: "14px 0 0" }}>
            {inr ? "TOP-UP ₹149 / 10 CREDITS" : "TOP-UP $5 / 10 CREDITS"} · STOCK RENDER 1 CR · AI IMAGES 2 CR · UPI, CARDS AND GST INVOICING IN INDIA
          </p>
        </div>

        {/* What it is not */}
        <div style={{ borderTop: `1px solid ${T.rule}` }} className="pb-[72px] pt-14">
          <h2 style={{ margin: "0 0 22px", letterSpacing: "-0.028em", fontWeight: 600 }} className="text-3xl sm:text-[40px]">What it is not.</h2>
          <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
            {NOTS.map(n => (
              <div key={n.t} style={{ ...panel, padding: "20px 22px" }}>
                <p style={{ margin: "0 0 8px", fontSize: 16, fontWeight: 600 }}>{n.t}</p>
                <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.6, color: T.dim }}>{n.d}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{ borderTop: `1px solid ${T.rule}`, background: T.panel }}>
        <div className="mx-auto flex max-w-[1240px] flex-wrap items-start justify-between gap-10 px-4 py-9 sm:px-6">
          <div>
            <p style={{ ...micro(T.text, "0.12em"), margin: "0 0 10px" }}>KLIPTOS</p>
            <p style={{ margin: 0, fontSize: 13, lineHeight: 1.6, color: T.dim }}>
              Trending topic → script → captioned vertical short → your channel.<br />Built for one-person channels in India and the US.
            </p>
          </div>
          <div className="flex flex-wrap gap-12">
            <div>
              <p style={{ ...micro(T.faint, "0.12em"), margin: "0 0 10px" }}>PRODUCT</p>
              <p style={{ margin: 0, fontSize: 13, lineHeight: 2, color: T.body }}>Formats<br />Clips from your footage<br />Standing orders</p>
            </div>
            <div>
              <p style={{ ...micro(T.faint, "0.12em"), margin: "0 0 10px" }}>LEGAL</p>
              <p style={{ margin: 0, fontSize: 13, lineHeight: 2 }}>
                <Link href="/privacy" style={{ color: T.signal }}>Privacy</Link><br />
                <Link href="/terms" style={{ color: T.signal }}>Terms</Link><br />
                <Link href="/refunds" style={{ color: T.signal }}>Refunds</Link>
              </p>
            </div>
            <div>
              <p style={{ ...micro(T.faint, "0.12em"), margin: "0 0 10px" }}>START</p>
              <button onClick={() => setSignInOpen(true)} style={{ background: T.signal, border: "none", color: T.bg, fontFamily: mono, fontSize: 10, letterSpacing: "0.06em", padding: "9px 14px", cursor: "pointer", borderRadius: 6 }}>SIGN IN WITH GOOGLE</button>
            </div>
          </div>
        </div>
      </div>

      {/* Sign-in modal */}
      {signInOpen && (
        <div style={{ position: "fixed", inset: 0, zIndex: 90, background: "#0A0B10d9", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
          <div className="grid w-[900px] max-w-full lg:grid-cols-2" style={{ border: `1px solid ${T.rule}`, borderRadius: 12, background: T.panel, overflow: "hidden" }}>
            <div className="lg:border-r" style={{ padding: "38px 36px", borderColor: T.rule }}>
              <p style={{ ...micro(T.signal, "0.14em"), margin: "0 0 22px" }}>SIGN IN</p>
              <p style={{ margin: "0 0 10px", fontSize: 30, fontWeight: 600, letterSpacing: "-0.025em", maxWidth: "20ch" }}>Your desk is waiting with three free renders.</p>
              <p style={{ margin: "0 0 28px", fontSize: 14.5, lineHeight: 1.6, color: T.dim }}>
                Google account only — no password to forget. Publishing permission is asked for separately, later, when you actually publish.
              </p>
              <button onClick={doSignIn} disabled={signingIn} style={{ width: "100%", background: signingIn ? "transparent" : T.signal, border: `1px solid ${T.signal}`, color: signingIn ? T.signal : T.bg, fontFamily: mono, fontSize: 12, letterSpacing: "0.06em", padding: 15, cursor: "pointer", borderRadius: 6 }}>
                {signingIn ? "OPENING GOOGLE…" : "CONTINUE WITH GOOGLE"}
              </button>
              <p style={{ margin: "16px 0 0", fontSize: 12.5, lineHeight: 1.6, color: T.faint }}>
                By signing in you agree to the <Link href="/terms" style={{ color: T.signal }}>Terms</Link> and <Link href="/privacy" style={{ color: T.signal }}>Privacy Policy</Link>.
              </p>
              <button onClick={() => setSignInOpen(false)} style={{ marginTop: 26, background: "transparent", border: `1px solid ${T.strong}`, color: T.dim, fontFamily: mono, fontSize: 10, letterSpacing: "0.06em", padding: "8px 12px", cursor: "pointer", borderRadius: 6 }}>BACK TO THE FRONT PAGE</button>
            </div>
            <div className="hidden lg:block" style={{ padding: "38px 36px", background: T.bg }}>
              <p style={{ ...micro(T.dim, "0.14em"), margin: "0 0 18px" }}>WHAT HAPPENS NEXT</p>
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {[
                  "Pick your niches. The harvester starts reading Google Trends and YouTube for you.",
                  "Your desk opens with five ranked bets and a recommended format for each.",
                  "Assign one. Amend the lines you don't like. Approve the render.",
                  "Connect a channel only when you're ready to publish — upload permission, nothing else.",
                ].map((step, i) => (
                  <div key={i} style={{ display: "grid", gridTemplateColumns: "26px 1fr", gap: 12 }}>
                    <span style={{ fontFamily: mono, fontSize: 11, color: T.faint }}>{`0${i + 1}`}</span>
                    <span style={{ fontSize: 13.5, lineHeight: 1.55, color: T.body }}>{step}</span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 26, border: `1px solid ${T.working}40`, borderRadius: 8, background: `${T.working}0F`, padding: "14px 16px" }}>
                <p style={{ ...micro(T.working, "0.08em"), margin: "0 0 6px" }}>ONE HONEST WARNING</p>
                <p style={{ margin: 0, fontSize: 13, lineHeight: 1.6, color: T.body }}>
                  Google may show an “unverified app” notice on the publishing step while our upload verification is in
                  review. Your footage and credentials stay yours regardless.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
