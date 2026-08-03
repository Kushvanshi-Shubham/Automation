"use client"

/**
 * Discover — trends with an opinion. Two ways to read the same signals:
 * FIELD: a momentum board — one column per niche, hotter trends sit higher
 *        and heavier; select one and its dossier opens on the right.
 * LIST:  dense ranked rows for fast scanning.
 * Everything the old page did is still here: niche + source filters,
 * harvest, format override, script-only, hooks, keywords.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useRouter } from "next/navigation"
import { useMemo, useState } from "react"
import {
  MdOutlineAutoAwesome, MdOutlineBolt, MdOutlineGridView, MdOutlineMovieFilter,
  MdOutlineRefresh, MdOutlineViewList, MdOutlineWhatshot,
} from "react-icons/md"
import { fetchApi } from "@/lib/api-client"
import { L, mono, grotesque, alpha } from "@/lib/line/tokens"

interface Topic {
  id: string; title: string; source: string | null; category: string | null
  best_format: string | null; format_reason: string | null
  keywords: string[] | null; score: number | null; hook_text: string | null
}
interface Format { key: string; label: string; emoji: string; desc: string; available: boolean; output_type: string }

const FAMILY_COLOR: Record<string, string> = {
  narrated: L.make, visual: L.live, fake_text: L.working, image: L.ready,
}

const card: React.CSSProperties = { background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 8 }
const clamp2: React.CSSProperties = { display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }

export default function DiscoverPage() {
  const qc = useQueryClient()
  const router = useRouter()
  const [view, setView] = useState<"field" | "list">("field")
  const [niche, setNiche] = useState<string | null>(null)
  const [source, setSource] = useState<string>("all")
  const [createAs, setCreateAs] = useState("auto")
  const [selected, setSelected] = useState<Topic | null>(null)
  const [creatingId, setCreatingId] = useState<string | null>(null)

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
    mutationFn: () => fetchApi("/topics/refresh", { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["topics"] }),
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

  const columns = useMemo(() => {
    const by = new Map<string, Topic[]>()
    for (const t of topics) {
      const k = t.category && t.category !== "general" ? t.category : "other"
      if (!by.has(k)) by.set(k, [])
      by.get(k)!.push(t)
    }
    return [...by.entries()]
      .map(([k, list]) => ({ key: k, list: list.sort((a, b) => (b.score ?? 0) - (a.score ?? 0)).slice(0, 8) }))
      .sort((a, b) => (b.list[0]?.score ?? 0) - (a.list[0]?.score ?? 0))
      .slice(0, 6)
  }, [topics])

  const nicheLabel = (k: string) => niches?.items.find(n => n.key === k)?.label.replace(/^[^\s]+\s/, "") ?? (k === "other" ? "Other" : k)
  const doCreate = (t: Topic) => { setCreatingId(t.id); create.mutate(t) }

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
            {([["field", MdOutlineGridView, "Field"], ["list", MdOutlineViewList, "List"]] as const).map(([v, Icon, label]) => (
              <button key={v} onClick={() => setView(v)} aria-pressed={view === v}
                style={{ display: "flex", alignItems: "center", gap: 6, background: view === v ? L.benchRaised : L.bench, border: "none", color: view === v ? L.ink : L.ash, fontFamily: grotesque, fontSize: 13, padding: "8px 12px", cursor: "pointer" }}>
                <Icon size={16} /> {label}
              </button>
            ))}
          </div>
          <button onClick={() => refresh.mutate()} disabled={refresh.isPending}
            style={{ display: "flex", alignItems: "center", gap: 6, background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 6, color: L.ink, fontFamily: grotesque, fontSize: 13, padding: "8px 12px", cursor: "pointer" }}>
            <MdOutlineRefresh size={16} className={refresh.isPending ? "animate-spin" : ""} />
            {refresh.isPending ? "Harvesting…" : "Refresh"}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 20 }}>
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
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12 }}>
          {Array.from({ length: 8 }).map((_, i) => <div key={i} style={{ ...card, height: 120, opacity: 0.5 }} />)}
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

      {/* ================= FIELD ================= */}
      {!isLoading && topics.length > 0 && view === "field" && (
        <div className="grid gap-4 lg:grid-cols-[1fr_340px]" style={{ alignItems: "start" }}>
          <div style={{ display: "grid", gridTemplateColumns: `repeat(${Math.max(Math.min(columns.length, 6), 1)}, 1fr)`, gap: 10 }}>
            {columns.map(col => (
              <div key={col.key} style={{ minWidth: 0 }}>
                <p style={{ margin: "0 0 8px", display: "flex", alignItems: "center", gap: 6, fontSize: 12, fontWeight: 600, color: L.ash, textTransform: "capitalize" }}>
                  <MdOutlineWhatshot size={14} color={L.working} /> {nicheLabel(col.key)}
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {col.list.map((t, i) => {
                    const heat = (t.score ?? 0) / maxScore
                    const famColor = FAMILY_COLOR[fmt(t.best_format)?.output_type ?? ""] ?? L.dust
                    const isSel = selected?.id === t.id
                    return (
                      <button key={t.id} onClick={() => setSelected(t)}
                        style={{
                          ...card,
                          borderColor: isSel ? L.make : alpha(famColor, 30 + Math.round(heat * 30)),
                          borderLeft: `3px solid ${isSel ? L.make : famColor}`,
                          textAlign: "left", cursor: "pointer", width: "100%",
                          padding: i === 0 ? "13px" : "10px 13px",
                          background: isSel ? L.benchRaised : L.bench,
                        }}>
                        <span style={{ ...clamp2, fontSize: i === 0 ? 14.5 : 13, fontWeight: i === 0 ? 600 : 500, lineHeight: 1.35, color: L.ink }}>
                          {t.title}
                        </span>
                        <span style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 6 }}>
                          <span style={{ flex: 1, height: 3, background: L.ruleFaint, borderRadius: 2, overflow: "hidden" }}>
                            <span style={{ display: "block", width: `${Math.max(heat * 100, 6)}%`, height: "100%", background: L.working }} />
                          </span>
                          <span style={{ fontFamily: mono, fontSize: 10, color: L.dust }}>{Math.round(t.score ?? 0)}</span>
                        </span>
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>

          {/* Dossier rail */}
          <aside style={{ ...card, padding: 20, position: "sticky", top: 16 }}>
            {selected ? (
              <>
                <p style={{ margin: "0 0 8px", fontSize: 16.5, fontWeight: 650, lineHeight: 1.35 }}>{selected.title}</p>
                <p style={{ margin: "0 0 14px", fontSize: 12, color: L.dust }}>
                  {selected.source === "youtube" ? "YouTube signal" : "Google Trends signal"}
                  {selected.category && selected.category !== "general" ? ` · ${nicheLabel(selected.category)}` : ""}
                  {" · "}score <span style={{ fontFamily: mono }}>{Math.round(selected.score ?? 0)}</span>
                </p>
                {fmt(selected.best_format) && (
                  <div style={{ border: `1px solid ${alpha(L.make, 30)}`, background: alpha(L.make, 6), borderRadius: 6, padding: "10px 12px", marginBottom: 12 }}>
                    <p style={{ margin: 0, display: "flex", alignItems: "center", gap: 6, fontSize: 12.5, fontWeight: 600, color: L.make }}>
                      <MdOutlineAutoAwesome size={14} /> Best format: {fmt(selected.best_format)!.label}
                    </p>
                    {selected.format_reason && <p style={{ margin: "4px 0 0", fontSize: 12.5, color: L.ash }}>{selected.format_reason}</p>}
                  </div>
                )}
                {selected.hook_text && (
                  <div style={{ borderLeft: `2px solid ${L.rule}`, paddingLeft: 10, marginBottom: 12 }}>
                    <p style={{ margin: 0, fontSize: 11, color: L.dust }}>Suggested hook</p>
                    <p style={{ margin: "2px 0 0", fontSize: 13, fontStyle: "italic", color: L.ash }}>&quot;{selected.hook_text}&quot;</p>
                  </div>
                )}
                {(selected.keywords ?? []).length > 0 && (
                  <p style={{ margin: "0 0 16px", fontSize: 12, color: L.dust }}>
                    {(selected.keywords ?? []).slice(0, 6).map(k => `#${k}`).join("  ")}
                  </p>
                )}
                <button onClick={() => doCreate(selected)} disabled={create.isPending}
                  style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 7, width: "100%", background: L.make, border: "none", color: "#fff", fontFamily: grotesque, fontSize: 14, fontWeight: 600, padding: "11px 16px", borderRadius: 6, cursor: "pointer" }}>
                  <MdOutlineBolt size={18} />
                  {creatingId === selected.id ? "Writing the script…" : createAs === "script" ? "Write the script (free)" : `Create ${createAs === "auto" ? (fmt(selected.best_format)?.label ?? "short") : fmt(createAs)?.label ?? "short"}`}
                </button>
                <p style={{ margin: "10px 0 0", fontSize: 11.5, color: L.dust, textAlign: "center" }}>
                  {createAs === "script" ? "Free · 5 per day" : "The script opens for your edits before anything renders"}
                </p>
              </>
            ) : (
              <>
                <p style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>Pick a trend</p>
                <p style={{ margin: "0 0 14px", fontSize: 13, lineHeight: 1.6, color: L.ash }}>
                  Hotter topics sit higher in each column. Select one to see why it&apos;s moving, the hook we&apos;d
                  open with, and the format it deserves.
                </p>
                <button onClick={() => router.push("/dashboard/studio")}
                  style={{ display: "flex", alignItems: "center", gap: 7, background: "transparent", border: `1px solid ${L.rule}`, color: L.ink, fontFamily: grotesque, fontSize: 13, padding: "9px 14px", borderRadius: 6, cursor: "pointer" }}>
                  <MdOutlineMovieFilter size={16} /> Or start from your own idea
                </button>
              </>
            )}
          </aside>
        </div>
      )}

      {/* ================= LIST ================= */}
      {!isLoading && topics.length > 0 && view === "list" && (
        <div style={{ ...card, overflow: "hidden" }}>
          {topics.slice(0, 30).map((t, i) => {
            const f = fmt(t.best_format)
            return (
              <div key={t.id} className="grid items-center gap-3.5 px-4 py-3 sm:grid-cols-[44px_1fr_190px_130px_150px]" style={{ borderTop: i ? `1px solid ${L.ruleFaint}` : "none" }}>
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
                  style={{ background: i === 0 ? L.make : "transparent", border: i === 0 ? "none" : `1px solid ${L.rule}`, color: i === 0 ? "#fff" : L.ink, fontFamily: grotesque, fontSize: 12.5, fontWeight: 600, padding: "8px 12px", borderRadius: 6, cursor: "pointer" }}>
                  {creatingId === t.id ? "Writing…" : "Create"}
                </button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
