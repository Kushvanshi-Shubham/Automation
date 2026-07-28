"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { motion } from "framer-motion"
import { Clapperboard, Clock, Loader2, PenTool, RefreshCw, Save, Sparkles, TrendingUp } from "lucide-react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { Suspense, useEffect, useState } from "react"
import { fetchApi } from "@/lib/api-client"

interface Segment {
  text: string
  visual_prompt: string
  duration_estimate: number
}

interface Script {
  video_id: string
  segments: Segment[]
  total_duration: number
}

export default function StudioPage() {
  return (
    <Suspense fallback={<div className="h-64 rounded-2xl bg-zinc-900 border border-white/5 animate-pulse" />}>
      <StudioContent />
    </Suspense>
  )
}

function StudioContent() {
  const searchParams = useSearchParams()
  const videoId = searchParams.get("video")

  if (!videoId) return <EmptyStudio />
  return <ScriptEditor videoId={videoId} />
}

const STYLES = [
  { value: "viral_story", label: "🎬 Viral Story", desc: "Hook-driven storytelling (default)" },
  { value: "news_update", label: "📰 News / Update", desc: "Patch notes, releases, results — facts first" },
  { value: "educational", label: "🎓 Educational", desc: "Explain one concept with an analogy" },
  { value: "commentary", label: "🎙️ Commentary", desc: "Opinionated take, invites comments" },
]

