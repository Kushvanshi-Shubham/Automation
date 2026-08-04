"use client"

/**
 * Analytics — honest version. Output stats are computed from your own
 * library today; channel performance (views, watch time) connects with
 * the YouTube Analytics API after deployment.
 */
import { useQuery } from "@tanstack/react-query"
import { fetchApi } from "@/lib/api-client"
import { L, mono, grotesque } from "@/lib/line/tokens"

interface VideoItem {
  id: string
  status: string
  output_type: string
  created_at: string | null
  published_at: string | null
}

const card: React.CSSProperties = { background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 10 }

export default function AnalyticsPage() {
  const { data } = useQuery<{ items: VideoItem[]; total: number }>({
    queryKey: ["videos-analytics"],
    queryFn: () => fetchApi("/videos?page=1&page_size=100"),
  })

  const videos = data?.items ?? []
  const now = new Date()
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)
  const thisMonth = videos.filter(v => v.created_at && new Date(v.created_at) >= monthStart)
  const live = videos.filter(v => v.status === "published")
  const liveThisMonth = live.filter(v => v.published_at && new Date(v.published_at) >= monthStart)
  const byType = videos.reduce<Record<string, number>>((acc, v) => {
    acc[v.output_type] = (acc[v.output_type] ?? 0) + 1
    return acc
  }, {})
  const typeName: Record<string, string> = {
    narrated: "Narrated shorts", visual: "Visual shorts", image: "Image posts",
    fake_text: "Text convos", clip: "Clips from footage", script: "Scripts only",
  }

  return (
    <div style={{ maxWidth: 860, fontFamily: grotesque, display: "flex", flexDirection: "column", gap: 18, paddingBottom: 24 }}>
      <div>
        <h1 style={{ margin: "0 0 4px", fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>Analytics</h1>
        <p style={{ margin: 0, fontSize: 14, color: L.ash }}>What you have made so far — from your own library.</p>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="Everything made" value={data?.total ?? 0} />
        <StatCard label="Made this month" value={thisMonth.length} />
        <StatCard label="Live on channels" value={live.length} />
        <StatCard label="Published this month" value={liveThisMonth.length} />
      </div>

      {Object.keys(byType).length > 0 && (
        <div style={{ ...card, padding: 18 }}>
          <p style={{ margin: "0 0 12px", fontSize: 14.5, fontWeight: 650 }}>By type</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {Object.entries(byType).sort((a, b) => b[1] - a[1]).map(([type, count]) => {
              const max = Math.max(...Object.values(byType))
              return (
                <div key={type} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span style={{ width: 150, fontSize: 13, color: L.ash, flexShrink: 0 }}>{typeName[type] ?? type}</span>
                  <div style={{ flex: 1, height: 8, background: L.benchRaised, borderRadius: 4, overflow: "hidden" }}>
                    <div style={{ width: `${(count / max) * 100}%`, height: "100%", background: L.make, borderRadius: 4 }} />
                  </div>
                  <span style={{ fontFamily: mono, fontSize: 12.5, color: L.ink, width: 30, textAlign: "right" }}>{count}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      <div style={{ ...card, padding: "16px 18px" }}>
        <p style={{ margin: "0 0 4px", fontSize: 14.5, fontWeight: 650 }}>Channel performance</p>
        <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.6, color: L.ash, maxWidth: "60ch" }}>
          Views, watch time, and subscriber impact per short connect through the YouTube Analytics API —
          that lands with deployment, once the channel connection is verified by Google. Until then,
          YouTube Studio has the numbers for anything you have published.
        </p>
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ ...card, padding: "14px 16px" }}>
      <p style={{ margin: "0 0 4px", fontSize: 12, color: L.dust }}>{label}</p>
      <p style={{ margin: 0, fontFamily: mono, fontSize: 24, fontWeight: 700 }}>{value}</p>
    </div>
  )
}
