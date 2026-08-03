"use client"

/**
 * The shell. Pages travel in with one light entrance — no exit animation
 * (keeping the old page mounted mid-slide is what made navigation feel
 * stuck). Sub-areas appear as quiet tabs only where a station has more
 * than one.
 */
import { motion, useReducedMotion } from "framer-motion"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { L, grotesque } from "@/lib/line/tokens"
import TransportBar from "@/components/line/transport-bar"

const BAYS: { match: (p: string) => boolean; tabs: { href: string; label: string }[] }[] = [
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
  const reduced = useReducedMotion()
  const bays = BAYS.find(b => b.match(pathname))?.tabs

  return (
    <div style={{ minHeight: "100vh", background: L.floor, color: L.ink, fontFamily: grotesque }}>
      {bays && (
        <header style={{ position: "sticky", top: 0, zIndex: 50, background: L.floor, borderBottom: `1px solid ${L.rule}`, display: "flex", alignItems: "center", gap: 4, padding: "0 24px" }}>
          {bays.map(b => {
            const on = pathname === b.href || (b.href !== "/dashboard" && pathname.startsWith(b.href))
            return (
              <Link key={b.href} href={b.href}
                style={{ fontSize: 13, fontWeight: on ? 600 : 400, color: on ? L.ink : L.dust, textDecoration: "none", padding: "10px 12px", borderBottom: `2px solid ${on ? L.ink : "transparent"}` }}>
                {b.label}
              </Link>
            )
          })}
        </header>
      )}

      <motion.main
        key={pathname.split("?")[0]}
        initial={reduced ? false : { x: 20, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: reduced ? 0 : 0.18, ease: [0.32, 0.72, 0.24, 1] }}
        style={{ minHeight: "calc(100vh - 48px)", padding: "28px 32px 76px", maxWidth: 1400, margin: "0 auto" }}
      >
        {children}
      </motion.main>

      <TransportBar />
    </div>
  )
}
