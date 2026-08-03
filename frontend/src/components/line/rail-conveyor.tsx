"use client"

/**
 * STATION 04 — THE RAIL. The signature surface of THE LINE.
 * Every in-flight short is a physical reel riding a rail through the five
 * real gates of the renderer. Position = actual telemetry, not theater.
 * Failure is never a toast: the reel shunts to the refund siding with its
 * receipt attached.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { motion, useReducedMotion } from "framer-motion"
import { useRouter } from "next/navigation"
import { fetchApi } from "@/lib/api-client"
import { L, mono, tele } from "@/lib/line/tokens"
import { StReel, StSiding } from "@/components/line/stencils"

const GATES = [
  { name: "QUEUED", at: 0 }, { name: "VOICE", at: 10 }, { name: "VISUALS", at: 35 },
  { name: "ASSEMBLY", at: 65 }, { name: "MUSIC", at: 90 }, { name: "READY", at: 100 },
]
const FORMAT_CODES: Record<string, string> = { narrated: "NR", visual: "VS", fake_text: "TX", image: "IM", clip: "CL", script: "SC" }
const INFO_W = 270 // left info block; the rail owns the rest

interface VideoT {
  id: string; status: string; output_type: string; title: string | null
  video_url: string | null; youtube_video_id: string | null; published_at: string | null
  scheduled_at: string | null; created_at: string | null; series_id?: string | null
}
interface ActiveJob { job_id: string; video_id: string; status: string; progress: { stage?: string; percent?: number } }

export default function RailConveyor() {
  const qc = useQueryClient()
  const router = useRouter()
  const reduced = useReducedMotion()

  const { data: videos } = useQuery<{ items: VideoT[] }>({
    queryKey: ["line-videos"],
    queryFn: () => fetchApi("/videos?page_size=40"),
    refetchInterval: 8000,
  })
  const anyWorking = (videos?.items ?? []).some(v => ["rendering", "publishing"].includes(v.status))
  const { data: active } = useQuery<{ items: ActiveJob[] }>({
    queryKey: ["pipeline-active"],
    queryFn: () => fetchApi("/pipeline/active"),
    refetchInterval: anyWorking ? 3000 : 15000,
  })
  const jobByVideo = new Map((active?.items ?? []).map(j => [j.video_id, j]))

  const retry = useMutation({
    mutationFn: (v: VideoT) => fetchApi("/pipeline/start", {
      method: "POST",
      body: JSON.stringify({ video_id: v.id, visual_engine: v.output_type === "image" ? "stock_image" : "pexels" }),
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["line-videos"] })
      qc.invalidateQueries({ queryKey: ["pipeline-active"] })
      qc.invalidateQueries({ queryKey: ["credits"] })
    },
  })

  const items = videos?.items ?? []
  const riding = items.filter(v => ["rendering", "publishing"].includes(v.status))
  const parked = items.filter(v => v.status === "ready" && !v.youtube_video_id && !v.published_at)
  const sided = items.filter(v => ["failed", "upload_failed"].includes(v.status)).slice(0, 5)
  const lanes = [...riding, ...parked]

  const reelPct = (v: VideoT): number => {
    if (v.status === "publishing") return 100
    if (v.status === "ready") return 100
    const j = jobByVideo.get(v.id)
    return Math.max(0, Math.min(100, j?.progress?.percent ?? 0))
  }
  const stateOf = (v: VideoT) => {
    if (v.status === "publishing") return { color: L.live, label: "Uploading to your channel" }
    if (v.status === "ready") return { color: L.ready, label: "Ready — waiting for you" }
    const j = jobByVideo.get(v.id)
    const stage = (j?.progress?.stage ?? "queued").toUpperCase()
    const pct = Math.round(j?.progress?.percent ?? 0)
    return { color: L.working, label: `${stage} · ${pct}%` }
  }

  return (
    <div>
      <h1 style={{ margin: "0 0 4px", fontSize: 30, fontWeight: 700, letterSpacing: "-0.025em" }}>In production</h1>
      <p style={{ margin: "0 0 28px", fontSize: 13.5, color: L.ash }}>
        {lanes.length === 0 ? "Nothing rendering right now" : `${riding.length} rendering · ${parked.length} waiting for your approval`} — positions are live, straight from the renderer
      </p>

      {/* Gate header */}
      <div style={{ display: "grid", gridTemplateColumns: `${INFO_W}px 1fr`, marginBottom: 6 }}>
        <span />
        <div style={{ position: "relative", height: 26 }}>
          {GATES.map(g => (
            <span key={g.name} style={{ position: "absolute", left: `${g.at}%`, transform: g.at === 0 ? "none" : g.at === 100 ? "translateX(-100%)" : "translateX(-50%)", ...tele(g.name === "READY" ? L.ready : L.dust, "0.12em"), fontSize: 9 }}>
              {g.name}
            </span>
          ))}
        </div>
      </div>

      {/* Lanes */}
      <div style={{ border: `1px solid ${L.rule}`, borderRadius: 2, background: L.bench, overflow: "hidden" }}>
        {lanes.length === 0 && (
          <div style={{ display: "grid", gridTemplateColumns: `${INFO_W}px 1fr`, minHeight: 96 }}>
            <div style={{ padding: "20px 18px", borderRight: `1px solid ${L.ruleFaint}` }}>
              <p style={{ margin: 0, fontSize: 14, color: L.ash, lineHeight: 1.55 }}>
                Nothing is rendering. Pick a trend in Discover or start from an idea in Create — the render travels these gates live.
              </p>
            </div>
            <div style={{ position: "relative" }}>
              <span aria-hidden style={{ position: "absolute", left: 0, right: 0, bottom: 28, height: 1, background: L.rule }} />
              {GATES.map(g => (
                <motion.span
                  key={g.name}
                  aria-hidden
                  animate={reduced ? {} : { opacity: [0.25, 0.7, 0.25] }}
                  transition={{ duration: 3.2, repeat: Infinity, delay: g.at / 60 }}
                  style={{ position: "absolute", left: `${g.at}%`, top: 16, bottom: 16, width: 1, background: L.rule, marginLeft: g.at === 100 ? -1 : 0 }}
                />
              ))}
            </div>
          </div>
        )}

        {lanes.map(v => {
          const pct = reelPct(v)
          const st = stateOf(v)
          const j = jobByVideo.get(v.id)
          return (
            <div key={v.id} style={{ display: "grid", gridTemplateColumns: `${INFO_W}px 1fr`, borderTop: `1px solid ${L.ruleFaint}`, minHeight: 78 }}>
              {/* Info block */}
              <div style={{ padding: "14px 18px", borderRight: `1px solid ${L.ruleFaint}`, minWidth: 0 }}>
                <p style={{ margin: "0 0 5px", fontSize: 14, fontWeight: 600, lineHeight: 1.3, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{v.title ?? "Untitled"}</p>
                <p style={{ margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ ...tele(L.dust, "0.06em") }}>{FORMAT_CODES[v.output_type] ?? "NR"}</span>
                  {v.series_id && <span style={{ ...tele(L.working, "0.06em"), border: `1px solid ${L.working}55`, padding: "1px 5px", borderRadius: 2 }}>AUTO</span>}
                  <span style={{ ...tele(st.color, "0.06em") }}>{st.label}</span>
                </p>
                {v.status === "ready" && (
                  <button
                    onClick={() => router.push(`/dashboard/preview/${v.id}`)}
                    style={{ marginTop: 8, background: L.make, border: "none", color: "#0B0C0E", fontFamily: mono, fontSize: 10, letterSpacing: "0.08em", padding: "7px 10px", borderRadius: 2, cursor: "pointer" }}
                  >
                    Review & approve
                  </button>
                )}
              </div>

              {/* The rail */}
              <button
                onClick={() => router.push(`/dashboard/preview/${v.id}${j ? `?job=${j.job_id}` : ""}`)}
                aria-label={`Open ${v.title ?? "reel"}`}
                style={{ position: "relative", background: "transparent", border: "none", cursor: "pointer", padding: 0 }}
              >
                <span aria-hidden style={{ position: "absolute", left: 0, right: 0, bottom: 24, height: 1, background: L.rule }} />
                {GATES.map(g => {
                  const passed = pct >= g.at && (v.status !== "rendering" || pct > 0 || g.at === 0)
                  return (
                    <span key={g.name} aria-hidden style={{ position: "absolute", left: `${g.at}%`, top: 14, bottom: 14, width: 1, marginLeft: g.at === 100 ? -1 : 0, background: passed ? (v.status === "ready" || v.status === "publishing" ? L.ready : L.working) : L.rule, opacity: passed ? 0.9 : 0.5 }} />
                  )
                })}
                {/* The reel — the object being made (the only violet on the floor) */}
                <span
                  style={{
                    position: "absolute", bottom: 13, left: `calc(${pct}% - 12px)`,
                    transition: reduced ? "none" : "left 1.4s linear",
                    display: "flex", flexDirection: "column", alignItems: "center", gap: 2,
                  }}
                >
                  <motion.span
                    animate={v.status === "rendering" && !reduced ? { rotate: 360 } : {}}
                    transition={{ duration: 2.4, repeat: Infinity, ease: "linear" }}
                    style={{ display: "block", lineHeight: 0 }}
                  >
                    <StReel size={24} color={v.status === "ready" ? L.ready : L.make} />
                  </motion.span>
                </span>
                {v.status === "publishing" && (
                  <span style={{ position: "absolute", right: 6, top: 10, ...tele(L.live, "0.1em"), fontSize: 9 }}>→ AIR</span>
                )}
              </button>
            </div>
          )
        })}
      </div>

      {/* The refund siding */}
      {sided.length > 0 && (
        <div style={{ marginTop: 26 }}>
          <p style={{ display: "flex", alignItems: "center", gap: 8, margin: "0 0 10px" }}>
            <StSiding size={14} color={L.refused} />
            <span style={{ fontSize: 13, fontWeight: 600, color: L.refused }}>Refused — credits returned automatically</span>
          </p>
          <div style={{ border: `1px solid ${L.refused}33`, borderRadius: 2, background: L.bench }}>
            {sided.map(v => (
              <div key={v.id} style={{ display: "grid", gridTemplateColumns: "24px 1fr auto auto", gap: 14, alignItems: "center", padding: "12px 16px", borderTop: `1px solid ${L.ruleFaint}` }}>
                <StReel size={18} color={L.refused} />
                <span style={{ minWidth: 0 }}>
                  <span style={{ display: "block", fontSize: 13.5, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{v.title ?? "Untitled"}</span>
                  <span style={{ ...tele(L.dust, "0.06em") }}>
                    {v.status === "upload_failed" ? "Upload failed — the render is intact" : "Render failed — refunded"}
                  </span>
                </span>
                <span style={{ ...tele(L.ready, "0.06em") }}>+1 CREDIT</span>
                {v.status === "upload_failed" ? (
                  <button onClick={() => router.push(`/dashboard/preview/${v.id}`)}
                    style={{ background: "transparent", border: `1px solid ${L.rule}`, color: L.ash, fontFamily: mono, fontSize: 10, letterSpacing: "0.06em", padding: "7px 10px", borderRadius: 2, cursor: "pointer" }}>
                    Publish again
                  </button>
                ) : (
                  <button onClick={() => retry.mutate(v)} disabled={retry.isPending}
                    style={{ background: "transparent", border: `1px solid ${L.make}66`, color: L.make, fontFamily: mono, fontSize: 10, letterSpacing: "0.06em", padding: "7px 10px", borderRadius: 2, cursor: "pointer" }}>
                    {retry.isPending ? "Requeueing…" : "Retry · 1 credit"}
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
