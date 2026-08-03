"use client"

/**
 * The transport bar — Kliptos' navigation instrument. Plain names, live
 * counts, Material icons, theme toggle. Keys 1–4 travel.
 */
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { signOut, useSession } from "next-auth/react"
import { useTheme } from "next-themes"
import { useEffect, useState } from "react"
import {
  MdOutlineExplore, MdOutlineMovieFilter, MdOutlinePrecisionManufacturing,
  MdOutlineVideoLibrary, MdOutlinePermMedia, MdOutlineDarkMode, MdOutlineLightMode,
} from "react-icons/md"
import { fetchApi } from "@/lib/api-client"
import { L, mono, grotesque, alpha } from "@/lib/line/tokens"

interface VideoT { id: string; status: string; youtube_video_id: string | null; published_at: string | null }

export const STATIONS = [
  { key: "discover", label: "Discover", href: "/dashboard/topics", Icon: MdOutlineExplore },
  { key: "create", label: "Create", href: "/dashboard/studio", Icon: MdOutlineMovieFilter },
  { key: "production", label: "Production", href: "/dashboard/rail", Icon: MdOutlinePrecisionManufacturing },
  { key: "library", label: "Library", href: "/dashboard", Icon: MdOutlineVideoLibrary },
] as const

export function stationIndexFor(pathname: string): number {
  if (pathname.startsWith("/dashboard/topics")) return 0
  if (pathname.startsWith("/dashboard/studio")) return 1
  if (pathname.startsWith("/dashboard/preview") || pathname.startsWith("/dashboard/uploads") || pathname.startsWith("/dashboard/rail")) return 2
  if (pathname.startsWith("/dashboard/analytics") || pathname === "/dashboard") return 3
  return -1
}

