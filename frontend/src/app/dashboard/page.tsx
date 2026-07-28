"use client"

import { useQuery } from "@tanstack/react-query"
import { motion } from "framer-motion"
import {
  AlertCircle,
  CheckCircle2,
  Clapperboard,
  Clock,
  Inbox,
  Loader2,
  PenTool,
  PlayCircle,
  Video as VideoIcon,
  Zap,
} from "lucide-react"
import Link from "next/link"
import { fetchApi } from "@/lib/api-client"
import { useCredits } from "@/hooks/use-credits"

interface VideoItem {
  id: string
  status: string
  title: string | null
  video_url: string | null
  created_at: string | null
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
}

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: { y: 0, opacity: 1, transition: { type: "spring" as const, stiffness: 300, damping: 24 } },
}

const STATUS_BADGE: Record<string, { icon: typeof CheckCircle2; cls: string; label: string }> = {
  published: { icon: CheckCircle2, cls: "bg-emerald-400/10 text-emerald-400 border-emerald-400/20", label: "Live" },
  scheduled: { icon: Clock, cls: "bg-violet-400/10 text-violet-400 border-violet-400/20", label: "Scheduled" },
  ready: { icon: PlayCircle, cls: "bg-blue-400/10 text-blue-400 border-blue-400/20", label: "Ready" },
  rendering: { icon: Loader2, cls: "bg-blue-400/10 text-blue-400 border-blue-400/20", label: "Rendering" },
  publishing: { icon: Loader2, cls: "bg-blue-400/10 text-blue-400 border-blue-400/20", label: "Uploading" },
  script_ready: { icon: PenTool, cls: "bg-amber-400/10 text-amber-400 border-amber-400/20", label: "Script" },
  draft: { icon: Clock, cls: "bg-zinc-400/10 text-zinc-400 border-zinc-400/20", label: "Draft" },
  failed: { icon: AlertCircle, cls: "bg-rose-400/10 text-rose-400 border-rose-400/20", label: "Failed" },
  upload_failed: { icon: AlertCircle, cls: "bg-rose-400/10 text-rose-400 border-rose-400/20", label: "Upload failed" },
}

export default function DashboardHome() {
  const { credits } = useCredits()
  const { data, isLoading } = useQuery<{ items: VideoItem[]; total: number }>({
    queryKey: ["videos"],
    queryFn: () => fetchApi("/videos?page=1&page_size=50"),
    refetchInterval: q =>
      (q.state.data?.items ?? []).some(v => ["rendering", "publishing"].includes(v.status)) ? 5000 : false,
  })

  const videos = data?.items ?? []
  const published = videos.filter(v => v.status === "published").length
  const inProgress = videos.filter(v => ["rendering", "publishing", "script_ready"].includes(v.status)).length

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-8">
      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total Shorts" value={data ? String(data.total) : "…"} icon={VideoIcon} color="violet" />
        <StatCard title="Credits Left" value={String(credits)} icon={Zap} color="blue" subtitle="1 credit per render" />
        <StatCard title="Published" value={data ? String(published) : "…"} icon={PlayCircle} color="emerald" />
        <StatCard title="In Progress" value={data ? String(inProgress) : "…"} icon={Clapperboard} color="orange" />
      </div>

      {/* Video Library */}
      <motion.div variants={itemVariants} className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Your Shorts</h2>
          <Link href="/dashboard/topics" className="text-sm text-violet-400 hover:text-violet-300 font-medium">
            + Create new
          </Link>
        </div>

        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-36 rounded-2xl bg-zinc-900 border border-white/5 animate-pulse" />
            ))}
          </div>
        )}

        {!isLoading && videos.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-center rounded-2xl bg-zinc-900/50 border border-white/5">
            <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-white/10 flex items-center justify-center mb-4">
              <Inbox className="w-8 h-8 text-zinc-500" />
            </div>
            <h3 className="text-lg font-semibold mb-1">No shorts yet</h3>
            <p className="text-zinc-400 text-sm mb-6">Pick a trending topic and create your first one.</p>
            <Link
              href="/dashboard/topics"
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 font-medium text-white text-sm"
            >
              <Zap className="w-4 h-4" /> Browse Topics
            </Link>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {videos.map(video => {
            const badge = STATUS_BADGE[video.status] ?? STATUS_BADGE.draft
            const BadgeIcon = badge.icon
            const href = video.status === "script_ready"
              ? `/dashboard/studio?video=${video.id}`
              : `/dashboard/preview/${video.id}`
            return (
              <Link key={video.id} href={href}>
                <div className="group rounded-2xl bg-zinc-900 border border-white/5 overflow-hidden hover:border-white/15 transition-all hover:-translate-y-1 p-5 space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium border ${badge.cls}`}>
                      <BadgeIcon className={`w-3.5 h-3.5 ${["rendering", "publishing"].includes(video.status) ? "animate-spin" : ""}`} />
                      {badge.label}
                    </div>
                    {video.created_at && (
                      <span className="text-xs text-zinc-600">{new Date(video.created_at).toLocaleDateString()}</span>
                    )}
                  </div>
                  <h4 className="font-medium leading-snug line-clamp-2 group-hover:text-violet-300 transition-colors">
                    {video.title ?? "Untitled short"}
                  </h4>
                  <p className="text-xs text-zinc-500">
                    {video.status === "script_ready" ? "Continue in Studio →" : "Open preview →"}
                  </p>
                </div>
              </Link>
            )
          })}
        </div>
      </motion.div>
    </motion.div>
  )
}

function StatCard({ title, value, icon: Icon, color, subtitle }: {
  title: string; value: string; icon: React.ElementType; color: string; subtitle?: string
}) {
  const colorMap: Record<string, string> = {
    violet: "text-violet-400 bg-violet-400/10 border-violet-400/20",
    blue: "text-blue-400 bg-blue-400/10 border-blue-400/20",
    emerald: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
    orange: "text-orange-400 bg-orange-400/10 border-orange-400/20",
  }

  return (
    <motion.div variants={itemVariants} className="p-6 rounded-2xl bg-zinc-900 border border-white/5 hover:bg-zinc-800/80 transition-colors">
      <div className="flex justify-between items-start mb-4">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center border ${colorMap[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
      <h3 className="text-3xl font-bold mb-1">{value}</h3>
      <p className="text-sm text-zinc-400 font-medium">{title}</p>
      {subtitle && <p className="text-xs text-zinc-500 mt-2">{subtitle}</p>}
    </motion.div>
  )
}
