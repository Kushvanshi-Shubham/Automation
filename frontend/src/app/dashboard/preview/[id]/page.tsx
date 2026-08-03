"use client"

/**
 * Preview & publish — watch the finished short, edit its metadata, send it
 * to your channel. While rendering, shows the same plainly-named five steps
 * as Production, driven by live telemetry. Themed, Material icons.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import Link from "next/link"
import { useParams, useSearchParams } from "next/navigation"
import { Suspense, useEffect, useState } from "react"
import {
  MdOutlineClose, MdOutlineEdit, MdOutlineErrorOutline, MdOutlineLiveTv,
  MdOutlinePhotoCamera, MdOutlineRateReview, MdOutlineSchedule,
} from "react-icons/md"
import { API_BASE_URL, fetchApi } from "@/lib/api-client"
import { usePipeline } from "@/hooks/use-pipeline"
import { L, mono, grotesque, alpha } from "@/lib/line/tokens"

const MEDIA_ORIGIN = API_BASE_URL.replace(/\/api\/?$/, "")

const STEPS = [
  { name: "Voice-over", from: 10 },
  { name: "Finding footage", from: 35 },
  { name: "Editing & captions", from: 65 },
  { name: "Adding music", from: 90 },
  { name: "Done", from: 100 },
]

interface VideoData {
  id: string; status: string; output_type: string; title: string | null
  description: string | null; tags: string[] | null; video_url: string | null
  thumbnail_url: string | null; youtube_video_id: string | null
  images: string[] | null; aspect_ratio: string | null; format: string | null
}
interface Channel { id: string; channel_name: string | null }
interface PublishRecord { id: string; platform: string; status: string; external_id: string | null; error_message: string | null }

const card: React.CSSProperties = { background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 10 }
const label: React.CSSProperties = { display: "block", fontSize: 12, fontWeight: 600, color: L.ash, marginBottom: 6 }
const field: React.CSSProperties = {
  width: "100%", boxSizing: "border-box", background: L.floor, border: `1px solid ${L.rule}`,
  borderRadius: 8, color: L.ink, fontFamily: grotesque, fontSize: 14, padding: "10px 12px", outline: "none",
}
const primaryBtn = (disabled = false): React.CSSProperties => ({
  display: "flex", alignItems: "center", justifyContent: "center", gap: 8, width: "100%",
  background: L.make, border: "none", color: "#fff", fontFamily: grotesque,
  fontSize: 14, fontWeight: 600, padding: "11px 16px", borderRadius: 8,
  cursor: disabled ? "default" : "pointer", opacity: disabled ? 0.55 : 1,
})
const banner = (color: string): React.CSSProperties => ({
  border: `1px solid ${alpha(color, 30)}`, background: alpha(color, 7), borderRadius: 8,
  padding: "12px 15px", fontSize: 13.5, color: L.ink, display: "flex", alignItems: "center", gap: 8,
})

export default function PreviewPage() {
  return (
    <Suspense fallback={<div style={{ ...card, height: 380, maxWidth: 420, opacity: 0.5 }} />}>
      <PreviewContent />
    </Suspense>
  )
}

function PreviewContent() {
  const { id } = useParams<{ id: string }>()
  const searchParams = useSearchParams()
  const jobId = searchParams.get("job")
  const queryClient = useQueryClient()

  const { data: video, isLoading, error } = useQuery<VideoData>({
    queryKey: ["video", id],
    queryFn: () => fetchApi(`/videos/${id}`),
    refetchInterval: q =>
      ["publishing", "rendering"].includes(q.state.data?.status ?? "") ? 4000 : false,
  })

  const isRendering = video?.status === "rendering" || video?.status === "script_ready"
  const pipeline = usePipeline(isRendering && jobId ? jobId : null)

  useEffect(() => {
    if (pipeline.status === "completed" || pipeline.status === "failed") {
      queryClient.invalidateQueries({ queryKey: ["video", id] })
    }
  }, [pipeline.status, id, queryClient])

  if (isLoading) return <div style={{ ...card, height: 380, maxWidth: 420, opacity: 0.5 }} />
  if (error || !video) {
    return (
      <div style={{ ...card, borderColor: alpha(L.refused, 35), padding: 20, maxWidth: 560, fontSize: 14, color: L.refused, fontFamily: grotesque }}>
        Failed to load video{error ? `: ${(error as Error).message}` : ""}
      </div>
    )
  }

  const aspect = video.aspect_ratio ?? "9:16"
  const aspectRatioCss = aspect === "16:9" ? "16/9" : aspect === "1:1" ? "1/1" : "9/16"
  const playerMax = aspect === "16:9" ? 620 : 380
  const pct = Math.max(0, Math.min(100, pipeline.progress))
  const stepIdx = pct < 10 ? 0 : STEPS.findLastIndex(s => pct >= s.from)
  const stepText = pct < 10 ? "Waiting in the queue" : STEPS[Math.min(stepIdx, STEPS.length - 2)].name

  const statusChip = video.status === "ready" ? { text: "Ready to publish", color: L.ready }
    : video.status === "published" ? { text: "Live on your channel", color: L.live }
    : video.status === "scheduled" ? { text: "Scheduled", color: L.working }
    : video.status === "publishing" ? { text: "Uploading…", color: L.working }
    : ["failed", "upload_failed"].includes(video.status) ? { text: "Needs attention", color: L.refused }
    : { text: "Rendering…", color: L.working }

  return (
    <div className="flex flex-col gap-8 lg:flex-row" style={{ fontFamily: grotesque, maxWidth: 1160 }}>
      {/* Player column */}
      <div style={{ width: "100%", maxWidth: playerMax, flexShrink: 0 }} className="mx-auto lg:mx-0">
        {video.output_type === "image" && video.status === "ready" && (video.images ?? []).length > 0 ? (
          <div className="grid grid-cols-2 gap-3">
            {(video.images ?? []).map((img, i) => (
              <a key={img} href={`${MEDIA_ORIGIN}${img}`} target="_blank" rel="noopener noreferrer"
                style={{ display: "block", borderRadius: 10, overflow: "hidden", border: `1px solid ${L.rule}` }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={`${MEDIA_ORIGIN}${img}`} alt={`Slide ${i + 1}`} style={{ width: "100%", aspectRatio: "4/5", objectFit: "cover", display: "block" }} />
              </a>
            ))}
          </div>
        ) : (
          <div style={{ aspectRatio: aspectRatioCss, borderRadius: 14, overflow: "hidden", background: L.bench, border: `1px solid ${L.rule}`, position: "relative" }}>
            {video.status !== "rendering" && video.status !== "script_ready" && video.video_url ? (
              <video src={`${MEDIA_ORIGIN}${video.video_url}`} controls playsInline
                style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            ) : video.status === "failed" ? (
              <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center", padding: 24 }}>
                <MdOutlineErrorOutline size={38} color={L.refused} />
                <p style={{ margin: "10px 0 4px", fontSize: 15, fontWeight: 600, color: L.refused }}>The render failed</p>
                <p style={{ margin: 0, fontSize: 12.5, color: L.ash }}>Your credit came back automatically.</p>
              </div>
            ) : (
              <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center", padding: 24 }}>
                <p style={{ margin: "0 0 4px", fontSize: 15, fontWeight: 600 }}>
                  Step {Math.min(stepIdx + 1, 5)} of 5 — {stepText}
                </p>
                <p style={{ margin: "0 0 16px", fontFamily: mono, fontSize: 12, color: L.ash }}>{Math.round(pct)}%</p>
                <div style={{ width: "100%", maxWidth: 260, display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 4 }}>
                  {STEPS.map((s, i) => {
                    const start = i === 0 ? 10 : STEPS[i - 1].from
                    const done = pct >= s.from
                    const current = !done && pct >= (i === 0 ? 0 : start)
                    const fill = done ? 100 : current ? Math.max(8, ((pct - start) / (s.from - start)) * 100) : 0
                    return (
                      <div key={s.name} style={{ height: 5, background: L.benchRaised, borderRadius: 3, overflow: "hidden" }}>
                        <div style={{ width: `${Math.min(100, fill)}%`, height: "100%", background: done ? L.ready : L.working, transition: "width 1.2s linear" }} />
                      </div>
                    )
                  })}
                </div>
                <p style={{ margin: "14px 0 0", fontSize: 12, color: L.dust, maxWidth: "32ch" }}>
                  You can leave this page — it will be waiting in Production when it&apos;s done.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Meta column */}
      <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: 18 }}>
        <div>
          <h1 style={{ margin: "0 0 8px", fontSize: 23, fontWeight: 700, lineHeight: 1.3, letterSpacing: "-0.015em" }}>{video.title ?? "Untitled short"}</h1>
          <span style={{ display: "inline-block", fontSize: 12, fontWeight: 600, color: statusChip.color, border: `1px solid ${alpha(statusChip.color, 35)}`, padding: "4px 10px", borderRadius: 6 }}>
            {statusChip.text}
          </span>
        </div>

        {video.description && (
          <div style={{ ...card, padding: "14px 16px" }}>
            <p style={{ ...label, marginBottom: 8 }}>Description</p>
            <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.55, color: L.ash, whiteSpace: "pre-line" }}>{video.description}</p>
          </div>
        )}

        <Link href={`/dashboard/studio?video=${video.id}`}
          style={{ display: "inline-flex", alignItems: "center", gap: 7, alignSelf: "flex-start", background: "transparent", border: `1px solid ${L.rule}`, color: L.ink, textDecoration: "none", fontSize: 13.5, padding: "9px 14px", borderRadius: 8 }}>
          <MdOutlineEdit size={16} /> Edit the script
        </Link>

        {video.output_type === "image" && video.status === "ready" && (
          <div style={{ ...card, padding: "14px 16px", fontSize: 13.5, lineHeight: 1.55, color: L.ash }}>
            Image post ready — click any slide to open full size and download. Direct Instagram carousel
            publishing arrives with the Meta app setup.
          </div>
        )}
        {video.output_type !== "image" && video.status === "ready" && <PublishPanel video={video} />}
        {video.output_type !== "image" && ["ready", "published", "scheduled"].includes(video.status) && <InstagramPanel video={video} />}

        {video.status === "publishing" && (
          <div style={banner(L.working)}><MdOutlineLiveTv size={17} color={L.working} /> Uploading to YouTube…</div>
        )}
        {video.status === "published" && (
          <div style={{ ...banner(L.live), justifyContent: "space-between" }}>
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}><MdOutlineLiveTv size={17} color={L.live} /> Published to YouTube</span>
            {video.youtube_video_id && (
              <a href={`https://www.youtube.com/watch?v=${video.youtube_video_id}`} target="_blank" rel="noopener noreferrer"
                style={{ color: L.live, fontWeight: 600, fontSize: 13, textDecoration: "none", border: `1px solid ${alpha(L.live, 40)}`, padding: "6px 12px", borderRadius: 6 }}>
                Watch on YouTube
              </a>
            )}
          </div>
        )}
        {video.status === "scheduled" && (
          <div style={banner(L.working)}><MdOutlineSchedule size={17} color={L.working} /> Scheduled — YouTube will make it public automatically.</div>
        )}
        {video.status === "upload_failed" && (
          <div style={banner(L.refused)}>
            <MdOutlineErrorOutline size={17} color={L.refused} /> Upload failed — check your channel connection in Settings, then publish again below.
          </div>
        )}
        {video.status === "upload_failed" && <PublishPanel video={video} />}

        {["ready", "published", "scheduled"].includes(video.status) && <FeedbackCard video={video} />}
      </div>
    </div>
  )
}

