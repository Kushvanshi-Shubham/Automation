"use client"

/**
 * Standing orders (series autopilot) — recurring shorts on a schedule,
 * from live trends or a fixed theme. Themed; all flows unchanged.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import {
  MdOutlineAdd, MdOutlineAutorenew, MdOutlineBolt, MdOutlineDeleteOutline,
  MdOutlinePause, MdOutlinePlayArrow,
} from "react-icons/md"
import { fetchApi } from "@/lib/api-client"
import { L, mono, grotesque, alpha } from "@/lib/line/tokens"

interface SeriesItem {
  id: string
  name: string
  category: string | null
  topic_prompt: string | null
  format: string | null
  style: string
  output_type: string
  language: string
  interval_hours: number
  auto_publish: boolean
  is_active: boolean
  last_run_at: string | null
  next_run_at: string | null
  last_error: string | null
  video_count: number
}

const INTERVALS = [
  { value: 24, label: "Daily" },
  { value: 48, label: "Every 2 days" },
  { value: 168, label: "Weekly" },
]

const STYLES = [
  { value: "viral_story", label: "Viral Story" },
  { value: "news_update", label: "News / Update" },
  { value: "educational", label: "Educational" },
  { value: "commentary", label: "Commentary" },
]

const card: React.CSSProperties = { background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 10 }
const label: React.CSSProperties = { display: "block", fontSize: 12.5, fontWeight: 600, color: L.ash, marginBottom: 6 }
const field: React.CSSProperties = {
  width: "100%", boxSizing: "border-box", background: L.floor, border: `1px solid ${L.rule}`,
  borderRadius: 8, color: L.ink, fontFamily: grotesque, fontSize: 13.5, padding: "9px 12px", outline: "none",
}
const primaryBtn = (disabled = false): React.CSSProperties => ({
  display: "flex", alignItems: "center", gap: 7, background: L.make, border: "none", color: "#fff",
  fontFamily: grotesque, fontSize: 13.5, fontWeight: 600, padding: "10px 16px", borderRadius: 8,
  cursor: disabled ? "default" : "pointer", opacity: disabled ? 0.55 : 1,
})
const iconBtn: React.CSSProperties = {
  display: "flex", alignItems: "center", justifyContent: "center", background: "transparent",
  border: `1px solid ${L.rule}`, color: L.ink, padding: 8, borderRadius: 7, cursor: "pointer",
}
const chip = (color: string): React.CSSProperties => ({
  fontSize: 11.5, fontWeight: 600, color, border: `1px solid ${alpha(color, 35)}`,
  padding: "2px 9px", borderRadius: 5,
})

export default function SeriesPage() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)

  const { data: series, isLoading } = useQuery<SeriesItem[]>({
    queryKey: ["series"],
    queryFn: () => fetchApi("/series"),
    refetchInterval: 30000,
  })
  const { data: formatCatalog } = useQuery<{ items: { key: string; label: string }[] }>({
    queryKey: ["formats"],
    queryFn: () => fetchApi("/scripts/formats"),
    staleTime: Infinity,
  })
  const formatLabel = (key: string | null) => formatCatalog?.items.find(x => x.key === key)?.label ?? null

  const toggle = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      fetchApi(`/series/${id}`, { method: "PATCH", body: JSON.stringify({ is_active: active }) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["series"] }),
  })
  const remove = useMutation({
    mutationFn: (id: string) => fetchApi(`/series/${id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["series"] }),
  })
  const runNow = useMutation({
    mutationFn: (id: string) => fetchApi(`/series/${id}/run-now`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["series"] }),
  })

  return (
    <div style={{ maxWidth: 860, fontFamily: grotesque, display: "flex", flexDirection: "column", gap: 18, paddingBottom: 24 }}>
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
        <div>
          <h1 style={{ margin: "0 0 4px", fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>Standing orders</h1>
          <p style={{ margin: 0, fontSize: 14, lineHeight: 1.5, color: L.ash, maxWidth: "58ch" }}>
            A standing order makes a fresh short on schedule — from your niche&apos;s live trends or a theme
            you set — and either publishes it or holds it for your review.
          </p>
        </div>
        <button onClick={() => setShowForm(!showForm)} style={primaryBtn()}>
          <MdOutlineAdd size={17} /> New standing order
        </button>
      </div>

      {showForm && <CreateForm onDone={() => setShowForm(false)} />}

      {isLoading && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {Array.from({ length: 2 }).map((_, i) => <div key={i} style={{ ...card, height: 96, opacity: 0.5 }} />)}
        </div>
      )}

      {!isLoading && (series ?? []).length === 0 && !showForm && (
        <div style={{ ...card, padding: "34px 30px", maxWidth: 640 }}>
          <h3 style={{ margin: "0 0 6px", display: "flex", alignItems: "center", gap: 8, fontSize: 17, fontWeight: 600 }}>
            <MdOutlineAutorenew size={20} color={L.ash} /> Nothing on autopilot yet
          </h3>
          <p style={{ margin: "0 0 16px", fontSize: 13.5, lineHeight: 1.6, color: L.ash, maxWidth: "52ch" }}>
            Set one up and Kliptos keeps your channel fed without you — each run costs 1 credit and is
            skipped safely if you run out. Start with auto-publish off: videos wait in your Library for review.
          </p>
          <button onClick={() => setShowForm(true)} style={primaryBtn()}>
            <MdOutlineAdd size={17} /> Create your first standing order
          </button>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {(series ?? []).map(s => (
          <div key={s.id} style={{ ...card, padding: "16px 18px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 14, flexWrap: "wrap" }}>
            <div style={{ minWidth: 0, flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <h3 style={{ margin: 0, fontSize: 15.5, fontWeight: 650 }}>{s.name}</h3>
                <span style={chip(s.is_active ? L.ready : L.dust)}>{s.is_active ? "Active" : "Paused"}</span>
                {s.auto_publish && <span style={chip(L.make)}>Auto-publish</span>}
              </div>
              <p style={{ margin: "6px 0 0", fontSize: 12.5, lineHeight: 1.5, color: L.dust }}>
                {s.topic_prompt ? `Theme: ${s.topic_prompt}` : `Niche: ${s.category ?? "all trends"}`}
                {" · "}{INTERVALS.find(i => i.value === s.interval_hours)?.label ?? `${s.interval_hours}h`}
                {" · "}{formatLabel(s.format) ?? (s.output_type === "visual" ? "Visual" : "Narrated")}
                {" · "}{s.language}
                {" · "}<span style={{ fontFamily: mono }}>{s.video_count}</span> video{s.video_count === 1 ? "" : "s"} made
              </p>
              {s.next_run_at && s.is_active && (
                <p style={{ margin: "3px 0 0", fontSize: 12, color: L.dust }}>
                  Next run: {new Date(s.next_run_at).toLocaleString()}
                </p>
              )}
              {s.last_error && <p style={{ margin: "3px 0 0", fontSize: 12, color: L.working }}>{s.last_error}</p>}
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
              <button onClick={() => runNow.mutate(s.id)} disabled={runNow.isPending}
                title="Create one video now (1 credit)"
                style={{ ...iconBtn, gap: 6, fontSize: 12.5, fontWeight: 600, fontFamily: grotesque, padding: "8px 12px", opacity: runNow.isPending ? 0.55 : 1 }}>
                <MdOutlineBolt size={16} /> {runNow.isPending ? "Starting…" : "Run now"}
              </button>
              <button onClick={() => toggle.mutate({ id: s.id, active: !s.is_active })}
                title={s.is_active ? "Pause" : "Resume"} style={iconBtn}>
                {s.is_active ? <MdOutlinePause size={17} /> : <MdOutlinePlayArrow size={17} />}
              </button>
              <button onClick={() => remove.mutate(s.id)} title="Delete (videos are kept)"
                style={{ ...iconBtn, border: "none", color: L.dust }}>
                <MdOutlineDeleteOutline size={18} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function CreateForm({ onDone }: { onDone: () => void }) {
  const queryClient = useQueryClient()
  const [name, setName] = useState("")
  const [mode, setMode] = useState<"trends" | "theme">("trends")
  const [category, setCategory] = useState("")
  const [theme, setTheme] = useState("")
  const [format, setFormat] = useState("viral_story")  // format key, or "custom"
  const [style, setStyle] = useState("viral_story")
  const [outputType, setOutputType] = useState("narrated")
  const [language, setLanguage] = useState("English")
  const [voiceId, setVoiceId] = useState("")
  const [interval, setInterval] = useState(24)
  const [autoPublish, setAutoPublish] = useState(false)
  const [channelId, setChannelId] = useState("")
  const [privacy, setPrivacy] = useState("unlisted")

  const { data: niches } = useQuery<{ items: { key: string; label: string }[] }>({
    queryKey: ["niches"],
    queryFn: () => fetchApi("/topics/niches"),
    staleTime: Infinity,
  })
  const { data: voiceData } = useQuery<{ voices: { id: string; label: string; language: string; vibe: string }[]; languages: string[] }>({
    queryKey: ["voices"],
    queryFn: () => fetchApi("/scripts/voices"),
    staleTime: Infinity,
  })
  const { data: channels } = useQuery<{ id: string; channel_name: string | null }[]>({
    queryKey: ["channels"],
    queryFn: () => fetchApi("/channels"),
  })
  const { data: formats } = useQuery<{ items: { key: string; label: string; output_type: string; available: boolean; own?: boolean }[] }>({
    queryKey: ["formats"],
    queryFn: () => fetchApi("/scripts/formats"),
    staleTime: Infinity,
  })
  // Series run on autopilot — only built-in video-producing formats qualify.
  const seriesFormats = (formats?.items ?? []).filter(f => f.available && !f.own && f.output_type !== "image")
  const effectiveOutput = format === "custom"
    ? outputType
    : (seriesFormats.find(f => f.key === format)?.output_type ?? "narrated")

  const create = useMutation({
    mutationFn: () =>
      fetchApi("/series", {
        method: "POST",
        body: JSON.stringify({
          name,
          category: mode === "trends" && category ? category : null,
          topic_prompt: mode === "theme" ? theme : null,
          format: format === "custom" ? null : format,
          style,
          output_type: format === "custom" ? outputType : effectiveOutput === "fake_text" ? "narrated" : effectiveOutput,
          language,
          voice_id: voiceId || null,
          interval_hours: interval,
          auto_publish: autoPublish,
          channel_id: autoPublish ? channelId || null : null,
          publish_privacy: privacy,
        }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["series"] })
      onDone()
    },
  })

  const canSubmit = name.trim().length >= 2 && (mode === "trends" || theme.trim().length >= 5)
    && (!autoPublish || channelId)

  const pill = (on: boolean): React.CSSProperties => ({
    background: on ? alpha(L.make, 8) : L.floor, border: `1px solid ${on ? alpha(L.make, 45) : L.rule}`,
    color: L.ink, fontFamily: grotesque, fontSize: 13, fontWeight: on ? 600 : 400,
    padding: "8px 14px", borderRadius: 8, cursor: "pointer",
  })

  return (
    <div style={{ ...card, borderColor: alpha(L.make, 30), padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <span style={label}>Name</span>
          <input value={name} onChange={e => setName(e.target.value.slice(0, 80))}
            placeholder="e.g. Daily gaming facts" style={field} />
        </div>
        <div>
          <span style={label}>How often</span>
          <select value={interval} onChange={e => setInterval(Number(e.target.value))} style={field}>
            {INTERVALS.map(i => <option key={i.value} value={i.value}>{i.label}</option>)}
          </select>
        </div>
      </div>

      <div>
        <span style={label}>Where topics come from</span>
        <div style={{ display: "flex", gap: 6, marginBottom: 10 }}>
          <button onClick={() => setMode("trends")} style={pill(mode === "trends")}>Live trends</button>
          <button onClick={() => setMode("theme")} style={pill(mode === "theme")}>A theme I set</button>
        </div>
        {mode === "trends" ? (
          <select value={category} onChange={e => setCategory(e.target.value)} style={{ ...field, maxWidth: 280 }}>
            <option value="">All niches</option>
            {(niches?.items ?? []).map(n => <option key={n.key} value={n.key}>{n.label}</option>)}
          </select>
        ) : (
          <input value={theme} onChange={e => setTheme(e.target.value.slice(0, 300))}
            placeholder="e.g. Interesting chess puzzles explained simply" style={field} />
        )}
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <span style={label}>Format</span>
          <select value={format} onChange={e => setFormat(e.target.value)}
            title="The recipe every episode runs" style={field}>
            {seriesFormats.map(f => <option key={f.key} value={f.key}>{f.label}</option>)}
            <option value="custom">Custom</option>
          </select>
        </div>
        {format === "custom" && (
          <>
            <div>
              <span style={label}>Style</span>
              <select value={style} onChange={e => setStyle(e.target.value)} style={field}>
                {STYLES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
            </div>
            <div>
              <span style={label}>Type</span>
              <select value={outputType} onChange={e => setOutputType(e.target.value)} style={field}>
                <option value="narrated">Narrated</option>
                <option value="visual">Visual</option>
              </select>
            </div>
          </>
        )}
        <div>
          <span style={label}>Language</span>
          <select value={language} onChange={e => setLanguage(e.target.value)} style={field}>
            {(voiceData?.languages ?? ["English"]).map(l => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
        <div>
          <span style={label}>Voice</span>
          <select value={voiceId} onChange={e => setVoiceId(e.target.value)} disabled={effectiveOutput !== "narrated"}
            style={{ ...field, opacity: effectiveOutput !== "narrated" ? 0.5 : 1 }}>
            <option value="">Default voice</option>
            {(voiceData?.voices ?? []).map(v => <option key={v.id} value={v.id}>{v.label} · {v.language}</option>)}
          </select>
        </div>
      </div>

      <div style={{ background: L.floor, border: `1px solid ${L.ruleFaint}`, borderRadius: 8, padding: "12px 14px", display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13.5, fontWeight: 600, cursor: "pointer" }}>
          <input type="checkbox" checked={autoPublish} onChange={e => setAutoPublish(e.target.checked)}
            style={{ width: 15, height: 15, accentColor: "var(--k-make)" }} />
          Publish to YouTube automatically
        </label>
        {autoPublish ? (
          <>
            <select value={channelId} onChange={e => setChannelId(e.target.value)} style={{ ...field, flex: 1, minWidth: 180 }}>
              <option value="">Select channel…</option>
              {(channels ?? []).map(c => <option key={c.id} value={c.id}>{c.channel_name ?? "Unnamed"}</option>)}
            </select>
            <select value={privacy} onChange={e => setPrivacy(e.target.value)} style={{ ...field, width: 130 }}>
              <option value="unlisted">Unlisted</option>
              <option value="public">Public</option>
              <option value="private">Private</option>
            </select>
          </>
        ) : (
          <span style={{ fontSize: 12, color: L.dust }}>Off = videos wait in your Library for review (recommended to start)</span>
        )}
      </div>

      {create.error && <p style={{ margin: 0, fontSize: 12.5, color: L.refused }}>{(create.error as Error).message}</p>}

      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <button onClick={() => create.mutate()} disabled={!canSubmit || create.isPending}
          style={primaryBtn(!canSubmit || create.isPending)}>
          <MdOutlineAutorenew size={16} /> {create.isPending ? "Creating…" : "Start the standing order"}
        </button>
        <button onClick={onDone}
          style={{ background: "transparent", border: `1px solid ${L.rule}`, color: L.ink, fontFamily: grotesque, fontSize: 13.5, padding: "10px 16px", borderRadius: 8, cursor: "pointer" }}>
          Cancel
        </button>
      </div>
      <p style={{ margin: 0, fontSize: 12, color: L.dust }}>
        Each video costs 1 credit; runs are skipped safely when you&apos;re out. First video within ~15 minutes.
      </p>
    </div>
  )
}