export default function TransportBar() {
  const pathname = usePathname()
  const router = useRouter()
  const { data: session } = useSession()
  const { resolvedTheme, setTheme } = useTheme()
  const [menuOpen, setMenuOpen] = useState(false)
  const [mounted, setMounted] = useState(false)
  useEffect(() => { const t = requestAnimationFrame(() => setMounted(true)); return () => cancelAnimationFrame(t) }, [])

  const { data: credits } = useQuery<{ balance: number; plan: string }>({
    queryKey: ["credits"], queryFn: () => fetchApi("/billing/credits"),
    staleTime: 20_000, refetchInterval: 60_000,
  })
  const { data: videos } = useQuery<{ items: VideoT[] }>({
    queryKey: ["line-videos"], queryFn: () => fetchApi("/videos?page_size=40"),
    staleTime: 8_000, refetchInterval: 15_000,
  })

  const items = videos?.items ?? []
  const working = items.filter(v => ["rendering", "publishing"].includes(v.status)).length
  const awaiting = items.filter(v => v.status === "ready" && !v.youtube_video_id && !v.published_at).length

  const active = stationIndexFor(pathname)
  const isFootage = pathname.startsWith("/dashboard/clips")
  const isAccount = ["/dashboard/settings", "/dashboard/billing", "/dashboard/series"].some(p => pathname.startsWith(p))

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = ["INPUT", "TEXTAREA", "SELECT"].includes((e.target as HTMLElement)?.tagName)
      if (typing || e.metaKey || e.ctrlKey || e.altKey) return
      const n = Number(e.key)
      if (n >= 1 && n <= 4) router.push(STATIONS[n - 1].href)
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [router])

  const lamp = (key: string) => {
    if (key === "production" && working > 0) return { color: L.working, label: String(working) }
    if (key === "production" && awaiting > 0) return { color: L.ready, label: String(awaiting) }
    if (key === "library" && awaiting > 0) return { color: L.ready, label: String(awaiting) }
    return null
  }

  return (
    <nav
      aria-label="Kliptos"
      style={{
        position: "fixed", left: 0, right: 0, bottom: 0, zIndex: 60, height: 50,
        background: L.bench, borderTop: `1px solid ${L.rule}`, fontFamily: grotesque,
        display: "grid", gridTemplateColumns: "auto 1fr auto",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", padding: "0 14px", borderRight: `1px solid ${L.rule}` }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/brand/kliptos-logo-2k.jpeg" alt="Kliptos" style={{ width: 24, height: 24, borderRadius: 4, objectFit: "cover" }} />
      </div>

      <div role="tablist" style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)" }}>
        {STATIONS.map((s, i) => {
          const isActive = active === i
          const l = lamp(s.key)
          return (
            <Link
              key={s.key} href={s.href} role="tab" aria-selected={isActive} prefetch
              style={{
                position: "relative", display: "flex", alignItems: "center", justifyContent: "center",
                gap: 8, textDecoration: "none", borderRight: `1px solid ${L.ruleFaint}`,
                background: isActive ? L.benchRaised : "transparent", transition: "background 120ms",
              }}
            >
              {isActive && <span aria-hidden style={{ position: "absolute", top: -1, left: 0, right: 0, height: 2, background: L.make }} />}
              <s.Icon size={19} color={isActive ? L.ink : L.ash} />
              <span style={{ fontSize: 13.5, fontWeight: isActive ? 600 : 400, color: isActive ? L.ink : L.ash }}>{s.label}</span>
              {l && (
                <span style={{ fontFamily: mono, fontSize: 10, color: l.color, border: `1px solid ${alpha(l.color, 40)}`, padding: "1px 5px", borderRadius: 3 }}>
                  {l.label}
                </span>
              )}
            </Link>
          )
        })}
      </div>

      <div style={{ display: "flex", alignItems: "center", borderLeft: `1px solid ${L.rule}` }}>
        <Link href="/dashboard/clips" prefetch
          style={{ display: "flex", alignItems: "center", gap: 7, padding: "0 14px", height: "100%", borderRight: `1px solid ${L.ruleFaint}`, background: isFootage ? L.benchRaised : "transparent", textDecoration: "none", position: "relative" }}>
          {isFootage && <span aria-hidden style={{ position: "absolute", top: -1, left: 0, right: 0, height: 2, background: L.make }} />}
          <MdOutlinePermMedia size={17} color={isFootage ? L.ink : L.ash} />
          <span className="hidden md:inline" style={{ fontSize: 13.5, color: isFootage ? L.ink : L.ash }}>Footage</span>
        </Link>
        <span style={{ padding: "0 14px", fontFamily: mono, fontSize: 12, color: L.ink }}>
          {credits?.balance ?? "…"}<span style={{ color: L.dust, fontSize: 10 }}> credits</span>
        </span>
        <button onClick={() => setMenuOpen(o => !o)} aria-expanded={menuOpen} aria-label="Account"
          style={{ display: "flex", alignItems: "center", gap: 8, padding: "0 14px", height: "100%", borderLeft: `1px solid ${L.ruleFaint}`, background: isAccount || menuOpen ? L.benchRaised : "transparent", border: "none", cursor: "pointer", position: "relative", fontFamily: grotesque }}>
          {isAccount && <span aria-hidden style={{ position: "absolute", top: -1, left: 0, right: 0, height: 2, background: L.make }} />}
          <span style={{ width: 24, height: 24, borderRadius: 4, background: L.benchRaised, border: `1px solid ${L.rule}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, color: L.ash, overflow: "hidden" }}>
            {session?.user?.image
              // eslint-disable-next-line @next/next/no-img-element
              ? <img src={session.user.image} alt="" referrerPolicy="no-referrer" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              : (session?.user?.name ?? "?").charAt(0).toUpperCase()}
          </span>
          <span className="hidden md:inline" style={{ fontSize: 13.5, color: isAccount || menuOpen ? L.ink : L.ash }}>Account</span>
        </button>
      </div>

      {menuOpen && (
        <div role="menu" style={{ position: "absolute", right: 8, bottom: 56, width: 250, background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 4, overflow: "hidden", fontFamily: grotesque, boxShadow: "0 8px 32px rgba(0,0,0,0.28)" }}>
          <div style={{ padding: "12px 14px 10px", borderBottom: `1px solid ${L.ruleFaint}` }}>
            <p style={{ margin: 0, fontSize: 13.5, fontWeight: 600, color: L.ink }}>{session?.user?.name}</p>
            <p style={{ margin: "2px 0 0", fontSize: 11.5, color: L.dust }}>{session?.user?.email}</p>
          </div>
          {[
            { href: "/dashboard/settings", label: "Settings — keys & channels" },
            { href: "/dashboard/billing", label: "Billing & credits" },
            { href: "/dashboard/series", label: "Standing orders" },
          ].map(i => (
            <Link key={i.href} href={i.href} role="menuitem" onClick={() => setMenuOpen(false)}
              style={{ display: "block", padding: "10px 14px", fontSize: 13, color: L.ink, textDecoration: "none", borderTop: `1px solid ${L.ruleFaint}` }}>
              {i.label}
            </Link>
          ))}
          {mounted && (
            <button role="menuitem" onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
              style={{ display: "flex", alignItems: "center", gap: 8, width: "100%", textAlign: "left", padding: "10px 14px", fontSize: 13, color: L.ink, background: "transparent", border: "none", borderTop: `1px solid ${L.ruleFaint}`, cursor: "pointer", fontFamily: grotesque }}>
              {resolvedTheme === "dark" ? <MdOutlineLightMode size={16} /> : <MdOutlineDarkMode size={16} />}
              {resolvedTheme === "dark" ? "Switch to light" : "Switch to dark"}
            </button>
          )}
          <button role="menuitem" onClick={() => signOut({ redirectTo: "/" })}
            style={{ display: "block", width: "100%", textAlign: "left", padding: "10px 14px", fontSize: 13, color: L.ash, background: "transparent", border: "none", borderTop: `1px solid ${L.ruleFaint}`, cursor: "pointer", fontFamily: grotesque }}>
            Sign out
          </button>
        </div>
      )}
    </nav>
  )
}
