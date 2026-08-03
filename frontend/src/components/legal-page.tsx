import Link from "next/link"

/** Shared shell for legal pages — quiet typography, brand header, cross-links. */
export default function LegalPage({
  title,
  updated,
  children,
}: {
  title: string
  updated: string
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <nav className="border-b border-white/5 bg-zinc-950/70 backdrop-blur-xl">
        <div className="flex items-center justify-between px-6 py-3.5 max-w-3xl mx-auto">
          <Link href="/" className="flex items-center gap-2.5">
            {/* eslint-disable-next-line @next/next/no-img-element -- small static brand asset */}
            <img src="/brand/kliptos-logo-2k.jpeg" alt="Kliptos" className="w-8 h-8 rounded-lg object-cover border border-white/10" />
            <span className="font-bold tracking-tight">Kliptos</span>
          </Link>
          <div className="flex gap-5 text-xs text-zinc-500">
            <Link href="/terms" className="hover:text-white transition-colors">Terms</Link>
            <Link href="/privacy" className="hover:text-white transition-colors">Privacy</Link>
            <Link href="/refunds" className="hover:text-white transition-colors">Refunds</Link>
          </div>
        </div>
      </nav>
      <main className="max-w-3xl mx-auto px-6 py-14">
        <h1 className="text-3xl font-bold tracking-tight mb-1">{title}</h1>
        <p className="text-xs text-zinc-500 mb-10">Last updated: {updated}</p>
        <div className="space-y-8 text-[15px] leading-relaxed text-zinc-300 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-zinc-100 [&_h2]:mb-2 [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:space-y-1.5 [&_a]:text-violet-400 hover:[&_a]:text-violet-300">
          {children}
        </div>
        <p className="text-xs text-zinc-600 mt-14 border-t border-white/5 pt-6">
          Questions about this policy: <a href="mailto:support@kliptos.app" className="text-violet-400">support@kliptos.app</a>
        </p>
      </main>
    </div>
  )
}
