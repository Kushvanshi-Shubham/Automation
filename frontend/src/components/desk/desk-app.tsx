"use client"

// Kliptos Desk — implemented from the Claude Design handoff (Kliptos Desk.dc.html).
// Three surfaces over the real APIs: DESK (today's bets) → LINE (work in
// flight) → VAULT (ledger, standing orders, source material).
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useSession } from "next-auth/react"
import { useCallback, useEffect, useMemo, useState } from "react"
import { API_BASE_URL, fetchApi } from "@/lib/api-client"
import { usePipeline } from "@/hooks/use-pipeline"
import { T, mono } from "@/components/desk/tokens"

const MEDIA_ORIGIN = API_BASE_URL.replace(/\/api\/?$/, "")

// The renderer's real stages (runner.py publishes these percentages).
const STAGE_DEFS = [
  { name: "QUEUED", at: 0 }, { name: "VOICE", at: 10 }, { name: "VISUALS", at: 35 },
  { name: "ASSEMBLY", at: 65 }, { name: "MUSIC", at: 90 }, { name: "COMPLETE", at: 100 },
]
const stageOf = (pct: number) => { let i = 0; STAGE_DEFS.forEach((d, k) => { if (pct >= d.at) i = k }); return i }

const FORMAT_CODES: Record<string, string> = { narrated: "NR", visual: "VS", fake_text: "TX", image: "IM", clip: "CL", script: "SC" }
const PLAN_LIMITS: Record<string, number> = { free: 3, pro: 50, studio: 150 }

interface TopicT { id: string; title: string; category: string | null; best_format: string | null; format_reason: string | null; score: number | null }
interface VideoT { id: string; status: string; output_type: string; title: string | null; description: string | null; tags: string[] | null; video_url: string | null; youtube_video_id: string | null; scheduled_at: string | null; published_at: string | null; created_at: string | null; aspect_ratio?: string | null }
interface SegmentT { text: string; visual_prompt: string; duration_estimate: number; media_id?: number | null; media_thumb?: string | null }
interface ScriptT { video_id: string; segments: SegmentT[]; total_duration: number; output_type: string; format?: string | null; defaults?: { voice_id?: string; caption_style?: string } | null }
interface SeriesT { id: string; name: string; format: string | null; output_type: string; interval_hours: number; auto_publish: boolean; is_active: boolean; next_run_at: string | null; last_error: string | null; video_count: number }
interface AssetT { id: string; filename: string; duration: number | null; status: string; highlights: { start: number; end: number; title: string; reason: string }[] | null }
interface ChannelT { id: string; channel_name: string | null }
interface FormatT { key: string; label: string; emoji: string; output_type: string; available: boolean }

const micro = (color: string = T.dim, ls = "0.1em"): React.CSSProperties => ({ fontFamily: mono, fontSize: 10, letterSpacing: ls, color })
const panel: React.CSSProperties = { background: T.panel, border: `1px solid ${T.rule}`, borderRadius: 8 }
const monoBtn = (kind: "signal" | "ghost" | "faint" = "ghost"): React.CSSProperties => ({
  background: kind === "signal" ? T.signal : "transparent",
  border: kind === "signal" ? "none" : `1px solid ${kind === "faint" ? T.rule : T.strong}`,
  color: kind === "signal" ? T.bg : kind === "faint" ? T.faint : T.body,
  fontFamily: mono, fontSize: 10, letterSpacing: "0.06em", padding: "8px 11px", cursor: "pointer", borderRadius: 6,
})
const pill = (on: boolean): React.CSSProperties => ({
  background: on ? T.signal : "transparent", border: `1px solid ${on ? T.signal : T.strong}`, borderRadius: 6,
  color: on ? T.bg : T.dim, fontSize: 12.5, padding: "8px 12px", cursor: "pointer",
})
const blockOpt = (on: boolean): React.CSSProperties => ({
  display: "block", width: "100%", textAlign: "left", cursor: "pointer", borderRadius: 8, padding: "13px 15px",
  background: on ? T.head : T.bg, border: `1px solid ${on ? T.signal : T.rule}`,
})

type Sheet = null | "publish" | "credits" | "channel" | "order"
type Surface = "desk" | "line" | "vault"

