"use client"

/**
 * Billing — credit balance, ledger, and the owner-only economics panel.
 * Themed; numbers in mono (real telemetry). All queries unchanged.
 */
import { useQuery } from "@tanstack/react-query"
import { MdOutlineInsights } from "react-icons/md"
import { fetchApi } from "@/lib/api-client"
import { L, mono, grotesque, alpha } from "@/lib/line/tokens"

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

const card: React.CSSProperties = { background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 10 }

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

  const renders = (ledger ?? []).filter(l => l.type === "video_debit").length

  return (
    <div style={{ maxWidth: 860, fontFamily: grotesque, display: "flex", flexDirection: "column", gap: 18, paddingBottom: 24 }}>
      <div>
        <h1 style={{ margin: "0 0 4px", fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>Billing</h1>
        <p style={{ margin: 0, fontSize: 14, color: L.ash }}>
          <span style={{ fontFamily: mono, color: L.ink }}>{credits?.balance ?? "…"}</span> credits left
          {" · "}<span style={{ textTransform: "capitalize" }}>{credits?.plan ?? "free"}</span> plan
          {" · "}<span style={{ fontFamily: mono, color: L.ink }}>{renders}</span> renders on the recent ledger
          {" · "}credit packs arrive with payments
        </p>
      </div>

      {/* Owner-only platform economics */}
      {eco && (
        <div style={{ ...card, borderColor: alpha(L.make, 35), padding: 18 }}>
          <p style={{ margin: "0 0 14px", display: "flex", alignItems: "center", gap: 8, fontSize: 14, fontWeight: 650, color: L.make }}>
            <MdOutlineInsights size={17} /> Platform economics — {eco.month} (owner view)
          </p>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4" style={{ marginBottom: 14 }}>
            <EcoStat label="Credits net spent" value={String(eco.credits.net_spent)} />
            <EcoStat label="Real API cost" value={`$${eco.estimated_cost_usd.total.toFixed(2)}`} />
            <EcoStat label="Implied revenue" value={`$${eco.implied_revenue_usd.toFixed(2)}`} sub={`at $${eco.credit_price_usd} per credit`} />
            <EcoStat label="Implied margin" value={`$${eco.implied_margin_usd.toFixed(2)}`}
              color={eco.implied_margin_usd >= 0 ? L.ready : L.refused} />
          </div>
          <p style={{ margin: 0, fontSize: 12, lineHeight: 1.6, color: L.dust }}>
            Usage: {Object.entries(eco.usage).filter(([, v]) => v > 0).map(([k, v]) => `${k}: ${v}`).join(" · ") || "none yet this month"}
            <br />{eco.note}
          </p>
        </div>
      )}

      {/* Ledger */}
      <div style={{ ...card, overflow: "hidden" }}>
        <p style={{ margin: 0, padding: "13px 18px", borderBottom: `1px solid ${L.ruleFaint}`, fontSize: 14.5, fontWeight: 650 }}>
          Recent activity
        </p>
        {(ledger ?? []).length === 0 && (
          <p style={{ margin: 0, padding: "20px 18px", fontSize: 13.5, color: L.ash }}>
            No activity yet — every render, refund, and credit grant shows up here.
          </p>
        )}
        {(ledger ?? []).map((entry, i) => (
          <div key={entry.id}
            style={{ padding: "11px 18px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, borderTop: i > 0 ? `1px solid ${L.ruleFaint}` : "none" }}>
            <div style={{ minWidth: 0 }}>
              <p style={{ margin: 0, fontSize: 13.5, color: L.ink, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {entry.description || TYPE_LABELS[entry.type] || entry.type}
              </p>
              <p style={{ margin: "2px 0 0", fontSize: 11.5, color: L.dust }}>
                {entry.created_at ? new Date(entry.created_at).toLocaleString() : ""}
              </p>
            </div>
            <span style={{ flexShrink: 0, fontFamily: mono, fontSize: 13.5, fontWeight: 600, color: entry.amount > 0 ? L.ready : L.ink }}>
              {entry.amount > 0 ? `+${entry.amount}` : entry.amount}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function EcoStat({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div>
      <p style={{ margin: "0 0 3px", fontSize: 11.5, color: L.dust }}>{label}</p>
      <p style={{ margin: 0, fontFamily: mono, fontSize: 19, fontWeight: 700, color: color ?? L.ink }}>{value}</p>
      {sub && <p style={{ margin: "2px 0 0", fontSize: 10.5, color: L.dust }}>{sub}</p>}
    </div>
  )
}
