"use client"

import { motion } from "framer-motion"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Search, Flame, TrendingUp as TrendingIcon, RefreshCw, Zap, Inbox } from "lucide-react"
import { useState } from "react"
import { fetchApi } from "@/lib/api-client"

interface Topic {
  id: string
  title: string
  source: string | null
  keywords: string[] | null
  score: number | null
  hook_text: string | null
  discovered_at: string | null
}

export default function TopicsPage() {
  const [filter, setFilter] = useState("all")
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery<{ items: Topic[] }>({
    queryKey: ["topics"],
    queryFn: () => fetchApi("/topics"),
    staleTime: 60_000,
  })

  const refresh = useMutation({
    mutationFn: () => fetchApi("/topics/refresh", { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["topics"] }),
  })

  const topics = data?.items ?? []
  const filteredTopics = topics.filter(t => filter === "all" || t.source === filter)

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Trending Topics</h1>
          <p className="text-zinc-400 mt-1">AI-curated viral opportunities from Google Trends & Reddit.</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => refresh.mutate()}
            disabled={refresh.isPending}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-zinc-900 border border-white/10 hover:bg-zinc-800 transition-colors text-sm font-medium disabled:opacity-60"
          >
            <RefreshCw className={`w-4 h-4 ${refresh.isPending ? "animate-spin text-violet-400" : ""}`} />
            {refresh.isPending ? "Harvesting…" : "Refresh"}
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2 mb-8 bg-zinc-900 p-1.5 rounded-xl border border-white/5 w-fit">
        <FilterButton active={filter === "all"} onClick={() => setFilter("all")} icon={Flame} label="All Trending" color="text-rose-400" />
        <FilterButton active={filter === "reddit"} onClick={() => setFilter("reddit")} icon={Search} label="Reddit" color="text-orange-500" />
        <FilterButton active={filter === "trends"} onClick={() => setFilter("trends")} icon={TrendingIcon} label="Google Trends" color="text-blue-400" />
      </div>

      {error && (
        <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
          Failed to load topics: {(error as Error).message}
        </div>
      )}

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-64 rounded-2xl bg-zinc-900 border border-white/5 animate-pulse" />
          ))}
        </div>
      )}

      {!isLoading && !error && filteredTopics.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-white/10 flex items-center justify-center mb-4">
            <Inbox className="w-8 h-8 text-zinc-500" />
          </div>
          <h3 className="text-lg font-semibold mb-1">No topics yet</h3>
          <p className="text-zinc-400 text-sm mb-6">Hit Refresh to harvest what&apos;s trending right now.</p>
          <button
            onClick={() => refresh.mutate()}
            disabled={refresh.isPending}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 font-medium text-white text-sm disabled:opacity-60"
          >
            <RefreshCw className={`w-4 h-4 ${refresh.isPending ? "animate-spin" : ""}`} />
            Harvest Topics
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredTopics.map((topic, i) => (
          <motion.div
            key={topic.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: Math.min(i * 0.05, 0.5) }}
            className="flex flex-col rounded-2xl bg-zinc-900 border border-white/5 overflow-hidden hover:border-white/20 transition-all hover:-translate-y-1 hover:shadow-xl hover:shadow-black/50 group"
          >
            <div className="p-6 flex-1">
              <div className="flex justify-between items-start mb-4">
                <div className={`px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider ${
                  topic.source === "reddit" ? "bg-orange-500/10 text-orange-500 border border-orange-500/20" : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                }`}>
                  {topic.source ?? "unknown"}
                </div>
                <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-white/5 border border-white/10 text-xs font-medium">
                  <Flame className="w-3.5 h-3.5 text-rose-400" /> Score: {topic.score ?? "—"}
                </div>
              </div>

              <h3 className="text-xl font-semibold mb-3 leading-tight text-zinc-100 group-hover:text-violet-300 transition-colors">
                {topic.title}
              </h3>

              {topic.hook_text && (
                <div className="bg-black/20 rounded-xl p-4 mb-4 border border-white/5">
                  <p className="text-xs font-medium text-zinc-500 mb-1 uppercase tracking-wider">Suggested Hook</p>
                  <p className="text-sm text-zinc-300 italic">&quot;{topic.hook_text}&quot;</p>
                </div>
              )}

              <div className="flex flex-wrap gap-2 mt-auto">
                {(topic.keywords ?? []).map(kw => (
                  <span key={kw} className="px-2 py-1 rounded-md bg-white/5 text-xs text-zinc-400">
                    #{kw}
                  </span>
                ))}
              </div>
            </div>

            <div className="p-4 border-t border-white/5 bg-zinc-950/50">
              <button className="w-full py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-colors text-sm font-medium flex items-center justify-center gap-2 group-hover:bg-violet-600 group-hover:border-violet-500 group-hover:text-white">
                <Zap className="w-4 h-4" /> Create Short
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

function FilterButton({ active, onClick, icon: Icon, label, color }: {
  active: boolean; onClick: () => void; icon: React.ElementType; label: string; color: string
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
        active ? "bg-white/10 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200 hover:bg-white/5"
      }`}
    >
      <Icon className={`w-4 h-4 ${active ? color : "text-zinc-500"}`} /> {label}
    </button>
  )
}
