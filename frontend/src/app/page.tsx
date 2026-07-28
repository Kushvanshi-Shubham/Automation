"use client"

import { motion } from "framer-motion"
import { TrendingUp, PenTool, Video, UploadCloud, ChevronRight, Play } from "lucide-react"
import Link from "next/link"

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5 }
}

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1
    }
  }
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-zinc-950 relative overflow-hidden text-zinc-50 font-sans selection:bg-violet-500/30">
      {/* Background Gradients */}
      <div className="absolute top-0 -left-1/4 w-1/2 h-1/2 bg-violet-600/20 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-0 -right-1/4 w-1/2 h-1/2 bg-blue-600/20 blur-[120px] rounded-full pointer-events-none" />
      
      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center font-bold text-lg shadow-[0_0_15px_rgba(139,92,246,0.5)]">
            K
          </div>
          <span className="font-bold text-xl tracking-tight">Kliptos</span>
        </div>
        <div className="flex gap-4">
          <Link href="/sign-in" className="px-4 py-2 text-sm font-medium text-zinc-300 hover:text-white transition-colors">
            Log In
          </Link>
          <Link href="/sign-in" className="px-4 py-2 text-sm font-medium bg-white/10 hover:bg-white/15 border border-white/10 rounded-full transition-all backdrop-blur-md">
            Sign Up
          </Link>
        </div>
      </nav>

      <main className="relative z-10 pb-20">
        {/* Hero Section */}
        <section className="pt-24 pb-32 px-6 text-center max-w-4xl mx-auto">
          <motion.div initial="initial" animate="animate" variants={staggerContainer} className="flex flex-col items-center gap-6">
            <motion.div variants={fadeIn} className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm text-sm font-medium text-violet-300">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-violet-500"></span>
              </span>
              Kliptos v1.0 is now live
            </motion.div>
            
            <motion.h1 variants={fadeIn} className="text-5xl md:text-7xl font-bold tracking-tight leading-tight">
              Turn Trends Into Shorts.<br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-500 to-blue-500">
                Automatically.
              </span>
            </motion.h1>
            
            <motion.p variants={fadeIn} className="text-lg md:text-xl text-zinc-400 max-w-2xl">
              AI discovers viral topics, writes scripts, generates visuals, and publishes to YouTube â€” while you sleep.
            </motion.p>
            
            <motion.div variants={fadeIn} className="flex flex-col sm:flex-row gap-4 mt-4 w-full sm:w-auto">
              <Link href="/sign-in" className="group relative px-8 py-4 bg-gradient-to-r from-violet-600 to-blue-600 rounded-full font-medium text-white shadow-[0_0_20px_rgba(124,58,237,0.3)] hover:shadow-[0_0_30px_rgba(124,58,237,0.5)] transition-all flex items-center justify-center gap-2">
                Start Creating Free
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
              <button className="px-8 py-4 rounded-full font-medium text-white bg-white/5 border border-white/10 hover:bg-white/10 transition-all backdrop-blur-md flex items-center justify-center gap-2">
                <Play className="w-4 h-4" />
                Watch Demo
              </button>
            </motion.div>
          </motion.div>
        </section>

        {/* Features Grid */}
        <section className="px-6 py-20 max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 gap-6">
            <FeatureCard 
              icon={<TrendingUp className="w-6 h-6 text-orange-400" />}
              title="ðŸ”¥ Trend Discovery"
              description="AI scans Reddit & Google Trends to find what's blowing up right now."
            />
            <FeatureCard 
              icon={<PenTool className="w-6 h-6 text-violet-400" />}
              title="âœï¸ Script & Voice"
              description="GPT writes the engaging script, advanced neural voices bring it to life."
            />
            <FeatureCard 
              icon={<Video className="w-6 h-6 text-blue-400" />}
              title="ðŸŽ¬ AI Visuals"
              description="Veo 3.1 or HiggsField generate cinematic clips â€” absolutely no stock footage needed."
            />
            <FeatureCard 
              icon={<UploadCloud className="w-6 h-6 text-emerald-400" />}
              title="ðŸš€ One-Click Publish"
              description="Upload straight to YouTube with an AI-optimised title, tags, and description."
            />
          </div>
        </section>

        {/* How It Works */}
        <section className="px-6 py-24 max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-16">How It Works</h2>
          <div className="flex flex-col md:flex-row gap-8 justify-between relative">
            <div className="hidden md:block absolute top-1/2 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-y-1/2 z-0" />
            
            <Step number="1" title="Pick a Trend" desc="Select from auto-curated viral topics" />
            <Step number="2" title="AI Creates Your Short" desc="Full script, voice, and video generation" />
            <Step number="3" title="Publish & Grow" desc="Upload and watch the views roll in" />
          </div>
        </section>

        {/* Pricing */}
        <section className="px-6 py-24 max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Simple Pricing</h2>
            <p className="text-zinc-400">Start for free. Scale when you grow.</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <PricingCard title="Free" price="$0" credits="3 credits/mo" features={["720p Exports", "Basic Voices", "Standard Generation", "Manual Publish"]} />
            <PricingCard title="Pro" price="$19" credits="50 credits/mo" popular features={["1080p Exports", "Premium ElevenLabs Voices", "Fast Generation", "Auto-Publish to YouTube", "Custom Watermark"]} />
            <PricingCard title="Studio" price="$49" credits="150 credits/mo" features={["4K Exports", "Voice Cloning", "Priority Generation", "Multi-Channel Publish", "API Access"]} />
          </div>
        </section>
      </main>

      <footer className="border-t border-white/10 bg-black/50 py-12 text-center relative z-10">
        <p className="text-zinc-500 font-medium">Built with AI. Designed for Creators.</p>
        <p className="text-zinc-600 text-sm mt-2">Â© 2026 Kliptos Inc. All rights reserved.</p>
      </footer>
    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <motion.div 
      whileHover={{ y: -5 }}
      className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl hover:bg-white/10 transition-colors"
    >
      <div className="w-12 h-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mb-4">
        {icon}
      </div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-zinc-400 leading-relaxed">{description}</p>
    </motion.div>
  )
}

