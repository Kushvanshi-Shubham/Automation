"use client"

import { useQuery } from "@tanstack/react-query"
import { Coins, ReceiptText, TrendingUp } from "lucide-react"
import { fetchApi } from "@/lib/api-client"

interface LedgerEntry {
  id: string
  amount: number
  type: string
  description: string | null
  created_at: string | null
}

interface Economics {
  month: string
  credits: { debited: number; refunded: number; net_spent: number; granted: number }
  usage: Record<string, number>
  estimated_cost_usd: Record<string, number>
  credit_price_usd: number
  implied_revenue_usd: number
  implied_margin_usd: number
  note: string
}

const TYPE_LABELS: Record<string, string> = {
  subscription_grant: "Credits granted",
  video_debit: "Render",
  refund: "Refund",
}

export default function BillingPage() {
  const { data: credits } = useQuery<{ balance: number; plan: string }>({
    queryKey: ["credits-page"],
    queryFn: () => fetchApi("/billing/credits"),
  })
  const { data: ledger } = useQuery<LedgerEntry[]>({
    queryKey: ["ledger"],
    queryFn: () => fetchApi("/billing/ledger"),
  })
  // Owner-only — 403 for everyone else, so never retry and render nothing.
  const { data: eco } = useQuery<Economics>({
    queryKey: ["economics"],
    queryFn: () => fetchApi("/billing/economics"),
    retry: false,
  })

  return (
    <div className="space-y-6 pb-12 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Billing & Credits</h1>
        <p className="text-zinc-400 mt-1">Every render costs credits — here&apos;s where they went.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-6 rounded-2xl bg-zinc-900/60 backdrop-blur-md border border-white/10">
          <div className="flex items-center gap-2 text-zinc-400 text-sm mb-2">
            <Coins className="w-4 h-4 text-violet-400" /> Credit balance
          </div>
          <p className="text-4xl font-bold">{credits?.balance ?? "…"}</p>
          <p className="text-xs text-zinc-500 mt-1 capitalize">{credits?.plan ?? ""} plan · packs arrive with billing</p>
        </div>
        <div className="p-6 rounded-2xl bg-zinc-900/60 backdrop-blur-md border border-white/10">
          <div className="flex items-center gap-2 text-zinc-400 text-sm mb-2">
            <ReceiptText className="w-4 h-4 text-blue-400" /> Recent renders
          </div>
          <p className="text-4xl font-bold">
            {(ledger ?? []).filter(l => l.type === "video_debit").length}
          </p>
          <p className="text-xs text-zinc-500 mt-1">on your latest ledger entries</p>
        </div>
      </div>

      {/* Owner-only platform economics */}
      {eco && (
        <div className="p-6 rounded-2xl bg-zinc-900/60 backdrop-blur-md border border-violet-500/20">
          <div className="flex items-center gap-2 text-sm font-semibold text-violet-300 mb-4">
            <TrendingUp className="w-4 h-4" /> Platform economics — {eco.month} (owner view)
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <Stat label="Credits net spent" value={String(eco.credits.net_spent)} />
            <Stat label="Real API cost" value={`$${eco.estimated_cost_usd.total.toFixed(2)}`} />
            <Stat label="Implied revenue" value={`$${eco.implied_revenue_usd.toFixed(2)}`} sub={`@ $${eco.credit_price_usd}/credit`} />
            <Stat
              label="Implied margin"
              value={`$${eco.implied_margin_usd.toFixed(2)}`}
              accent={eco.implied_margin_usd >= 0 ? "text-emerald-400" : "text-rose-400"}
            />
          </div>
          <div className="text-xs text-zinc-500 space-y-1">
            <p>
              Usage: {Object.entries(eco.usage).filter(([, v]) => v > 0).map(([k, v]) => `${k}: ${v}`).join(" · ") || "none yet this month"}
            </p>
            <p>{eco.note}</p>
          </div>
        </div>
      )}

      {/* Ledger */}
      <div className="rounded-2xl bg-zinc-900/60 backdrop-blur-md border border-white/10 overflow-hidden">
        <p className="px-5 py-3.5 text-sm font-semibold border-b border-white/5">Recent activity</p>
        {(ledger ?? []).length === 0 && (
          <p className="px-5 py-6 text-sm text-zinc-500">No activity yet — create your first short.</p>
        )}
        {(ledger ?? []).map(entry => (
          <div key={entry.id} className="px-5 py-3 flex items-center justify-between border-t border-white/5 first:border-t-0">
            <div className="min-w-0">
              <p className="text-sm truncate">{entry.description || TYPE_LABELS[entry.type] || entry.type}</p>
              <p className="text-xs text-zinc-500">
                {entry.created_at ? new Date(entry.created_at).toLocaleString() : ""}
              </p>
            </div>
            <span className={`text-sm font-semibold flex-shrink-0 ${entry.amount > 0 ? "text-emerald-400" : "text-zinc-300"}`}>
              {entry.amount > 0 ? `+${entry.amount}` : entry.amount}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function Stat({ label, value, sub, accent }: { label: string; value: string; sub?: string; accent?: string }) {
  return (
    <div>
      <p className="text-xs text-zinc-500 mb-1">{label}</p>
      <p className={`text-xl font-bold ${accent ?? ""}`}>{value}</p>
      {sub && <p className="text-[10px] text-zinc-600">{sub}</p>}
    </div>
  )
}
