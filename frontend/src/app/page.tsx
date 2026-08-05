"use client"

/**
 * Landing — the product in its own language. Same identity as the app
 * (THE LINE): quiet surfaces, plain words, violet only where you commit.
 * Real renders as proof, no mockups, no gradient theater.
 */
import Link from "next/link"
import { useState } from "react"
import {
  MdOutlineExpandMore, MdOutlineExplore, MdOutlineLink, MdOutlineMovieFilter,
  MdOutlinePermMedia, MdOutlinePrecisionManufacturing, MdOutlineRateReview,
  MdOutlineSchool, MdOutlineVideoLibrary,
} from "react-icons/md"
import { L, mono, grotesque, alpha } from "@/lib/line/tokens"

const FAQS = [
  {
    q: "Do I need to show my face or record anything?",
    a: "No. Kliptos builds fully faceless shorts: AI writes the script, a neural voice narrates it (or on-screen text for music-led videos), footage is matched to every line, and captions and music are added automatically. If you DO have footage, even better — your scenes can play your own clips.",
  },
  {
    q: "What exactly does one credit get me?",
    a: "One rendered short (narrated or visual), one clip cut from your footage, or one image carousel. Script-only generations are free (5 per day), and failed renders refund themselves automatically. Heavier engines cost more credits, priced from what they actually cost to run — an AI-image carousel is 4, a premium AI-video render is far more. You always see the price on the button before you spend anything.",
  },
  {
    q: "Can it copy a style I like?",
    a: "Yes — upload a few reference reels you have the rights to, and Kliptos learns the hook pattern, pacing and voice from their transcripts. The result becomes your own format, next to the built-in ones. Nothing is ever scraped from other creators.",
  },
  {
    q: "What is the actual difference between Free and Pro?",
    a: "Free is a real tool, not a demo: every format, every creation route, 5 free scripts a day, and videos you can download and post. Pro changes the output — no watermark, full 1080p, shorts up to three minutes, your logo and colours, studio-grade voices — and it changes the workflow: publishing and scheduling from inside Kliptos, standing orders that make a Short a day unattended, teaching it your own style, and your own footage inside scenes. If you bring your own AI keys, your scripts run on your quota and cost fewer credits.",
  },
  {
    q: "Can I use my own script, my own footage, or my own AI keys?",
    a: "All three. Paste a script and only structure is added — your wording stays untouched. Upload your footage and any scene can play your clip instead of stock (or let auto-match pin the right moments for you). And bring your own Gemini, OpenAI or Hugging Face key to generate on your own quota.",
  },
  {
    q: "How does publishing work?",
    a: "Connect your YouTube channel once, then publish or schedule from the preview page with an editable AI-written title, description and tags. Standing orders can even run the whole loop on a schedule — or hold every video for your review. Instagram Reels publishing is next.",
  },
  {
    q: "Will YouTube penalize AI content?",
    a: "YouTube rewards videos people watch and penalizes mass-produced spam. Kliptos is built for the former: real trending topics, editable scripts, your own footage and style, and standing feedback the system actually remembers. We recommend reviewing every video before publishing.",
  },
]

const card: React.CSSProperties = { background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 12 }
const makeBtn: React.CSSProperties = {
  display: "inline-flex", alignItems: "center", gap: 8, background: L.make, color: "#fff",
  textDecoration: "none", fontFamily: grotesque, fontSize: 14.5, fontWeight: 600,
  padding: "13px 22px", borderRadius: 9,
}
const quietBtn: React.CSSProperties = {
  display: "inline-flex", alignItems: "center", gap: 8, background: "transparent",
  border: `1px solid ${L.rule}`, color: L.ink, textDecoration: "none", fontFamily: grotesque,
  fontSize: 14.5, padding: "12px 20px", borderRadius: 9,
}

