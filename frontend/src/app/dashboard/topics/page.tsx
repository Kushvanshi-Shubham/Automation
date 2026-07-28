"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Search, Flame, TrendingUp as TrendingIcon, RefreshCw, Filter, Zap } from "lucide-react"

const MOCK_TOPICS = [
  { id: 1, title: "Is Devin AI replacing software engineers?", source: "reddit", score: 98, category: "Tech", hook: "Everyone is panicking about Devin AI, but here's the truth no one is telling you.", keywords: ["AI", "Coding", "Devin"] },
  { id: 2, title: "The hidden lore of Elden Ring DLC", source: "trends", score: 92, category: "Gaming", hook: "Did you notice this massive secret hidden in the first 10 seconds of the Elden Ring DLC trailer?", keywords: ["Elden Ring", "Gaming", "Lore"] },
  { id: 3, title: "Why intermittent fasting might actually be bad", source: "reddit", score: 85, category: "Health", hook: "A new study just dropped about intermittent fasting, and it changes everything.", keywords: ["Health", "Fasting", "Science"] },
  { id: 4, title: "MrBeast's new strategy explained", source: "trends", score: 88, category: "YouTube", hook: "MrBeast just quietly changed his entire thumbnail strategy. Here is why.", keywords: ["MrBeast", "YouTube", "Strategy"] },
  { id: 5, title: "The weirdest exoplanet we just discovered", source: "reddit", score: 79, category: "Space", hook: "NASA just found a planet where it literally rains glass sideways.", keywords: ["Space", "NASA", "Science"] },
  { id: 6, title: "Dune Part 2 visual effects breakdown", source: "trends", score: 95, category: "Movies", hook: "How Dune Part 2 achieved the impossible with practical effects.", keywords: ["Dune", "VFX", "Movies"] },
]

export default function TopicsPage() {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [filter, setFilter] = useState("all")

  const refreshTopics = () => {
    setIsRefreshing(true)
    setTimeout(() => setIsRefreshing(false), 1500)
  }

  const filteredTopics = MOCK_TOPICS.filter(t => filter === "all" || t.source === filter)

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Trending Topics</h1>
          <p className="text-zinc-400 mt-1">AI-curated viral opportunities updated in real-time.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button 
            onClick={refreshTopics}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-zinc-900 border border-white/10 hover:bg-zinc-800 transition-colors text-sm font-medium"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin text-violet-400" : ""}`} />
            Refresh
          </button>
          <button className="flex items-center gap-2 px-6 py-2 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 font-medium text-white shadow-lg hover:shadow-violet-500/25 transition-all text-sm">
            <Zap className="w-4 h-4" /> Custom Topic
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2 mb-8 bg-zinc-900 p-1.5 rounded-xl border border-white/5 w-fit">
        <FilterButton active={filter === "all"} onClick={() => setFilter("all")} icon={Flame} label="All Trending" color="text-rose-400" />
        <FilterButton active={filter === "reddit"} onClick={() => setFilter("reddit")} icon={Search} label="Reddit" color="text-orange-500" />
        <FilterButton active={filter === "trends"} onClick={() => setFilter("trends")} icon={TrendingIcon} label="Google Trends" color="text-blue-400" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredTopics.map((topic, i) => (
          <motion.div 
            key={topic.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="flex flex-col rounded-2xl bg-zinc-900 border border-white/5 overflow-hidden hover:border-white/20 transition-all hover:-translate-y-1 hover:shadow-xl hover:shadow-black/50 group"
          >
            <div className="p-6 flex-1">
              <div className="flex justify-between items-start mb-4">
                <div className={`px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider ${
                  topic.source === "reddit" ? "bg-orange-500/10 text-orange-500 border border-orange-500/20" : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                }`}>
                  {topic.source}
                </div>
                <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-white/5 border border-white/10 text-xs font-medium">
                  <Flame className="w-3.5 h-3.5 text-rose-400" /> Score: {topic.score}
                </div>
              </div>
              
              <h3 className="text-xl font-semibold mb-3 leading-tight text-zinc-100 group-hover:text-violet-300 transition-colors">
                {topic.title}
              </h3>
              
              <div className="bg-black/20 rounded-xl p-4 mb-4 border border-white/5">
                <p className="text-xs font-medium text-zinc-500 mb-1 uppercase tracking-wider">Suggested Hook</p>
                <p className="text-sm text-zinc-300 italic">"{topic.hook}"</p>
              </div>

              <div className="flex flex-wrap gap-2 mt-auto">
                {topic.keywords.map(kw => (
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

function FilterButton({ active, onClick, icon: Icon, label, color }: any) {
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