function Step({ number, title, desc }: { number: string, title: string, desc: string }) {
  return (
    <div className="flex flex-col items-center relative z-10">
      <div className="w-12 h-12 rounded-full bg-zinc-900 border border-white/20 flex items-center justify-center text-xl font-bold mb-4 shadow-[0_0_15px_rgba(0,0,0,0.5)]">
        {number}
      </div>
      <h4 className="text-lg font-semibold mb-2">{title}</h4>
      <p className="text-zinc-400 text-sm max-w-[200px]">{desc}</p>
    </div>
  )
}

function PricingCard({ title, price, credits, popular, features }: { title: string, price: string, credits: string, popular?: boolean, features: string[] }) {
  return (
    <div className={`p-8 rounded-3xl backdrop-blur-xl relative flex flex-col ${
      popular 
        ? "bg-gradient-to-b from-violet-500/10 to-blue-500/10 border border-violet-500/30 shadow-[0_0_30px_rgba(139,92,246,0.1)] transform md:-translate-y-4" 
        : "bg-white/5 border border-white/10"
    }`}>
      {popular && (
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 px-3 py-1 bg-gradient-to-r from-violet-500 to-blue-500 rounded-full text-xs font-bold tracking-wider">
          MOST POPULAR
        </div>
      )}
      <h3 className="text-xl font-semibold mb-2 text-zinc-300">{title}</h3>
      <div className="mb-2">
        <span className="text-4xl font-bold">{price}</span>
        <span className="text-zinc-500">/mo</span>
      </div>
      <p className="text-violet-400 font-medium mb-6 pb-6 border-b border-white/10">{credits}</p>
      
      <ul className="space-y-4 mb-8 flex-1">
        {features.map((f, i) => (
          <li key={i} className="flex items-center gap-3 text-sm text-zinc-300">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            {f}
          </li>
        ))}
      </ul>
      
      <button className={`w-full py-3 rounded-xl font-medium transition-all ${
        popular 
          ? "bg-gradient-to-r from-violet-600 to-blue-600 text-white shadow-lg hover:shadow-violet-500/25" 
          : "bg-white/10 text-white hover:bg-white/15"
      }`}>
        Choose {title}
      </button>
    </div>
  )
}
