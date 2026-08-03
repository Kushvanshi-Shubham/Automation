"use client"

import { useQuery } from "@tanstack/react-query"
import { AlertCircle, CheckCircle2, Clock, ExternalLink, Inbox, Loader2 } from "lucide-react"
import Link from "next/link"
import { fetchApi } from "@/lib/api-client"

interface UploadVideo {
  id: string
  status: string
  title: string | null
  scheduled_at: string | null
  published_at: string | null
  created_at: string | null
}

const STATUS_STYLE: Record<string, { icon: typeof CheckCircle2; cls: string; label: string }> = {
  published: { icon: CheckCircle2, cls: "bg-emerald-400/10 text-emerald-400 border-emerald-400/20", label: "Published" },
  scheduled: { icon: Clock, cls: "bg-violet-400/10 text-violet-400 border-violet-400/20", label: "Scheduled" },
  publishing: { icon: Loader2, cls: "bg-blue-400/10 text-blue-400 border-blue-400/20", label: "Uploading" },
  upload_failed: { icon: AlertCircle, cls: "bg-rose-400/10 text-rose-400 border-rose-400/20", label: "Failed" },
}

export default function UploadsPage() {
  const { data, isLoading } = useQuery<UploadVideo[]>({
    queryKey: ["uploads"],
    queryFn: () => fetchApi("/uploads"),
    refetchInterval: q => (q.state.data ?? []).some(v => v.status === "publishing") ? 5000 : false,
  })

  const uploads = data ?? []

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Upload Manager</h1>
        <p className="text-zinc-400 mt-1">Everything you&apos;ve published or scheduled.</p>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-20 rounded-2xl bg-zinc-900/60 backdrop-blur-md border border-white/10 animate-pulse" />
          ))}
        </div>
      )}

      {!isLoading && uploads.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-white/10 flex items-center justify-center mb-4">
            <Inbox className="w-8 h-8 text-zinc-500" />
          </div>
          <h3 className="text-lg font-semibold mb-1">Nothing published yet</h3>
          <p className="text-zinc-400 text-sm">Render a short and hit Publish — it&apos;ll show up here.</p>
        </div>
      )}

      <div className="space-y-3">
        {uploads.map(video => {
          const style = STATUS_STYLE[video.status] ?? STATUS_STYLE.publishing
          const StatusIcon = style.icon
          return (
            <div key={video.id} className="p-5 rounded-2xl bg-zinc-900/60 backdrop-blur-md border border-white/10 flex items-center justify-between gap-4">
              <div className="min-w-0">
                <p className="font-medium truncate">{video.title ?? "Untitled short"}</p>
                <p className="text-xs text-zinc-500 mt-1">
                  {video.status === "scheduled" && video.scheduled_at
                    ? `Goes public ${new Date(video.scheduled_at).toLocaleString()}`
                    : video.published_at
                      ? `Published ${new Date(video.published_at).toLocaleString()}`
                      : ""}
                </p>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                <span className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${style.cls}`}>
                  <StatusIcon className={`w-3.5 h-3.5 ${video.status === "publishing" ? "animate-spin" : ""}`} />
                  {style.label}
                </span>
                <Link
                  href={`/dashboard/preview/${video.id}`}
                  className="p-2 rounded-lg text-zinc-500 hover:text-white hover:bg-white/5 transition-colors"
                  title="Open preview"
                >
                  <ExternalLink className="w-4 h-4" />
                </Link>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
