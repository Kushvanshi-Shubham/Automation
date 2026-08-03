"use client"

import { motion } from "framer-motion"
import {
  ArrowRight,
  Captions,
  ChevronDown,
  Clapperboard,
  Globe2,
  KeyRound,
  Mic,
  Music,
  PenTool,
  Sparkles,
  TrendingUp,
  UploadCloud,
} from "lucide-react"
import Link from "next/link"
import { useState } from "react"

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-80px" },
  transition: { duration: 0.55 },
}

const FAQS = [
  {
    q: "Do I need to show my face or record anything?",
    a: "No. Kliptos builds fully faceless shorts: AI writes the script, a neural voice narrates it (or on-screen text for music-style videos), stock footage is matched to every line, and captions + music are added automatically.",
  },
  {
    q: "What exactly does one credit get me?",
    a: "One rendered short (narrated or visual) or one image carousel. Script-only generations are free (5 per day). Premium AI-video engines will cost more credits when they launch — you always see the price before rendering.",
  },
  {
    q: "Can I use my own script or my own AI keys?",
    a: "Yes to both. Paste your own script and Kliptos only adds structure and visuals — your wording stays untouched. And you can plug in your own Gemini or OpenAI API key to generate on your own quota.",
  },
  {
    q: "How does publishing work?",
    a: "Connect your YouTube channel once, then publish or schedule directly from Kliptos with an AI-written title, description and tags — all editable before upload. Instagram Reels publishing is next.",
  },
  {
    q: "Will YouTube penalize AI content?",
    a: "YouTube rewards videos people watch, and penalizes mass-produced spam. Kliptos is built for the former: real trending topics, editable scripts, styles and custom instructions so every short is genuinely yours. We recommend reviewing every video before publishing.",
  },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-zinc-950 relative overflow-x-clip text-zinc-50 font-sans selection:bg-violet-500/30">
      {/* Ambient background */}
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-violet-600/25 blur-[160px] rounded-full" />
        <div className="absolute top-[38rem] -left-64 w-[600px] h-[400px] bg-blue-600/15 blur-[140px] rounded-full" />
        <div className="absolute bottom-0 -right-64 w-[600px] h-[500px] bg-fuchsia-600/10 blur-[160px] rounded-full" />
        <div
          className="absolute inset-0"
          style={{
            opacity: 0.05,
            backgroundImage:
              "linear-gradient(to right, rgba(255,255,255,0.6) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.6) 1px, transparent 1px)",
            backgroundSize: "72px 72px",
            maskImage: "radial-gradient(ellipse 80% 50% at 50% 0%, black, transparent)",
            WebkitMaskImage: "radial-gradient(ellipse 80% 50% at 50% 0%, black, transparent)",
          }}
        />
      </div>

      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/5 bg-zinc-950/70 backdrop-blur-xl">
        <div className="flex items-center justify-between px-6 py-3.5 max-w-6xl mx-auto">
          <div className="flex items-center gap-2.5">
            {/* eslint-disable-next-line @next/next/no-img-element -- small static brand asset */}
            <img
              src="/brand/kliptos-logo-2k.jpeg"
              alt="Kliptos"
              className="w-9 h-9 rounded-xl object-cover border border-white/10 shadow-[0_0_18px_rgba(139,92,246,0.45)]"
            />
            <span className="font-bold text-lg tracking-tight">Kliptos</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-zinc-400">
            <a href="#how" className="hover:text-white transition-colors">How it works</a>
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
            <a href="#faq" className="hover:text-white transition-colors">FAQ</a>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/sign-in" className="px-4 py-2 text-sm font-medium text-zinc-300 hover:text-white transition-colors">
              Log in
            </Link>
            <Link
              href="/sign-in"
              className="px-4 py-2 text-sm font-semibold bg-white text-zinc-950 hover:bg-zinc-200 rounded-full transition-colors"
            >
              Start free
            </Link>
          </div>
        </div>
      </nav>

      <main className="relative z-10">
        {/* Hero */}
        <section className="px-6 pt-20 pb-24 max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-[1.2fr_1fr] gap-16 items-center">
            <div>
              <motion.div {...fadeUp} className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-violet-300 mb-6">
                <Sparkles className="w-3.5 h-3.5" />
                Faceless content, minus the 4 hours of editing
              </motion.div>

              <motion.h1
                {...fadeUp}
                className="text-5xl md:text-6xl xl:text-7xl font-bold tracking-tight leading-[1.05] mb-6"
              >
                The right trend, into
                <span className="block text-transparent bg-clip-text bg-gradient-to-r from-violet-400 via-fuchsia-400 to-blue-400">
                  the right Short.
                </span>
              </motion.h1>

              <motion.p {...fadeUp} className="text-lg md:text-xl text-zinc-400 max-w-xl mb-8 leading-relaxed">
                Kliptos finds what&apos;s trending in your niche, recommends the format that fits it — story,
                music-led visual, or carousel — writes it, renders it with captions and voice, and publishes
                to YouTube. You stay in control of every word.
              </motion.p>

              <motion.div {...fadeUp} className="flex flex-col sm:flex-row gap-3">
                <Link
                  href="/sign-in"
                  className="group px-7 py-3.5 bg-gradient-to-r from-violet-600 to-blue-600 rounded-full font-semibold text-white shadow-[0_0_28px_rgba(124,58,237,0.35)] hover:shadow-[0_0_40px_rgba(124,58,237,0.55)] transition-all flex items-center justify-center gap-2"
                >
                  Create your first short free
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>
                <a
                  href="#how"
                  className="px-7 py-3.5 rounded-full font-medium text-zinc-300 bg-white/5 border border-white/10 hover:bg-white/10 transition-all flex items-center justify-center gap-2"
                >
                  See how it works
                  <ChevronDown className="w-4 h-4" />
                </a>
              </motion.div>

              <motion.p {...fadeUp} className="text-xs text-zinc-600 mt-5">
                3 free credits on signup · no credit card · scripts are always free
              </motion.p>
            </div>

            {/* Phone playing a REAL Kliptos render — no mockup */}
            <motion.div
              initial={{ opacity: 0, y: 40, rotate: 2 }}
              animate={{ opacity: 1, y: 0, rotate: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="relative mx-auto w-[270px]"
            >
              <div className="absolute -inset-8 bg-gradient-to-tr from-violet-600/30 to-blue-600/20 blur-3xl rounded-full" aria-hidden />
              <div className="relative aspect-[9/16] rounded-[2.6rem] border-[6px] border-zinc-800 bg-zinc-900 overflow-hidden shadow-2xl">
                <video
                  src="/demos/demo-reddit.mp4"
                  autoPlay
                  muted
                  loop
                  playsInline
                  className="absolute inset-0 w-full h-full object-cover"
                />
                <div className="absolute bottom-4 inset-x-4 z-10 flex items-center gap-2">
                  <span className="px-2 py-1 rounded-md bg-emerald-400/15 border border-emerald-400/25 text-emerald-300 text-[10px] font-semibold backdrop-blur-sm">
                    ✓ Made by Kliptos — untouched
                  </span>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Honest capability strip */}
        <section className="border-y border-white/5 bg-white/[0.02]">
          <div className="max-w-6xl mx-auto px-6 py-6 grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            {[
              ["4", "ways to create — video, visual, images, script"],
              ["2", "live trend sources, clustered by niche"],
              ["60s", "from trending topic to editable script"],
              ["1-click", "publish & schedule to YouTube"],
            ].map(([stat, label]) => (
              <div key={label}>
                <p className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-blue-400">{stat}</p>
                <p className="text-xs text-zinc-500 mt-1">{label}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Format demos — real renders, straight out of the pipeline */}
        <section className="px-6 py-24 max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-3">Every video here was made by Kliptos.</h2>
            <p className="text-zinc-400 max-w-xl mx-auto">
              Different trends need different formats. Pick one — script, visuals, captions, pacing and music are all part of the recipe.
            </p>
          </div>
          <div className="grid sm:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {[
              { src: "/demos/demo-reddit.mp4", label: "👽 Reddit Story", desc: "First-person storytime over satisfying footage" },
              { src: "/demos/demo-chat.mp4", label: "💬 Fake Text Convo", desc: "A chat escalates in bubbles with typing beats" },
              { src: "/demos/demo-story.mp4", label: "🎬 Viral Story", desc: "Hook-driven narration with word-synced captions" },
            ].map(d => (
              <motion.div
                key={d.src}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                className="text-center"
              >
                <div className="relative aspect-[9/16] rounded-[2rem] border-[5px] border-zinc-800 bg-zinc-900 overflow-hidden shadow-xl mb-4 mx-auto max-w-[220px]">
                  <video src={d.src} autoPlay muted loop playsInline className="absolute inset-0 w-full h-full object-cover" />
                </div>
                <p className="font-semibold">{d.label}</p>
                <p className="text-xs text-zinc-500 mt-1">{d.desc}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* How it works */}
        <section id="how" className="px-6 py-24 max-w-6xl mx-auto scroll-mt-20">
          <motion.div {...fadeUp} className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-4">Idea to published in four steps</h2>
            <p className="text-zinc-400 max-w-xl mx-auto">Every step is editable — automation that never takes the wheel from you.</p>
          </motion.div>

          <div className="grid md:grid-cols-4 gap-5">
            {[
              { icon: TrendingUp, step: "01", title: "Pick a trend", desc: "Live topics from Google Trends & YouTube, clustered by your niche — gaming, tech, education and more." },
              { icon: PenTool, step: "02", title: "Shape the script", desc: "Choose a style — story, news, explainer, commentary — or paste your own script. Edit every line." },
              { icon: Clapperboard, step: "03", title: "Render the short", desc: "Neural voice, matched footage, word-synced captions and music. 9:16, ready in minutes." },
              { icon: UploadCloud, step: "04", title: "Publish or schedule", desc: "Straight to YouTube with editable AI title, description, tags and category. Instagram next." },
            ].map((s, i) => (
              <motion.div
                key={s.step}
                {...fadeUp}
                transition={{ duration: 0.5, delay: i * 0.08 }}
                className="relative p-6 rounded-2xl bg-zinc-900/80 border border-white/5 hover:border-violet-500/30 transition-colors group"
              >
                <span className="absolute top-5 right-6 text-4xl font-black text-white/5 group-hover:text-violet-500/15 transition-colors">{s.step}</span>
                <div className="w-11 h-11 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center mb-4">
                  <s.icon className="w-5 h-5 text-violet-400" />
                </div>
                <h3 className="font-semibold mb-2">{s.title}</h3>
                <p className="text-sm text-zinc-400 leading-relaxed">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Features */}
        <section id="features" className="px-6 py-24 max-w-6xl mx-auto scroll-mt-20">
          <motion.div {...fadeUp} className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-4">Not just narrated stories</h2>
            <p className="text-zinc-400 max-w-xl mx-auto">Most tools make one kind of video. Kliptos makes what the trend actually needs.</p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            <Feature icon={Mic} color="text-violet-400" title="Narrated shorts" desc="Hook-driven scripts spoken by neural voices over footage matched to every sentence." />
            <Feature icon={Music} color="text-blue-400" title="Visual & music shorts" desc="No narration — punchy on-screen text and music-forward edits, ready for trending audio." />
            <Feature icon={Captions} color="text-fuchsia-400" title="Word-synced captions" desc="Bold, wrapped, perfectly timed captions burned in — the style short-form viewers expect." />
            <Feature icon={Globe2} color="text-emerald-400" title="Niche trend radar" desc="Google Trends + YouTube charts, clustered into your niche so you never scroll irrelevant noise." />
            <Feature icon={KeyRound} color="text-amber-400" title="Bring your own AI" desc="Plug in your own Gemini or OpenAI key and generate on your quota. Choose the model per script." />
            <Feature icon={UploadCloud} color="text-rose-400" title="Publish & schedule" desc="YouTube today — with editable metadata before every upload. Instagram Reels shipping next." />
          </div>
        </section>

        {/* Pricing */}
        <section id="pricing" className="px-6 py-24 max-w-6xl mx-auto scroll-mt-20">
          <motion.div {...fadeUp} className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-4">Honest, launch-phase pricing</h2>
            <p className="text-zinc-400">Credits are a currency — heavier engines cost more, scripts cost nothing.</p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6 items-start">
            <PriceCard
              title="Free"
              price="$0"
              inr="₹0"
              credits="3 credits to start"
              features={[
                "All 4 creation types",
                "Free scripts — 5 every day",
                "Stock footage & photo engines",
                "Captions + music included",
                "Manual YouTube publish",
              ]}
              cta="Start free"
            />
            <PriceCard
              popular
              title="Pro"
              price="$19"
              inr="₹499"
              credits="50 credits / month"
              features={[
                "Everything in Free",
                "Publish & schedule to YouTube",
                "Model choice + custom instructions",
                "Bring-your-own API keys",
                "Priority render queue",
              ]}
              cta="Coming at launch"
              disabled
            />
            <PriceCard
              title="Studio"
              price="$49"
              inr="₹1,299"
              credits="150 credits / month"
              features={[
                "Everything in Pro",
                "Premium AI video engines (soon)",
                "Multiple channels",
                "Bulk creation queue",
                "Early access to new platforms",
              ]}
              cta="Coming at launch"
              disabled
            />
          </div>
          <p className="text-center text-xs text-zinc-600 mt-8">
            Paid plans open at public launch — early testers get grandfathered pricing. India pricing billed in INR via UPI.
          </p>
        </section>

        {/* FAQ */}
        <section id="faq" className="px-6 py-24 max-w-3xl mx-auto scroll-mt-20">
          <motion.div {...fadeUp} className="text-center mb-12">
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight">Questions, answered</h2>
          </motion.div>
          <div className="space-y-3">
            {FAQS.map((f, i) => (
              <FaqItem key={i} q={f.q} a={f.a} />
            ))}
          </div>
        </section>

        {/* Final CTA */}
        <section className="px-6 pb-28 pt-8 max-w-4xl mx-auto text-center">
          <motion.div
            {...fadeUp}
            className="relative rounded-3xl border border-violet-500/20 bg-gradient-to-b from-violet-600/15 to-blue-600/10 p-12 overflow-hidden"
          >
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(139,92,246,0.25),transparent_60%)]" aria-hidden />
            <h2 className="relative text-3xl md:text-4xl font-bold tracking-tight mb-4">
              Your niche is trending right now.
            </h2>
            <p className="relative text-zinc-400 mb-8 max-w-md mx-auto">
              Three free credits. A script in a minute. A published short before your coffee cools.
            </p>
            <Link
              href="/sign-in"
              className="relative inline-flex items-center gap-2 px-8 py-4 bg-white text-zinc-950 rounded-full font-semibold hover:bg-zinc-200 transition-colors"
            >
              Start creating free <ArrowRight className="w-4 h-4" />
            </Link>
          </motion.div>
        </section>
      </main>

      <footer className="border-t border-white/5 bg-black/40 relative z-10">
        <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center font-bold text-sm">
              K
            </div>
            <span className="font-semibold">Kliptos</span>
          </div>
          <p className="text-zinc-600 text-sm">AI-assisted shorts, human-approved. © 2026 Kliptos.</p>
          <div className="flex gap-6 text-sm text-zinc-500">
            <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
            <a href="#faq" className="hover:text-white transition-colors">FAQ</a>
            <Link href="/sign-in" className="hover:text-white transition-colors">Sign in</Link>
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
                "Kliptos finds trending topics in your niche, writes the script with AI, renders a captioned 9:16 short with voice and music, and publishes it to YouTube.",
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

function Feature({ icon: Icon, color, title, desc }: {
  icon: React.ElementType; color: string; title: string; desc: string
}) {
  return (
    <motion.div
      {...fadeUp}
      className="p-6 rounded-2xl bg-zinc-900/80 border border-white/5 hover:border-white/15 hover:-translate-y-0.5 transition-all"
    >
      <div className="w-11 h-11 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mb-4">
        <Icon className={`w-5 h-5 ${color}`} />
      </div>
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-sm text-zinc-400 leading-relaxed">{desc}</p>
    </motion.div>
  )
}

function PriceCard({ title, price, inr, credits, features, cta, popular, disabled }: {
  title: string; price: string; inr: string; credits: string
  features: string[]; cta: string; popular?: boolean; disabled?: boolean
}) {
  return (
    <motion.div
      {...fadeUp}
      className={`relative p-8 rounded-3xl flex flex-col ${
        popular
          ? "bg-gradient-to-b from-violet-600/15 to-blue-600/10 border border-violet-500/40 shadow-[0_0_40px_rgba(139,92,246,0.12)] md:-translate-y-3"
          : "bg-zinc-900/80 border border-white/5"
      }`}
    >
      {popular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-gradient-to-r from-violet-500 to-blue-500 rounded-full text-[11px] font-bold tracking-wider">
          MOST POPULAR
        </div>
      )}
      <h3 className="text-lg font-semibold text-zinc-300 mb-3">{title}</h3>
      <div className="flex items-baseline gap-2 mb-1">
        <span className="text-4xl font-bold">{price}</span>
        <span className="text-zinc-500 text-sm">/mo · {inr} in India</span>
      </div>
      <p className="text-violet-400 text-sm font-medium mb-6 pb-6 border-b border-white/10">{credits}</p>
      <ul className="space-y-3.5 mb-8 flex-1">
        {features.map(f => (
          <li key={f} className="flex items-start gap-3 text-sm text-zinc-300">
            <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0" />
            {f}
          </li>
        ))}
      </ul>
      {disabled ? (
        <span className="w-full py-3 rounded-xl font-medium text-center text-sm bg-white/5 text-zinc-500 border border-white/10 cursor-default">
          {cta}
        </span>
      ) : (
        <Link
          href="/sign-in"
          className={`w-full py-3 rounded-xl font-semibold text-center text-sm transition-all ${
            popular
              ? "bg-gradient-to-r from-violet-600 to-blue-600 text-white hover:shadow-lg hover:shadow-violet-500/25"
              : "bg-white text-zinc-950 hover:bg-zinc-200"
          }`}
        >
          {cta}
        </Link>
      )}
    </motion.div>
  )
}

function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="rounded-2xl bg-zinc-900/80 border border-white/5 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-4 px-6 py-4 text-left"
      >
        <span className="font-medium text-sm md:text-base">{q}</span>
        <ChevronDown className={`w-4 h-4 text-zinc-500 flex-shrink-0 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && <p className="px-6 pb-5 text-sm text-zinc-400 leading-relaxed">{a}</p>}
    </div>
  )
}
