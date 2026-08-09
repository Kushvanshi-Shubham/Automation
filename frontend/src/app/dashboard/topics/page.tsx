"use client"

/**
 * Discover — trends with an opinion.
 * Rich cards (the anatomy that worked: title, recommendation + reason,
 * hook, keywords, one clear action) in the new design system, plus a
 * compact list for fast scanning. Light + dark, Material icons.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useRouter } from "next/navigation"
import { useMemo, useState } from "react"
import {
  MdOutlineAutoAwesome, MdOutlineBolt, MdOutlineGridView,
  MdOutlineMovieFilter, MdOutlineRefresh, MdOutlineViewList,
} from "react-icons/md"
import { fetchApi } from "@/lib/api-client"
import { L, mono, grotesque, alpha } from "@/lib/line/tokens"

interface Topic {
  id: string; title: string; source: string | null; category: string | null
  best_format: string | null; format_reason: string | null
  keywords: string[] | null; score: number | null; hook_text: string | null
}
interface Format { key: string; label: string; desc: string; available: boolean; output_type: string }

const card: React.CSSProperties = { background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 10 }

export default function DiscoverPage() {
  const qc = useQueryClient()
  const router = useRouter()
  const [view, setView] = useState<"cards" | "list">("cards")
  const [niche, setNiche] = useState<string | null>(null)
  const [source, setSource] = useState<string>("all")
  const [createAs, setCreateAs] = useState("auto")
  const [creatingId, setCreatingId] = useState<string | null>(null)
  const [region, setRegion] = useState("IN")

  const { data: topicsData, isLoading } = useQuery<{ items: Topic[] }>({
    queryKey: ["topics", niche],
    queryFn: () => fetchApi(niche ? `/topics?category=${niche}` : "/topics"),
    staleTime: 60_000,
  })
  const { data: niches } = useQuery<{ items: { key: string; label: string }[] }>({
    queryKey: ["niches"], queryFn: () => fetchApi("/topics/niches"), staleTime: Infinity,
  })
  const { data: formats } = useQuery<{ items: Format[] }>({
    queryKey: ["formats"], queryFn: () => fetchApi("/scripts/formats"), staleTime: Infinity,
  })
  const fmt = (key: string | null) => formats?.items.find(f => f.key === key)

  const refresh = useMutation({
    mutationFn: (): Promise<{ fetched: number; added: number; errors: Record<string, string>; geo: string }> =>
      fetchApi(`/topics/refresh?geo=${region}`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["topics"] }),
  })
  const { data: regions } = useQuery<{ items: { key: string; label: string }[]; default: string }>({
    queryKey: ["regions"], queryFn: () => fetchApi("/topics/regions"), staleTime: Infinity,
  })

  const create = useMutation({
    mutationFn: (t: Topic) =>
      fetchApi("/scripts/generate", {
        method: "POST",
        body: JSON.stringify(
          createAs === "script"
            ? { topic_id: t.id, output_type: "script" }
            : { topic_id: t.id, format: createAs === "auto" ? (fmt(t.best_format)?.key ?? "viral_story") : createAs }
        ),
      }) as Promise<{ video_id: string }>,
    onSuccess: d => router.push(`/dashboard/studio?video=${d.video_id}`),
    onSettled: () => setCreatingId(null),
  })

  const topics = useMemo(
    () => (topicsData?.items ?? []).filter(t => source === "all" || t.source === source),
    [topicsData, source]
  )
  const maxScore = Math.max(1, ...topics.map(t => t.score ?? 0))
  const nicheLabel = (k: string | null) => (k ? niches?.items.find(n => n.key === k)?.label.replace(/^[^\s]+\s/, "") ?? k : null)
  const doCreate = (t: Topic) => { setCreatingId(t.id); create.mutate(t) }
  const createLabel = (t: Topic) =>
    createAs === "script" ? "Write the script — free"
      : `Create ${createAs === "auto" ? (fmt(t.best_format)?.label ?? "short") : (fmt(createAs)?.label ?? "short")}`

  const pill = (on: boolean): React.CSSProperties => ({
    background: on ? L.benchRaised : "transparent", border: `1px solid ${on ? L.ink : L.rule}`,
    color: on ? L.ink : L.ash, fontFamily: grotesque, fontSize: 12.5, padding: "6px 12px",
    borderRadius: 20, cursor: "pointer", whiteSpace: "nowrap",
  })

  return (
    <div style={{ fontFamily: grotesque }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 20, flexWrap: "wrap", marginBottom: 18 }}>
        <div>
          <h1 style={{ margin: "0 0 4px", fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>Discover</h1>
          <p style={{ margin: 0, fontSize: 14, color: L.ash }}>
            What&apos;s trending right now — and which video format each trend deserves.
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          <select value={createAs} onChange={e => setCreateAs(e.target.value)} title="What gets made when you hit Create"
            style={{ background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 6, color: L.ink, fontFamily: grotesque, fontSize: 13, padding: "8px 10px" }}>
            <option value="auto">Create as: best format (auto)</option>
            {(formats?.items ?? []).filter(f => f.available).map(f => (
              <option key={f.key} value={f.key}>Create as: {f.label}</option>
            ))}
            <option value="script">Create as: script only (free)</option>
          </select>
          <div style={{ display: "flex", border: `1px solid ${L.rule}`, borderRadius: 6, overflow: "hidden" }}>
            {([["cards", MdOutlineGridView, "Cards"], ["list", MdOutlineViewList, "List"]] as const).map(([v, Icon, label]) => (
              <button key={v} onClick={() => setView(v)} aria-pressed={view === v}
                style={{ display: "flex", alignItems: "center", gap: 6, background: view === v ? L.benchRaised : L.bench, border: "none", color: view === v ? L.ink : L.ash, fontFamily: grotesque, fontSize: 13, padding: "8px 12px", cursor: "pointer" }}>
                <Icon size={16} /> {label}
              </button>
            ))}
          </div>
          <select value={region} onChange={e => setRegion(e.target.value)} title="Which country's trends to harvest"
            style={{ background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 6, color: L.ink, fontFamily: grotesque, fontSize: 13, padding: "8px 10px" }}>
            {(regions?.items ?? [{ key: "IN", label: "India" }]).map(r => (
              <option key={r.key} value={r.key}>Trends in: {r.label}</option>
            ))}
          </select>
          <button onClick={() => refresh.mutate()} disabled={refresh.isPending}
            style={{ display: "flex", alignItems: "center", gap: 6, background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 6, color: L.ink, fontFamily: grotesque, fontSize: 13, padding: "8px 12px", cursor: "pointer" }}>
            <MdOutlineRefresh size={16} className={refresh.isPending ? "animate-spin" : ""} />
            {refresh.isPending ? "Harvesting…" : "Refresh"}
          </button>
        </div>
      </div>

      {/* Honest reporting: say WHICH source went quiet instead of silently
          showing half the trends. */}
      {refresh.data && Object.keys(refresh.data.errors ?? {}).length > 0 && (
        <div style={{ border: `1px solid ${alpha(L.working, 30)}`, background: alpha(L.working, 6), borderRadius: 8, padding: "10px 14px", marginBottom: 16, fontSize: 12.5, lineHeight: 1.5, color: L.ash }}>
          {Object.keys(refresh.data.errors).includes("trends")
            ? "Google Trends didn't answer this time (it throttles requests from servers) — these results are from YouTube only. Try Refresh again in a minute."
            : `Some sources went quiet: ${Object.keys(refresh.data.errors).join(", ")}. The rest are shown.`}
        </div>
      )}
      {refresh.data && Object.keys(refresh.data.errors ?? {}).length === 0 && refresh.data.added === 0 && (
        <div style={{ border: `1px solid ${L.rule}`, borderRadius: 8, padding: "10px 14px", marginBottom: 16, fontSize: 12.5, color: L.ash }}>
          Nothing new since the last harvest — the trends below are still current.
        </div>
      )}

      {/* Filters */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 22 }}>
        <button onClick={() => setNiche(null)} style={pill(niche === null)}>All niches</button>
        {(niches?.items ?? []).map(n => (
          <button key={n.key} onClick={() => setNiche(n.key)} style={pill(niche === n.key)}>{n.label.replace(/^[^\s]+\s/, "")}</button>
        ))}
        <span aria-hidden style={{ width: 1, height: 18, background: L.rule, margin: "0 4px" }} />
        {(["all", "trends", "youtube"] as const).map(s => (
          <button key={s} onClick={() => setSource(s)} style={pill(source === s)}>
            {s === "all" ? "All sources" : s === "trends" ? "Google Trends" : "YouTube"}
          </button>
        ))}
      </div>

      {isLoading && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => <div key={i} style={{ ...card, height: 260, opacity: 0.5 }} />)}
        </div>
      )}

      {!isLoading && topics.length === 0 && (
        <div style={{ ...card, padding: "36px 32px", maxWidth: 720 }}>
          <h2 style={{ margin: "0 0 8px", fontSize: 18, fontWeight: 600 }}>No trends harvested yet</h2>
          <p style={{ margin: "0 0 18px", fontSize: 14, lineHeight: 1.6, color: L.ash, maxWidth: "56ch" }}>
            Kliptos reads Google Trends and YouTube for your niches and recommends the right video format for each
            topic. Hit refresh to sweep for what&apos;s moving right now.
          </p>
          <button onClick={() => refresh.mutate()} disabled={refresh.isPending}
            style={{ display: "flex", alignItems: "center", gap: 7, background: L.make, border: "none", color: "#fff", fontFamily: grotesque, fontSize: 13.5, fontWeight: 600, padding: "10px 16px", borderRadius: 6, cursor: "pointer" }}>
            <MdOutlineRefresh size={17} /> {refresh.isPending ? "Harvesting…" : "Harvest trends"}
          </button>
        </div>
      )}

      {/* ============ CARDS — the anatomy that works, in the new skin ============ */}
      {!isLoading && topics.length > 0 && view === "cards" && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {topics.slice(0, 24).map(t => {
            const f = fmt(t.best_format)
            const heat = (t.score ?? 0) / maxScore
            return (
              <div key={t.id} style={{ ...card, display: "flex", flexDirection: "column", padding: "20px 22px", transition: "border-color 120ms" }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = L.ash)}
                onMouseLeave={e => (e.currentTarget.style.borderColor = "var(--k-rule)")}>
                {/* Meta row */}
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, marginBottom: 12 }}>
                  <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.02em", color: t.source === "youtube" ? L.refused : L.live, border: `1px solid ${alpha(t.source === "youtube" ? L.refused : L.live, 30)}`, padding: "3px 8px", borderRadius: 5 }}>
                      {t.source === "youtube" ? "YouTube" : "Google Trends"}
                    </span>
                    {t.category && t.category !== "general" && (
                      <span style={{ fontSize: 11.5, color: L.ash, textTransform: "capitalize" }}>{nicheLabel(t.category)}</span>
                    )}
                  </span>
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ width: 44, height: 4, background: L.ruleFaint, borderRadius: 2, overflow: "hidden" }}>
                      <span style={{ display: "block", width: `${Math.max(heat * 100, 8)}%`, height: "100%", background: L.working }} />
                    </span>
                    <span style={{ fontFamily: mono, fontSize: 11.5, color: L.ash }}>{Math.round(t.score ?? 0)}</span>
                  </span>
                </div>

                {/* Title */}
                <h3 style={{ margin: "0 0 12px", fontSize: 18.5, fontWeight: 650, lineHeight: 1.3, letterSpacing: "-0.01em" }}>{t.title}</h3>

                {/* Recommendation */}
                {f && (
                  <div style={{ border: `1px solid ${alpha(L.make, 25)}`, background: alpha(L.make, 6), borderRadius: 8, padding: "10px 13px", marginBottom: 12 }}>
                    <p style={{ margin: 0, display: "flex", alignItems: "center", gap: 6, fontSize: 12.5, fontWeight: 600, color: L.make }}>
                      <MdOutlineAutoAwesome size={14} /> Best format: {f.label}
                    </p>
                    {t.format_reason && <p style={{ margin: "3px 0 0", fontSize: 12.5, lineHeight: 1.45, color: L.ash }}>{t.format_reason}</p>}
                  </div>
                )}

                {/* Hook */}
                {t.hook_text && (
                  <div style={{ borderLeft: `2px solid ${L.rule}`, paddingLeft: 10, marginBottom: 12 }}>
                    <p style={{ margin: 0, fontSize: 10.5, letterSpacing: "0.04em", color: L.dust, textTransform: "uppercase" }}>Suggested hook</p>
                    <p style={{ margin: "3px 0 0", fontSize: 13, lineHeight: 1.45, fontStyle: "italic", color: L.ash }}>&quot;{t.hook_text}&quot;</p>
                  </div>
                )}

                {/* Keywords */}
                {(t.keywords ?? []).length > 0 && (
                  <p style={{ margin: "0 0 14px", fontSize: 12, color: L.dust, lineHeight: 1.7 }}>
                    {(t.keywords ?? []).slice(0, 5).map(k => `#${k}`).join("  ")}
                  </p>
                )}

                {/* Action */}
                <button onClick={() => doCreate(t)} disabled={create.isPending}
                  style={{ marginTop: "auto", display: "flex", alignItems: "center", justifyContent: "center", gap: 7, width: "100%", background: "transparent", border: `1px solid ${alpha(L.make, 45)}`, color: L.make, fontFamily: grotesque, fontSize: 13.5, fontWeight: 600, padding: "10px 14px", borderRadius: 7, cursor: "pointer", transition: "background 120ms, color 120ms" }}
                  onMouseEnter={e => { e.currentTarget.style.background = L.make; e.currentTarget.style.color = "#fff" }}
                  onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "var(--k-make)" }}>
                  <MdOutlineBolt size={17} />
                  {creatingId === t.id ? "Writing the script…" : createLabel(t)}
                </button>
              </div>
            )
          })}
        </div>
      )}

      {/* ============ LIST ============ */}
      {!isLoading && topics.length > 0 && view === "list" && (
        <div style={{ ...card, overflow: "hidden" }}>
          {topics.slice(0, 30).map((t, i) => {
            const f = fmt(t.best_format)
            return (
              <div key={t.id} className="grid items-center gap-3.5 px-5 py-3.5 sm:grid-cols-[44px_1fr_190px_130px_170px]" style={{ borderTop: i ? `1px solid ${L.ruleFaint}` : "none" }}>
                <span style={{ fontFamily: mono, fontSize: 12, color: i < 3 ? L.working : L.dust }}>{String(i + 1).padStart(2, "0")}</span>
                <span style={{ minWidth: 0 }}>
                  <span style={{ display: "block", fontSize: 14.5, fontWeight: i < 3 ? 600 : 500, color: L.ink, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t.title}</span>
                  {t.format_reason && <span style={{ display: "block", marginTop: 2, fontSize: 12, color: L.dust, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t.format_reason}</span>}
                </span>
                <span className="hidden sm:block" style={{ fontSize: 12.5, color: L.ash, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{f ? f.label : "—"}</span>
                <span className="hidden sm:flex" style={{ alignItems: "center", gap: 8 }}>
                  <span style={{ flex: 1, height: 3, background: L.ruleFaint, borderRadius: 2, overflow: "hidden" }}>
                    <span style={{ display: "block", width: `${Math.max(((t.score ?? 0) / maxScore) * 100, 5)}%`, height: "100%", background: L.working }} />
                  </span>
                  <span style={{ fontFamily: mono, fontSize: 11, color: L.dust }}>{Math.round(t.score ?? 0)}</span>
                </span>
                <button onClick={() => doCreate(t)} disabled={create.isPending}
                  style={{ background: "transparent", border: `1px solid ${alpha(L.make, 45)}`, color: L.make, fontFamily: grotesque, fontSize: 12.5, fontWeight: 600, padding: "8px 12px", borderRadius: 6, cursor: "pointer" }}>
                  {creatingId === t.id ? "Writing…" : "Create"}
                </button>
              </div>
            )
          })}
        </div>
      )}

      {/* Own idea */}
      {!isLoading && topics.length > 0 && (
        <button onClick={() => router.push("/dashboard/studio")}
          style={{ marginTop: 18, display: "flex", alignItems: "center", gap: 7, background: "transparent", border: `1px dashed ${L.rule}`, color: L.ash, fontFamily: grotesque, fontSize: 13, padding: "10px 16px", borderRadius: 8, cursor: "pointer" }}>
          <MdOutlineMovieFilter size={16} /> None of these? Start from your own idea
        </button>
      )}
    </div>
  )
}