function EmptyStudio() {
  const router = useRouter()
  const [mode, setMode] = useState<"idea" | "own">("idea")
  const [prompt, setPrompt] = useState("")
  const [ownScript, setOwnScript] = useState("")
  const [style, setStyle] = useState("viral_story")

  const create = useMutation({
    mutationFn: () =>
      fetchApi("/scripts/generate", {
        method: "POST",
        body: JSON.stringify(
          mode === "own" ? { custom_script: ownScript } : { custom_prompt: prompt, style }
        ),
      }),
    onSuccess: (data: { video_id: string }) => router.push(`/dashboard/studio?video=${data.video_id}`),
  })

  const canSubmit = mode === "own" ? ownScript.trim().length >= 40 : prompt.trim().length >= 10

  return (
    <div className="max-w-2xl mx-auto space-y-6 pb-12">
      <div className="text-center pt-4">
        <h1 className="text-3xl font-bold mb-2">Script Studio</h1>
        <p className="text-zinc-400">
          Start from an idea, or{" "}
          <Link href="/dashboard/topics" className="text-violet-400 hover:text-violet-300">
            pick a trending topic
          </Link>
          .
        </p>
      </div>

      <div className="flex items-center gap-2 bg-zinc-900 p-1.5 rounded-xl border border-white/5 w-fit mx-auto">
        <button
          onClick={() => setMode("idea")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${mode === "idea" ? "bg-white/10 text-white" : "text-zinc-400 hover:text-zinc-200"}`}
        >
          <PenTool className="w-4 h-4 inline mr-1.5" />AI writes it
        </button>
        <button
          onClick={() => setMode("own")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${mode === "own" ? "bg-white/10 text-white" : "text-zinc-400 hover:text-zinc-200"}`}
        >
          ✍️ I have my own script
        </button>
      </div>

      <div className="rounded-2xl bg-zinc-900 border border-white/5 p-6 space-y-5">
        {mode === "idea" ? (
          <>
            <div>
              <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider block mb-2">What&apos;s the video about?</label>
              <textarea
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                rows={3}
                placeholder="e.g. Apex Legends new season — everything that changed"
                className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm focus:outline-none focus:border-violet-500/50 resize-none"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider block mb-2">Video style</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {STYLES.map(s => (
                  <button
                    key={s.value}
                    onClick={() => setStyle(s.value)}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      style === s.value
                        ? "bg-violet-500/10 border-violet-500/40"
                        : "bg-black/20 border-white/10 hover:border-white/20"
                    }`}
                  >
                    <p className="text-sm font-medium">{s.label}</p>
                    <p className="text-xs text-zinc-500 mt-0.5">{s.desc}</p>
                  </button>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div>
            <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider block mb-2">
              Paste your script — your wording stays exactly as written
            </label>
            <textarea
              value={ownScript}
              onChange={e => setOwnScript(e.target.value)}
              rows={10}
              placeholder="Write or paste your full narration here. We only split it into segments and pick matching visuals — not a single word gets changed."
              className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm focus:outline-none focus:border-violet-500/50 resize-none"
            />
          </div>
        )}

        {create.error && <p className="text-xs text-rose-400">{(create.error as Error).message}</p>}

        <button
          onClick={() => create.mutate()}
          disabled={!canSubmit || create.isPending}
          className="w-full py-3 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 font-medium text-white text-sm disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {create.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          {create.isPending ? "Working…" : mode === "own" ? "Structure My Script" : "Generate Script"}
        </button>
      </div>
    </div>
  )
}

function ScriptEditor({ videoId }: { videoId: string }) {
  const queryClient = useQueryClient()
  const router = useRouter()
  const [segments, setSegments] = useState<Segment[]>([])
  const [dirty, setDirty] = useState(false)
  const [regenIndex, setRegenIndex] = useState<number | null>(null)
  const [feedback, setFeedback] = useState("")

  const { data, isLoading, error } = useQuery<Script>({
    queryKey: ["script", videoId],
    queryFn: () => fetchApi(`/scripts/${videoId}`),
  })

  useEffect(() => {
    if (data?.segments) {
      setSegments(data.segments)
      setDirty(false)
    }
  }, [data])

  const save = useMutation({
    mutationFn: () => fetchApi(`/scripts/${videoId}`, { method: "PUT", body: JSON.stringify({ segments }) }),
    onSuccess: () => {
      setDirty(false)
      queryClient.invalidateQueries({ queryKey: ["script", videoId] })
    },
  })

  const regen = useMutation({
    mutationFn: (index: number) =>
      fetchApi(`/scripts/${videoId}/regenerate-segment`, {
        method: "POST",
        body: JSON.stringify({ segment_index: index, feedback: feedback || "make it punchier and more engaging" }),
      }),
    onSuccess: () => {
      setRegenIndex(null)
      setFeedback("")
      queryClient.invalidateQueries({ queryKey: ["script", videoId] })
    },
  })

  const render = useMutation({
    mutationFn: () =>
      fetchApi("/pipeline/start", {
        method: "POST",
        body: JSON.stringify({ video_id: videoId, visual_engine: "pexels" }),
      }),
    onSuccess: (data: { job_id: string }) => {
      queryClient.invalidateQueries({ queryKey: ["credits"] })
      router.push(`/dashboard/preview/${videoId}?job=${data.job_id}`)
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-32 rounded-2xl bg-zinc-900 border border-white/5 animate-pulse" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
        Failed to load script: {(error as Error).message}
      </div>
    )
  }

  const totalDuration = segments.reduce((sum, s) => sum + (s.duration_estimate || 0), 0)

  const updateSegment = (index: number, patch: Partial<Segment>) => {
    setSegments(prev => prev.map((s, i) => (i === index ? { ...s, ...patch } : s)))
    setDirty(true)
  }

  return (
    <div className="space-y-6 pb-12 max-w-4xl">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Script Studio</h1>
          <p className="text-zinc-400 mt-1 flex items-center gap-2">
            <Clock className="w-4 h-4" /> ~{Math.round(totalDuration)}s spoken · {segments.length} segments
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => save.mutate()}
            disabled={!dirty || save.isPending}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 font-medium text-sm disabled:opacity-50 transition-colors"
          >
            {save.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {dirty ? "Save Changes" : "Saved"}
          </button>
          <button
            onClick={() => render.mutate()}
            disabled={render.isPending || dirty}
            title={dirty ? "Save your changes first" : "Costs 1 credit (Pexels visuals)"}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 font-medium text-white text-sm disabled:opacity-50"
          >
            {render.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Clapperboard className="w-4 h-4" />}
            Generate Video · 1 credit
          </button>
        </div>
      </div>

      {render.error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
          {(render.error as Error).message}
        </div>
      )}

      <div className="space-y-4">
        {segments.map((segment, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: Math.min(i * 0.05, 0.4) }}
            className="rounded-2xl bg-zinc-900 border border-white/5 overflow-hidden"
          >
            <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between bg-zinc-950/40">
              <span className="text-xs font-bold uppercase tracking-wider text-zinc-500">
                {i === 0 ? "🎣 Hook" : i === segments.length - 1 ? "🏁 Payoff" : `Segment ${i + 1}`}
                <span className="ml-3 text-zinc-600 normal-case font-medium">~{segment.duration_estimate}s</span>
              </span>
              <button
                onClick={() => setRegenIndex(regenIndex === i ? null : i)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-violet-300 hover:bg-violet-500/10 border border-transparent hover:border-violet-500/20 transition-colors"
              >
                <Sparkles className="w-3.5 h-3.5" /> Regenerate
              </button>
            </div>

            <div className="p-5 space-y-4">
              <div>
                <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider block mb-1.5">Narration</label>
                <textarea
                  value={segment.text}
                  onChange={e => updateSegment(i, { text: e.target.value })}
                  rows={2}
                  className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-zinc-100 focus:outline-none focus:border-violet-500/50 resize-none"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider block mb-1.5">Visual Prompt</label>
                <input
                  value={segment.visual_prompt}
                  onChange={e => updateSegment(i, { visual_prompt: e.target.value })}
                  className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-zinc-300 focus:outline-none focus:border-violet-500/50"
                />
              </div>

              {regenIndex === i && (
                <div className="flex gap-2 pt-1">
                  <input
                    value={feedback}
                    onChange={e => setFeedback(e.target.value)}
                    placeholder="What should change? e.g. 'shorter, more dramatic'"
                    className="flex-1 bg-black/30 border border-violet-500/30 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-violet-500"
                  />
                  <button
                    onClick={() => regen.mutate(i)}
                    disabled={regen.isPending}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-violet-600 text-white text-sm font-medium disabled:opacity-60"
                  >
                    {regen.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                    Go
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
