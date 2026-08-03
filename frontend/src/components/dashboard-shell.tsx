"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { signOut } from "next-auth/react"
import { Home, TrendingUp, PenTool, Upload, BarChart3, Settings, CreditCard, Plus, Bell, LogOut, ChevronLeft, ChevronRight, Repeat, Scissors } from "lucide-react"
import { useCredits } from "@/hooks/use-credits"

const navItems = [
  { href: "/dashboard", icon: Home, label: "Dashboard" },
  { href: "/dashboard/topics", icon: TrendingUp, label: "Topics" },
  { href: "/dashboard/studio", icon: PenTool, label: "Create" },
  { href: "/dashboard/series", icon: Repeat, label: "Series" },
  { href: "/dashboard/clips", icon: Scissors, label: "Clips" },
  { href: "/dashboard/uploads", icon: Upload, label: "Upload Manager" },
  { href: "/dashboard/analytics", icon: BarChart3, label: "Analytics" },
  { href: "/dashboard/billing", icon: CreditCard, label: "Billing" },
  { href: "/dashboard/settings", icon: Settings, label: "Settings" },
]

const PLAN_CREDIT_LIMITS: Record<string, number> = { free: 3, pro: 50, studio: 150 }

interface DashboardShellProps {
  user: { name?: string | null; email?: string | null; image?: string | null }
  children: React.ReactNode
}

export default function DashboardShell({ user, children }: DashboardShellProps) {
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const { credits, plan, isLoading: creditsLoading } = useCredits()

  const activePage = navItems.find(item => item.href === pathname)?.label || "Dashboard"
  const creditLimit = PLAN_CREDIT_LIMITS[plan] ?? PLAN_CREDIT_LIMITS.free
  const creditPct = Math.min(100, Math.round((credits / creditLimit) * 100))
  const planLabel = plan.charAt(0).toUpperCase() + plan.slice(1)

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-50 overflow-hidden font-sans">
      {/* Ambient brand glow behind the glass surfaces */}
      <div aria-hidden className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute -top-32 left-1/3 w-[700px] h-[400px] bg-violet-600/15 blur-[140px] rounded-full" />
        <div className="absolute bottom-0 -right-40 w-[500px] h-[400px] bg-blue-600/10 blur-[140px] rounded-full" />
      </div>

      {/* Sidebar */}
      <motion.aside
        animate={{ width: isCollapsed ? 80 : 260 }}
        className="h-full bg-zinc-900/60 backdrop-blur-xl border-r border-white/10 flex flex-col relative flex-shrink-0 z-20 transition-all duration-300"
      >
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute -right-3 top-6 w-6 h-6 rounded-full bg-zinc-800 border border-white/10 flex items-center justify-center hover:bg-zinc-700 transition-colors z-30"
        >
          {isCollapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronLeft className="w-3 h-3" />}
        </button>

        <div className="p-6 flex items-center gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element -- small static brand asset */}
          <img
            src="/brand/kliptos-logo-2k.jpeg"
            alt="Kliptos"
            className="w-9 h-9 rounded-xl object-cover flex-shrink-0 border border-white/10 shadow-[0_0_14px_rgba(139,92,246,0.45)]"
          />
          <AnimatePresence>
            {!isCollapsed && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: "auto" }}
                exit={{ opacity: 0, width: 0 }}
                className="font-bold text-xl tracking-tight whitespace-nowrap overflow-hidden"
              >
                Kliptos
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link key={item.href} href={item.href}>
                <div className={`flex items-center gap-3 px-3 py-3 rounded-xl transition-all group relative overflow-hidden ${
                  isActive
                    ? "bg-white/10 text-white shadow-inner"
                    : "text-zinc-400 hover:text-white hover:bg-white/5"
                }`}>
                  {isActive && (
                    <motion.div layoutId="activeNav" className="absolute left-0 top-0 bottom-0 w-1 bg-violet-500 rounded-r-full" />
                  )}
                  <item.icon className={`w-5 h-5 flex-shrink-0 ${isActive ? "text-violet-400" : ""}`} />
                  {!isCollapsed && <span className="font-medium whitespace-nowrap">{item.label}</span>}
                </div>
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-white/5">
          {!isCollapsed ? (
            <div className="bg-zinc-800/50 rounded-xl p-4 mb-4 border border-white/5">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-zinc-400 font-medium">Credits</span>
                <span className="text-xs font-bold text-violet-400">
                  {creditsLoading ? "…" : `${credits}/${creditLimit}`}
                </span>
              </div>
              <div className="w-full h-1.5 bg-zinc-900 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-violet-500 to-blue-500 transition-all"
                  style={{ width: `${creditsLoading ? 0 : creditPct}%` }}
                />
              </div>
            </div>
          ) : (
            <div className="w-10 h-10 mx-auto rounded-full bg-zinc-800 flex items-center justify-center text-xs font-bold text-violet-400 mb-4 border border-white/5">
              {creditsLoading ? "…" : credits}
            </div>
          )}

          <div className={`flex items-center gap-3 ${isCollapsed ? "justify-center" : "px-2"}`}>
            <div className="w-9 h-9 rounded-full bg-zinc-700 flex-shrink-0 overflow-hidden border border-white/10">
              {user.image ? (
                // eslint-disable-next-line @next/next/no-img-element -- external avatar host, no optimizer benefit
                <img src={user.image} alt={user.name ?? "User"} className="w-full h-full object-cover" referrerPolicy="no-referrer" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-sm font-bold text-zinc-300">
                  {(user.name ?? user.email ?? "?").charAt(0).toUpperCase()}
                </div>
              )}
            </div>
            {!isCollapsed && (
              <div className="flex-1 overflow-hidden">
                <p className="text-sm font-medium truncate">{user.name ?? user.email}</p>
                <p className="text-xs text-zinc-500 truncate">{planLabel} Plan</p>
              </div>
            )}
            {!isCollapsed && (
              <button
                onClick={() => signOut({ redirectTo: "/" })}
                className="p-2 text-zinc-500 hover:text-white transition-colors"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </motion.aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative z-10 overflow-hidden">
        {/* Topbar */}
        <header className="h-20 border-b border-white/10 bg-zinc-950/60 backdrop-blur-xl flex items-center justify-between px-8 flex-shrink-0 z-10">
          <h1 className="text-2xl font-semibold tracking-tight">{activePage}</h1>
          <div className="flex items-center gap-4">
            <button className="w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-white/10 transition-colors">
              <Bell className="w-5 h-5" />
            </button>
            <Link href="/dashboard/topics" className="px-5 py-2.5 rounded-full bg-gradient-to-r from-violet-600 to-blue-600 font-medium text-white shadow-lg hover:shadow-violet-500/25 transition-all flex items-center gap-2">
              <Plus className="w-4 h-4" />
              New Short
            </Link>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-y-auto p-8 relative">
          <div className="max-w-7xl mx-auto h-full">
            {children}
          </div>
        </div>
      </main>
    </div>
  )
}
