"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { motion } from "framer-motion"
import { AlertCircle, Clapperboard, Clock, Loader2, Tv } from "lucide-react"
import Link from "next/link"
import { useParams, useSearchParams } from "next/navigation"
import { Suspense, useEffect, useState } from "react"
import { API_BASE_URL, fetchApi } from "@/lib/api-client"
import { usePipeline } from "@/hooks/use-pipeline"

const MEDIA_ORIGIN = API_BASE_URL.replace(/\/api\/?$/, "")

interface VideoData {
  id: string
  status: string
  title: string | null
  description: string | null
  tags: string[] | null
  video_url: string | null
  thumbnail_url: string | null
  youtube_video_id: string | null
}

interface Channel {
  id: string
  channel_name: string | null
}

export default function PreviewPage() {
  return (
    <Suspense fallback={<div className="h-96 rounded-2xl bg-zinc-900 border border-white/5 animate-pulse max-w-sm mx-auto" />}>
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

  if (isLoading) {
    return <div className="h-96 rounded-2xl bg-zinc-900 border border-white/5 animate-pulse max-w-sm mx-auto" />
  }
  if (error || !video) {
    return (
      <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm max-w-lg">
        Failed to load video{error ? `: ${(error as Error).message}` : ""}
      </div>
    )
  }

  return (
    <div className="flex flex-col lg:flex-row gap-10 pb-12 max-w-5xl">
      {/* Player column */}
      <div className="w-full max-w-sm mx-auto lg:mx-0 flex-shrink-0">
        <div className="aspect-[9/16] rounded-3xl overflow-hidden bg-zinc-900 border border-white/10 relative shadow-2xl">
          {video.status === "ready" && video.video_url ? (
            <video
              src={`${MEDIA_ORIGIN}${video.video_url}`}
              controls
              playsInline
              className="w-full h-full object-cover"
            />
          ) : video.status === "failed" ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-6">
              <AlertCircle className="w-10 h-10 text-rose-400 mb-3" />
              <p className="font-medium text-rose-300 mb-1">Render failed</p>
              <p className="text-xs text-zinc-500">Your credit was refunded automatically.</p>
            </div>
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-6">
              <Loader2 className="w-10 h-10 text-violet-400 animate-spin mb-4" />
              <p className="font-medium mb-1 capitalize">{pipeline.stage !== "initializing" ? pipeline.stage : "Preparing"}…</p>
              <div className="w-full max-w-[200px] h-1.5 bg-zinc-800 rounded-full overflow-hidden mt-3">
                <motion.div
                  animate={{ width: `${pipeline.progress}%` }}
                  className="h-full bg-gradient-to-r from-violet-500 to-blue-500 rounded-full"
                />
              </div>
              <p className="text-xs text-zinc-500 mt-2">{Math.round(pipeline.progress)}%</p>
            </div>
          )}
        </div>
      </div>

      {/* Meta column */}
      <div className="flex-1 space-y-6">
        <div>
          <h1 className="text-2xl font-bold leading-tight mb-2">{video.title ?? "Untitled short"}</h1>
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${
            video.status === "ready"
              ? "bg-emerald-400/10 text-emerald-400 border-emerald-400/20"
              : video.status === "failed"
                ? "bg-rose-400/10 text-rose-400 border-rose-400/20"
                : "bg-blue-400/10 text-blue-400 border-blue-400/20"
          }`}>
            {video.status === "ready" ? <Clapperboard className="w-3.5 h-3.5" /> : <Clock className="w-3.5 h-3.5" />}
            {video.status}
          </span>
        </div>

        {video.description && (
          <div className="p-4 rounded-xl bg-zinc-900 border border-white/5">
            <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">Description</p>
            <p className="text-sm text-zinc-300 whitespace-pre-line">{video.description}</p>
          </div>
        )}

        <div className="flex gap-3">
          <Link
            href={`/dashboard/studio?video=${video.id}`}
            className="px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-sm font-medium transition-colors"
          >
            Edit Script
          </Link>
        </div>

        {video.status === "ready" && <PublishPanel video={video} />}
        {["ready", "published", "scheduled"].includes(video.status) && <InstagramPanel video={video} />}
        {video.status === "publishing" && (
          <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-300 text-sm flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Uploading to YouTube…
          </div>
        )}
        {video.status === "published" && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm flex items-center justify-between gap-2">
            <span className="flex items-center gap-2"><Tv className="w-4 h-4" /> Published to YouTube 🎉</span>
            {video.youtube_video_id && (
              <a
                href={`https://www.youtube.com/watch?v=${video.youtube_video_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 font-medium transition-colors"
              >
                Watch on YouTube →
              </a>
            )}
          </div>
        )}
        {video.status === "scheduled" && (
          <div className="p-4 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-300 text-sm flex items-center gap-2">
            <Clock className="w-4 h-4" /> Scheduled — YouTube will make it public automatically.
          </div>
        )}
        {video.status === "upload_failed" && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
            Upload failed. Check your channel connection in Settings and try again.
          </div>
        )}
      </div>
    </div>
  )
}

