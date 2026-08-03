"use client"

/**
 * THE TRANSPORT BAR — the signature navigation element of THE LINE.
 * Nav + system state in one instrument: five station segments with live
 * telemetry, a playhead marking where you stand, keys 1–5 to travel.
 * There is no sidebar. There is no navbar. There is the line.
 */
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { signOut, useSession } from "next-auth/react"
import { useEffect, useState } from "react"
import { fetchApi } from "@/lib/api-client"
import { L, mono, tele } from "@/lib/line/tokens"
import { StSignal, StDesk, StStage, StRail, StAir, StVault, StConsole } from "@/components/line/stencils"

interface VideoT { id: string; status: string; youtube_video_id: string | null; published_at: string | null }

export const STATIONS = [
  { n: 1, key: "signal", name: "SIGNAL", href: "/dashboard/topics", Icon: StSignal },
  { n: 2, key: "desk", name: "DESK", href: "/dashboard/studio", Icon: StDesk },
  { n: 3, key: "stage", name: "STAGE", href: "/dashboard/studio", Icon: StStage, fitting: "FITS OUT · P4" },
  { n: 4, key: "rail", name: "RAIL", href: "/dashboard/uploads", Icon: StRail },
  { n: 5, key: "air", name: "AIR", href: "/dashboard", Icon: StAir },
] as const

export function stationIndexFor(pathname: string): number {
  if (pathname.startsWith("/dashboard/topics")) return 0
  if (pathname.startsWith("/dashboard/studio")) return 1
  if (pathname.startsWith("/dashboard/preview") || pathname.startsWith("/dashboard/uploads")) return 3
  if (pathname.startsWith("/dashboard/analytics") || pathname === "/dashboard") return 4
  return -1 // vault (clips) / console (settings, billing, series)
}

