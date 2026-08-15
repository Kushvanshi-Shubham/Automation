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
    <div className="min-h-screen" style={{ background: "var(--k-floor)", color: "var(--k-ink)" }}>
      <nav style={{ borderBottom: "1px solid var(--k-rule)", background: "var(--k-bench)" }}>
        <div className="flex items-center justify-between px-6 py-3.5 max-w-3xl mx-auto">
          <Link href="/" className="flex items-center gap-2.5" style={{ color: "inherit", textDecoration: "none" }}>
            {/* eslint-disable-next-line @next/next/no-img-element -- small static brand asset */}
            <img src="/brand/kliptos-logo-2k.jpeg" alt="Kliptos" className="w-8 h-8 rounded-lg object-cover"
              style={{ border: "1px solid var(--k-rule)" }} />
            <span className="font-bold tracking-tight">Kliptos</span>
          </Link>
          <div className="flex gap-5 text-xs" style={{ color: "var(--k-dust)" }}>
            <Link href="/terms" style={{ color: "inherit", textDecoration: "none" }}>Terms</Link>
            <Link href="/privacy" style={{ color: "inherit", textDecoration: "none" }}>Privacy</Link>
            <Link href="/refunds" style={{ color: "inherit", textDecoration: "none" }}>Refunds</Link>
          </div>
        </div>
      </nav>
      <main className="max-w-3xl mx-auto px-6 py-14">
        <h1 className="text-3xl font-bold tracking-tight mb-1">{title}</h1>
        <p className="text-xs mb-10" style={{ color: "var(--k-dust)" }}>Last updated: {updated}</p>
        <div
          className="space-y-8 text-[15px] leading-relaxed [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-[var(--k-ink)] [&_h2]:mb-2 [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:space-y-1.5 [&_strong]:text-[var(--k-ink)] [&_a]:text-[var(--k-make)]"
          style={{ color: "var(--k-ash)" }}
        >
          {children}
        </div>
        <p className="text-xs mt-14 pt-6" style={{ color: "var(--k-dust)", borderTop: "1px solid var(--k-rule-faint)" }}>
          Questions about this policy: <a href="mailto:support@kliptos.app" style={{ color: "var(--k-make)" }}>support@kliptos.app</a>
        </p>
      </main>
    </div>
  )
}