interface PublishRecord {
  id: string
  platform: string
  status: string
  external_id: string | null
  error_message: string | null
}

function InstagramPanel({ video }: { video: VideoData }) {
  const queryClient = useQueryClient()
  const [caption, setCaption] = useState("")

  const { data: igStatus } = useQuery<{ enabled: boolean }>({
    queryKey: ["ig-status"],
    queryFn: () => fetchApi("/instagram/status"),
    staleTime: Infinity,
  })
  const { data: accounts } = useQuery<{ id: string; username: string | null }[]>({
    queryKey: ["ig-accounts"],
    queryFn: () => fetchApi("/instagram"),
    enabled: igStatus?.enabled === true,
  })
  const { data: publishes } = useQuery<{ items: PublishRecord[] }>({
    queryKey: ["publishes", video.id],
    queryFn: () => fetchApi(`/uploads/publishes/${video.id}`),
    refetchInterval: q =>
      (q.state.data?.items ?? []).some(p => p.status === "publishing") ? 5000 : false,
  })

  const publish = useMutation({
    mutationFn: () =>
      fetchApi(`/uploads/${video.id}/publish-instagram`, {
        method: "POST",
        body: JSON.stringify({ caption }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["publishes", video.id] }),
  })

  if (!igStatus?.enabled) return null

  const igPublish = (publishes?.items ?? []).find(p => p.platform === "instagram")

  return (
    <div className="p-5 rounded-2xl bg-zinc-900 border border-white/5 space-y-3">
      <h3 className="font-semibold text-sm flex items-center gap-2">📸 Publish to Instagram (Reel)</h3>

      {igPublish?.status === "published" && (
        <p className="text-sm text-emerald-400">Published to Instagram ✓ (media {igPublish.external_id})</p>
      )}
      {igPublish?.status === "publishing" && (
        <p className="text-sm text-blue-300 flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin" /> Uploading Reel — Instagram is processing the video…
        </p>
      )}
      {igPublish?.status === "failed" && (
        <p className="text-xs text-rose-400">Failed: {igPublish.error_message}</p>
      )}

      {(!igPublish || igPublish.status === "failed") && (
        (accounts ?? []).length === 0 ? (
          <p className="text-sm text-zinc-400">
            <Link href="/dashboard/settings" className="text-violet-400 hover:text-violet-300 font-medium">
              Connect an Instagram account
            </Link>{" "}
            to publish Reels.
          </p>
        ) : (
          <>
            <textarea
              value={caption}
              onChange={e => setCaption(e.target.value.slice(0, 2200))}
              rows={2}
              placeholder="Caption (leave empty to use the video title + description)"
              className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm focus:outline-none focus:border-pink-500/50 resize-none"
            />
            <button
              onClick={() => publish.mutate()}
              disabled={publish.isPending}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-pink-600 to-rose-600 text-sm font-medium text-white disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {publish.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : "📸"}
              Publish Reel to @{accounts![0].username}
            </button>
            {publish.error && <p className="text-xs text-rose-400">{(publish.error as Error).message}</p>}
          </>
        )
      )}
    </div>
  )
}

function PublishPanel({ video }: { video: VideoData }) {
  const queryClient = useQueryClient()
  const videoId = video.id

  const { data: channels } = useQuery<Channel[]>({
    queryKey: ["channels"],
    queryFn: () => fetchApi("/channels"),
  })
  const { data: categories } = useQuery<{ items: { id: string; label: string }[] }>({
    queryKey: ["yt-categories"],
    queryFn: () => fetchApi("/uploads/categories"),
    staleTime: Infinity,
  })

  const [channelId, setChannelId] = useState("")
  const [privacy, setPrivacy] = useState("unlisted")
  const [scheduleAt, setScheduleAt] = useState("")
  const [categoryId, setCategoryId] = useState("24")

  // Editable metadata, prefilled from the AI-generated values.
  const [title, setTitle] = useState(video.title ?? "")
  const [description, setDescription] = useState(video.description ?? "")
  const [tagsText, setTagsText] = useState((video.tags ?? []).join(", "))

  const publish = useMutation({
    mutationFn: async () => {
      const tags = tagsText.split(",").map(t => t.trim().replace(/^#/, "")).filter(Boolean).slice(0, 30)
      // 1) persist edited metadata, 2) dispatch upload
      await fetchApi(`/videos/${videoId}/metadata`, {
        method: "PUT",
        body: JSON.stringify({ title: title.trim() || null, description, tags }),
      })
      if (scheduleAt) {
        return fetchApi(`/uploads/${videoId}/schedule`, {
          method: "POST",
          body: JSON.stringify({
            channel_id: channelId,
            publish_at: new Date(scheduleAt).toISOString(),
            category_id: categoryId,
          }),
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
      <div className="p-4 rounded-xl bg-zinc-900 border border-white/5 text-sm text-zinc-400">
        <Link href="/dashboard/settings" className="text-violet-400 hover:text-violet-300 font-medium">
          Connect a YouTube channel
        </Link>{" "}
        to publish this short.
      </div>
    )
  }

  return (
    <div className="p-5 rounded-2xl bg-zinc-900 border border-white/5 space-y-4">
      <h3 className="font-semibold text-sm flex items-center gap-2">
        <Tv className="w-4 h-4 text-rose-500" /> Publish to YouTube
      </h3>

      {/* Metadata editor */}
      <div>
        <label className="text-xs text-zinc-500 block mb-1.5">
          Title <span className="text-zinc-600">({95 - title.length} left)</span>
        </label>
        <input
          value={title}
          onChange={e => setTitle(e.target.value.slice(0, 95))}
          className="w-full bg-black/20 border border-white/10 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-violet-500/50"
        />
      </div>
      <div>
        <label className="text-xs text-zinc-500 block mb-1.5">Description</label>
        <textarea
          value={description}
          onChange={e => setDescription(e.target.value.slice(0, 4900))}
          rows={4}
          className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm focus:outline-none focus:border-violet-500/50 resize-none"
        />
      </div>
      <div>
        <label className="text-xs text-zinc-500 block mb-1.5">Tags <span className="text-zinc-600">(comma-separated, max 30)</span></label>
        <input
          value={tagsText}
          onChange={e => setTagsText(e.target.value)}
          placeholder="apex legends, gaming, shorts"
          className="w-full bg-black/20 border border-white/10 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-violet-500/50"
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <select
          value={channelId}
          onChange={e => setChannelId(e.target.value)}
          className="bg-black/20 border border-white/10 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-violet-500/50"
        >
          <option value="">Select channel…</option>
          {channels.map(c => (
            <option key={c.id} value={c.id}>{c.channel_name ?? "Unnamed channel"}</option>
          ))}
        </select>
        <select
          value={categoryId}
          onChange={e => setCategoryId(e.target.value)}
          className="bg-black/20 border border-white/10 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-violet-500/50"
        >
          {(categories?.items ?? [{ id: "24", label: "Entertainment" }]).map(c => (
            <option key={c.id} value={c.id}>{c.label}</option>
          ))}
        </select>
        <select
          value={privacy}
          onChange={e => setPrivacy(e.target.value)}
          disabled={!!scheduleAt}
          className="bg-black/20 border border-white/10 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-violet-500/50 disabled:opacity-50"
        >
          <option value="unlisted">Unlisted</option>
          <option value="public">Public</option>
          <option value="private">Private</option>
        </select>
      </div>

      <div>
        <label className="text-xs text-zinc-500 block mb-1.5">Schedule (optional — goes public automatically)</label>
        <input
          type="datetime-local"
          value={scheduleAt}
          onChange={e => setScheduleAt(e.target.value)}
          className="w-full bg-black/20 border border-white/10 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-violet-500/50"
        />
      </div>

      {publish.error && (
        <p className="text-xs text-rose-400">{(publish.error as Error).message}</p>
      )}

      <button
        onClick={() => publish.mutate()}
        disabled={!channelId || !title.trim() || publish.isPending}
        className="w-full py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 text-sm font-medium text-white disabled:opacity-50 flex items-center justify-center gap-2"
      >
        {publish.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Tv className="w-4 h-4" />}
        {scheduleAt ? "Save & Schedule" : "Save & Publish Now"}
      </button>
    </div>
  )
}
