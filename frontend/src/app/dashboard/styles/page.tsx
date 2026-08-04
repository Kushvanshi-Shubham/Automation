"use client"

/**
 * Your styles — teach Kliptos a style from your own reference reels.
 * Pick 2+ uploaded reels, name the style, and it becomes a personal
 * format in Create. Plain words, themed, Material icons.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import Link from "next/link"
import { useState } from "react"
import {
  MdOutlineAutoAwesome, MdOutlineCheckBox, MdOutlineCheckBoxOutlineBlank,
  MdOutlineDeleteOutline, MdOutlineMovieFilter, MdOutlineSchool,
} from "react-icons/md"
import { fetchApi } from "@/lib/api-client"
import { L, mono, grotesque, alpha } from "@/lib/line/tokens"

interface AssetItem { id: string; filename: string; kind: string; status: string; duration: number | null }
interface StyleProfile { summary?: string; reels?: number; avg_wps?: number; hooks?: string[] }
interface UserStyle {
  id: string; name: string; status: string; error_message: string | null
  output_type: string; profile: StyleProfile | null; created_at: string | null
}

const card: React.CSSProperties = { background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 10 }
const label: React.CSSProperties = { display: "block", fontSize: 12.5, fontWeight: 600, color: L.ash, marginBottom: 8 }
const field: React.CSSProperties = {
  width: "100%", boxSizing: "border-box", background: L.floor, border: `1px solid ${L.rule}`,
  borderRadius: 8, color: L.ink, fontFamily: grotesque, fontSize: 14, padding: "10px 12px", outline: "none",
}

export default function StylesPage() {
  const queryClient = useQueryClient()
  const [name, setName] = useState("")
  const [outputType, setOutputType] = useState<"narrated" | "visual">("narrated")
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const { data: styleData } = useQuery<{ items: UserStyle[] }>({
    queryKey: ["user-styles"],
    queryFn: () => fetchApi("/styles"),
    refetchInterval: q =>
      (q.state.data?.items ?? []).some(s => s.status === "learning") ? 5000 : false,
  })
  const { data: assetData } = useQuery<AssetItem[]>({
    queryKey: ["media-assets"], queryFn: () => fetchApi("/media-assets"),
  })

  const footage = (assetData ?? []).filter(a => a.kind === "video" && a.status === "ready")
  const styles = styleData?.items ?? []

  const learn = useMutation({
    mutationFn: () => fetchApi("/styles/learn", {
      method: "POST",
      body: JSON.stringify({ name: name.trim(), asset_ids: [...selected], output_type: outputType }),
    }),
    onSuccess: () => {
      setName("")
      setSelected(new Set())
      queryClient.invalidateQueries({ queryKey: ["user-styles"] })
    },
  })
  const remove = useMutation({
    mutationFn: (id: string) => fetchApi(`/styles/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user-styles"] })
      queryClient.invalidateQueries({ queryKey: ["formats"] })
    },
  })

  const toggle = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }
  const canLearn = name.trim().length >= 2 && selected.size >= 2 && !learn.isPending

  return (
    <div style={{ fontFamily: grotesque, maxWidth: 1060 }}>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ margin: "0 0 6px", fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>Your styles</h1>
        <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6, color: L.ash, maxWidth: "68ch" }}>
          Teach Kliptos a style from real videos. Upload 2 or more reference reels on the{" "}
          <Link href="/dashboard/clips" style={{ color: L.make }}>Footage</Link> page (your own copies —
          nothing is scraped), pick them below, and it learns the hook pattern, pacing, vocabulary and
          rhythm. The result shows up in Create as a format of your own.
        </p>
      </div>

      <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,440px)_1fr]">
        {/* Teach form */}
        <div style={{ ...card, padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
          <h2 style={{ margin: 0, display: "flex", alignItems: "center", gap: 8, fontSize: 15, fontWeight: 650 }}>
            <MdOutlineSchool size={18} /> Teach a new style
          </h2>

          <div>
            <span style={label}>Name it</span>
            <input value={name} onChange={e => setName(e.target.value.slice(0, 60))}
              placeholder="e.g. Fast tech-news style" style={field} />
          </div>

          <div>
            <span style={label}>It makes</span>
            <div style={{ display: "flex", gap: 6 }}>
              {([["narrated", "Narrated shorts"], ["visual", "Visual shorts (text + music)"]] as const).map(([k, text]) => (
                <button key={k} onClick={() => setOutputType(k)}
                  style={{
                    background: outputType === k ? alpha(L.make, 8) : L.floor,
                    border: `1px solid ${outputType === k ? alpha(L.make, 45) : L.rule}`,
                    color: L.ink, fontFamily: grotesque, fontSize: 12.5, fontWeight: outputType === k ? 600 : 400,
                    padding: "7px 12px", borderRadius: 7, cursor: "pointer",
                  }}>
                  {text}
                </button>
              ))}
            </div>
          </div>

          <div>
            <span style={label}>Reference reels <span style={{ fontWeight: 400, color: L.dust }}>(pick 2 or more)</span></span>
            {footage.length === 0 ? (
              <p style={{ margin: 0, fontSize: 13, lineHeight: 1.55, color: L.dust }}>
                No analyzed footage yet — upload your reference reels on the{" "}
                <Link href="/dashboard/clips" style={{ color: L.make }}>Footage</Link> page first.
                Each upload is transcribed automatically; come back here once they say ready.
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 4, maxHeight: 260, overflowY: "auto" }}>
                {footage.map(a => {
                  const on = selected.has(a.id)
                  return (
                    <button key={a.id} onClick={() => toggle(a.id)}
                      style={{
                        display: "flex", alignItems: "center", gap: 9, textAlign: "left",
                        background: on ? alpha(L.make, 6) : "transparent",
                        border: `1px solid ${on ? alpha(L.make, 35) : L.ruleFaint}`,
                        borderRadius: 7, padding: "8px 10px", cursor: "pointer",
                        fontFamily: grotesque, fontSize: 13, color: L.ink,
                      }}>
                      {on ? <MdOutlineCheckBox size={17} color={L.make} /> : <MdOutlineCheckBoxOutlineBlank size={17} color={L.dust} />}
                      <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{a.filename}</span>
                      {a.duration != null && <span style={{ fontFamily: mono, fontSize: 11, color: L.dust }}>{Math.round(a.duration)}s</span>}
                    </button>
                  )
                })}
              </div>
            )}
          </div>

          {learn.error && <p style={{ margin: 0, fontSize: 12.5, color: L.refused }}>{(learn.error as Error).message}</p>}

          <button onClick={() => learn.mutate()} disabled={!canLearn}
            style={{
              display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
              background: L.make, border: "none", color: "#fff", fontFamily: grotesque,
              fontSize: 14, fontWeight: 600, padding: "12px 18px", borderRadius: 8,
              cursor: canLearn ? "pointer" : "default", opacity: canLearn ? 1 : 0.55,
            }}>
            <MdOutlineAutoAwesome size={17} />
            {learn.isPending ? "Starting…" : `Learn this style${selected.size >= 2 ? ` from ${selected.size} reels` : ""}`}
          </button>
          <p style={{ margin: "-6px 0 0", fontSize: 11.5, color: L.dust }}>
            Free — it reads the transcripts your uploads already have. Up to 5 styles.
          </p>
        </div>

        {/* Learned styles */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {styles.length === 0 && (
            <div style={{ ...card, padding: "28px 26px" }}>
              <h2 style={{ margin: "0 0 6px", fontSize: 16, fontWeight: 600 }}>Nothing learned yet</h2>
              <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.6, color: L.ash, maxWidth: "52ch" }}>
                Your learned styles will live here. Each one captures how a set of reels hooks,
                paces, and talks — then writes new scripts the same way, on any topic you give it.
              </p>
            </div>
          )}

          {styles.map(s => {
            const chip = s.status === "ready" ? { text: "Ready", color: L.ready }
              : s.status === "failed" ? { text: "Failed", color: L.refused }
              : { text: "Learning…", color: L.working }
            const p = s.profile ?? {}
            return (
              <div key={s.id} style={{ ...card, padding: "16px 18px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                  <h3 style={{ margin: 0, flex: 1, fontSize: 15.5, fontWeight: 650 }}>{s.name}</h3>
                  <span style={{ fontSize: 11.5, fontWeight: 600, color: chip.color, border: `1px solid ${alpha(chip.color, 35)}`, padding: "3px 9px", borderRadius: 5 }}>
                    {chip.text}
                  </span>
                  <button onClick={() => remove.mutate(s.id)} title="Delete this style"
                    style={{ background: "none", border: "none", color: L.dust, cursor: "pointer", padding: 4 }}>
                    <MdOutlineDeleteOutline size={17} />
                  </button>
                </div>

                {s.status === "failed" && s.error_message && (
                  <p style={{ margin: "0 0 8px", fontSize: 12.5, color: L.refused }}>{s.error_message}</p>
                )}
                {s.status === "learning" && (
                  <p style={{ margin: 0, fontSize: 13, color: L.ash }}>
                    Reading the transcripts and pacing of your reels — usually under a minute.
                  </p>
                )}
                {s.status === "ready" && (
                  <>
                    {p.summary && (
                      <p style={{ margin: "0 0 10px", fontSize: 13.5, lineHeight: 1.55, color: L.ash }}>{p.summary}</p>
                    )}
                    <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
                      <span style={{ fontSize: 12, color: L.dust }}>
                        <span style={{ fontFamily: mono, color: L.ink }}>{p.reels ?? "?"}</span> reels
                        {p.avg_wps ? <> · <span style={{ fontFamily: mono, color: L.ink }}>{p.avg_wps}</span> words/sec</> : null}
                        {" · "}{s.output_type === "visual" ? "visual shorts" : "narrated shorts"}
                      </span>
                      <Link href="/dashboard/studio"
                        style={{ display: "flex", alignItems: "center", gap: 6, marginLeft: "auto", fontSize: 12.5, fontWeight: 600, color: L.make, textDecoration: "none" }}>
                        <MdOutlineMovieFilter size={15} /> Use it in Create
                      </Link>
                    </div>
                  </>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