export default function DeskApp() {
  const qc = useQueryClient()
  const { data: session } = useSession()

  const [surface, setSurface] = useState<Surface>("desk")
  const [activeId, setActiveId] = useState<string | null>(null)
  const [sheet, setSheet] = useState<Sheet>(null)
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [query, setQuery] = useState("")
  const [ownIdea, setOwnIdea] = useState("")
  const [assignedTopics, setAssignedTopics] = useState<Set<string>>(new Set())
  const [jobMap, setJobMap] = useState<Record<string, string>>({})
  const [sceneIndex, setSceneIndex] = useState(0)
  const [scenes, setScenes] = useState<SegmentT[]>([])
  const [dirty, setDirty] = useState(false)
  const [busy, setBusy] = useState<string | null>(null)

  // ---------- data ----------
  const { data: topicsData } = useQuery<{ items: TopicT[] }>({ queryKey: ["topics", null], queryFn: () => fetchApi("/topics"), staleTime: 60_000 })
  const { data: formatsData } = useQuery<{ items: FormatT[] }>({ queryKey: ["formats"], queryFn: () => fetchApi("/scripts/formats"), staleTime: Infinity })
  const { data: videosData } = useQuery<{ items: VideoT[] }>({
    queryKey: ["desk-videos"],
    queryFn: () => fetchApi("/videos?page_size=40"),
    refetchInterval: q => ((q.state.data?.items ?? []).some(v => ["rendering", "publishing"].includes(v.status)) ? 4000 : 15000),
  })
  const { data: credits } = useQuery<{ balance: number; plan: string }>({ queryKey: ["credits"], queryFn: () => fetchApi("/billing/credits"), refetchInterval: 30_000 })
  const { data: channels } = useQuery<ChannelT[]>({ queryKey: ["channels"], queryFn: () => fetchApi("/channels") })
  const { data: seriesData } = useQuery<SeriesT[]>({ queryKey: ["series"], queryFn: () => fetchApi("/series"), staleTime: 30_000 })
  const { data: assets } = useQuery<AssetT[]>({ queryKey: ["media-assets"], queryFn: () => fetchApi("/media-assets"), staleTime: 30_000 })
  const { data: niches } = useQuery<{ items: { key: string; label: string }[] }>({ queryKey: ["niches"], queryFn: () => fetchApi("/topics/niches"), staleTime: Infinity })

  const fmtByKey = useMemo(() => new Map((formatsData?.items ?? []).map(f => [f.key, f])), [formatsData])
  const codeOf = (f: FormatT | undefined, outputType: string) => FORMAT_CODES[f?.output_type ?? outputType] ?? "NR"

  // Lanes: everything a user still owes attention to.
  const lanes = useMemo(() => (videosData?.items ?? []).filter(v =>
    ["script_ready", "rendering", "publishing"].includes(v.status) ||
    (v.status === "ready" && !v.youtube_video_id && !v.published_at)
  ), [videosData])
  const active = lanes.find(l => l.id === activeId) ?? null
  const readyLanes = lanes.filter(l => l.status === "ready")
  const workingCount = lanes.filter(l => ["rendering", "publishing"].includes(l.status)).length

  const { data: script } = useQuery<ScriptT>({
    queryKey: ["script", activeId],
    queryFn: () => fetchApi(`/scripts/${activeId}`),
    enabled: !!activeId,
  })
  // Sync fetched script into the editable strip (derive-during-render).
  const [syncedScript, setSyncedScript] = useState<ScriptT | null>(null)
  if (script && script !== syncedScript) {
    setSyncedScript(script)
    setScenes(script.segments)
    setSceneIndex(0)
    setDirty(false)
  }

  const pipeline = usePipeline(activeId ? jobMap[activeId] ?? null : null)
  const activePct = active?.status === "rendering" ? (jobMap[active.id] ? pipeline.progress : null) : active?.status === "ready" ? 100 : 0
  useEffect(() => {
    if (pipeline.status === "completed" || pipeline.status === "failed") qc.invalidateQueries({ queryKey: ["desk-videos"] })
  }, [pipeline.status, qc])

  const { data: mediaOptions } = useQuery<{ items: { id: number; thumb: string }[] }>({
    queryKey: ["media-options", activeId, sceneIndex],
    queryFn: () => fetchApi(`/scripts/${activeId}/segments/${sceneIndex}/media-options`),
    enabled: !!activeId && surface === "line" && active?.status === "script_ready" && scenes.length > 0,
    staleTime: Infinity,
  })

  // ---------- actions ----------
  const openLane = useCallback((id: string) => { setActiveId(id); setSurface("line"); setSceneIndex(0) }, [])

  const assign = useMutation({
    mutationFn: (p: { topic?: TopicT; idea?: string }) =>
      fetchApi("/scripts/generate", {
        method: "POST",
        body: JSON.stringify(p.topic
          ? { topic_id: p.topic.id, format: fmtByKey.has(p.topic.best_format ?? "") ? p.topic.best_format : "viral_story" }
          : { custom_prompt: p.idea, format: "viral_story" }),
      }) as Promise<{ video_id: string }>,
    onSuccess: (data, p) => {
      if (p.topic) setAssignedTopics(prev => new Set(prev).add(p.topic!.id))
      setOwnIdea("")
      qc.invalidateQueries({ queryKey: ["desk-videos"] })
      openLane(data.video_id)
    },
    onSettled: () => setBusy(null),
  })

  const saveScript = useCallback(async (nextScenes?: SegmentT[]) => {
    if (!activeId) return
    await fetchApi(`/scripts/${activeId}`, { method: "PUT", body: JSON.stringify({ segments: nextScenes ?? scenes }) })
    setDirty(false)
  }, [activeId, scenes])

  const rewriteScene = useMutation({
    mutationFn: () => fetchApi(`/scripts/${activeId}/regenerate-segment`, {
      method: "POST",
      body: JSON.stringify({ segment_index: sceneIndex, feedback: "make it punchier and more engaging" }),
    }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["script", activeId] }),
  })

  const sendToLine = useCallback(async () => {
    if (!active) return
    if ((credits?.balance ?? 0) < 1) { setSheet("credits"); return }
    setBusy("render")
    try {
      if (dirty) await saveScript()
      const res = await fetchApi("/pipeline/start", {
        method: "POST",
        body: JSON.stringify({ video_id: active.id, visual_engine: active.output_type === "image" ? "stock_image" : "pexels", aspect_ratio: "9:16" }),
      }) as { job_id: string }
      setJobMap(m => ({ ...m, [active.id]: res.job_id }))
      qc.invalidateQueries({ queryKey: ["desk-videos"] })
      qc.invalidateQueries({ queryKey: ["credits"] })
    } catch (e) {
      if (String(e).includes("402")) setSheet("credits")
      else alert(String((e as Error).message).slice(0, 300))
    } finally { setBusy(null) }
  }, [active, credits, dirty, saveScript, qc])

  const advance = useCallback(() => {
    if (!active) return
    if (active.status === "script_ready") void sendToLine()
    else if (active.status === "ready") setSheet("publish")
  }, [active, sendToLine])

  const cutMoment = useMutation({
    mutationFn: (p: { assetId: string; h: { start: number; end: number; title: string } }) =>
      fetchApi(`/media-assets/${p.assetId}/clips`, {
        method: "POST",
        body: JSON.stringify({ start: p.h.start, end: p.h.end, title: p.h.title }),
      }) as Promise<{ video_id: string; job_id: string }>,
    onSuccess: data => {
      setJobMap(m => ({ ...m, [data.video_id]: data.job_id }))
      qc.invalidateQueries({ queryKey: ["desk-videos"] })
      qc.invalidateQueries({ queryKey: ["credits"] })
      openLane(data.video_id)
    },
  })

  // ---------- keyboard ----------
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const meta = e.metaKey || e.ctrlKey
      const typing = ["INPUT", "TEXTAREA"].includes((e.target as HTMLElement)?.tagName)
      if (meta && e.key.toLowerCase() === "k") { e.preventDefault(); setPaletteOpen(true); return }
      if (e.key === "Escape") { setPaletteOpen(false); setSheet(null); return }
      if (meta && e.key === "Enter") { e.preventDefault(); advance(); return }
      if (e.key === "Enter" && !meta && !typing && surface === "desk") {
        const next = (topicsData?.items ?? []).slice(0, 5).find(t => !assignedTopics.has(t.id))
        if (next) { e.preventDefault(); setBusy(next.id); assign.mutate({ topic: next }) }
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [surface, topicsData, assignedTopics, advance, assign])

  // ---------- derived display ----------
  const bets = (topicsData?.items ?? []).slice(0, 5)
  const nextOrder = (seriesData ?? []).filter(s => s.is_active && s.next_run_at).sort((a, b) => (a.next_run_at! < b.next_run_at! ? -1 : 1))[0]
  const planLimit = PLAN_LIMITS[credits?.plan ?? "free"] ?? 3
  const laneState = (l: VideoT) => l.status === "ready" ? { color: T.ready, label: "AWAITING APPROVAL" }
    : l.status === "rendering" ? { color: T.working, label: jobMap[l.id] && activeId === l.id ? `${STAGE_DEFS[Math.min(stageOf(pipeline.progress), 5)].name} · ${Math.round(pipeline.progress)}%` : "RENDERING" }
    : l.status === "publishing" ? { color: T.live, label: "PUBLISHING" }
    : { color: T.idle, label: "AWAITING YOUR EDIT" }

  const totalDuration = Math.round(scenes.reduce((a, s) => a + (s.duration_estimate || 0), 0))
  const scene = scenes[sceneIndex]
  const scriptFmt = script?.format ? fmtByKey.get(script.format) : undefined
  const activeCode = active ? codeOf(scriptFmt, active.output_type) : "NR"

  const tabStyle = (on: boolean): React.CSSProperties => ({
    background: "transparent", border: "none", cursor: "pointer", fontFamily: mono, fontSize: 10,
    letterSpacing: "0.06em", padding: "8px 12px", borderRadius: 0,
    color: on ? T.text : T.dim, borderBottom: `2px solid ${on ? T.signal : "transparent"}`,
  })

  const updateScene = (patch: Partial<SegmentT>) => {
    setScenes(prev => prev.map((s, i) => (i === sceneIndex ? { ...s, ...patch } : s)))
    setDirty(true)
  }

  return (
    <div style={{ minWidth: 1180, height: "100vh", display: "flex", flexDirection: "column", background: T.bg, color: T.text, fontFamily: "var(--font-archivo), Archivo, system-ui, sans-serif", overflow: "hidden" }}>

      {/* Top bar */}
      <div style={{ height: 32, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 14px", background: T.panel, borderBottom: `1px solid ${T.rule}`, ...micro(T.dim, "0.12em") }}>
        <div style={{ display: "flex", alignItems: "center", gap: 2 }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/brand/kliptos-logo-2k.jpeg" alt="Kliptos" style={{ width: 20, height: 20, borderRadius: 5, objectFit: "cover", marginRight: 14 }} />
          <button onClick={() => setSurface("desk")} style={tabStyle(surface === "desk")}>DESK</button>
          <button onClick={() => setSurface("line")} style={tabStyle(surface === "line")}>LINE <span style={{ color: T.working }}>{lanes.length || ""}</span></button>
          <button onClick={() => setSurface("vault")} style={tabStyle(surface === "vault")}>VAULT</button>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <span style={{ color: T.working }}>{workingCount} WORKING</span>
          <span style={{ color: T.ready }}>{readyLanes.length} AWAITING YOU</span>
          {nextOrder && <span>NEXT {new Date(nextOrder.next_run_at!).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} · {nextOrder.name.toUpperCase().slice(0, 26)}</span>}
          <span style={{ color: T.text }}>{credits?.balance ?? "…"} CR</span>
          <button onClick={() => setPaletteOpen(true)} style={{ background: "transparent", border: `1px solid ${T.strong}`, color: T.dim, fontFamily: mono, fontSize: 10, letterSpacing: "0.12em", padding: "3px 7px", cursor: "pointer", borderRadius: 6 }}>CMD+K</button>
        </div>
      </div>

      <div style={{ flex: 1, minHeight: 0, display: "grid", gridTemplateColumns: "1fr 240px" }}>
        {/* Main column */}
        <div style={{ minWidth: 0, overflowY: "auto", borderRight: `1px solid ${T.rule}` }}>

          {/* ==================== DESK ==================== */}
          {surface === "desk" && (
            <div style={{ padding: "28px 32px 48px" }}>
              <p style={{ margin: "0 0 2px", fontSize: 32, fontWeight: 700, letterSpacing: "-0.028em" }}>
                {readyLanes.length ? (readyLanes.length === 1 ? "One short is waiting for you" : `${readyLanes.length} shorts are waiting for you`) : `${Math.min(bets.length, 5) || "No"} bets for ${new Date().toLocaleDateString([], { weekday: "long" })}`}
              </p>
              <p style={{ ...micro(T.dim, "0.08em"), fontSize: 11, margin: "0 0 22px" }}>
                GOOGLE TRENDS + YOUTUBE SIGNALS · RANKED BY TOPIC SCORE · ✨ FORMAT RECOMMENDED PER TREND
              </p>

              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {bets.map((bet, i) => {
                  const taken = assignedTopics.has(bet.id)
                  const first = i === 0
                  const fmt = bet.best_format ? fmtByKey.get(bet.best_format) : undefined
                  return (
                    <div key={bet.id} style={{ ...panel, borderLeft: first ? `2px solid ${T.signal}` : `1px solid ${T.rule}`, padding: first ? 18 : "14px 18px", display: "grid", gridTemplateColumns: "30px 1fr 132px 92px 116px", gap: 16, alignItems: "center" }}>
                      <span style={{ fontFamily: mono, fontSize: first ? 16 : 13, color: first ? T.signal : T.faint }}>0{i + 1}</span>
                      <span style={{ minWidth: 0 }}>
                        <span style={{ display: "block", fontSize: first ? 20 : i < 3 ? 17 : 15, fontWeight: first ? 600 : 500, letterSpacing: "-0.015em", color: i < 3 ? T.text : T.body }}>{bet.title}</span>
                        <span style={{ display: "block", marginTop: 4, fontSize: 13, color: T.dim }}>
                          {fmt ? `Best format: ${fmt.label}${bet.format_reason ? ` — ${bet.format_reason}` : ""}` : bet.category ?? ""}
                        </span>
                      </span>
                      <span style={{ fontFamily: mono, fontSize: 11, color: first ? T.ready : T.dim }}>SCORE {Math.round(bet.score ?? 0)}</span>
                      <span style={{ fontFamily: mono, fontSize: 11, color: T.dim }}>{codeOf(fmt, "narrated")} · 1 CR</span>
                      <button
                        onClick={() => { if (!taken && !assign.isPending) { setBusy(bet.id); assign.mutate({ topic: bet }) } }}
                        style={taken ? { ...monoBtn("faint"), cursor: "default" } : first ? monoBtn("signal") : monoBtn("ghost")}
                      >
                        {busy === bet.id ? "WRITING…" : taken ? "ON THE LINE" : first ? "ASSIGN ENTER" : "ASSIGN"}
                      </button>
                    </div>
                  )
                })}
                {bets.length === 0 && (
                  <div style={{ ...panel, padding: "20px 18px" }}>
                    <p style={{ margin: 0, fontSize: 14, color: T.dim }}>No signals harvested yet — the harvester runs on a schedule, or assign your own idea below.</p>
                  </div>
                )}
              </div>

              {/* Own idea */}
              <div style={{ marginTop: 20, ...panel, borderRadius: 7, display: "flex", alignItems: "center", gap: 14, padding: "0 16px" }}>
                <span style={{ ...micro(T.faint, "0.14em"), flexShrink: 0 }}>Or assign your own</span>
                <input
                  value={ownIdea}
                  onChange={e => setOwnIdea(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter" && ownIdea.trim().length >= 10) { setBusy("own"); assign.mutate({ idea: ownIdea.trim() }) } }}
                  placeholder="Type an idea, paste a script, or drop a URL…"
                  style={{ flex: 1, minWidth: 0, background: "transparent", border: "none", outline: "none", padding: "15px 0", fontSize: 14, color: T.text }}
                />
                <button
                  onClick={() => { if (ownIdea.trim().length >= 10) { setBusy("own"); assign.mutate({ idea: ownIdea.trim() }) } }}
                  style={ownIdea.trim().length >= 10 ? monoBtn("signal") : { ...monoBtn("faint"), cursor: "default" }}
                >
                  {busy === "own" ? "WRITING…" : "ASSIGN ENTER"}
                </button>
              </div>

              {/* Awaiting approval */}
              <p style={{ margin: "40px 0 12px", fontSize: 12.5, fontWeight: 500, color: T.dim }}>Awaiting your approval</p>
              {readyLanes.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {readyLanes.map(lane => (
                    <div key={lane.id} style={{ ...panel, borderLeft: `2px solid ${T.ready}`, padding: "14px 18px", display: "grid", gridTemplateColumns: "1fr 120px 96px 140px", gap: 16, alignItems: "center" }}>
                      <span style={{ fontSize: 16, fontWeight: 500 }}>{lane.title ?? "Untitled"}</span>
                      <span style={{ fontFamily: mono, fontSize: 11, color: T.ready }}>READY</span>
                      <span style={{ fontFamily: mono, fontSize: 11, color: T.dim }}>{FORMAT_CODES[lane.output_type] ?? "NR"} · {lane.aspect_ratio ?? "9:16"}</span>
                      <button onClick={() => openLane(lane.id)} style={{ ...monoBtn("signal"), letterSpacing: "0.1em" }}>REVIEW CMD+ENTER</button>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ ...panel, borderRadius: 7, padding: "20px 18px" }}>
                  <p style={{ margin: 0, fontSize: 14, color: T.dim }}>
                    {nextOrder
                      ? `Nothing waiting on you. "${nextOrder.name}" renders on schedule and holds its shorts here for review.`
                      : "Nothing waiting on you. Assign a bet above — or create a standing order in the Vault and mornings start themselves."}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* ==================== LINE ==================== */}
          {surface === "line" && (
            active && script ? (
              <div style={{ minHeight: "100%", display: "flex", flexDirection: "column" }}>
                <div style={{ padding: "20px 32px 18px", borderBottom: `1px solid ${T.rule}`, display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 24 }}>
                  <div style={{ minWidth: 0 }}>
                    <p style={{ margin: "0 0 4px", fontSize: 26, fontWeight: 600, letterSpacing: "-0.025em" }}>{active.title ?? "Untitled"}</p>
                    <p style={{ ...micro(T.dim, "0.08em"), fontSize: 11, margin: 0 }}>
                      {activeCode} · {active.aspect_ratio ?? "9:16"} · {(script.defaults?.caption_style ?? "classic").toUpperCase()} · {totalDuration}s · {laneState(active).label}
                    </p>
                  </div>
                  <button onClick={advance} disabled={busy === "render" || active.status === "rendering" || active.status === "publishing"}
                    style={{ ...((active.status === "rendering" || active.status === "publishing") ? { background: "transparent", border: `1px solid ${T.working}55`, color: T.working } : { background: T.signal, border: "none", color: T.bg }), fontFamily: mono, fontSize: 11, letterSpacing: "0.04em", padding: "12px 18px", borderRadius: 6, cursor: "pointer", flexShrink: 0 }}>
                    {busy === "render" ? "SENDING…"
                      : active.status === "script_ready" ? "SEND TO LINE · 1 CR"
                      : active.status === "rendering" ? `RENDERING${activePct !== null ? ` · ${STAGE_DEFS[Math.min(stageOf(activePct), 5)].name} · ${Math.round(activePct)}%` : "…"}`
                      : active.status === "publishing" ? "PUBLISHING…"
                      : "APPROVE & PUBLISH CMD+ENTER"}
                  </button>
                </div>

                {/* Scene strip */}
                <div style={{ padding: "18px 32px", borderBottom: `1px solid ${T.rule}` }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                    <p style={{ margin: 0, fontSize: 12.5, fontWeight: 500, color: T.dim }}>Scene strip · {scenes.length} scenes · {totalDuration}s{dirty && <button onClick={() => void saveScript()} style={{ ...monoBtn("signal"), marginLeft: 12, padding: "4px 8px" }}>SAVE</button>}</p>
                    <p style={{ ...micro(T.faint), margin: 0 }}>WIDTH = DURATION</p>
                  </div>
                  <div style={{ display: "flex", gap: 2, height: 62 }}>
                    {scenes.map((sc, i) => (
                      <button key={i} onClick={() => setSceneIndex(i)} style={{ flex: Math.max(sc.duration_estimate, 1), minWidth: 0, background: i === sceneIndex ? T.head : T.panel, border: `1px solid ${i === sceneIndex ? T.signal : sc.media_id ? T.live : T.rule}`, padding: 8, cursor: "pointer", textAlign: "left", display: "flex", flexDirection: "column", justifyContent: "space-between", borderRadius: 0 }}>
                        <span style={{ ...micro(i === sceneIndex ? T.signal : T.faint), fontSize: 9 }}>{i === 0 ? "HOOK" : i === scenes.length - 1 ? "PAYOFF" : `0${i + 1}`}</span>
                        <span style={{ fontFamily: mono, fontSize: 9, color: T.dim }}>{Math.round(sc.duration_estimate)}s</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", minHeight: 0 }}>
                  {/* Scene editor */}
                  <div style={{ padding: "22px 32px 40px", borderRight: `1px solid ${T.rule}`, minWidth: 0 }}>
                    {scene && <>
                      <p style={{ margin: "0 0 12px", fontSize: 12.5, fontWeight: 500, color: T.signal }}>
                        SCENE {sceneIndex + 1} · {sceneIndex === 0 ? "HOOK" : sceneIndex === scenes.length - 1 ? "PAYOFF" : `0${sceneIndex + 1}`} · {Math.round(scene.duration_estimate)}s
                      </p>
                      <textarea value={scene.text} onChange={e => updateScene({ text: e.target.value })} rows={3}
                        style={{ width: "100%", boxSizing: "border-box", background: T.panel, border: `1px solid ${T.strong}`, outline: "none", padding: "14px 16px", fontSize: 17, lineHeight: 1.5, resize: "none", marginBottom: 8, color: T.text, borderRadius: 6, fontFamily: "inherit" }} />
                      <div style={{ display: "flex", gap: 8, marginBottom: 26 }}>
                        <button onClick={() => rewriteScene.mutate()} disabled={rewriteScene.isPending} style={monoBtn("ghost")}>{rewriteScene.isPending ? "REWRITING…" : "REWRITE CMD+R"}</button>
                        <button onClick={() => updateScene({ duration_estimate: scene.duration_estimate + 2 })} style={monoBtn("ghost")}>HOLD 2s LONGER</button>
                      </div>

                      <p style={{ margin: "0 0 10px", fontSize: 12.5, fontWeight: 500, color: T.dim }}>Visual direction</p>
                      <input value={scene.visual_prompt} onChange={e => updateScene({ visual_prompt: e.target.value })}
                        style={{ width: "100%", boxSizing: "border-box", background: T.panel, border: `1px solid ${T.rule}`, borderRadius: 7, outline: "none", padding: "11px 14px", fontFamily: mono, fontSize: 13, color: T.body, marginBottom: 14 }} />
                      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                        {(mediaOptions?.items ?? []).slice(0, 7).map(opt => (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img key={opt.id} src={opt.thumb} alt="" onClick={() => updateScene({ media_id: scene.media_id === opt.id ? null : opt.id, media_thumb: scene.media_id === opt.id ? null : opt.thumb })}
                            style={{ width: 38, height: 54, objectFit: "cover", cursor: "pointer", border: `1px solid ${scene.media_id === opt.id ? T.live : T.rule}`, borderRadius: 2 }} />
                        ))}
                        <span style={{ alignSelf: "flex-end", ...micro(T.faint), paddingBottom: 2 }}>
                          {scene.media_id ? `SCENE ${sceneIndex + 1} PINNED · REST AUTO-SOURCED` : "CLICK TO PIN A CLIP · ELSE AUTO-SOURCED"}
                        </span>
                      </div>

                      <p style={{ margin: "28px 0 10px", fontSize: 12.5, fontWeight: 500, color: T.dim }}>Render recipe</p>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                        {[
                          `${activeCode} ${(scriptFmt?.label ?? active.output_type).toUpperCase()}`,
                          `${active.aspect_ratio ?? "9:16"} · 1080×1920`,
                          (script.defaults?.voice_id ?? "CHRISTOPHER · ENGLISH (US)").toUpperCase().replace("EN-US-", "").replace("NEURAL", " · ENGLISH (US)"),
                          `${(script.defaults?.caption_style ?? "classic").toUpperCase()} CAPTIONS`,
                          "MUSIC BED · CC-BY",
                        ].map(chip => (
                          <span key={chip} style={{ border: `1px solid ${T.strong}`, padding: "7px 11px", ...micro(T.body), borderRadius: 6 }}>{chip}</span>
                        ))}
                      </div>
                    </>}
                  </div>

                  {/* Right: player + stage readout + publish rail */}
                  <div style={{ padding: 22, display: "flex", flexDirection: "column", gap: 16 }}>
                    <div style={{ width: "100%", aspectRatio: "9/16", maxHeight: 280, background: T.panel, border: `1px solid ${T.rule}`, borderRadius: 8, overflow: "hidden", display: "flex", alignItems: "flex-end", justifyContent: "center" }}>
                      {active.status === "ready" && active.video_url ? (
                        <video src={`${MEDIA_ORIGIN}${active.video_url}`} controls playsInline style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                      ) : (
                        <span style={{ ...micro(T.faint, "0.12em"), fontSize: 9, paddingBottom: 14 }}>
                          {active.status === "rendering" ? "RENDERING" : "PREVIEW BUILDS AFTER STAGE 5"}
                        </span>
                      )}
                    </div>
                    <div>
                      <p style={{ ...micro(active.status === "rendering" ? T.working : active.status === "ready" ? T.ready : T.dim, "0.14em"), margin: "0 0 10px" }}>
                        {active.status === "script_ready" ? "NOT YET ON THE LINE" : active.status === "ready" ? "RENDER COMPLETE · 100%" : active.status === "publishing" ? "PUBLISHING TO CHANNEL" : `ON THE LINE${activePct !== null ? ` · ${Math.round(activePct)}%` : ""}`}
                      </p>
                      <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                        {STAGE_DEFS.map((d, i) => {
                          const pct = activePct ?? -1
                          const done = active.status === "ready" || active.status === "publishing" || (pct >= 0 && i < stageOf(pct))
                          const now = active.status === "rendering" && pct >= 0 && i === stageOf(pct)
                          const color = done ? T.ready : now ? T.working : T.faint
                          return (
                            <span key={d.name} style={{ display: "grid", gridTemplateColumns: "1fr 48px", gap: 8, fontFamily: mono, fontSize: 10, letterSpacing: "0.08em", color }}>
                              <span style={{ borderLeft: `2px solid ${done ? T.ready : now ? T.working : T.rule}`, paddingLeft: 8 }}>{d.name}</span>
                              <span style={{ textAlign: "right" }}>{done ? "done" : now ? `${Math.round(pct)}%` : `${d.at}%`}</span>
                            </span>
                          )
                        })}
                      </div>
                    </div>
                    <div style={{ marginTop: "auto", borderTop: `1px solid ${T.rule}`, paddingTop: 14 }}>
                      <p style={{ margin: "0 0 8px", fontSize: 12.5, fontWeight: 500, color: T.dim }}>Publish to</p>
                      <p style={{ margin: "0 0 12px", fontFamily: mono, fontSize: 11, color: T.body, lineHeight: 1.7 }}>
                        {(channels ?? []).length ? <>{channels![0].channel_name?.toUpperCase() ?? "YOUR CHANNEL"} · YOUTUBE SHORTS<br /><span style={{ color: T.faint }}>UNLISTED BY DEFAULT</span></> : <>NO CHANNEL CONNECTED<br /><span style={{ color: T.faint }}>CONNECT WHEN YOU PUBLISH</span></>}
                      </p>
                      <button onClick={advance} style={{ width: "100%", ...monoBtn(active.status === "ready" ? "signal" : "ghost"), padding: 12 }}>
                        {active.status === "script_ready" ? "SEND TO LINE · 1 CR" : active.status === "ready" ? "APPROVE & PUBLISH" : "WORKING…"}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ padding: "28px 32px" }}>
                <p style={{ margin: "0 0 2px", fontSize: 32, fontWeight: 700, letterSpacing: "-0.028em" }}>The line is clear</p>
                <p style={{ margin: "0 0 26px", fontSize: 15, color: T.dim, maxWidth: "60ch" }}>
                  The renderer reports five stages over the pipeline socket. Assign a bet from the desk and it appears here, reporting itself.
                </p>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(6,1fr)", gap: 8, maxWidth: 860 }}>
                  {STAGE_DEFS.map(d => (
                    <div key={d.name} style={{ ...panel, borderRadius: 7, padding: "16px 14px" }}>
                      <p style={{ ...micro(T.dim, "0.12em"), margin: "0 0 8px" }}>{d.name === "COMPLETE" ? "READY" : d.name}</p>
                      <p style={{ margin: 0, fontFamily: mono, fontSize: 13, color: T.text }}>{d.at}%</p>
                    </div>
                  ))}
                </div>
              </div>
            )
          )}

          {/* ==================== VAULT ==================== */}
          {surface === "vault" && (
            <VaultSurface
              videos={videosData?.items ?? []}
              series={seriesData ?? []}
              assets={assets ?? []}
              formats={fmtByKey}
              onCut={(assetId, h) => cutMoment.mutate({ assetId, h })}
              cutting={cutMoment.isPending}
              openOrderSheet={() => setSheet("order")}
              onToggleSeries={async (s) => { await fetchApi(`/series/${s.id}`, { method: "PATCH", body: JSON.stringify({ is_active: !s.is_active }) }); qc.invalidateQueries({ queryKey: ["series"] }) }}
            />
          )}
        </div>

        {/* Right rail */}
        <div style={{ minWidth: 0, overflowY: "auto", padding: 12, background: T.bg }}>
          <p style={{ margin: "0 0 12px", fontSize: 12.5, fontWeight: 500, color: T.dim }}>The line · {lanes.length}</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {lanes.map(lane => {
              const st = laneState(lane)
              const pct = lane.id === activeId ? activePct : lane.status === "ready" ? 100 : null
              return (
                <button key={lane.id} onClick={() => openLane(lane.id)} style={{ display: "block", width: "100%", textAlign: "left", cursor: "pointer", background: lane.id === activeId ? T.head : T.panel, border: `1px solid ${T.rule}`, borderLeft: `2px solid ${st.color}`, padding: "10px 12px", borderRadius: 0 }}>
                  <span style={{ display: "block", fontSize: 13, fontWeight: 500, lineHeight: 1.35, marginBottom: 6, color: T.text }}>{lane.title ?? "Untitled"}</span>
                  <span style={{ display: "block", ...micro(st.color, "0.08em"), marginBottom: 6 }}>{st.label}</span>
                  <span style={{ display: "flex", gap: 2 }}>
                    {STAGE_DEFS.map((d, i) => {
                      const color = lane.status === "ready" || lane.status === "publishing" ? T.ready
                        : pct !== null && pct >= 0 ? (i < stageOf(pct) ? T.ready : i === stageOf(pct) ? T.working : T.rule)
                        : lane.status === "rendering" ? (i < 2 ? T.working : T.rule) : T.rule
                      return <span key={d.name} style={{ flex: 1, height: 3, display: "block", background: color }} />
                    })}
                  </span>
                </button>
              )
            })}
          </div>
          {lanes.length === 0 && (
            <p style={{ margin: 0, fontFamily: mono, fontSize: 10, lineHeight: 1.8, letterSpacing: "0.06em", color: "#4E4842" }}>—— ·· ——<br />NOTHING IN FLIGHT</p>
          )}

          <p style={{ margin: "26px 0 10px", fontSize: 12.5, fontWeight: 500, color: T.dim }}>Credits</p>
          <div style={{ ...panel, borderRadius: 7, padding: 12 }}>
            <p style={{ margin: "0 0 8px", fontFamily: mono, fontSize: 20, letterSpacing: "-0.02em", color: T.text }}>
              {credits?.balance ?? "…"}<span style={{ fontSize: 11, color: T.faint }}> / {planLimit} · {(credits?.plan ?? "free").toUpperCase()}</span>
            </p>
            <span style={{ display: "flex", gap: 2 }}>
              {Array.from({ length: 10 }, (_, i) => (
                <span key={i} style={{ flex: 1, height: 4, display: "block", background: i < Math.round(((credits?.balance ?? 0) / planLimit) * 10) ? T.signal : T.rule }} />
              ))}
            </span>
            <p style={{ margin: "10px 0 0", ...micro(T.faint, "0.06em") }}>STOCK RENDER 1 CR · AI IMAGES 2 CR · REFUNDED ON FAILURE</p>
          </div>

          <p style={{ margin: "26px 0 10px", fontSize: 12.5, fontWeight: 500, color: T.dim }}>Identity</p>
          <div style={{ ...panel, borderRadius: 7, padding: 12, display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ width: 26, height: 26, background: T.head, border: `1px solid ${T.strong}`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: mono, fontSize: 11, color: T.body, borderRadius: 4 }}>
              {(session?.user?.name ?? session?.user?.email ?? "?").charAt(0).toUpperCase()}
            </span>
            <span style={{ minWidth: 0 }}>
              <span style={{ display: "block", fontSize: 12.5, fontWeight: 500, color: T.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{session?.user?.name ?? session?.user?.email}</span>
              <span style={{ display: "block", fontFamily: mono, fontSize: 10, color: T.faint }}>{(credits?.plan ?? "FREE").toUpperCase()} · {(channels ?? []).length} CHANNEL{(channels ?? []).length === 1 ? "" : "S"}</span>
            </span>
          </div>
        </div>
      </div>

      {/* Sheets + palette */}
      {sheet && (
        <DeskSheets
          sheet={sheet} close={() => setSheet(null)}
          active={active} credits={credits} channels={channels ?? []} niches={niches?.items ?? []}
          onPublished={() => { setSheet(null); setActiveId(null); setSurface("vault"); qc.invalidateQueries({ queryKey: ["desk-videos"] }) }}
          openChannelSheet={() => setSheet("channel")}
          onOrderCreated={() => { setSheet(null); qc.invalidateQueries({ queryKey: ["series"] }) }}
        />
      )}
      {paletteOpen && (
        <Palette
          query={query} setQuery={setQuery} close={() => { setPaletteOpen(false); setQuery("") }}
          commands={[
            { group: "ASSIGN", color: T.signal, label: bets.find(b => !assignedTopics.has(b.id)) ? `Assign top bet — ${bets.find(b => !assignedTopics.has(b.id))!.title}` : "All of today's bets assigned", keys: "ENTER", run: () => { const n = bets.find(b => !assignedTopics.has(b.id)); if (n) { setBusy(n.id); assign.mutate({ topic: n }) } } },
            { group: "GO", color: T.dim, label: "Desk — today's bets", keys: "CMD+1", run: () => setSurface("desk") },
            { group: "GO", color: T.dim, label: "Line — work in flight", keys: "CMD+2", run: () => setSurface("line") },
            { group: "GO", color: T.dim, label: "Vault — ledger, orders, source material", keys: "CMD+3", run: () => setSurface("vault") },
            { group: "AMEND", color: T.working, label: "Rewrite the selected scene", keys: "CMD+R", run: () => { setSurface("line"); if (activeId) rewriteScene.mutate() } },
            { group: "APPROVE", color: T.ready, label: readyLanes.length ? `Approve & publish — ${readyLanes[0].title}` : "Nothing awaiting approval", keys: "CMD+ENTER", run: () => { if (readyLanes.length) { openLane(readyLanes[0].id); setSheet("publish") } } },
            { group: "SETUP", color: T.idle, label: "Buy credits · connect a channel", keys: "", run: () => setSheet("credits") },
          ]}
        />
      )}
    </div>
  )
}

/* ==================== VAULT ==================== */
function VaultSurface({ videos, series, assets, formats, onCut, cutting, openOrderSheet, onToggleSeries }: {
  videos: VideoT[]; series: SeriesT[]; assets: AssetT[]; formats: Map<string, FormatT>
  onCut: (assetId: string, h: { start: number; end: number; title: string }) => void
  cutting: boolean; openOrderSheet: () => void; onToggleSeries: (s: SeriesT) => void
}) {
  const rows = videos.slice(0, 14).map(v => {
    const state = v.youtube_video_id || v.published_at ? { label: "LIVE", color: T.live }
      : v.scheduled_at ? { label: `HOLDING ${new Date(v.scheduled_at).toLocaleDateString([], { day: "numeric", month: "short" })}`, color: T.idle }
      : v.status === "ready" ? { label: "READY", color: T.ready }
      : v.status === "rendering" || v.status === "publishing" ? { label: v.status.toUpperCase(), color: T.working }
      : ["failed", "upload_failed"].includes(v.status) ? { label: "REFUSED", color: T.failed }
      : { label: "DRAFT", color: T.idle }
    return { v, state }
  })
  const srcAsset = assets.find(a => a.status === "ready" && (a.highlights ?? []).length > 0)
  const fmtDur = (s: number) => `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(Math.floor(s % 60)).padStart(2, "0")}`

  return (
    <div style={{ padding: "28px 32px 48px" }}>
      <p style={{ margin: "0 0 2px", fontSize: 32, fontWeight: 700, letterSpacing: "-0.028em" }}>Vault</p>
      <p style={{ ...micro(T.dim, "0.08em"), fontSize: 11, margin: "0 0 26px" }}>
        {videos.length} ITEMS · {series.length} STANDING ORDER{series.length === 1 ? "" : "S"} · {assets.length} SOURCE FILE{assets.length === 1 ? "" : "S"}
      </p>

      <p style={{ margin: "0 0 12px", fontSize: 12.5, fontWeight: 500, color: T.dim }}>Ledger</p>
      <div style={{ ...panel, borderRadius: 7, padding: "0 18px 8px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 70px 150px 90px", gap: 14, padding: "12px 0", borderBottom: `1px solid ${T.rule}`, ...micro(T.faint, "0.14em"), fontSize: 9 }}>
          <span>TITLE</span><span>TYPE</span><span>STATE</span><span style={{ textAlign: "right" }}>CREATED</span>
        </div>
        {rows.map(({ v, state }) => (
          <div key={v.id} style={{ display: "grid", gridTemplateColumns: "1fr 70px 150px 90px", gap: 14, padding: "12px 0", borderBottom: `1px solid ${T.head}`, alignItems: "center" }}>
            <span style={{ fontSize: 13.5, color: state.label === "LIVE" ? T.text : T.body, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{v.title ?? "Untitled"}</span>
            <span style={{ fontFamily: mono, fontSize: 10, color: T.dim }}>{FORMAT_CODES[v.output_type] ?? "NR"}</span>
            <span style={{ ...micro(state.color, "0.08em") }}>{state.label}</span>
            <span style={{ fontFamily: mono, fontSize: 11, textAlign: "right", color: T.faint }}>{v.created_at ? new Date(v.created_at).toLocaleDateString([], { day: "numeric", month: "short" }) : "—"}</span>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginTop: 36 }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <p style={{ margin: 0, fontSize: 12.5, fontWeight: 500, color: T.dim }}>Standing orders</p>
            <button onClick={openOrderSheet} style={{ background: "transparent", border: `1px solid ${T.strong}`, color: T.body, fontSize: 12, padding: "6px 10px", cursor: "pointer", borderRadius: 6 }}>New standing order</button>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {series.map(s => (
              <div key={s.id} style={{ ...panel, padding: "15px 16px", display: "grid", gridTemplateColumns: "1fr 96px", gap: 12, alignItems: "center" }}>
                <span>
                  <span style={{ display: "block", fontSize: 15, fontWeight: 500 }}>{s.name}</span>
                  <span style={{ display: "block", marginTop: 4, ...micro(T.dim, "0.06em") }}>
                    {s.interval_hours === 24 ? "DAILY" : s.interval_hours === 48 ? "EVERY 2 DAYS" : "WEEKLY"} · {s.auto_publish ? "AUTO-PUBLISH" : "REVIEW FIRST"} · {(formats.get(s.format ?? "")?.label ?? s.output_type).toUpperCase()} · {s.video_count} RUNS{s.last_error ? " · ⚠" : ""}
                  </span>
                </span>
                <button onClick={() => onToggleSeries(s)} style={{ fontFamily: mono, fontSize: 10, letterSpacing: "0.06em", color: s.is_active ? T.ready : T.idle, background: "transparent", border: `1px solid ${s.is_active ? `${T.ready}40` : T.strong}`, borderRadius: 5, padding: "6px 8px", textAlign: "center", cursor: "pointer" }}>
                  {s.is_active ? "RUNNING" : "PAUSED"}
                </button>
              </div>
            ))}
            {series.length === 0 && (
              <div style={{ ...panel, padding: "16px 18px" }}>
                <p style={{ margin: 0, fontSize: 13.5, color: T.dim }}>No standing orders yet. Work that happens without you — one credit per run.</p>
              </div>
            )}
          </div>
        </div>

        <div style={{ minWidth: 0 }}>
          <p style={{ margin: "0 0 12px", fontSize: 12.5, fontWeight: 500, color: T.dim }}>Source material</p>
          {srcAsset ? (
            <div style={{ ...panel, borderRadius: 7, padding: "16px 18px" }}>
              <p style={{ margin: "0 0 4px", fontSize: 15, fontWeight: 600 }}>{srcAsset.filename}</p>
              <p style={{ ...micro(T.dim, "0.08em"), margin: "0 0 14px" }}>
                {srcAsset.duration ? fmtDur(srcAsset.duration) : "—"} · TRANSCRIBED · {(srcAsset.highlights ?? []).length} MOMENTS FOUND · YOUR FOOTAGE
              </p>
              <div style={{ position: "relative", height: 38, background: T.bg, backgroundImage: `repeating-linear-gradient(90deg, ${T.head} 0 1px, transparent 1px 7px)`, border: `1px solid ${T.rule}`, borderRadius: 6, marginBottom: 12 }}>
                {(srcAsset.highlights ?? []).map((h, i) => srcAsset.duration ? (
                  <span key={i} style={{ position: "absolute", left: `${(h.start / srcAsset.duration) * 100}%`, top: 0, bottom: 0, width: `${Math.max(((h.end - h.start) / srcAsset.duration) * 100, 1.5)}%`, background: `${T.signal}33`, borderLeft: `2px solid ${T.signal}`, display: "block" }} />
                ) : null)}
              </div>
              {(srcAsset.highlights ?? []).slice(0, 3).map((h, i) => (
                <div key={i} style={{ display: "grid", gridTemplateColumns: "100px 1fr 96px", gap: 12, padding: "11px 0", borderTop: `1px solid ${T.head}`, alignItems: "center" }}>
                  <span style={{ fontFamily: mono, fontSize: 11, color: i === 0 ? T.signal : T.dim }}>{fmtDur(h.start)}–{fmtDur(h.end)}</span>
                  <span style={{ fontSize: 13, minWidth: 0, color: i === 0 ? T.text : T.body }}>{h.title} — {h.reason}</span>
                  <button onClick={() => onCut(srcAsset.id, h)} disabled={cutting} style={i === 0 ? monoBtn("signal") : monoBtn("ghost")}>{cutting ? "CUTTING…" : "CUT · 1 CR"}</button>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ ...panel, borderRadius: 7, padding: "16px 18px" }}>
              <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.6, color: T.dim }}>
                Upload a podcast or long video in the classic dashboard&apos;s Clips page and its best moments appear here, ready to cut.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/* ==================== SHEETS ==================== */
function DeskSheets({ sheet, close, active, credits, channels, niches, onPublished, openChannelSheet, onOrderCreated }: {
  sheet: Exclude<Sheet, null>; close: () => void; active: VideoT | null
  credits?: { balance: number; plan: string }; channels: ChannelT[]; niches: { key: string; label: string }[]
  onPublished: () => void; openChannelSheet: () => void; onOrderCreated: () => void
}) {
  const [pubTitle, setPubTitle] = useState(active?.title ?? "")
  const [pubDesc, setPubDesc] = useState(active?.description ?? "")
  const [pubTags, setPubTags] = useState((active?.tags ?? []).join(", "))
  const [privacy, setPrivacy] = useState<"unlisted" | "public">("unlisted")
  const [pubWhen, setPubWhen] = useState("")
  const [orderTitle, setOrderTitle] = useState("Daily gaming update")
  const [orderNiche, setOrderNiche] = useState<string | null>("gaming")
  const [orderCadence, setOrderCadence] = useState(24)
  const [orderReview, setOrderReview] = useState(true)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const publishNow = async () => {
    if (!active) return close()
    if (channels.length === 0) return openChannelSheet()
    setWorking(true); setError(null)
    try {
      await fetchApi(`/videos/${active.id}/metadata`, { method: "PUT", body: JSON.stringify({ title: pubTitle, description: pubDesc, tags: pubTags.split(",").map(t => t.trim()).filter(Boolean) }) })
      const held = pubWhen.trim() ? new Date(pubWhen.trim()) : null
      if (held && !isNaN(held.getTime()) && held > new Date()) {
        await fetchApi(`/uploads/${active.id}/schedule`, { method: "POST", body: JSON.stringify({ channel_id: channels[0].id, privacy, category_id: "24", publish_at: held.toISOString() }) })
      } else {
        await fetchApi(`/uploads/${active.id}/publish`, { method: "POST", body: JSON.stringify({ channel_id: channels[0].id, privacy, category_id: "24" }) })
      }
      onPublished()
    } catch (e) { setError(String((e as Error).message).slice(0, 240)) } finally { setWorking(false) }
  }

  const createOrder = async () => {
    setWorking(true); setError(null)
    try {
      await fetchApi("/series", {
        method: "POST",
        body: JSON.stringify({
          name: orderTitle || "Untitled order", category: orderNiche, format: "viral_story",
          interval_hours: orderCadence, auto_publish: orderReview ? false : channels.length > 0,
          channel_id: !orderReview && channels.length ? channels[0].id : null,
        }),
      })
      onOrderCreated()
    } catch (e) { setError(String((e as Error).message).slice(0, 240)) } finally { setWorking(false) }
  }

  const connectYouTube = async () => {
    try { const r = await fetchApi("/channels/connect") as { url: string }; window.location.href = r.url } catch (e) { setError(String((e as Error).message).slice(0, 200)) }
  }

  const titles: Record<string, [string, string]> = {
    publish: ["Approve & publish", "Everything here is editable before it leaves."],
    credits: ["Credits", "The render is waiting, not lost."],
    channel: ["Connect a channel", "Upload permission only."],
    order: ["New standing order", "Work that happens without you."],
  }

  const label = (t: string) => <p style={{ margin: "0 0 8px", fontSize: 12.5, fontWeight: 500, color: T.dim }}>{t}</p>
  const input: React.CSSProperties = { width: "100%", boxSizing: "border-box", background: T.bg, border: `1px solid ${T.rule}`, outline: "none", padding: "11px 13px", fontSize: 14, color: T.text, borderRadius: 6 }

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 70, background: "#0A0B10c9", display: "flex", justifyContent: "flex-end" }} onClick={close}>
      <div onClick={e => e.stopPropagation()} style={{ width: 460, height: "100%", background: T.panel, borderLeft: `1px solid ${T.rule}`, display: "flex", flexDirection: "column" }}>
        <div style={{ flexShrink: 0, padding: "18px 22px", borderBottom: `1px solid ${T.rule}`, display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
          <div>
            <p style={{ margin: "0 0 4px", fontSize: 20, fontWeight: 600, letterSpacing: "-0.02em" }}>{titles[sheet][0]}</p>
            <p style={{ margin: 0, fontSize: 13, color: T.dim }}>{titles[sheet][1]}</p>
          </div>
          <button onClick={close} style={{ ...monoBtn("faint"), padding: "4px 8px" }}>ESC</button>
        </div>

        <div style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: 22 }}>
          {sheet === "publish" && (
            <div>
              {active && (
                <div style={{ border: `1px solid ${T.rule}`, borderRadius: 8, background: T.bg, padding: "14px 16px", marginBottom: 20, display: "flex", alignItems: "center", gap: 14 }}>
                  <span style={{ width: 40, height: 56, borderRadius: 4, background: T.head, overflow: "hidden", flexShrink: 0 }}>
                    {active.video_url && <video src={`${MEDIA_ORIGIN}${active.video_url}`} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />}
                  </span>
                  <span>
                    <span style={{ display: "block", fontFamily: mono, fontSize: 11, color: T.ready, marginBottom: 4 }}>READY · {FORMAT_CODES[active.output_type] ?? "NR"} · {active.aspect_ratio ?? "9:16"}</span>
                    <span style={{ display: "block", fontSize: 13, color: T.dim }}>CC-BY music credit is added to your description automatically when used</span>
                  </span>
                </div>
              )}
              {label(`Title — ${95 - pubTitle.length} left`)}
              <input value={pubTitle} onChange={e => setPubTitle(e.target.value.slice(0, 95))} style={{ ...input, marginBottom: 16 }} />
              {label("Description")}
              <textarea value={pubDesc} onChange={e => setPubDesc(e.target.value)} rows={4} style={{ ...input, fontSize: 13.5, lineHeight: 1.5, resize: "none", marginBottom: 16, fontFamily: "inherit" }} />
              {label("Tags")}
              <input value={pubTags} onChange={e => setPubTags(e.target.value)} style={{ ...input, fontFamily: mono, fontSize: 12.5, color: T.body, marginBottom: 20 }} />
              {label("Channel")}
              {channels.length > 0 ? (
                <div style={{ border: `1px solid ${T.rule}`, borderRadius: 7, background: T.bg, padding: "12px 14px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 16 }}>
                  <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ width: 22, height: 22, borderRadius: "50%", background: T.head, border: `1px solid ${T.strong}`, display: "block" }} />
                    <span style={{ fontSize: 13.5 }}>{channels[0].channel_name ?? "Your channel"}</span>
                    <span style={{ fontFamily: mono, fontSize: 10, color: T.ready }}>CONNECTED</span>
                  </span>
                  <span style={{ fontFamily: mono, fontSize: 10, color: T.faint }}>YOUTUBE</span>
                </div>
              ) : (
                <div style={{ border: `1px solid ${T.failed}40`, borderRadius: 7, background: `${T.failed}0F`, padding: 14, marginBottom: 16 }}>
                  <p style={{ margin: "0 0 10px", fontSize: 13.5, color: T.body }}>No channel connected yet — connect one without leaving this sheet.</p>
                  <button onClick={openChannelSheet} style={monoBtn("signal")}>CONNECT YOUTUBE</button>
                </div>
              )}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 16 }}>
                <div>
                  {label("Visibility")}
                  <div style={{ display: "flex", gap: 6 }}>
                    <button onClick={() => setPrivacy("unlisted")} style={pill(privacy === "unlisted")}>Unlisted</button>
                    <button onClick={() => setPrivacy("public")} style={pill(privacy === "public")}>Public</button>
                  </div>
                </div>
                <div>
                  {label("Hold until")}
                  <input value={pubWhen} onChange={e => setPubWhen(e.target.value)} placeholder="now · or 2026-08-05 09:00" style={{ ...input, fontFamily: mono, fontSize: 12, padding: "9px 11px" }} />
                </div>
              </div>
              {error && <p style={{ margin: 0, fontSize: 12.5, color: T.failed }}>{error}</p>}
            </div>
          )}

          {sheet === "credits" && (
            <div>
              <div style={{ border: `1px solid ${T.working}40`, borderRadius: 8, background: `${T.working}0F`, padding: 16, marginBottom: 22 }}>
                <p style={{ ...micro(T.working, "0.06em"), fontSize: 11, margin: "0 0 6px" }}>{(credits?.balance ?? 0) < 1 ? "RENDER REFUSED · 0 CREDITS" : `${credits?.balance} CREDITS ON HAND`}</p>
                <p style={{ margin: 0, fontSize: 14, lineHeight: 1.55, color: T.body }}>Your script and edits are saved on the line. Add credits and it renders immediately — nothing is lost.</p>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 20 }}>
                {[
                  { label: "Top-up · 10 credits", note: "One-off. Stays on your current plan.", price: "₹149", hot: false },
                  { label: "Pro · 50 credits / month", note: "No watermark · all engines · standing orders", price: "₹499", hot: true },
                  { label: "Studio · 150 credits / month", note: "Priority render · bulk queue · media kit", price: "₹1,299", hot: false },
                ].map(p => (
                  <div key={p.label} style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 12, alignItems: "center", background: T.bg, border: `1px solid ${p.hot ? T.signal : T.rule}`, borderRadius: 8, padding: "15px 16px", opacity: 0.75 }}>
                    <span>
                      <span style={{ display: "block", fontSize: 16, fontWeight: 600 }}>{p.label}</span>
                      <span style={{ display: "block", marginTop: 3, fontSize: 12.5, color: T.dim }}>{p.note}</span>
                    </span>
                    <span style={{ fontFamily: mono, fontSize: 14, color: p.hot ? T.signal : T.body }}>{p.price}</span>
                  </div>
                ))}
              </div>
              <p style={{ margin: 0, fontSize: 12.5, lineHeight: 1.6, color: T.faint }}>
                Buying switches on with the payment milestone — Razorpay and UPI for India. Until then plan credits refill monthly and failed renders always come back. Or bring your own Gemini / OpenAI / Hugging Face key in the classic dashboard&apos;s Settings.
              </p>
            </div>
          )}

          {sheet === "channel" && (
            <div>
              <div style={{ border: `1px solid ${T.rule}`, borderRadius: 8, background: T.bg, padding: 16, marginBottom: 18 }}>
                <p style={{ margin: "0 0 8px", fontSize: 14, lineHeight: 1.55, color: T.body }}>Kliptos uploads as you, to your channel. It asks for upload permission only — it never reads your analytics or edits existing videos.</p>
                <p style={{ margin: 0, fontFamily: mono, fontSize: 11, color: T.faint }}>SCOPE: youtube.upload</p>
              </div>
              <button onClick={connectYouTube} style={{ ...monoBtn("signal"), width: "100%", padding: 13, marginBottom: 10, fontSize: 11 }}>CONTINUE WITH GOOGLE</button>
              <button disabled style={{ ...monoBtn("ghost"), width: "100%", padding: 13, marginBottom: 16, fontSize: 11, opacity: 0.55, cursor: "default" }}>INSTAGRAM (REELS) — AFTER META REVIEW</button>
              <p style={{ margin: 0, fontSize: 12.5, lineHeight: 1.6, color: T.faint }}>
                Google may show an “unverified app” notice until our upload verification completes. Your footage and credentials stay yours either way.
              </p>
              {error && <p style={{ margin: "12px 0 0", fontSize: 12.5, color: T.failed }}>{error}</p>}
            </div>
          )}

          {sheet === "order" && (
            <div>
              {label("What it makes")}
              <input value={orderTitle} onChange={e => setOrderTitle(e.target.value)} style={{ ...input, marginBottom: 18 }} />
              {label("Signal source")}
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 18 }}>
                <button onClick={() => setOrderNiche(null)} style={pill(orderNiche === null)}>All niches</button>
                {niches.map(n => (
                  <button key={n.key} onClick={() => setOrderNiche(n.key)} style={pill(orderNiche === n.key)}>{n.label.replace(/^[^ ]+ /, "")}</button>
                ))}
              </div>
              {label("Cadence")}
              <div style={{ display: "flex", gap: 6, marginBottom: 18 }}>
                {[[24, "Daily"], [48, "Every 2 days"], [168, "Weekly"]].map(([v, l]) => (
                  <button key={v} onClick={() => setOrderCadence(v as number)} style={pill(orderCadence === v)}>{l}</button>
                ))}
              </div>
              {label("When it finishes")}
              <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 20 }}>
                <button onClick={() => setOrderReview(true)} style={blockOpt(orderReview)}>
                  <span style={{ display: "block", fontSize: 14, fontWeight: 500, color: T.text }}>Hold for my approval</span>
                  <span style={{ display: "block", marginTop: 3, fontSize: 12.5, color: T.dim }}>Lands on the desk. Forty seconds of your morning.</span>
                </button>
                <button onClick={() => setOrderReview(false)} style={blockOpt(!orderReview)}>
                  <span style={{ display: "block", fontSize: 14, fontWeight: 500, color: T.text }}>Publish without me</span>
                  <span style={{ display: "block", marginTop: 3, fontSize: 12.5, color: T.dim }}>{channels.length ? "Goes live on your channel at each run." : "Needs a connected channel — falls back to review until then."}</span>
                </button>
              </div>
              <p style={{ margin: 0, fontSize: 12.5, lineHeight: 1.6, color: T.faint }}>
                {orderReview ? "One credit per run, charged when it renders. Nothing publishes until you approve it." : "One credit per run. It posts on its own — you can still pull anything from the ledger."}
              </p>
              {error && <p style={{ margin: "12px 0 0", fontSize: 12.5, color: T.failed }}>{error}</p>}
            </div>
          )}
        </div>

        <div style={{ flexShrink: 0, padding: "16px 22px", borderTop: `1px solid ${T.rule}`, display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          <span style={{ fontFamily: mono, fontSize: 11, color: T.faint }}>
            {sheet === "publish" ? (pubWhen.trim() ? `HOLDS UNTIL ${pubWhen.trim().toUpperCase()}` : "GOES OUT IMMEDIATELY")
              : sheet === "credits" ? `${credits?.balance ?? 0} CR NOW`
              : sheet === "channel" ? "REVOCABLE ANY TIME"
              : "0 CR TO CREATE · 1 CR PER RUN"}
          </span>
          <button
            onClick={sheet === "publish" ? publishNow : sheet === "order" ? createOrder : close}
            disabled={working}
            style={sheet === "credits" || sheet === "channel"
              ? { ...monoBtn("ghost"), padding: "11px 16px", fontSize: 11 }
              : { ...monoBtn("signal"), padding: "11px 18px", fontSize: 11 }}
          >
            {working ? "WORKING…" : sheet === "publish" ? (pubWhen.trim() ? "SAVE & HOLD" : "PUBLISH NOW") : sheet === "credits" ? "MAYBE LATER" : sheet === "channel" ? "DO THIS LATER" : "START ORDER"}
          </button>
        </div>
      </div>
    </div>
  )
}

/* ==================== PALETTE ==================== */
function Palette({ query, setQuery, close, commands }: {
  query: string; setQuery: (q: string) => void; close: () => void
  commands: { group: string; color: string; label: string; keys: string; run: () => void }[]
}) {
  const filtered = commands.filter(c => !query || c.label.toLowerCase().includes(query.toLowerCase()) || c.group.toLowerCase().includes(query.toLowerCase()))
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 80, background: "#0A0B10cc", display: "flex", alignItems: "flex-start", justifyContent: "center", paddingTop: "14vh" }} onClick={close}>
      <div onClick={e => e.stopPropagation()} style={{ width: 620, background: T.panel, border: `1px solid ${T.strong}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "0 16px", borderBottom: `1px solid ${T.rule}` }}>
          <span style={{ fontSize: 12.5, fontWeight: 500, color: T.signal }}>CMD</span>
          <input autoFocus value={query} onChange={e => setQuery(e.target.value)} placeholder="Assign, amend, approve, jump…"
            style={{ flex: 1, background: "transparent", border: "none", outline: "none", padding: "16px 0", fontSize: 16, color: T.text }} />
          <button onClick={close} style={{ ...monoBtn("faint"), padding: "3px 7px" }}>ESC</button>
        </div>
        <div style={{ maxHeight: 300, overflowY: "auto" }}>
          {filtered.map(cmd => (
            <button key={cmd.label} onClick={() => { close(); cmd.run() }}
              style={{ display: "grid", gridTemplateColumns: "64px 1fr 110px", gap: 14, alignItems: "center", width: "100%", textAlign: "left", cursor: "pointer", background: "transparent", border: "none", borderBottom: `1px solid ${T.head}`, padding: "12px 16px", borderRadius: 0 }}>
              <span style={{ ...micro(cmd.color, "0.12em") }}>{cmd.group}</span>
              <span style={{ fontSize: 14, minWidth: 0, color: T.text }}>{cmd.label}</span>
              <span style={{ ...micro(T.faint, "0.08em"), textAlign: "right" }}>{cmd.keys}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
