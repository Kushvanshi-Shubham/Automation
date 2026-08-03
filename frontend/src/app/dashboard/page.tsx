"use client"

/**
 * Library — everything you've made, with real thumbnails and statuses in
 * plain words. A compact summary line instead of KPI cards. Themed.
 */
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { useState } from "react"
import { MdOutlineExplore, MdOutlineMovieFilter } from "react-icons/md"
import { API_BASE_URL, fetchApi } from "@/lib/api-client"
import { useCredits } from "@/hooks/use-credits"
import { L, mono, grotesque, alpha } from "@/lib/line/tokens"

const MEDIA_ORIGIN = API_BASE_URL.replace(/\/api\/?$/, "")

interface VideoItem {
  id: string
  status: string
  output_type: string
  title: string | null
  video_url: string | null
  created_at: string | null
}

const STATUS: Record<string, { label: string; color: string; spin?: boolean }> = {
  published: { label: "Live on your channel", color: L.live },
  scheduled: { label: "Scheduled", color: L.working },
  ready: { label: "Ready to publish", color: L.ready },
  rendering: { label: "Rendering…", color: L.working, spin: true },
  publishing: { label: "Uploading…", color: L.working, spin: true },
  script_ready: { label: "Script — continue editing", color: L.ash },
  draft: { label: "Draft", color: L.dust },
  failed: { label: "Failed — refunded", color: L.refused },
  upload_failed: { label: "Upload failed", color: L.refused },
}

const FILTERS = [
  { key: "all", label: "All" },
  { key: "live", label: "Live" },
  { key: "ready", label: "Ready" },
  { key: "working", label: "In progress" },
  { key: "scripts", label: "Scripts" },
] as const

const card: React.CSSProperties = { background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 10 }

