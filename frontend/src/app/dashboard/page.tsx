"use client"

import { motion } from "framer-motion"
import { Video, Zap, PlayCircle, Eye, Activity, Clock, AlertCircle, CheckCircle2 } from "lucide-react"
import Link from "next/link"

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
}

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { type: "spring" as const, stiffness: 300, damping: 24 }
  }
}

export default function DashboardHome() {
  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-8">
      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total Shorts" value="128" icon={Video} trend="+12%" color="violet" />
        <StatCard title="Credits Left" value="42" icon={Zap} trend="-8" color="blue" subtitle="Resets in 5 days" />
        <StatCard title="Videos Live" value="115" icon={PlayCircle} trend="+5%" color="emerald" />
        <StatCard title="Total Views" value="2.4M" icon={Eye} trend="+42%" color="orange" />
      </div>

      {/* Active Pipelines */}
      <motion.div variants={itemVariants} className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Activity className="w-5 h-5 text-violet-400" />
            Active Pipelines
          </h2>
          <span className="text-sm text-zinc-400">1 task running</span>
        </div>
        
        <div className="p-6 rounded-2xl bg-zinc-900 border border-white/5 relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-1 h-full bg-blue-500" />
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity" />
          
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/20 text-blue-400 border border-blue-500/20">
                  Generating Video
                </span>
                <span className="text-xs text-zinc-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> ~2m remaining
                </span>
              </div>
              <h3 className="text-lg font-medium">"Why Rome actually fell in 476 AD"</h3>
              <p className="text-sm text-zinc-400">History Niche • Veo 3.1 Model</p>
            </div>
            
            <div className="w-full md:w-1/3 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-zinc-400">Progress</span>
                <span className="font-medium">65%</span>
              </div>
              <div className="h-2 w-full bg-zinc-800 rounded-full overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: "65%" }}
                  className="h-full bg-gradient-to-r from-violet-500 to-blue-500 rounded-full relative"
                >
                  <div className="absolute inset-0 bg-white/20 animate-pulse" />
                </motion.div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Recent Shorts */}
      <motion.div variants={itemVariants} className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Recent Shorts</h2>
          <Link href="/dashboard/uploads" className="text-sm text-violet-400 hover:text-violet-300 font-medium">
            View all &rarr;
          </Link>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <ShortCard 
            title="The secret to 10x productivity"
            status="published"
            views="14.2K"
            date="2 hours ago"
            thumbnail="https://images.unsplash.com/photo-1611162616475-46b635cb6868?q=80&w=300&h=400&fit=crop"
          />
          <ShortCard 
            title="Top 5 AI tools for 2026"
            status="draft"
            views="-"
            date="5 hours ago"
            thumbnail="https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=300&h=400&fit=crop"
          />
          <ShortCard 
            title="Mind-blowing space facts"
            status="failed"
            views="-"
            date="1 day ago"
            thumbnail="https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=300&h=400&fit=crop"
          />
        </div>
      </motion.div>
    </motion.div>
  )
}

function StatCard({ title, value, icon: Icon, trend, color, subtitle }: any) {
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
        <span className={`text-sm font-medium ${trend.startsWith('+') ? 'text-emerald-400' : 'text-zinc-400'}`}>
          {trend}
        </span>
      </div>
      <h3 className="text-3xl font-bold mb-1">{value}</h3>
      <p className="text-sm text-zinc-400 font-medium">{title}</p>
      {subtitle && <p className="text-xs text-zinc-500 mt-2">{subtitle}</p>}
    </motion.div>
  )
}

function ShortCard({ title, status, views, date, thumbnail }: any) {
  const statusMap: Record<string, { icon: typeof CheckCircle2; color: string; bg: string; border: string; label: string }> = {
    published: { icon: CheckCircle2, color: "text-emerald-400", bg: "bg-emerald-400/10", border: "border-emerald-400/20", label: "Live" },
    draft: { icon: Clock, color: "text-amber-400", bg: "bg-amber-400/10", border: "border-amber-400/20", label: "Draft" },
    failed: { icon: AlertCircle, color: "text-rose-400", bg: "bg-rose-400/10", border: "border-rose-400/20", label: "Failed" },
  }
  const statusConfig = statusMap[status as string] || statusMap["draft"]

  const StatusIcon = statusConfig.icon

  return (
    <div className="group rounded-2xl bg-zinc-900 border border-white/5 overflow-hidden hover:border-white/10 transition-all">
      <div className="aspect-[9/16] relative bg-zinc-800 overflow-hidden">
        <img src={thumbnail} alt={title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
        
        <div className="absolute top-3 left-3">
          <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium backdrop-blur-md border ${statusConfig.bg} ${statusConfig.color} ${statusConfig.border}`}>
            <StatusIcon className="w-3.5 h-3.5" />
            {statusConfig.label}
          </div>
        </div>
        
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 backdrop-blur-sm">
          <button className="px-6 py-2 rounded-full bg-white/20 hover:bg-white/30 text-white font-medium border border-white/30 transition-colors flex items-center gap-2">
            <PlayCircle className="w-4 h-4" /> View
          </button>
        </div>
        
        <div className="absolute bottom-4 left-4 right-4">
          <h4 className="text-white font-medium line-clamp-2 mb-2 leading-tight drop-shadow-md">{title}</h4>
          <div className="flex items-center justify-between text-xs text-zinc-300">
            <span>{date}</span>
            <span className="flex items-center gap-1"><Eye className="w-3 h-3" /> {views}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
