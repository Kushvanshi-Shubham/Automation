"use client"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { motion } from "framer-motion"
import { AlertCircle, Clapperboard, Clock, Loader2 } from "lucide-react"
import Link from "next/link"
import { useParams, useSearchParams } from "next/navigation"
import { Suspense, useEffect } from "react"
import { API_BASE_URL, fetchApi } from "@/lib/api-client"
import { usePipeline } from "@/hooks/use-pipeline"

const MEDIA_ORIGIN = API_BASE_URL.replace(/\/api\/?$/, "")

interface VideoData {
  id: string
  status: string
  title: string | null
  description: string | null
  video_url: string | null
  thumbnail_url: string | null
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
          <button
            disabled
            title="YouTube publishing lands in the next milestone"
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 text-sm font-medium text-white opacity-50 cursor-not-allowed"
          >
            Publish to YouTube (soon)
          </button>
        </div>
      </div>
    </div>
  )
}
