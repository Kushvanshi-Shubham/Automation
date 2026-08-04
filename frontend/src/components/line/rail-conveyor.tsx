"use client"

/**
 * Production — written for someone on their first day.
 * Finished videos lead as watchable cards. Anything still rendering shows
 * its real position across five plainly-named steps (live telemetry).
 * Failures sit in "Needs attention" with the refund stated and a retry.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useRouter } from "next/navigation"
import { MdOutlineCheckCircle, MdOutlineExplore, MdOutlineMovieFilter, MdOutlineReplay } from "react-icons/md"
import { fetchApi, mediaUrl } from "@/lib/api-client"
import { L, mono, grotesque, alpha } from "@/lib/line/tokens"


// The renderer's real stages, in words a creator understands.
const STEPS = [
  { name: "Voice-over", from: 10 },
  { name: "Finding footage", from: 35 },
  { name: "Editing & captions", from: 65 },
  { name: "Adding music", from: 90 },
  { name: "Done", from: 100 },
]
const stepLabel = (pct: number) => {
  if (pct < 10) return { idx: 0, text: "Waiting in the queue" }
  const i = STEPS.findLastIndex(s => pct >= s.from)
  return { idx: i, text: STEPS[Math.min(i, STEPS.length - 2)].name }
}

const FORMAT_HUMAN: Record<string, string> = {
  narrated: "Narrated short", visual: "Visual short", fake_text: "Text-story short",
  image: "Image post", clip: "Clip from your footage", script: "Script",
}

interface VideoT {
  id: string; status: string; output_type: string; title: string | null
  video_url: string | null; youtube_video_id: string | null; published_at: string | null
  scheduled_at: string | null; created_at: string | null; series_id?: string | null; aspect_ratio?: string | null
}
interface ActiveJob { job_id: string; video_id: string; status: string; progress: { stage?: string; percent?: number } }

const card: React.CSSProperties = { background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 8, overflow: "hidden" }
const sectionTitle: React.CSSProperties = { margin: "0 0 4px", fontSize: 17, fontWeight: 600, letterSpacing: "-0.01em" }
const sectionSub: React.CSSProperties = { margin: "0 0 14px", fontSize: 13, color: L.ash }

export default function RailConveyor() {
  const qc = useQueryClient()
  const router = useRouter()

  const { data: videos } = useQuery<{ items: VideoT[] }>({
    queryKey: ["line-videos"],
    queryFn: () => fetchApi("/videos?page_size=40"),
    staleTime: 8_000, refetchInterval: 8000,
  })
  const anyWorking = (videos?.items ?? []).some(v => ["rendering", "publishing"].includes(v.status))
  const { data: active } = useQuery<{ items: ActiveJob[] }>({
    queryKey: ["pipeline-active"],
    queryFn: () => fetchApi("/pipeline/active"),
    refetchInterval: anyWorking ? 3000 : 20000,
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
  const rendering = items.filter(v => ["rendering", "publishing"].includes(v.status))
  const ready = items.filter(v => v.status === "ready" && !v.youtube_video_id && !v.published_at)
  const failed = items.filter(v => ["failed", "upload_failed"].includes(v.status)).slice(0, 6)
  const empty = rendering.length === 0 && ready.length === 0 && failed.length === 0

  return (
    <div style={{ fontFamily: grotesque }}>
      <h1 style={{ margin: "0 0 4px", fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>Production</h1>
      <p style={{ margin: "0 0 30px", fontSize: 14, color: L.ash, maxWidth: "72ch" }}>
        Every video is made in five steps — voice-over, footage, editing &amp; captions, music, done.
        This page shows yours moving through them, live.
      </p>

      {/* Ready to review — leads, as cards you can watch */}
      {ready.length > 0 && (
        <section style={{ marginBottom: 36 }}>
          <h2 style={sectionTitle}>Ready for your review</h2>
          <p style={sectionSub}>Watch each one — nothing publishes until you approve it.</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 14 }}>
            {ready.map(v => (
              <div key={v.id} style={card}>
                <div style={{ display: "grid", gridTemplateColumns: "132px 1fr", minHeight: 168 }}>
                  <div style={{ background: L.benchRaised, position: "relative" }}>
                    {v.video_url && (
                      <video src={mediaUrl(v.video_url)} preload="metadata" muted playsInline
                        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
                    )}
                  </div>
                  <div style={{ padding: "14px 16px", display: "flex", flexDirection: "column" }}>
                    <p style={{ margin: "0 0 6px", fontSize: 15, fontWeight: 600, lineHeight: 1.35 }}>{v.title ?? "Untitled"}</p>
                    <p style={{ margin: "0 0 4px", fontSize: 12.5, color: L.ash }}>
                      {FORMAT_HUMAN[v.output_type] ?? "Short"} · {v.aspect_ratio ?? "9:16"}
                      {v.series_id ? " · made by your standing order" : ""}
                    </p>
                    <p style={{ margin: 0, display: "flex", alignItems: "center", gap: 6, fontSize: 12.5, color: L.ready }}>
                      <MdOutlineCheckCircle size={15} /> Finished — waiting for you
                    </p>
                    <button
                      onClick={() => router.push(`/dashboard/preview/${v.id}`)}
                      style={{ marginTop: "auto", alignSelf: "flex-start", background: L.make, border: "none", color: "#fff", fontFamily: grotesque, fontSize: 13, fontWeight: 600, padding: "9px 16px", borderRadius: 6, cursor: "pointer" }}
                    >
                      Review &amp; publish
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Rendering now — the five steps, live */}
      {rendering.length > 0 && (
        <section style={{ marginBottom: 36 }}>
          <h2 style={sectionTitle}>Being made right now</h2>
          <p style={sectionSub}>Positions come straight from the renderer — this is not an animation.</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {rendering.map(v => {
              const j = jobByVideo.get(v.id)
              const pct = v.status === "publishing" ? 100 : Math.max(0, Math.min(100, j?.progress?.percent ?? 0))
              const step = v.status === "publishing"
                ? { idx: 4, text: "Uploading to your channel" }
                : stepLabel(pct)
              return (
                <div key={v.id} style={{ ...card, padding: "16px 20px" }}>
                  <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 16, marginBottom: 12, flexWrap: "wrap" }}>
                    <p style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>
                      {v.title ?? "Untitled"}
                      {v.series_id && <span style={{ marginLeft: 8, fontSize: 11, fontWeight: 400, color: L.working, border: `1px solid ${alpha(L.working, 40)}`, padding: "1px 6px", borderRadius: 3 }}>standing order</span>}
                    </p>
                    <p style={{ margin: 0, fontSize: 13, color: v.status === "publishing" ? L.live : L.working }}>
                      Step {Math.min(step.idx + 1, 5)} of 5 — {step.text}
                      <span style={{ fontFamily: mono, marginLeft: 8 }}>{Math.round(pct)}%</span>
                    </p>
                  </div>
                  {/* Five plainly-named steps */}
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 4 }}>
                    {STEPS.map((s, i) => {
                      const stepStart = i === 0 ? 10 : STEPS[i - 1].from
                      const done = pct >= s.from
                      const current = !done && pct >= (i === 0 ? 0 : stepStart)
                      const fill = done ? 100 : current ? Math.max(8, ((pct - stepStart) / (s.from - stepStart)) * 100) : 0
                      return (
                        <div key={s.name}>
                          <div style={{ height: 6, background: L.benchRaised, borderRadius: 3, overflow: "hidden" }}>
                            <div style={{ width: `${Math.min(100, fill)}%`, height: "100%", background: done ? L.ready : L.working, transition: "width 1.2s linear" }} />
                          </div>
                          <p style={{ margin: "6px 0 0", fontSize: 11, color: done ? L.ready : current ? L.ink : L.dust }}>{s.name}</p>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* Needs attention */}
      {failed.length > 0 && (
        <section style={{ marginBottom: 36 }}>
          <h2 style={sectionTitle}>Needs attention</h2>
          <p style={sectionSub}>These didn&apos;t finish. Your credit came back automatically — retrying costs 1 credit again.</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {failed.map(v => (
              <div key={v.id} style={{ ...card, borderColor: alpha(L.refused, 35), display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, padding: "13px 18px", flexWrap: "wrap" }}>
                <div style={{ minWidth: 0 }}>
                  <p style={{ margin: "0 0 2px", fontSize: 14, fontWeight: 600 }}>{v.title ?? "Untitled"}</p>
                  <p style={{ margin: 0, fontSize: 12.5, color: L.ash }}>
                    {v.status === "upload_failed" ? "The video is fine — publishing to YouTube failed." : "The render failed part-way."}{" "}
                    <span style={{ color: L.ready }}>Credit refunded.</span>
                  </p>
                </div>
                {v.status === "upload_failed" ? (
                  <button onClick={() => router.push(`/dashboard/preview/${v.id}`)}
                    style={{ display: "flex", alignItems: "center", gap: 6, background: "transparent", border: `1px solid ${L.rule}`, color: L.ink, fontFamily: grotesque, fontSize: 13, padding: "8px 14px", borderRadius: 6, cursor: "pointer" }}>
                    Try publishing again
                  </button>
                ) : (
                  <button onClick={() => retry.mutate(v)} disabled={retry.isPending}
                    style={{ display: "flex", alignItems: "center", gap: 6, background: "transparent", border: `1px solid ${alpha(L.make, 50)}`, color: L.make, fontFamily: grotesque, fontSize: 13, padding: "8px 14px", borderRadius: 6, cursor: "pointer" }}>
                    <MdOutlineReplay size={15} /> {retry.isPending ? "Starting…" : "Retry render · 1 credit"}
                  </button>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Empty — teach, don't decorate */}
      {empty && (
        <div style={{ ...card, padding: "36px 32px", maxWidth: 760 }}>
          <h2 style={{ margin: "0 0 8px", fontSize: 18, fontWeight: 600 }}>Nothing in production yet</h2>
          <p style={{ margin: "0 0 20px", fontSize: 14, lineHeight: 1.6, color: L.ash, maxWidth: "58ch" }}>
            When you create a video, it comes here and moves through five steps — voice-over, footage,
            editing &amp; captions, music, done. You&apos;ll watch its progress live, then review and publish it yourself.
          </p>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button onClick={() => router.push("/dashboard/topics")}
              style={{ display: "flex", alignItems: "center", gap: 7, background: L.make, border: "none", color: "#fff", fontFamily: grotesque, fontSize: 13.5, fontWeight: 600, padding: "10px 16px", borderRadius: 6, cursor: "pointer" }}>
              <MdOutlineExplore size={17} /> Pick a trending topic
            </button>
            <button onClick={() => router.push("/dashboard/studio")}
              style={{ display: "flex", alignItems: "center", gap: 7, background: "transparent", border: `1px solid ${L.rule}`, color: L.ink, fontFamily: grotesque, fontSize: 13.5, padding: "10px 16px", borderRadius: 6, cursor: "pointer" }}>
              <MdOutlineMovieFilter size={17} /> Start from your own idea
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
