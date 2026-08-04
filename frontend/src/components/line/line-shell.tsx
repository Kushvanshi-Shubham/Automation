"use client"

/**
 * The shell. No page-transition animation at all — navigation must feel
 * instant. Width is given to the content; sub-areas appear as quiet tabs
 * only where a section has more than one.
 */
import Link from "next/link"
import { usePathname } from "next/navigation"
import { L, grotesque } from "@/lib/line/tokens"
import TransportBar from "@/components/line/transport-bar"

const BAYS: { match: (p: string) => boolean; tabs: { href: string; label: string }[] }[] = [
  {
    match: p => p.startsWith("/dashboard/studio") || p.startsWith("/dashboard/styles"),
    tabs: [
      { href: "/dashboard/studio", label: "Studio" },
      { href: "/dashboard/styles", label: "Your styles" },
    ],
  },
  {
    match: p => p.startsWith("/dashboard/rail") || p.startsWith("/dashboard/uploads") || p.startsWith("/dashboard/preview"),
    tabs: [
      { href: "/dashboard/rail", label: "In production" },
      { href: "/dashboard/uploads", label: "Publish list" },
    ],
  },
  {
    match: p => p === "/dashboard" || p.startsWith("/dashboard/analytics"),
    tabs: [
      { href: "/dashboard", label: "Videos" },
      { href: "/dashboard/analytics", label: "Analytics" },
    ],
  },
  {
    match: p => ["/dashboard/settings", "/dashboard/billing", "/dashboard/series"].some(x => p.startsWith(x)),
    tabs: [
      { href: "/dashboard/settings", label: "Settings" },
      { href: "/dashboard/billing", label: "Billing" },
      { href: "/dashboard/series", label: "Standing orders" },
    ],
  },
]

export default function LineShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const bays = BAYS.find(b => b.match(pathname))?.tabs

  return (
    <div style={{ minHeight: "100vh", background: L.floor, color: L.ink, fontFamily: grotesque }}>
      {bays && (
        <header style={{ position: "sticky", top: 0, zIndex: 50, background: L.floor, borderBottom: `1px solid ${L.rule}`, display: "flex", alignItems: "center", gap: 4, padding: "0 32px" }}>
          {bays.map(b => {
            const on = pathname === b.href || (b.href !== "/dashboard" && pathname.startsWith(b.href))
            return (
              <Link key={b.href} href={b.href} prefetch
                style={{ fontSize: 13.5, fontWeight: on ? 600 : 400, color: on ? L.ink : L.dust, textDecoration: "none", padding: "11px 12px", borderBottom: `2px solid ${on ? L.make : "transparent"}` }}>
                {b.label}
              </Link>
            )
          })}
        </header>
      )}

      <main style={{ minHeight: "calc(100vh - 50px)", padding: "28px 40px 84px" }}>
        {children}
      </main>

      <TransportBar />
    </div>
  )
}