export default function LibraryPage() {
  const { credits } = useCredits()
  const [filter, setFilter] = useState<(typeof FILTERS)[number]["key"]>("all")

  const { data, isLoading } = useQuery<{ items: VideoItem[]; total: number }>({
    queryKey: ["videos"],
    queryFn: () => fetchApi("/videos?page=1&page_size=50"),
    refetchInterval: q =>
      (q.state.data?.items ?? []).some(v => ["rendering", "publishing"].includes(v.status)) ? 5000 : false,
  })

  const videos = data?.items ?? []
  const live = videos.filter(v => v.status === "published").length
  const working = videos.filter(v => ["rendering", "publishing"].includes(v.status)).length
  const readyCount = videos.filter(v => v.status === "ready").length

  const filtered = videos.filter(v => {
    if (filter === "live") return v.status === "published" || v.status === "scheduled"
    if (filter === "ready") return v.status === "ready"
    if (filter === "working") return ["rendering", "publishing", "failed", "upload_failed"].includes(v.status)
    if (filter === "scripts") return ["script_ready", "draft"].includes(v.status)
    return true
  })

  const pill = (on: boolean): React.CSSProperties => ({
    background: on ? L.benchRaised : "transparent", border: `1px solid ${on ? L.ink : L.rule}`,
    color: on ? L.ink : L.ash, fontFamily: grotesque, fontSize: 12.5, padding: "6px 12px",
    borderRadius: 20, cursor: "pointer", whiteSpace: "nowrap",
  })

  return (
    <div style={{ fontFamily: grotesque }}>
      {/* Header + summary line */}
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 20, flexWrap: "wrap", marginBottom: 18 }}>
        <div>
          <h1 style={{ margin: "0 0 4px", fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>Library</h1>
          <p style={{ margin: 0, fontSize: 14, color: L.ash }}>
            <span style={{ fontFamily: mono, color: L.ink }}>{data?.total ?? "…"}</span> shorts
            {" · "}<span style={{ fontFamily: mono, color: L.live }}>{live}</span> live
            {readyCount > 0 && <>{" · "}<span style={{ fontFamily: mono, color: L.ready }}>{readyCount}</span> ready for you</>}
            {working > 0 && <>{" · "}<span style={{ fontFamily: mono, color: L.working }}>{working}</span> in progress</>}
            {" · "}<span style={{ fontFamily: mono, color: L.ink }}>{credits}</span> credits left
          </p>
        </div>
        <Link href="/dashboard/topics"
          style={{ display: "flex", alignItems: "center", gap: 7, background: L.make, color: "#fff", textDecoration: "none", fontSize: 13.5, fontWeight: 600, padding: "10px 16px", borderRadius: 8 }}>
          <MdOutlineExplore size={17} /> Create from a trend
        </Link>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 20 }}>
        {FILTERS.map(f => (
          <button key={f.key} onClick={() => setFilter(f.key)} style={pill(filter === f.key)}>{f.label}</button>
        ))}
      </div>

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => <div key={i} style={{ ...card, height: 180, opacity: 0.5 }} />)}
        </div>
      )}

      {!isLoading && videos.length === 0 && (
        <div style={{ ...card, padding: "36px 32px", maxWidth: 720 }}>
          <h2 style={{ margin: "0 0 8px", fontSize: 18, fontWeight: 600 }}>Nothing here yet</h2>
          <p style={{ margin: "0 0 18px", fontSize: 14, lineHeight: 1.6, color: L.ash, maxWidth: "56ch" }}>
            Everything you make lands here — scripts, renders in progress, finished shorts, and what&apos;s live on
            your channel. Start with a trending topic or your own idea.
          </p>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Link href="/dashboard/topics"
              style={{ display: "flex", alignItems: "center", gap: 7, background: L.make, color: "#fff", textDecoration: "none", fontSize: 13.5, fontWeight: 600, padding: "10px 16px", borderRadius: 8 }}>
              <MdOutlineExplore size={17} /> Pick a trending topic
            </Link>
            <Link href="/dashboard/studio"
              style={{ display: "flex", alignItems: "center", gap: 7, background: "transparent", border: `1px solid ${L.rule}`, color: L.ink, textDecoration: "none", fontSize: 13.5, padding: "10px 16px", borderRadius: 8 }}>
              <MdOutlineMovieFilter size={17} /> Start from your own idea
            </Link>
          </div>
        </div>
      )}

      {!isLoading && filtered.length === 0 && videos.length > 0 && (
        <p style={{ fontSize: 14, color: L.ash }}>Nothing matches this filter.</p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filtered.map(video => {
          const st = STATUS[video.status] ?? STATUS.draft
          const href = video.status === "script_ready"
            ? `/dashboard/studio?video=${video.id}`
            : `/dashboard/preview/${video.id}`
          return (
            <Link key={video.id} href={href} style={{ textDecoration: "none" }}>
              <div
                style={{ ...card, overflow: "hidden", transition: "border-color 120ms, transform 120ms" }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = L.ash; e.currentTarget.style.transform = "translateY(-2px)" }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--k-rule)"; e.currentTarget.style.transform = "none" }}
              >
                {/* Thumbnail */}
                <div style={{ position: "relative", aspectRatio: "16/10", background: L.benchRaised }}>
                  {video.video_url ? (
                    <video src={`${MEDIA_ORIGIN}${video.video_url}`} preload="metadata" muted playsInline
                      style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
                  ) : (
                    <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <MdOutlineMovieFilter size={30} color={L.dust} />
                    </div>
                  )}
                  <span style={{ position: "absolute", left: 10, top: 10, fontSize: 11, fontWeight: 600, color: st.color, background: "var(--k-bench)", border: `1px solid ${alpha(st.color, 35)}`, padding: "3px 8px", borderRadius: 5 }}>
                    {st.label}
                  </span>
                </div>
                <div style={{ padding: "13px 15px" }}>
                  <p style={{ margin: "0 0 4px", fontSize: 14.5, fontWeight: 600, lineHeight: 1.35, color: L.ink, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                    {video.title ?? "Untitled short"}
                  </p>
                  <p style={{ margin: 0, fontSize: 12, color: L.dust }}>
                    {video.created_at ? new Date(video.created_at).toLocaleDateString() : ""}
                    {" · "}{video.status === "script_ready" ? "Continue editing" : "Open"}
                  </p>
                </div>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
