"use client"

/**
 * THE LINE — station shell. One continuous place, five stations.
 * Motion law: nothing fades — things travel along the line axis.
 * Old pages render inside their stations until each is rebuilt (P2–P6).
 */
import { AnimatePresence, motion, useReducedMotion } from "framer-motion"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState } from "react"
import { L, MOTION, grotesque, tele } from "@/lib/line/tokens"
import TransportBar, { stationIndexFor } from "@/components/line/transport-bar"
import { StSignal, StDesk, StRail, StAir, StVault, StConsole, StationNumeral } from "@/components/line/stencils"

const FRAMES: Record<string, { n: number | null; name: string; Icon: React.ComponentType<{ size?: number; color?: string }>; bays: { href: string; label: string }[]; note?: string }> = {
  signal: { n: 1, name: "SIGNAL", Icon: StSignal, bays: [{ href: "/dashboard/topics", label: "FIELD" }], note: "THE SCOPE ARRIVES P3 — THE WIRE RUNS MEANWHILE" },
  desk: { n: 2, name: "DESK", Icon: StDesk, bays: [{ href: "/dashboard/studio", label: "BENCH" }], note: "LIGHT TABLE ARRIVES P4" },
  rail: { n: 4, name: "RAIL", Icon: StRail, bays: [{ href: "/dashboard/uploads", label: "QUEUE" }], note: "THE CONVEYOR ARRIVES P2" },
  air: { n: 5, name: "AIR", Icon: StAir, bays: [{ href: "/dashboard", label: "SHELF" }, { href: "/dashboard/analytics", label: "INSTRUMENTS" }] },
  vault: { n: null, name: "VAULT", Icon: StVault, bays: [{ href: "/dashboard/clips", label: "FOOTAGE" }] },
  console: {
    n: null, name: "CONSOLE", Icon: StConsole,
    bays: [
      { href: "/dashboard/settings", label: "KEYS & CHANNELS" },
      { href: "/dashboard/billing", label: "LEDGER" },
      { href: "/dashboard/series", label: "STANDING ORDERS" },
    ],
    note: "COMMAND-FIRST SERVICE PANEL ARRIVES P6",
  },
}

function frameFor(pathname: string) {
  if (pathname.startsWith("/dashboard/topics")) return FRAMES.signal
  if (pathname.startsWith("/dashboard/studio")) return FRAMES.desk
  if (pathname.startsWith("/dashboard/preview") || pathname.startsWith("/dashboard/uploads")) return FRAMES.rail
  if (pathname.startsWith("/dashboard/clips")) return FRAMES.vault
  if (["/dashboard/settings", "/dashboard/billing", "/dashboard/series"].some(p => pathname.startsWith(p))) return FRAMES.console
  return FRAMES.air
}

export default function LineShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const reduced = useReducedMotion()
  const frame = frameFor(pathname)
  const idx = stationIndexFor(pathname)
  // Travel direction: derived during render from the last station stood at.
  const [prev, setPrev] = useState({ idx: idx >= 0 ? idx : 0, direction: 1 })
  const direction = idx >= 0 && idx !== prev.idx ? Math.sign(idx - prev.idx) || 1 : prev.direction
  if (idx >= 0 && idx !== prev.idx) setPrev({ idx, direction })

  return (
    <div style={{ minHeight: "100vh", background: L.floor, color: L.ink, fontFamily: grotesque }}>
      {/* Station header strip */}
      <header style={{ position: "sticky", top: 0, zIndex: 50, height: 40, background: L.floor, borderBottom: `1px solid ${L.rule}`, display: "flex", alignItems: "center", gap: 16, padding: "0 20px" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <frame.Icon size={14} color={L.ash} />
          <span style={{ ...tele(L.ink, "0.16em"), fontSize: 11 }}>
            {frame.n ? `STATION ${"0" + frame.n} · ` : ""}{frame.name}
          </span>
        </span>
        <span aria-hidden style={{ flex: "0 0 1px", height: 16, background: L.rule }} />
        <nav aria-label="Bays" style={{ display: "flex", gap: 2 }}>
          {frame.bays.map(b => {
            const on = pathname === b.href || (b.href !== "/dashboard" && pathname.startsWith(b.href))
            return (
              <Link key={b.href} href={b.href}
                style={{ ...tele(on ? L.ink : L.dust, "0.12em"), textDecoration: "none", padding: "5px 10px", borderBottom: `2px solid ${on ? L.ink : "transparent"}` }}>
                {b.label}
              </Link>
            )
          })}
        </nav>
        {frame.note && (
          <span className="hidden lg:inline" style={{ ...tele(L.dust, "0.08em"), fontSize: 9, marginLeft: "auto" }}>{frame.note}</span>
        )}
      </header>

      {/* The floor — content travels through it */}
      <div style={{ position: "relative", overflow: "hidden" }}>
        {/* Painted floor numeral */}
        <div aria-hidden style={{ position: "absolute", top: 18, right: 24, opacity: 0.5, pointerEvents: "none", zIndex: 0 }}>
          {frame.n && <StationNumeral n={frame.n} size={110} color={L.ruleFaint} />}
        </div>
        {/* Lane rule */}
        <div aria-hidden style={{ position: "absolute", left: 0, right: 0, top: 0, height: "100%", pointerEvents: "none", backgroundImage: `repeating-linear-gradient(90deg, transparent 0 calc(20% - 1px), ${L.ruleFaint}33 calc(20% - 1px) 20%)` }} />

        <AnimatePresence mode="popLayout" initial={false} custom={direction}>
          <motion.main
            key={frame.name + (frame.bays.some(b => pathname.startsWith(b.href) && b.href !== "/dashboard") ? pathname : "")}
            custom={direction}
            initial={reduced ? {} : { x: 56 * direction, opacity: 0.4 }}
            animate={{ x: 0, opacity: 1 }}
            exit={reduced ? {} : { x: -56 * direction, opacity: 0 }}
            transition={{ duration: reduced ? 0 : MOTION.station, ease: MOTION.ease }}
            style={{ position: "relative", zIndex: 1, minHeight: "calc(100vh - 86px)", padding: "28px 32px 76px", maxWidth: 1400, margin: "0 auto" }}
          >
            {children}
          </motion.main>
        </AnimatePresence>
      </div>

      <TransportBar />
    </div>
  )
}