export default function LandingPage() {
  return (
    <div style={{ minHeight: "100vh", background: L.floor, color: L.ink, fontFamily: grotesque }}>
      {/* Top bar */}
      <nav style={{ position: "sticky", top: 0, zIndex: 50, background: L.floor, borderBottom: `1px solid ${L.rule}` }}>
        <div style={{ maxWidth: 1120, margin: "0 auto", padding: "12px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {/* eslint-disable-next-line @next/next/no-img-element -- small static brand asset */}
            <img src="/brand/kliptos-logo-2k.jpeg" alt="Kliptos"
              style={{ width: 32, height: 32, borderRadius: 8, objectFit: "cover", border: `1px solid ${L.rule}` }} />
            <span style={{ fontSize: 17, fontWeight: 700, letterSpacing: "-0.01em" }}>Kliptos</span>
          </div>
          <div className="hidden md:flex" style={{ gap: 26, fontSize: 13.5, color: L.ash }}>
            <a href="#line" style={{ color: "inherit", textDecoration: "none" }}>How it works</a>
            <a href="#proof" style={{ color: "inherit", textDecoration: "none" }}>Real renders</a>
            <a href="#pricing" style={{ color: "inherit", textDecoration: "none" }}>Pricing</a>
            <a href="#faq" style={{ color: "inherit", textDecoration: "none" }}>Questions</a>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <Link href="/sign-in" style={{ fontSize: 13.5, color: L.ash, textDecoration: "none", padding: "8px 10px" }}>Sign in</Link>
            <Link href="/sign-in" style={{ ...makeBtn, fontSize: 13.5, padding: "9px 16px" }}>Start free</Link>
          </div>
        </div>
      </nav>

      <main>
        {/* Opening */}
        <section style={{ maxWidth: 1120, margin: "0 auto", padding: "72px 24px 64px" }}>
          <div className="grid items-center gap-14 lg:grid-cols-[1.25fr_1fr]">
            <div>
              <p style={{ margin: "0 0 18px", fontFamily: mono, fontSize: 12.5, color: L.ash }}>
                Discover · Create · Production · Library
              </p>
              <h1 style={{ margin: "0 0 20px", fontSize: "clamp(38px, 6vw, 62px)", fontWeight: 700, letterSpacing: "-0.03em", lineHeight: 1.05 }}>
                A trend goes in.
                <br />A Short comes out.
                <br /><span style={{ color: L.make }}>You approve every word.</span>
              </h1>
              <p style={{ margin: "0 0 28px", fontSize: 17, lineHeight: 1.6, color: L.ash, maxWidth: "56ch" }}>
                Kliptos watches what&apos;s rising in your niche, recommends the format that fits,
                writes the script, renders the video with voice, captions and music — and publishes
                it to your channel. From a trend, a link, your own script, or your own footage.
              </p>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <Link href="/sign-in" style={makeBtn}>Make your first Short free</Link>
                <a href="#line" style={quietBtn}>See how it works</a>
              </div>
              <p style={{ margin: "18px 0 0", fontSize: 12.5, color: L.dust }}>
                3 free credits on signup · no card · scripts are always free · failed renders refund themselves
              </p>
            </div>

            {/* A real Kliptos render — no mockup */}
            <div style={{ margin: "0 auto", width: 260 }}>
              <div style={{ position: "relative", aspectRatio: "9/16", borderRadius: 28, border: `6px solid ${L.benchRaised}`, background: L.bench, overflow: "hidden", boxShadow: "0 24px 60px rgba(0,0,0,0.18)" }}>
                <video src="/demos/demo-reddit.mp4" autoPlay muted loop playsInline
                  style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
                <span style={{ position: "absolute", left: 10, bottom: 10, fontSize: 10.5, fontWeight: 600, color: "#fff", background: "rgba(0,0,0,0.62)", padding: "4px 9px", borderRadius: 6 }}>
                  Made by Kliptos — untouched
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* The line — the four stations, exactly as they exist in the product */}
        <section id="line" style={{ borderTop: `1px solid ${L.rule}`, borderBottom: `1px solid ${L.rule}`, background: L.bench, scrollMarginTop: 70 }}>
          <div style={{ maxWidth: 1120, margin: "0 auto", padding: "56px 24px" }}>
            <h2 style={{ margin: "0 0 8px", fontSize: 30, fontWeight: 700, letterSpacing: "-0.02em" }}>
              The whole pipeline is one line.
            </h2>
            <p style={{ margin: "0 0 32px", fontSize: 14.5, color: L.ash, maxWidth: "60ch" }}>
              Four stations, in the order the work actually happens. Everything is editable at every step —
              the automation never takes the wheel from you.
            </p>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { Icon: MdOutlineExplore, name: "Discover", desc: "Live topics from Google Trends and YouTube, clustered into your niche, each with a recommended format and a suggested hook." },
                { Icon: MdOutlineMovieFilter, name: "Create", desc: "Pick a format — or a style taught from your own reels. The script appears in a minute; edit every line, swap any visual, pin your own footage." },
                { Icon: MdOutlinePrecisionManufacturing, name: "Production", desc: "Voice-over, footage, captions and music assemble on their own. Watch the five steps live, or walk away — it waits for you." },
                { Icon: MdOutlineVideoLibrary, name: "Library", desc: "Everything you have made in one place. Review, then publish or schedule to YouTube with editable title, description and tags." },
              ].map((s, i) => (
                <div key={s.name} style={{ background: L.floor, border: `1px solid ${L.rule}`, borderRadius: 12, padding: "20px 20px 22px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
                    <s.Icon size={21} color={L.make} />
                    <span style={{ fontSize: 15.5, fontWeight: 650 }}>{s.name}</span>
                    <span style={{ marginLeft: "auto", fontFamily: mono, fontSize: 11, color: L.dust }}>{i + 1}/4</span>
                  </div>
                  <p style={{ margin: 0, fontSize: 13, lineHeight: 1.6, color: L.ash }}>{s.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Real renders */}
        <section id="proof" style={{ maxWidth: 1120, margin: "0 auto", padding: "64px 24px", scrollMarginTop: 70 }}>
          <h2 style={{ margin: "0 0 8px", fontSize: 30, fontWeight: 700, letterSpacing: "-0.02em", textAlign: "center" }}>
            Every video here was made by Kliptos.
          </h2>
          <p style={{ margin: "0 auto 36px", fontSize: 14.5, color: L.ash, maxWidth: "56ch", textAlign: "center" }}>
            Different trends need different formats. Each format is a full recipe — script rules,
            footage, captions, pacing and music.
          </p>
          <div className="grid gap-8 sm:grid-cols-3" style={{ maxWidth: 820, margin: "0 auto" }}>
            {[
              { src: "/demos/demo-reddit.mp4", label: "Reddit Story", desc: "First-person storytime over satisfying footage" },
              { src: "/demos/demo-chat.mp4", label: "Fake Text Convo", desc: "A chat escalates in bubbles with typing beats" },
              { src: "/demos/demo-story.mp4", label: "Viral Story", desc: "Hook-driven narration with word-synced captions" },
            ].map(d => (
              <div key={d.src} style={{ textAlign: "center" }}>
                <div style={{ position: "relative", aspectRatio: "9/16", borderRadius: 22, border: `5px solid ${L.benchRaised}`, background: L.bench, overflow: "hidden", maxWidth: 210, margin: "0 auto 14px", boxShadow: "0 14px 34px rgba(0,0,0,0.12)" }}>
                  <video src={d.src} autoPlay muted loop playsInline
                    style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
                </div>
                <p style={{ margin: "0 0 3px", fontSize: 14.5, fontWeight: 650 }}>{d.label}</p>
                <p style={{ margin: 0, fontSize: 12.5, color: L.dust }}>{d.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* What makes it yours */}
        <section style={{ borderTop: `1px solid ${L.rule}`, background: L.bench }}>
          <div style={{ maxWidth: 1120, margin: "0 auto", padding: "56px 24px" }}>
            <h2 style={{ margin: "0 0 8px", fontSize: 30, fontWeight: 700, letterSpacing: "-0.02em" }}>
              Not a template machine. Yours.
            </h2>
            <p style={{ margin: "0 0 32px", fontSize: 14.5, color: L.ash, maxWidth: "62ch" }}>
              Most tools make one kind of video, the same way, for everyone. Kliptos learns your
              sources, your footage, your style, and your corrections.
            </p>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[
                { Icon: MdOutlineLink, title: "Create from a link", desc: "Paste a YouTube video, article or launch post — the script is written from the page's actual facts, with your angle steering it. Nothing is ever downloaded from third-party links." },
                { Icon: MdOutlinePermMedia, title: "Your footage in any scene", desc: "Upload your podcast, stream or long video. Any scene can play your clip instead of stock — or one click auto-matches your footage's moments to the whole script." },
                { Icon: MdOutlineSchool, title: "Teach it a style", desc: "Give it a few of your reference reels and it learns the hook pattern, pacing and voice. The result is a format of your own, next to the built-in eight." },
                { Icon: MdOutlineRateReview, title: "It remembers your feedback", desc: "Say it once — \"captions bigger\", \"never say insane\" — and every future video applies it automatically. Corrections compound instead of repeating." },
                { Icon: MdOutlinePrecisionManufacturing, title: "Standing orders", desc: "A fresh short on schedule from your niche's live trends or a theme you set — published automatically, or held in your Library for review." },
                { Icon: MdOutlineMovieFilter, title: "Your keys, your models", desc: "Bring your own Gemini, OpenAI or Hugging Face key and generate on your quota, with model choice per script. Keys are encrypted and never shown back." },
              ].map(f => (
                <div key={f.title} style={{ background: L.floor, border: `1px solid ${L.rule}`, borderRadius: 12, padding: "20px 20px 22px" }}>
                  <f.Icon size={21} color={L.make} style={{ marginBottom: 10, display: "block" }} />
                  <p style={{ margin: "0 0 6px", fontSize: 15, fontWeight: 650 }}>{f.title}</p>
                  <p style={{ margin: 0, fontSize: 13, lineHeight: 1.6, color: L.ash }}>{f.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Pricing */}
        <section id="pricing" style={{ maxWidth: 1120, margin: "0 auto", padding: "64px 24px", scrollMarginTop: 70 }}>
          <h2 style={{ margin: "0 0 8px", fontSize: 30, fontWeight: 700, letterSpacing: "-0.02em", textAlign: "center" }}>
            Honest, launch-phase pricing
          </h2>
          <p style={{ margin: "0 0 36px", fontSize: 14.5, color: L.ash, textAlign: "center" }}>
            Credits are a currency — heavier engines cost more, scripts cost nothing, failures refund themselves.
          </p>
          <div className="grid items-start gap-5 md:grid-cols-3" style={{ maxWidth: 960, margin: "0 auto" }}>
            <PriceCard title="Free" price="$0" inr="₹0" credits="3 credits to start"
              features={[
                { text: "Every creation type — trends, links, your own script" },
                { text: "Free scripts — 5 a day" },
                { text: "720p with a small Kliptos mark" },
                { text: "Up to 45 seconds" },
                { text: "Download and post it yourself" },
              ]}
              cta="Start free" />
            <PriceCard popular title="Pro" price="$19" inr="₹499" credits="50 credits a month"
              features={[
                { text: "No watermark, full 1080p" },
                { text: "Shorts up to 3 minutes" },
                { text: "Publish & schedule to YouTube" },
                { text: "Standing orders — a Short a day, unattended" },
                { text: "Teach it your style, use your own footage" },
                { text: "Your logo and brand colours" },
                { text: "Priority render queue" },
                { text: "Studio-grade voices", soon: true },
              ]}
              cta="Coming at launch" disabled />
            <PriceCard title="Studio" price="$49" inr="₹1,299" credits="150 credits a month"
              features={[
                { text: "Everything in Pro" },
                { text: "Multiple channels" },
                { text: "Bulk creation queue" },
                { text: "Premium AI video engines", soon: true },
                { text: "Early access to new platforms" },
              ]}
              cta="Coming at launch" disabled />
          </div>
          <p style={{ margin: "28px auto 0", maxWidth: "62ch", fontSize: 12, lineHeight: 1.6, color: L.dust, textAlign: "center" }}>
            India has its own pricing — deliberately about a third of the US price, billed in INR over UPI,
            because a US price tag makes no sense for a creator earning in rupees. Paid plans open at public
            launch and early testers keep whatever they signed up on. Anything marked coming soon is not
            built yet — we do not charge for it.
          </p>
        </section>

        {/* FAQ */}
        <section id="faq" style={{ maxWidth: 720, margin: "0 auto", padding: "24px 24px 64px", scrollMarginTop: 70 }}>
          <h2 style={{ margin: "0 0 24px", fontSize: 30, fontWeight: 700, letterSpacing: "-0.02em", textAlign: "center" }}>
            Questions, answered
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {FAQS.map((f, i) => <FaqItem key={i} q={f.q} a={f.a} />)}
          </div>
        </section>

        {/* Final CTA */}
        <section style={{ maxWidth: 760, margin: "0 auto", padding: "0 24px 80px", textAlign: "center" }}>
          <div style={{ ...card, borderColor: alpha(L.make, 30), padding: "44px 32px" }}>
            <h2 style={{ margin: "0 0 10px", fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>
              Your niche is trending right now.
            </h2>
            <p style={{ margin: "0 auto 24px", fontSize: 14.5, lineHeight: 1.6, color: L.ash, maxWidth: "40ch" }}>
              Three free credits. A script in a minute. A published Short before your coffee cools.
            </p>
            <Link href="/sign-in" style={makeBtn}>Start creating free</Link>
          </div>
        </section>
      </main>

      <footer style={{ borderTop: `1px solid ${L.rule}`, background: L.bench }}>
        <div style={{ maxWidth: 1120, margin: "0 auto", padding: "32px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
            {/* eslint-disable-next-line @next/next/no-img-element -- small static brand asset */}
            <img src="/brand/kliptos-logo-2k.jpeg" alt="Kliptos"
              style={{ width: 26, height: 26, borderRadius: 6, objectFit: "cover", border: `1px solid ${L.rule}` }} />
            <span style={{ fontSize: 14.5, fontWeight: 650 }}>Kliptos</span>
          </div>
          <p style={{ margin: 0, fontSize: 13, color: L.dust }}>AI-assisted Shorts, human-approved. © 2026 Kliptos.</p>
          <div style={{ display: "flex", gap: 20, fontSize: 13, color: L.ash, flexWrap: "wrap" }}>
            <a href="#pricing" style={{ color: "inherit", textDecoration: "none" }}>Pricing</a>
            <a href="#faq" style={{ color: "inherit", textDecoration: "none" }}>Questions</a>
            <Link href="/terms" style={{ color: "inherit", textDecoration: "none" }}>Terms</Link>
            <Link href="/privacy" style={{ color: "inherit", textDecoration: "none" }}>Privacy</Link>
            <Link href="/refunds" style={{ color: "inherit", textDecoration: "none" }}>Refunds</Link>
            <Link href="/sign-in" style={{ color: "inherit", textDecoration: "none" }}>Sign in</Link>
          </div>
        </div>
      </footer>

      {/* Structured data for search engines */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify([
            {
              "@context": "https://schema.org",
              "@type": "SoftwareApplication",
              name: "Kliptos",
              applicationCategory: "MultimediaApplication",
              operatingSystem: "Web",
              description:
                "Kliptos finds trending topics in your niche, writes the script with AI, renders a captioned 9:16 short with voice and music, and publishes it to YouTube. Create from a trend, a link, your own script, or your own footage.",
              offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
            },
            {
              "@context": "https://schema.org",
              "@type": "FAQPage",
              mainEntity: FAQS.map(f => ({
                "@type": "Question",
                name: f.q,
                acceptedAnswer: { "@type": "Answer", text: f.a },
              })),
            },
          ]),
        }}
      />
    </div>
  )
}

function PriceCard({ title, price, inr, credits, features, cta, popular, disabled }: {
  title: string; price: string; inr: string; credits: string
  features: { text: string; soon?: boolean }[]; cta: string; popular?: boolean; disabled?: boolean
}) {
  return (
    <div style={{ ...card, borderColor: popular ? alpha(L.make, 45) : L.rule, padding: "26px 24px", display: "flex", flexDirection: "column" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <h3 style={{ margin: 0, fontSize: 15, fontWeight: 650, color: L.ash }}>{title}</h3>
        {popular && (
          <span style={{ fontSize: 10.5, fontWeight: 700, color: L.make, border: `1px solid ${alpha(L.make, 40)}`, padding: "3px 8px", borderRadius: 5 }}>
            Most popular
          </span>
        )}
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <span style={{ fontFamily: mono, fontSize: 32, fontWeight: 700 }}>{price}</span>
        <span style={{ fontSize: 12.5, color: L.dust }}>/mo</span>
      </div>
      <p style={{ margin: "4px 0 0", fontSize: 12.5, color: L.ash }}>
        In India <span style={{ fontFamily: mono, color: L.ink }}>{inr}</span>/mo
        <span style={{ color: L.dust }}> · regional price, not a conversion</span>
      </p>
      <p style={{ margin: "14px 0 18px", paddingBottom: 16, borderBottom: `1px solid ${L.ruleFaint}`, fontSize: 13, fontWeight: 600, color: L.make }}>
        {credits}
      </p>
      <ul style={{ margin: "0 0 22px", padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 10, flex: 1 }}>
        {features.map(f => (
          <li key={f.text} style={{ display: "flex", alignItems: "flex-start", gap: 9, fontSize: 13.5, color: f.soon ? L.ash : L.ink }}>
            <span style={{ marginTop: 7, width: 5, height: 5, borderRadius: "50%", background: f.soon ? L.dust : L.ready, flexShrink: 0 }} />
            <span>
              {f.text}
              {f.soon && (
                <span style={{ marginLeft: 7, fontSize: 10.5, fontWeight: 600, color: L.working, border: `1px solid ${alpha(L.working, 40)}`, padding: "1px 6px", borderRadius: 4, whiteSpace: "nowrap" }}>
                  coming soon
                </span>
              )}
            </span>
          </li>
        ))}
      </ul>
      {disabled ? (
        <span style={{ ...quietBtn, justifyContent: "center", color: L.dust, cursor: "default" }}>{cta}</span>
      ) : (
        <Link href="/sign-in" style={{ ...makeBtn, justifyContent: "center" }}>{cta}</Link>
      )}
    </div>
  )
}

function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div style={{ ...card, overflow: "hidden" }}>
      <button onClick={() => setOpen(!open)}
        style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 14, background: "none", border: "none", padding: "15px 18px", textAlign: "left", cursor: "pointer", fontFamily: grotesque, fontSize: 14.5, fontWeight: 600, color: L.ink }}>
        {q}
        <MdOutlineExpandMore size={19} color={L.dust}
          style={{ flexShrink: 0, transform: open ? "rotate(180deg)" : "none" }} />
      </button>
      {open && (
        <p style={{ margin: 0, padding: "0 18px 16px", fontSize: 13.5, lineHeight: 1.65, color: L.ash }}>{a}</p>
      )}
    </div>
  )
}
