"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Loader2, Pause, Play, Plus, Repeat, Trash2, Zap } from "lucide-react"
import { useState } from "react"
import { fetchApi } from "@/lib/api-client"

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
  { value: "viral_story", label: "🎬 Viral Story" },
  { value: "news_update", label: "📰 News / Update" },
  { value: "educational", label: "🎓 Educational" },
  { value: "commentary", label: "🎙️ Commentary" },
]

export default function SeriesPage() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)

  const { data: series, isLoading } = useQuery<SeriesItem[]>({
    queryKey: ["series"],
    queryFn: () => fetchApi("/series"),
    refetchInterval: 30000,
  })
  const { data: formatCatalog } = useQuery<{ items: { key: string; label: string; emoji: string }[] }>({
    queryKey: ["formats"],
    queryFn: () => fetchApi("/scripts/formats"),
    staleTime: Infinity,
  })
  const formatLabel = (key: string | null) => {
    const f = formatCatalog?.items.find(x => x.key === key)
    return f ? `${f.emoji} ${f.label}` : null
  }

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
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Series Autopilot</h1>
          <p className="text-zinc-400 mt-1">
            Recurring shorts from live trends — rendered on schedule, published automatically or held for review.
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 text-sm font-medium text-white"
        >
          <Plus className="w-4 h-4" /> New Series
        </button>
      </div>

      {showForm && <CreateForm onDone={() => setShowForm(false)} />}

      {isLoading && (
        <div className="space-y-3">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="h-28 rounded-2xl bg-zinc-900/60 backdrop-blur-md border border-white/10 animate-pulse" />
          ))}
        </div>
      )}

      {!isLoading && (series ?? []).length === 0 && !showForm && (
        <div className="flex flex-col items-center justify-center py-20 text-center rounded-2xl bg-zinc-900/50 border border-white/5">
          <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-white/10 flex items-center justify-center mb-4">
            <Repeat className="w-8 h-8 text-zinc-500" />
          </div>
          <h3 className="text-lg font-semibold mb-1">No series yet</h3>
          <p className="text-zinc-400 text-sm mb-6 max-w-sm">
            A series creates a fresh short on schedule — from your niche&apos;s live trends or a theme you set.
          </p>
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 font-medium text-white text-sm"
          >
            <Plus className="w-4 h-4" /> Create your first series
          </button>
        </div>
      )}

      <div className="space-y-3">
        {(series ?? []).map(s => (
          <div key={s.id} className="p-5 rounded-2xl bg-zinc-900/60 backdrop-blur-md border border-white/10">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-semibold">{s.name}</h3>
                  <span className={`px-2 py-0.5 rounded-md text-xs font-medium border ${
                    s.is_active
                      ? "bg-emerald-400/10 text-emerald-400 border-emerald-400/20"
                      : "bg-zinc-400/10 text-zinc-400 border-zinc-400/20"
                  }`}>
                    {s.is_active ? "Active" : "Paused"}
                  </span>
                  {s.auto_publish && (
                    <span className="px-2 py-0.5 rounded-md text-xs font-medium bg-violet-400/10 text-violet-300 border border-violet-400/20">
                      Auto-publish
                    </span>
                  )}
                </div>
                <p className="text-xs text-zinc-500 mt-1.5">
                  {s.topic_prompt ? `Theme: ${s.topic_prompt}` : `Niche: ${s.category ?? "all trends"}`}
                  {" · "}{INTERVALS.find(i => i.value === s.interval_hours)?.label ?? `${s.interval_hours}h`}
                  {" · "}{formatLabel(s.format) ?? (s.output_type === "visual" ? "🎵 visual" : "🎙️ narrated")}
                  {" · "}{s.language}
                  {" · "}{s.video_count} video{s.video_count === 1 ? "" : "s"} created
                </p>
                {s.next_run_at && s.is_active && (
                  <p className="text-xs text-zinc-600 mt-1">Next run: {new Date(s.next_run_at).toLocaleString()}</p>
                )}
                {s.last_error && <p className="text-xs text-amber-400 mt-1">⚠ {s.last_error}</p>}
              </div>

              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  onClick={() => runNow.mutate(s.id)}
                  disabled={runNow.isPending}
                  title="Create one video now (1 credit)"
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 text-xs font-medium transition-colors disabled:opacity-50"
                >
                  {runNow.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
                  Run now
                </button>
                <button
                  onClick={() => toggle.mutate({ id: s.id, active: !s.is_active })}
                  title={s.is_active ? "Pause" : "Resume"}
                  className="p-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                >
                  {s.is_active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </button>
                <button
                  onClick={() => remove.mutate(s.id)}
                  title="Delete series (videos are kept)"
                  className="p-2 rounded-lg text-zinc-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
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
  const { data: formats } = useQuery<{ items: { key: string; label: string; emoji: string; output_type: string; available: boolean }[] }>({
    queryKey: ["formats"],
    queryFn: () => fetchApi("/scripts/formats"),
    staleTime: Infinity,
  })
  // Series run on autopilot — only video-producing formats qualify.
  const seriesFormats = (formats?.items ?? []).filter(f => f.available && f.output_type !== "image")
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

  return (
    <div className="p-6 rounded-2xl bg-zinc-900 border border-violet-500/20 space-y-5">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider block mb-1.5">Series name</label>
          <input
            value={name}
            onChange={e => setName(e.target.value.slice(0, 80))}
            placeholder="e.g. Daily Gaming Facts"
            className="w-full bg-black/20 border border-white/10 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-violet-500/50"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider block mb-1.5">Cadence</label>
          <select
            value={interval}
            onChange={e => setInterval(Number(e.target.value))}
            className="w-full bg-black/20 border border-white/10 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-violet-500/50"
          >
            {INTERVALS.map(i => <option key={i.value} value={i.value}>{i.label}</option>)}
          </select>
        </div>
      </div>

      <div>
        <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider block mb-2">Topic source</label>
        <div className="flex gap-2 mb-3">
          <button
            onClick={() => setMode("trends")}
            className={`px-3.5 py-2 rounded-lg text-sm font-medium border transition-all ${mode === "trends" ? "bg-violet-500/10 border-violet-500/40" : "bg-black/20 border-white/10"}`}
          >
            🔥 Live trends
          </button>
          <button
            onClick={() => setMode("theme")}
            className={`px-3.5 py-2 rounded-lg text-sm font-medium border transition-all ${mode === "theme" ? "bg-violet-500/10 border-violet-500/40" : "bg-black/20 border-white/10"}`}
          >
            🎯 Fixed theme
          </button>
        </div>
        {mode === "trends" ? (
          <select
            value={category}
            onChange={e => setCategory(e.target.value)}
            className="w-full sm:w-64 bg-black/20 border border-white/10 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-violet-500/50"
          >
            <option value="">🌐 All niches</option>
            {(niches?.items ?? []).map(n => <option key={n.key} value={n.key}>{n.label}</option>)}
          </select>
        ) : (
          <input
            value={theme}
            onChange={e => setTheme(e.target.value.slice(0, 300))}
            placeholder="e.g. Interesting chess puzzles explained simply"
            className="w-full bg-black/20 border border-white/10 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-violet-500/50"
          />
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <select value={format} onChange={e => setFormat(e.target.value)}
                title="The pipeline recipe every episode runs"
                className="bg-black/20 border border-white/10 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-violet-500/50">
          {seriesFormats.map(f => <option key={f.key} value={f.key}>{f.emoji} {f.label}</option>)}
          <option value="custom">🛠️ Custom</option>
        </select>
        {format === "custom" && (
          <>
            <select value={style} onChange={e => setStyle(e.target.value)}
                    className="bg-black/20 border border-white/10 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-violet-500/50">
              {STYLES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
            <select value={outputType} onChange={e => setOutputType(e.target.value)}
                    className="bg-black/20 border border-white/10 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-violet-500/50">
              <option value="narrated">🎙️ Narrated</option>
              <option value="visual">🎵 Visual</option>
            </select>
          </>
        )}
        <select value={language} onChange={e => setLanguage(e.target.value)}
                className="bg-black/20 border border-white/10 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-violet-500/50">
          {(voiceData?.languages ?? ["English"]).map(l => <option key={l} value={l}>{l}</option>)}
        </select>
        <select value={voiceId} onChange={e => setVoiceId(e.target.value)} disabled={effectiveOutput !== "narrated"}
                className="bg-black/20 border border-white/10 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-violet-500/50 disabled:opacity-40">
          <option value="">Default voice</option>
          {(voiceData?.voices ?? []).map(v => <option key={v.id} value={v.id}>{v.label} · {v.language}</option>)}
        </select>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center gap-3 p-4 rounded-xl bg-black/20 border border-white/5">
        <label className="flex items-center gap-2 text-sm font-medium cursor-pointer">
          <input type="checkbox" checked={autoPublish} onChange={e => setAutoPublish(e.target.checked)}
                 className="w-4 h-4 accent-violet-600" />
          Auto-publish to YouTube
        </label>
        {autoPublish && (
          <>
            <select value={channelId} onChange={e => setChannelId(e.target.value)}
                    className="flex-1 bg-black/30 border border-white/10 rounded-xl px-3 py-2 text-sm focus:outline-none">
              <option value="">Select channel…</option>
              {(channels ?? []).map(c => <option key={c.id} value={c.id}>{c.channel_name ?? "Unnamed"}</option>)}
            </select>
            <select value={privacy} onChange={e => setPrivacy(e.target.value)}
                    className="bg-black/30 border border-white/10 rounded-xl px-3 py-2 text-sm focus:outline-none">
              <option value="unlisted">Unlisted</option>
              <option value="public">Public</option>
              <option value="private">Private</option>
            </select>
          </>
        )}
        {!autoPublish && (
          <span className="text-xs text-zinc-500">Off = videos wait in your library for review (recommended to start)</span>
        )}
      </div>

      {create.error && <p className="text-xs text-rose-400">{(create.error as Error).message}</p>}

      <div className="flex gap-3">
        <button
          onClick={() => create.mutate()}
          disabled={!canSubmit || create.isPending}
          className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 text-sm font-medium text-white disabled:opacity-50"
        >
          {create.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Repeat className="w-4 h-4" />}
          Start Series
        </button>
        <button onClick={onDone} className="px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm font-medium">
          Cancel
        </button>
      </div>
      <p className="text-xs text-zinc-600">
        Each video costs 1 credit. Runs are skipped safely when you&apos;re out of credits. First video within ~15 minutes.
      </p>
    </div>
  )
}