export default function TransportBar() {
  const pathname = usePathname()
  const router = useRouter()
  const { data: session } = useSession()
  const [endCapOpen, setEndCapOpen] = useState(false)

  const { data: credits } = useQuery<{ balance: number; plan: string }>({
    queryKey: ["credits"], queryFn: () => fetchApi("/billing/credits"), refetchInterval: 30_000,
  })
  const { data: videos } = useQuery<{ items: VideoT[] }>({
    queryKey: ["line-videos"], queryFn: () => fetchApi("/videos?page_size=40"), refetchInterval: 10_000,
  })

  const items = videos?.items ?? []
  const working = items.filter(v => ["rendering", "publishing"].includes(v.status)).length
  const awaiting = items.filter(v => v.status === "ready" && !v.youtube_video_id && !v.published_at).length
  const onAir = items.filter(v => v.youtube_video_id || v.published_at).length

  const active = stationIndexFor(pathname)
  const isVault = pathname.startsWith("/dashboard/clips")
  const isConsole = ["/dashboard/settings", "/dashboard/billing", "/dashboard/series"].some(p => pathname.startsWith(p))

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = ["INPUT", "TEXTAREA", "SELECT"].includes((e.target as HTMLElement)?.tagName)
      if (typing || e.metaKey || e.ctrlKey || e.altKey) return
      const n = Number(e.key)
      if (n >= 1 && n <= 5) router.push(STATIONS[n - 1].href)
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [router])

  const lamp = (station: (typeof STATIONS)[number]) => {
    if (station.key === "rail" && working > 0) return { color: L.working, label: String(working) }
    if (station.key === "rail" && awaiting > 0) return { color: L.ready, label: String(awaiting) }
    if (station.key === "air" && awaiting > 0) return { color: L.ready, label: String(awaiting) }
    if (station.key === "air" && onAir > 0) return { color: L.live, label: String(onAir) }
    return null
  }

  return (
    <nav
      aria-label="The line"
      style={{
        position: "fixed", left: 0, right: 0, bottom: 0, zIndex: 60, height: 46,
        background: L.bench, borderTop: `1px solid ${L.rule}`,
        display: "grid", gridTemplateColumns: "auto 1fr auto",
      }}
    >
      {/* Left end cap — the mark */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "0 14px", borderRight: `1px solid ${L.rule}` }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/brand/kliptos-logo-2k.jpeg" alt="Kliptos" style={{ width: 20, height: 20, borderRadius: 2, objectFit: "cover" }} />
        <span style={{ ...tele(L.dust, "0.14em") }} className="hidden sm:inline">THE LINE</span>
      </div>

      {/* The five stations */}
      <div role="tablist" style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)" }}>
        {STATIONS.map((s, i) => {
          const isActive = active === i || (s.key === "desk" && active === 1)
          const l = lamp(s)
          return (
            <Link
              key={s.key + s.n}
              href={s.href}
              role="tab"
              aria-selected={isActive}
              aria-label={`Station ${s.n} — ${s.name}`}
              style={{
                position: "relative", display: "flex", alignItems: "center", justifyContent: "center",
                gap: 8, textDecoration: "none", borderRight: `1px solid ${L.ruleFaint}`,
                background: isActive ? L.benchRaised : "transparent",
                transition: "background 120ms",
              }}
            >
              {/* Playhead */}
              {isActive && <span aria-hidden style={{ position: "absolute", top: -1, left: 0, right: 0, height: 2, background: L.ink }} />}
              <span style={{ ...tele(isActive ? L.ink : L.dust, "0.04em"), fontSize: 11 }}>{s.n}</span>
              <s.Icon size={14} color={isActive ? L.ink : L.ash} />
              <span className="hidden md:inline" style={{ ...tele(isActive ? L.ink : L.ash, "0.12em") }}>{s.name}</span>
              {l && (
                <span style={{ ...tele(l.color, "0.04em"), fontSize: 10, border: `1px solid ${l.color}55`, padding: "1px 5px", borderRadius: 2 }}>
                  {l.label}
                </span>
              )}
              {"fitting" in s && s.fitting && (
                <span className="hidden lg:inline" style={{ ...tele(L.dust, "0.06em"), fontSize: 8 }}>{s.fitting}</span>
              )}
            </Link>
          )
        })}
      </div>

      {/* Right end cap — vault, console, credits, identity */}
      <div style={{ display: "flex", alignItems: "center", borderLeft: `1px solid ${L.rule}` }}>
        <Link href="/dashboard/clips" aria-label="Vault — your footage"
          style={{ display: "flex", alignItems: "center", gap: 7, padding: "0 12px", height: "100%", borderRight: `1px solid ${L.ruleFaint}`, background: isVault ? L.benchRaised : "transparent", textDecoration: "none", position: "relative" }}>
          {isVault && <span aria-hidden style={{ position: "absolute", top: -1, left: 0, right: 0, height: 2, background: L.ink }} />}
          <StVault size={14} color={isVault ? L.ink : L.ash} />
          <span className="hidden lg:inline" style={{ ...tele(isVault ? L.ink : L.ash, "0.12em") }}>VAULT</span>
        </Link>
        <button onClick={() => setEndCapOpen(o => !o)} aria-label="Console — services" aria-expanded={endCapOpen}
          style={{ display: "flex", alignItems: "center", gap: 7, padding: "0 12px", height: "100%", borderRight: `1px solid ${L.ruleFaint}`, background: isConsole || endCapOpen ? L.benchRaised : "transparent", border: "none", cursor: "pointer", position: "relative" }}>
          {isConsole && <span aria-hidden style={{ position: "absolute", top: -1, left: 0, right: 0, height: 2, background: L.ink }} />}
          <StConsole size={14} color={isConsole || endCapOpen ? L.ink : L.ash} />
          <span className="hidden lg:inline" style={{ ...tele(isConsole || endCapOpen ? L.ink : L.ash, "0.12em") }}>CONSOLE</span>
        </button>
        <div style={{ padding: "0 14px", display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontFamily: mono, fontSize: 12, color: L.ink }}>{credits?.balance ?? "…"}<span style={{ color: L.dust, fontSize: 10 }}> CR</span></span>
          <span title={session?.user?.email ?? ""} style={{ width: 20, height: 20, borderRadius: 2, background: L.benchRaised, border: `1px solid ${L.rule}`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: mono, fontSize: 10, color: L.ash }}>
            {(session?.user?.name ?? session?.user?.email ?? "?").charAt(0).toUpperCase()}
          </span>
        </div>
      </div>

      {/* Console popover (transitional until P6 makes it command-first) */}
      {endCapOpen && (
        <div
          role="menu"
          style={{ position: "absolute", right: 8, bottom: 52, width: 230, background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 2, overflow: "hidden" }}
        >
          <p style={{ ...tele(L.dust, "0.14em"), margin: 0, padding: "10px 12px 6px" }}>SERVICES · ⌘K ARRIVES P6</p>
          {[
            { href: "/dashboard/settings", label: "Keys & channels" },
            { href: "/dashboard/billing", label: "Credits & ledger" },
            { href: "/dashboard/series", label: "Standing orders" },
          ].map(i => (
            <Link key={i.href} href={i.href} role="menuitem" onClick={() => setEndCapOpen(false)}
              style={{ display: "block", padding: "9px 12px", fontSize: 13, color: L.ink, textDecoration: "none", borderTop: `1px solid ${L.ruleFaint}` }}>
              {i.label}
            </Link>
          ))}
          <button role="menuitem" onClick={() => signOut({ redirectTo: "/" })}
            style={{ display: "block", width: "100%", textAlign: "left", padding: "9px 12px", fontSize: 13, color: L.ash, background: "transparent", border: "none", borderTop: `1px solid ${L.ruleFaint}`, cursor: "pointer" }}>
            Sign out
          </button>
        </div>
      )}
    </nav>
  )
}
