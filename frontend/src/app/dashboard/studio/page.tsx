"use client"

/**
 * Create — the proven anatomy in the new design system.
 * Start screen: mode toggle, format grid, prompt, advanced options.
 * Editor: segments on the left, a sticky settings rail (voice, captions,
 * aspect, render) on the right. Light + dark, Material icons.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { Suspense, useState } from "react"
import {
  MdOutlineAutoAwesome, MdOutlineContentCopy, MdOutlineEditNote, MdOutlineImage,
  MdOutlinePlayArrow, MdOutlineSave, MdOutlineSmartDisplay, MdOutlineTimer,
} from "react-icons/md"
import { API_BASE_URL, fetchApi } from "@/lib/api-client"
import { L, mono, grotesque, alpha } from "@/lib/line/tokens"

interface Segment {
  text: string
  visual_prompt: string
  duration_estimate: number
  media_id?: number | null
  media_thumb?: string | null
}
interface MediaOption { id: number; thumb: string; kind: string; duration?: number; photographer?: string }
interface Script {
  video_id: string; segments: Segment[]; total_duration: number; output_type: string
  format?: string | null; defaults?: { voice_id?: string; caption_style?: string } | null
}
interface Voice { id: string; label: string; language: string; gender: string; vibe: string }
interface Format { key: string; label: string; emoji: string; desc: string; output_type: string; available: boolean }

const STYLES = [
  { value: "viral_story", label: "Viral Story", desc: "Hook-driven storytelling (default)" },
  { value: "news_update", label: "News / Update", desc: "Patch notes, releases, results — facts first" },
  { value: "educational", label: "Educational", desc: "Explain one concept with an analogy" },
  { value: "commentary", label: "Commentary", desc: "Opinionated take, invites comments" },
]
const TONE_PRESETS = [
  "engaging and curious", "hype and energetic", "dramatic and suspenseful",
  "funny and meme-y", "calm and professional",
]
const OUTPUT_TYPES = [
  { value: "narrated", label: "Narrated short", desc: "AI voice narrates over visuals", badge: "1 credit" },
  { value: "visual", label: "Visual short", desc: "On-screen text + music, no voice — add trending audio when posting", badge: "1 credit" },
  { value: "image", label: "Image post", desc: "3–6 slide carousel with captions (stock photos)", badge: "1 credit" },
  { value: "script", label: "Script only", desc: "Just the script — film it yourself", badge: "Free · 5/day" },
]

const card: React.CSSProperties = { background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 10 }
const label: React.CSSProperties = { display: "block", fontSize: 12.5, fontWeight: 600, color: L.ash, marginBottom: 8 }
const field: React.CSSProperties = {
  width: "100%", boxSizing: "border-box", background: L.floor, border: `1px solid ${L.rule}`,
  borderRadius: 8, color: L.ink, fontFamily: grotesque, fontSize: 14, padding: "10px 12px", outline: "none",
}
const optionBtn = (on: boolean, disabled = false): React.CSSProperties => ({
  padding: "12px 14px", borderRadius: 8, textAlign: "left", cursor: disabled ? "not-allowed" : "pointer",
  background: on ? alpha(L.make, 8) : L.floor,
  border: `1px solid ${on ? alpha(L.make, 45) : L.rule}`,
  opacity: disabled ? 0.5 : 1, fontFamily: grotesque, width: "100%",
})
const primaryBtn = (disabled = false): React.CSSProperties => ({
  display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
  background: L.make, border: "none", color: "#fff", fontFamily: grotesque,
  fontSize: 14, fontWeight: 600, padding: "11px 18px", borderRadius: 8,
  cursor: disabled ? "default" : "pointer", opacity: disabled ? 0.55 : 1,
})
const ghostBtn: React.CSSProperties = {
  display: "flex", alignItems: "center", gap: 7, background: "transparent",
  border: `1px solid ${L.rule}`, color: L.ink, fontFamily: grotesque,
  fontSize: 13.5, padding: "10px 14px", borderRadius: 8, cursor: "pointer",
}

export default function StudioPage() {
  return (
    <Suspense fallback={<div style={{ ...card, height: 260, opacity: 0.5 }} />}>
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

/* ==================== START SCREEN ==================== */
function EmptyStudio() {
  const router = useRouter()
  const [mode, setMode] = useState<"idea" | "own">("idea")
  const [prompt, setPrompt] = useState("")
  const [ownScript, setOwnScript] = useState("")
  const [style, setStyle] = useState("viral_story")
  const [outputType, setOutputType] = useState("narrated")
  const [format, setFormat] = useState<string>("viral_story")
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [model, setModel] = useState("auto")
  const [tone, setTone] = useState(TONE_PRESETS[0])
  const [customTone, setCustomTone] = useState("")
  const [instructions, setInstructions] = useState("")
  const [language, setLanguage] = useState("English")

  const { data: models } = useQuery<{ items: { key: string; label: string }[] }>({
    queryKey: ["llm-models"], queryFn: () => fetchApi("/scripts/models"), staleTime: Infinity,
  })
  const { data: voiceData } = useQuery<{ voices: Voice[]; languages: string[] }>({
    queryKey: ["voices"], queryFn: () => fetchApi("/scripts/voices"), staleTime: Infinity,
  })
  const { data: formats } = useQuery<{ items: Format[] }>({
    queryKey: ["formats"], queryFn: () => fetchApi("/scripts/formats"), staleTime: Infinity,
  })

  const create = useMutation({
    mutationFn: () =>
      fetchApi("/scripts/generate", {
        method: "POST",
        body: JSON.stringify(
          mode === "own"
            ? { custom_script: ownScript, model, output_type: outputType }
            : {
                custom_prompt: prompt, model, language,
                tone: tone === "__custom__" ? (customTone || TONE_PRESETS[0]) : tone,
                custom_instructions: instructions.trim() || undefined,
                ...(format === "custom" ? { style, output_type: outputType } : { format }),
              }
        ),
      }),
    onSuccess: (data: { video_id: string }) => router.push(`/dashboard/studio?video=${data.video_id}`),
  })

  const canSubmit = mode === "own" ? ownScript.trim().length >= 40 : prompt.trim().length >= 10

  const outputTypeGrid = (
    <div>
      <span style={label}>What do you want to make?</span>
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        {OUTPUT_TYPES.map(t => (
          <button key={t.value} onClick={() => setOutputType(t.value)} style={optionBtn(outputType === t.value)}>
            <span style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: L.ink }}>{t.label}</span>
              <span style={{ fontSize: 10.5, fontWeight: 700, color: t.value === "script" ? L.ready : L.ash, border: `1px solid ${alpha(t.value === "script" ? L.ready : L.ash, 30)}`, padding: "2px 6px", borderRadius: 4, whiteSpace: "nowrap" }}>{t.badge}</span>
            </span>
            <span style={{ display: "block", marginTop: 4, fontSize: 12, lineHeight: 1.45, color: L.dust }}>{t.desc}</span>
          </button>
        ))}
      </div>
    </div>
  )

  return (
    <div style={{ maxWidth: 1060, margin: "0 auto", fontFamily: grotesque, paddingBottom: 24 }}>
      <div style={{ textAlign: "center", padding: "8px 0 22px" }}>
        <h1 style={{ margin: "0 0 6px", fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>Create</h1>
        <p style={{ margin: 0, fontSize: 14, color: L.ash }}>
          Start from an idea, or <Link href="/dashboard/topics" style={{ color: L.make }}>pick a trending topic</Link>.
        </p>
      </div>

      {/* Mode toggle */}
      <div style={{ display: "flex", gap: 2, background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 10, padding: 4, width: "fit-content", margin: "0 auto 22px" }}>
        {([["idea", "AI writes it"], ["own", "I have my own script"]] as const).map(([m, text]) => (
          <button key={m} onClick={() => setMode(m)}
            style={{ display: "flex", alignItems: "center", gap: 7, padding: "9px 16px", borderRadius: 7, border: "none", cursor: "pointer", background: mode === m ? L.benchRaised : "transparent", color: mode === m ? L.ink : L.ash, fontFamily: grotesque, fontSize: 13.5, fontWeight: mode === m ? 600 : 400 }}>
            <MdOutlineEditNote size={17} /> {text}
          </button>
        ))}
      </div>

      <div style={{ ...card, padding: 26, display: "flex", flexDirection: "column", gap: 22 }}>
        {mode === "idea" ? (
          <div>
            <span style={label}>Pick a format — each one is a full recipe: script rules, footage, captions, pacing, music</span>
            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
              {(formats?.items ?? []).map(f => (
                <button key={f.key} onClick={() => f.available && setFormat(f.key)} disabled={!f.available}
                  title={f.available ? f.desc : `${f.desc} — coming soon`} style={optionBtn(format === f.key, !f.available)}>
                  <span style={{ display: "block", fontSize: 14, fontWeight: 600, color: L.ink }}>{f.label}</span>
                  <span style={{ display: "block", marginTop: 4, fontSize: 12, lineHeight: 1.45, color: L.dust }}>
                    {f.available ? f.desc : "Coming soon"}
                  </span>
                </button>
              ))}
              <button onClick={() => setFormat("custom")} style={optionBtn(format === "custom")}>
                <span style={{ display: "block", fontSize: 14, fontWeight: 600, color: L.ink }}>Custom</span>
                <span style={{ display: "block", marginTop: 4, fontSize: 12, lineHeight: 1.45, color: L.dust }}>Pick output type &amp; style yourself</span>
              </button>
            </div>
          </div>
        ) : outputTypeGrid}

        {mode === "idea" && format === "custom" && outputTypeGrid}

        {mode === "idea" ? (
          <>
            <div>
              <span style={label}>What&apos;s the video about?</span>
              <textarea value={prompt} onChange={e => setPrompt(e.target.value)} rows={3}
                placeholder="e.g. Apex Legends new season — everything that changed"
                style={{ ...field, resize: "none", lineHeight: 1.5 }} />
            </div>
            <div>
              <span style={label}>Script language</span>
              <select value={language} onChange={e => setLanguage(e.target.value)} style={{ ...field, width: 240 }}>
                {(voiceData?.languages ?? ["English"]).map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
            {format === "custom" && (
              <div>
                <span style={label}>Video style</span>
                <div className="grid gap-2 sm:grid-cols-2">
                  {STYLES.map(s => (
                    <button key={s.value} onClick={() => setStyle(s.value)} style={optionBtn(style === s.value)}>
                      <span style={{ display: "block", fontSize: 14, fontWeight: 600, color: L.ink }}>{s.label}</span>
                      <span style={{ display: "block", marginTop: 3, fontSize: 12, color: L.dust }}>{s.desc}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div>
            <span style={label}>Paste your script — your wording stays exactly as written</span>
            <textarea value={ownScript} onChange={e => setOwnScript(e.target.value)} rows={10}
              placeholder="Write or paste your full narration here. We only split it into segments and pick matching visuals — not a single word gets changed."
              style={{ ...field, resize: "none", lineHeight: 1.55 }} />
          </div>
        )}

        {/* Advanced */}
        <div style={{ borderTop: `1px solid ${L.ruleFaint}`, paddingTop: 16 }}>
          <button onClick={() => setShowAdvanced(!showAdvanced)}
            style={{ background: "transparent", border: "none", color: L.ash, fontFamily: grotesque, fontSize: 12.5, fontWeight: 600, cursor: "pointer", padding: 0 }}>
            Advanced options {showAdvanced ? "▴" : "▾"}
          </button>
          {showAdvanced && (
            <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 16 }}>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <span style={label}>AI model</span>
                  <select value={model} onChange={e => setModel(e.target.value)} style={field}>
                    {(models?.items ?? [{ key: "auto", label: "Auto (best available)" }]).map(m => (
                      <option key={m.key} value={m.key}>{m.label}</option>
                    ))}
                  </select>
                </div>
                {mode === "idea" && (
                  <div>
                    <span style={label}>Tone</span>
                    <select value={tone} onChange={e => setTone(e.target.value)} style={{ ...field, textTransform: "capitalize" }}>
                      {TONE_PRESETS.map(t => <option key={t} value={t}>{t}</option>)}
                      <option value="__custom__">Custom…</option>
                    </select>
                  </div>
                )}
              </div>
              {mode === "idea" && tone === "__custom__" && (
                <input value={customTone} onChange={e => setCustomTone(e.target.value)}
                  placeholder="Describe the tone, e.g. 'sarcastic but warm'" style={field} />
              )}
              {mode === "idea" && (
                <div>
                  <span style={label}>Custom instructions <span style={{ fontWeight: 400, color: L.dust }}>(optional · {600 - instructions.length} left)</span></span>
                  <textarea value={instructions} onChange={e => setInstructions(e.target.value.slice(0, 600))} rows={3}
                    placeholder="e.g. Always end with 'follow for part 2'. Never use the word 'insane'. Mention my channel GamerX once."
                    style={{ ...field, resize: "none", lineHeight: 1.5 }} />
                </div>
              )}
            </div>
          )}
        </div>

        {create.error && <p style={{ margin: 0, fontSize: 12.5, color: L.refused }}>{(create.error as Error).message}</p>}

        <button onClick={() => create.mutate()} disabled={!canSubmit || create.isPending} style={{ ...primaryBtn(!canSubmit || create.isPending), width: "100%", padding: "13px 18px" }}>
          <MdOutlineAutoAwesome size={18} />
          {create.isPending ? "Writing…" : mode === "own" ? "Structure my script" : "Generate the script"}
        </button>
      </div>
    </div>
  )
}

/* ==================== EDITOR ==================== */
function ScriptEditor({ videoId }: { videoId: string }) {
  const queryClient = useQueryClient()
  const router = useRouter()
  const [segments, setSegments] = useState<Segment[]>([])
  const [dirty, setDirty] = useState(false)
  const [regenIndex, setRegenIndex] = useState<number | null>(null)
  const [feedback, setFeedback] = useState("")
  const [swapIndex, setSwapIndex] = useState<number | null>(null)
  const [mediaOptions, setMediaOptions] = useState<MediaOption[]>([])
  const [mediaLoading, setMediaLoading] = useState(false)
  const [voiceId, setVoiceId] = useState("en-US-ChristopherNeural")
  const [previewLoading, setPreviewLoading] = useState(false)
  const [captionStyle, setCaptionStyle] = useState("classic")
  const [aspectRatio, setAspectRatio] = useState("9:16")

  const openSwap = async (index: number) => {
    if (swapIndex === index) { setSwapIndex(null); return }
    setSwapIndex(index)
    setMediaLoading(true)
    setMediaOptions([])
    try {
      const data = await fetchApi(`/scripts/${videoId}/segments/${index}/media-options`)
      setMediaOptions(data.items ?? [])
    } finally {
      setMediaLoading(false)
    }
  }
  const pinMedia = (index: number, option: MediaOption | null) => {
    setSegments(prev => prev.map((s, i) =>
      i === index ? { ...s, media_id: option?.id ?? null, media_thumb: option?.thumb ?? null } : s
    ))
    setDirty(true)
    setSwapIndex(null)
  }

  const { data: aspectRatios } = useQuery<{ items: { key: string; label: string; desc: string }[] }>({
    queryKey: ["aspect-ratios"], queryFn: () => fetchApi("/pipeline/aspect-ratios"), staleTime: Infinity,
  })
  const { data: editorFormats } = useQuery<{ items: Format[] }>({
    queryKey: ["formats"], queryFn: () => fetchApi("/scripts/formats"), staleTime: Infinity,
  })
  const { data: voiceData } = useQuery<{ voices: Voice[] }>({
    queryKey: ["voices"], queryFn: () => fetchApi("/scripts/voices"), staleTime: Infinity,
  })
  const { data: captionStyles } = useQuery<{ items: { key: string; label: string; desc: string }[] }>({
    queryKey: ["caption-styles"], queryFn: () => fetchApi("/pipeline/caption-styles"), staleTime: Infinity,
  })

  const playPreview = async () => {
    setPreviewLoading(true)
    try {
      const { preview_url } = await fetchApi(`/scripts/voices/${voiceId}/preview`)
      new Audio(`${API_BASE_URL.replace(/\/api\/?$/, "")}${preview_url}`).play()
    } finally {
      setPreviewLoading(false)
    }
  }

  const { data, isLoading, error } = useQuery<Script>({
    queryKey: ["script", videoId],
    queryFn: () => fetchApi(`/scripts/${videoId}`),
  })

  // Sync fetched script into editable state during render (not in an effect).
  const [syncedData, setSyncedData] = useState<Script | null>(null)
  if (data && data !== syncedData) {
    setSyncedData(data)
    setSegments(data.segments)
    setDirty(false)
    if (data.defaults?.voice_id) setVoiceId(data.defaults.voice_id)
    if (data.defaults?.caption_style) setCaptionStyle(data.defaults.caption_style)
  }

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
        body: JSON.stringify({
          video_id: videoId,
          visual_engine: outputType === "image" ? "stock_image" : "pexels",
          voice_id: outputType === "narrated" ? voiceId : undefined,
          caption_style: outputType !== "image" && outputType !== "fake_text" ? captionStyle : undefined,
          aspect_ratio: aspectRatio,
        }),
      }),
    onSuccess: (d: { job_id: string }) => {
      queryClient.invalidateQueries({ queryKey: ["credits"] })
      router.push(`/dashboard/preview/${videoId}?job=${d.job_id}`)
    },
  })

  if (isLoading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {Array.from({ length: 4 }).map((_, i) => <div key={i} style={{ ...card, height: 120, opacity: 0.5 }} />)}
      </div>
    )
  }
  if (error) {
    return (
      <div style={{ ...card, borderColor: alpha(L.refused, 35), padding: 22, fontSize: 14, color: L.refused }}>
        Failed to load script: {(error as Error).message}
      </div>
    )
  }

  const totalDuration = segments.reduce((sum, s) => sum + (s.duration_estimate || 0), 0)
  const outputType = data?.output_type ?? "narrated"
  const editorFormat = editorFormats?.items.find(f => f.key === data?.format)
  const typeName = editorFormat ? editorFormat.label
    : outputType === "script" ? "Script only" : outputType === "visual" ? "Visual short"
    : outputType === "image" ? "Image post" : "Narrated short"

  const updateSegment = (index: number, patch: Partial<Segment>) => {
    setSegments(prev => prev.map((s, i) => (i === index ? { ...s, ...patch } : s)))
    setDirty(true)
  }
  const copyScript = () => navigator.clipboard.writeText(segments.map(s => s.text).join("\n\n"))

  return (
    <div style={{ fontFamily: grotesque }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 16, flexWrap: "wrap", marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: "0 0 4px", display: "flex", alignItems: "center", gap: 12, fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>
            Create
            <span style={{ fontSize: 12, fontWeight: 600, color: L.ash, border: `1px solid ${L.rule}`, padding: "4px 10px", borderRadius: 6 }}>{typeName}</span>
          </h1>
          <p style={{ margin: 0, display: "flex", alignItems: "center", gap: 6, fontSize: 13.5, color: L.ash }}>
            <MdOutlineTimer size={16} /> ~{Math.round(totalDuration)}s {outputType === "visual" ? "on screen" : "spoken"} · {segments.length} segments
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <button onClick={() => save.mutate()} disabled={!dirty || save.isPending}
            style={{ ...ghostBtn, opacity: !dirty || save.isPending ? 0.55 : 1, cursor: !dirty ? "default" : "pointer" }}>
            <MdOutlineSave size={17} /> {save.isPending ? "Saving…" : dirty ? "Save changes" : "Saved"}
          </button>
          {outputType === "script" ? (
            <button onClick={copyScript} style={{ ...primaryBtn(), background: L.ready }}>
              <MdOutlineContentCopy size={17} /> Copy script
            </button>
          ) : (
            <button onClick={() => render.mutate()} disabled={render.isPending || dirty}
              title={dirty ? "Save your changes first" : "Costs 1 credit"} style={primaryBtn(render.isPending || dirty)}>
              <MdOutlineSmartDisplay size={18} />
              {render.isPending ? "Starting…" : outputType === "image" ? "Generate images · 1 credit" : "Generate video · 1 credit"}
            </button>
          )}
        </div>
      </div>

      {render.error && (
        <div style={{ ...card, borderColor: alpha(L.refused, 35), padding: "12px 16px", fontSize: 13.5, color: L.refused, marginBottom: 16 }}>
          {(render.error as Error).message}
        </div>
      )}

      <div className="grid items-start gap-5 lg:grid-cols-[1fr_320px]">
        {/* Segments */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {outputType === "visual" && (
            <div style={{ border: `1px solid ${alpha(L.live, 30)}`, background: alpha(L.live, 7), borderRadius: 8, padding: "10px 14px", fontSize: 12.5, lineHeight: 1.5, color: L.ash }}>
              Visual short: these lines appear as on-screen text with music — no narration. Tip: attach a trending sound in the YouTube/Instagram editor when you post.
            </div>
          )}
          {outputType === "fake_text" && (
            <div style={{ border: `1px solid ${alpha(L.live, 30)}`, background: alpha(L.live, 7), borderRadius: 8, padding: "10px 14px", fontSize: 12.5, lineHeight: 1.5, color: L.ash }}>
              Fake text convo: each line is one chat message (keep the A: / B: prefixes — A is grey, B is blue). Messages appear as bubbles with typing beats over background footage.
            </div>
          )}

          {segments.map((segment, i) => (
            <div key={i} style={{ ...card, overflow: "hidden" }}>
              <div style={{ padding: "10px 18px", borderBottom: `1px solid ${L.ruleFaint}`, display: "flex", alignItems: "center", justifyContent: "space-between", background: L.benchRaised }}>
                <span style={{ fontSize: 12, fontWeight: 700, color: i === 0 || i === segments.length - 1 ? L.make : L.ash }}>
                  {i === 0 ? "Hook" : i === segments.length - 1 ? "Payoff" : `Segment ${i + 1}`}
                  <span style={{ marginLeft: 10, fontFamily: mono, fontSize: 11, fontWeight: 400, color: L.dust }}>~{segment.duration_estimate}s</span>
                </span>
                <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  {outputType !== "script" && (
                    <button onClick={() => openSwap(i)}
                      style={{ display: "flex", alignItems: "center", gap: 6, background: "transparent", border: "none", color: segment.media_id ? L.live : L.ash, fontFamily: grotesque, fontSize: 12.5, fontWeight: 500, padding: "6px 10px", borderRadius: 6, cursor: "pointer" }}>
                      <MdOutlineImage size={15} /> {segment.media_id ? "Visual pinned" : "Swap visuals"}
                    </button>
                  )}
                  <button onClick={() => setRegenIndex(regenIndex === i ? null : i)}
                    style={{ display: "flex", alignItems: "center", gap: 6, background: "transparent", border: "none", color: L.make, fontFamily: grotesque, fontSize: 12.5, fontWeight: 500, padding: "6px 10px", borderRadius: 6, cursor: "pointer" }}>
                    <MdOutlineAutoAwesome size={15} /> Regenerate
                  </button>
                </div>
              </div>

              <div style={{ padding: 18, display: "flex", flexDirection: "column", gap: 14 }}>
                <div>
                  <span style={{ ...label, marginBottom: 6, fontSize: 11.5 }}>{outputType === "visual" ? "On-screen text" : outputType === "fake_text" ? "Message" : "Narration"}</span>
                  <textarea value={segment.text} onChange={e => updateSegment(i, { text: e.target.value })} rows={2}
                    style={{ ...field, fontSize: 15, lineHeight: 1.5, resize: "none" }} />
                </div>
                <div>
                  <span style={{ ...label, marginBottom: 6, fontSize: 11.5 }}>Visual direction</span>
                  <input value={segment.visual_prompt} onChange={e => updateSegment(i, { visual_prompt: e.target.value })}
                    style={{ ...field, fontSize: 13, color: L.ash }} />
                </div>

                {regenIndex === i && (
                  <div style={{ display: "flex", gap: 8 }}>
                    <input value={feedback} onChange={e => setFeedback(e.target.value)}
                      placeholder="What should change? e.g. 'shorter, more dramatic'"
                      style={{ ...field, flex: 1, borderColor: alpha(L.make, 40) }} />
                    <button onClick={() => regen.mutate(i)} disabled={regen.isPending} style={primaryBtn(regen.isPending)}>
                      {regen.isPending ? "Rewriting…" : "Go"}
                    </button>
                  </div>
                )}

                {segment.media_thumb && swapIndex !== i && (
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={segment.media_thumb} alt="Pinned media" style={{ width: 40, height: 56, objectFit: "cover", borderRadius: 6, border: `1px solid ${alpha(L.live, 50)}` }} />
                    <span style={{ fontSize: 12.5, color: L.live }}>Visuals pinned for this scene</span>
                    <button onClick={() => pinMedia(i, null)}
                      style={{ background: "transparent", border: "none", color: L.dust, fontFamily: grotesque, fontSize: 12, textDecoration: "underline", cursor: "pointer", padding: 0 }}>
                      unpin
                    </button>
                  </div>
                )}

                {swapIndex === i && (
                  <div>
                    <p style={{ margin: "0 0 8px", fontSize: 12.5, color: L.ash }}>
                      {mediaLoading ? "Searching stock media…" : "Pick the visuals for this scene:"}
                    </p>
                    {mediaLoading ? (
                      <div className="grid grid-cols-4 gap-2 sm:grid-cols-8">
                        {Array.from({ length: 8 }).map((_, j) => (
                          <div key={j} style={{ aspectRatio: "9/16", borderRadius: 6, background: L.benchRaised, opacity: 0.6 }} />
                        ))}
                      </div>
                    ) : (
                      <div className="grid grid-cols-4 gap-2 sm:grid-cols-8">
                        {mediaOptions.map(opt => (
                          <button key={opt.id} onClick={() => pinMedia(i, opt)}
                            title={opt.photographer ? `by ${opt.photographer} (Pexels)` : "Pexels"}
                            style={{ position: "relative", aspectRatio: "9/16", borderRadius: 6, overflow: "hidden", border: `2px solid ${segment.media_id === opt.id ? L.live : "transparent"}`, cursor: "pointer", padding: 0, background: L.benchRaised }}>
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img src={opt.thumb} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                            {opt.duration && (
                              <span style={{ position: "absolute", bottom: 3, right: 3, padding: "1px 4px", borderRadius: 3, background: "rgba(0,0,0,0.72)", color: "#fff", fontFamily: mono, fontSize: 9 }}>
                                {opt.duration}s
                              </span>
                            )}
                          </button>
                        ))}
                        {mediaOptions.length === 0 && (
                          <p style={{ gridColumn: "1 / -1", margin: 0, fontSize: 12.5, color: L.dust }}>No portrait media found — try editing the visual direction.</p>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Settings rail */}
        {outputType !== "script" ? (
          <aside style={{ ...card, padding: 20, position: "sticky", top: 16, display: "flex", flexDirection: "column", gap: 18 }}>
            <p style={{ margin: 0, fontSize: 14.5, fontWeight: 650 }}>Render settings</p>
            {outputType === "narrated" && (
              <div>
                <span style={label}>Voice</span>
                <div style={{ display: "flex", gap: 8 }}>
                  <select value={voiceId} onChange={e => setVoiceId(e.target.value)} style={{ ...field, flex: 1, minWidth: 0 }}>
                    {(voiceData?.voices ?? []).map(v => (
                      <option key={v.id} value={v.id}>{v.label} · {v.language} · {v.vibe}</option>
                    ))}
                  </select>
                  <button onClick={playPreview} disabled={previewLoading} title="Hear this voice"
                    style={{ ...ghostBtn, padding: "0 12px" }}>
                    <MdOutlinePlayArrow size={18} />
                  </button>
                </div>
              </div>
            )}
            {outputType !== "image" && outputType !== "fake_text" && (
              <div>
                <span style={label}>Captions</span>
                <select value={captionStyle} onChange={e => setCaptionStyle(e.target.value)} style={field}>
                  {(captionStyles?.items ?? [{ key: "classic", label: "Classic Bold", desc: "" }]).map(s => (
                    <option key={s.key} value={s.key}>{s.label}{s.desc ? ` — ${s.desc}` : ""}</option>
                  ))}
                </select>
              </div>
            )}
            <div>
              <span style={label}>Aspect ratio</span>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {(aspectRatios?.items ?? [{ key: "9:16", label: "Vertical", desc: "Shorts · Reels · TikTok" }]).map(a => (
                  <button key={a.key} onClick={() => setAspectRatio(a.key)} title={a.desc}
                    style={{ ...optionBtn(aspectRatio === a.key), padding: "9px 12px", display: "flex", alignItems: "baseline", gap: 8 }}>
                    <span style={{ fontFamily: mono, fontSize: 13, color: L.ink }}>{a.key}</span>
                    <span style={{ fontSize: 12, color: L.dust }}>{a.label}</span>
                  </button>
                ))}
              </div>
            </div>
            <div style={{ borderTop: `1px solid ${L.ruleFaint}`, paddingTop: 14 }}>
              <button onClick={() => render.mutate()} disabled={render.isPending || dirty}
                title={dirty ? "Save your changes first" : "Costs 1 credit"} style={{ ...primaryBtn(render.isPending || dirty), width: "100%" }}>
                <MdOutlineSmartDisplay size={18} />
                {render.isPending ? "Starting…" : outputType === "image" ? "Generate images" : "Generate video"}
              </button>
              <p style={{ margin: "8px 0 0", fontSize: 11.5, color: L.dust, textAlign: "center" }}>
                1 credit · refunded automatically if the render fails
              </p>
            </div>
          </aside>
        ) : (
          <aside style={{ ...card, padding: 20, position: "sticky", top: 16 }}>
            <p style={{ margin: "0 0 8px", fontSize: 14.5, fontWeight: 650 }}>Script-only mode</p>
            <p style={{ margin: "0 0 14px", fontSize: 13, lineHeight: 1.6, color: L.ash }}>
              This creation is free — edit the lines, then copy the script and film it yourself. Five free scripts a day.
            </p>
            <button onClick={copyScript} style={{ ...primaryBtn(), background: L.ready, width: "100%" }}>
              <MdOutlineContentCopy size={17} /> Copy script
            </button>
          </aside>
        )}
      </div>
    </div>
  )
}