/* ==================== FEEDBACK MEMORY ==================== */
interface FeedbackNote { id: string; format: string | null; note: string }

function FeedbackCard({ video }: { video: VideoData }) {
  const queryClient = useQueryClient()
  const [note, setNote] = useState("")
  const [scope, setScope] = useState<"format" | "all">(video.format ? "format" : "all")

  const { data } = useQuery<{ items: FeedbackNote[] }>({
    queryKey: ["feedback-notes", video.format],
    queryFn: () => fetchApi(`/feedback-notes${video.format ? `?format=${video.format}` : ""}`),
  })

  const save = useMutation({
    mutationFn: () => fetchApi("/feedback-notes", {
      method: "POST",
      body: JSON.stringify({
        note: note.trim(),
        format: scope === "format" ? video.format : null,
      }),
    }),
    onSuccess: () => {
      setNote("")
      queryClient.invalidateQueries({ queryKey: ["feedback-notes"] })
    },
  })
  const remove = useMutation({
    mutationFn: (id: string) => fetchApi(`/feedback-notes/${id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["feedback-notes"] }),
  })

  const notes = data?.items ?? []

  return (
    <div style={{ ...card, padding: 18, display: "flex", flexDirection: "column", gap: 12 }}>
      <h3 style={{ margin: 0, display: "flex", alignItems: "center", gap: 8, fontSize: 14.5, fontWeight: 650 }}>
        <MdOutlineRateReview size={17} /> For next time
      </h3>
      <p style={{ margin: 0, fontSize: 13, lineHeight: 1.55, color: L.ash }}>
        Tell Kliptos what should be different in future videos — it remembers and applies
        every note automatically.
      </p>

      <textarea value={note} onChange={e => setNote(e.target.value.slice(0, 300))} rows={2}
        placeholder="e.g. Make the captions bigger. Never hold a static shot longer than a second."
        style={{ ...field, resize: "none", fontSize: 13.5 }} />

      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        {video.format && (
          <div style={{ display: "flex", gap: 6 }}>
            {([["format", "This format only"], ["all", "Every video"]] as const).map(([k, text]) => (
              <button key={k} onClick={() => setScope(k)}
                style={{
                  background: scope === k ? L.benchRaised : "transparent",
                  border: `1px solid ${scope === k ? L.ink : L.rule}`,
                  color: scope === k ? L.ink : L.ash, fontFamily: grotesque,
                  fontSize: 12, padding: "5px 10px", borderRadius: 6, cursor: "pointer",
                }}>
                {text}
              </button>
            ))}
          </div>
        )}
        <button onClick={() => save.mutate()} disabled={note.trim().length < 3 || save.isPending}
          style={{
            marginLeft: "auto", background: "transparent", border: `1px solid ${alpha(L.make, 45)}`,
            color: L.make, fontFamily: grotesque, fontSize: 13, fontWeight: 600,
            padding: "7px 14px", borderRadius: 7,
            cursor: note.trim().length < 3 || save.isPending ? "default" : "pointer",
            opacity: note.trim().length < 3 ? 0.55 : 1,
          }}>
          {save.isPending ? "Saving…" : "Remember this"}
        </button>
      </div>
      {save.error && <p style={{ margin: 0, fontSize: 12.5, color: L.refused }}>{(save.error as Error).message}</p>}

      {notes.length > 0 && (
        <div style={{ borderTop: `1px solid ${L.ruleFaint}`, paddingTop: 10, display: "flex", flexDirection: "column", gap: 6 }}>
          {notes.map(n => (
            <div key={n.id} style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 12.5, color: L.ash }}>
              <span style={{ flex: 1, lineHeight: 1.5 }}>
                {n.note}
                {n.format === null && video.format && (
                  <span style={{ color: L.dust }}> · every video</span>
                )}
              </span>
              <button onClick={() => remove.mutate(n.id)} title="Forget this note"
                style={{ background: "none", border: "none", color: L.dust, cursor: "pointer", padding: 2 }}>
                <MdOutlineClose size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/* ==================== YOUTUBE ==================== */
function PublishPanel({ video }: { video: VideoData }) {
  const queryClient = useQueryClient()
  const videoId = video.id

  const { data: channels } = useQuery<Channel[]>({ queryKey: ["channels"], queryFn: () => fetchApi("/channels") })
  const { data: categories } = useQuery<{ items: { id: string; label: string }[] }>({
    queryKey: ["yt-categories"], queryFn: () => fetchApi("/uploads/categories"), staleTime: Infinity,
  })

  const [channelId, setChannelId] = useState("")
  const [privacy, setPrivacy] = useState("unlisted")
  const [scheduleAt, setScheduleAt] = useState("")
  const [categoryId, setCategoryId] = useState("24")
  const [title, setTitle] = useState(video.title ?? "")
  const [description, setDescription] = useState(video.description ?? "")
  const [tagsText, setTagsText] = useState((video.tags ?? []).join(", "))

  const publish = useMutation({
    mutationFn: async () => {
      const tags = tagsText.split(",").map(t => t.trim().replace(/^#/, "")).filter(Boolean).slice(0, 30)
      await fetchApi(`/videos/${videoId}/metadata`, {
        method: "PUT",
        body: JSON.stringify({ title: title.trim() || null, description, tags }),
      })
      if (scheduleAt) {
        return fetchApi(`/uploads/${videoId}/schedule`, {
          method: "POST",
          body: JSON.stringify({ channel_id: channelId, publish_at: new Date(scheduleAt).toISOString(), category_id: categoryId }),
        })
      }
      return fetchApi(`/uploads/${videoId}/publish`, {
        method: "POST",
        body: JSON.stringify({ channel_id: channelId, privacy, category_id: categoryId }),
      })
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["video", videoId] }),
  })

  if (!channels || channels.length === 0) {
    return (
      <div style={{ ...card, padding: "14px 16px", fontSize: 13.5, color: L.ash }}>
        <Link href="/dashboard/settings" style={{ color: L.make, fontWeight: 600 }}>Connect a YouTube channel</Link>{" "}
        to publish this short.
      </div>
    )
  }

  return (
    <div style={{ ...card, padding: 18, display: "flex", flexDirection: "column", gap: 14 }}>
      <h3 style={{ margin: 0, display: "flex", alignItems: "center", gap: 8, fontSize: 14.5, fontWeight: 650 }}>
        <MdOutlineLiveTv size={17} color={L.refused} /> Publish to YouTube
      </h3>

      <div>
        <span style={label}>Title <span style={{ fontWeight: 400, color: L.dust }}>({95 - title.length} left)</span></span>
        <input value={title} onChange={e => setTitle(e.target.value.slice(0, 95))} style={field} />
      </div>
      <div>
        <span style={label}>Description</span>
        <textarea value={description} onChange={e => setDescription(e.target.value.slice(0, 4900))} rows={4}
          style={{ ...field, resize: "none", fontSize: 13.5, lineHeight: 1.5 }} />
      </div>
      <div>
        <span style={label}>Tags <span style={{ fontWeight: 400, color: L.dust }}>(comma-separated, max 30)</span></span>
        <input value={tagsText} onChange={e => setTagsText(e.target.value)} placeholder="apex legends, gaming, shorts" style={field} />
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <select value={channelId} onChange={e => setChannelId(e.target.value)} style={field}>
          <option value="">Select channel…</option>
          {channels.map(c => <option key={c.id} value={c.id}>{c.channel_name ?? "Unnamed channel"}</option>)}
        </select>
        <select value={categoryId} onChange={e => setCategoryId(e.target.value)} style={field}>
          {(categories?.items ?? [{ id: "24", label: "Entertainment" }]).map(c => (
            <option key={c.id} value={c.id}>{c.label}</option>
          ))}
        </select>
        <select value={privacy} onChange={e => setPrivacy(e.target.value)} disabled={!!scheduleAt}
          style={{ ...field, opacity: scheduleAt ? 0.55 : 1 }}>
          <option value="unlisted">Unlisted</option>
          <option value="public">Public</option>
          <option value="private">Private</option>
        </select>
      </div>

      <div>
        <span style={label}>Schedule (optional — goes public automatically)</span>
        <input type="datetime-local" value={scheduleAt} onChange={e => setScheduleAt(e.target.value)} style={field} />
      </div>

      {publish.error && <p style={{ margin: 0, fontSize: 12.5, color: L.refused }}>{(publish.error as Error).message}</p>}

      <button onClick={() => publish.mutate()} disabled={!channelId || !title.trim() || publish.isPending}
        style={primaryBtn(!channelId || !title.trim() || publish.isPending)}>
        <MdOutlineLiveTv size={17} />
        {publish.isPending ? "Sending…" : scheduleAt ? "Save & schedule" : "Save & publish now"}
      </button>
    </div>
  )
}

/* ==================== INSTAGRAM ==================== */
function InstagramPanel({ video }: { video: VideoData }) {
  const queryClient = useQueryClient()
  const [caption, setCaption] = useState("")

  const { data: igStatus } = useQuery<{ enabled: boolean }>({
    queryKey: ["ig-status"], queryFn: () => fetchApi("/instagram/status"), staleTime: Infinity,
  })
  const { data: accounts } = useQuery<{ id: string; username: string | null }[]>({
    queryKey: ["ig-accounts"], queryFn: () => fetchApi("/instagram"), enabled: igStatus?.enabled === true,
  })
  const { data: publishes } = useQuery<{ items: PublishRecord[] }>({
    queryKey: ["publishes", video.id],
    queryFn: () => fetchApi(`/uploads/publishes/${video.id}`),
    refetchInterval: q =>
      (q.state.data?.items ?? []).some(p => p.status === "publishing") ? 5000 : false,
  })

  const publish = useMutation({
    mutationFn: () => fetchApi(`/uploads/${video.id}/publish-instagram`, { method: "POST", body: JSON.stringify({ caption }) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["publishes", video.id] }),
  })

  if (!igStatus?.enabled) return null
  const igPublish = (publishes?.items ?? []).find(p => p.platform === "instagram")

  return (
    <div style={{ ...card, padding: 18, display: "flex", flexDirection: "column", gap: 12 }}>
      <h3 style={{ margin: 0, display: "flex", alignItems: "center", gap: 8, fontSize: 14.5, fontWeight: 650 }}>
        <MdOutlinePhotoCamera size={17} /> Publish to Instagram (Reel)
      </h3>

      {igPublish?.status === "published" && (
        <p style={{ margin: 0, fontSize: 13.5, color: L.ready }}>Published to Instagram (media {igPublish.external_id})</p>
      )}
      {igPublish?.status === "publishing" && (
        <p style={{ margin: 0, fontSize: 13.5, color: L.working }}>Uploading Reel — Instagram is processing the video…</p>
      )}
      {igPublish?.status === "failed" && (
        <p style={{ margin: 0, fontSize: 12.5, color: L.refused }}>Failed: {igPublish.error_message}</p>
      )}

      {(!igPublish || igPublish.status === "failed") && (
        (accounts ?? []).length === 0 ? (
          <p style={{ margin: 0, fontSize: 13.5, color: L.ash }}>
            <Link href="/dashboard/settings" style={{ color: L.make, fontWeight: 600 }}>Connect an Instagram account</Link>{" "}
            to publish Reels.
          </p>
        ) : (
          <>
            <textarea value={caption} onChange={e => setCaption(e.target.value.slice(0, 2200))} rows={2}
              placeholder="Caption (leave empty to use the video title + description)"
              style={{ ...field, resize: "none", fontSize: 13.5 }} />
            <button onClick={() => publish.mutate()} disabled={publish.isPending} style={primaryBtn(publish.isPending)}>
              <MdOutlinePhotoCamera size={16} />
              {publish.isPending ? "Sending…" : `Publish Reel to @${accounts![0].username}`}
            </button>
            {publish.error && <p style={{ margin: 0, fontSize: 12.5, color: L.refused }}>{(publish.error as Error).message}</p>}
          </>
        )
      )}
    </div>
  )
}
