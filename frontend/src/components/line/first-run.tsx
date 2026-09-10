"use client"

/**
 * First run — two questions, then out of the way.
 *
 * A new account used to land on an empty dashboard holding three credits
 * with nothing to guide it, and trends for every category at once. So the
 * first thing a gaming creator saw was mostly irrelevant to them.
 *
 * An overlay rather than a /dashboard/onboarding route: it cannot be
 * navigated around, it does not change the URL, and there is no back
 * button to land someone half-way through it.
 *
 * Skipping is a real answer and is remembered. Being asked again on every
 * visit is worse than having no preference, which is why the API stamps
 * onboarded_at even when nothing was chosen.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { MdOutlineArrowForward } from "react-icons/md"
import { fetchApi } from "@/lib/api-client"
import { L, grotesque, mono, alpha } from "@/lib/line/tokens"

interface Me {
  name: string | null
  onboarded_at: string | null
  niche: string | null
  language: string | null
}

export default function FirstRun() {
  const qc = useQueryClient()
  const [niche, setNiche] = useState<string | null>(null)
  const [language, setLanguage] = useState("English")

  const { data: me } = useQuery<Me>({
    queryKey: ["me"], queryFn: () => fetchApi("/auth/me"), staleTime: 60_000,
  })
  const { data: niches } = useQuery<{ items: { key: string; label: string }[] }>({
    queryKey: ["niches"], queryFn: () => fetchApi("/topics/niches"), staleTime: Infinity,
  })
  const { data: voices } = useQuery<{ languages: string[] }>({
    queryKey: ["voices"], queryFn: () => fetchApi("/scripts/voices"), staleTime: Infinity,
  })

  const save = useMutation({
    mutationFn: (body: { niche?: string; language?: string }) =>
      fetchApi("/auth/onboarding", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => {
      // Both: "me" hides this overlay, "topics" refetches under the new niche.
      qc.invalidateQueries({ queryKey: ["me"] })
      qc.invalidateQueries({ queryKey: ["topics"] })
    },
  })

  // Only ever shown to an account that has never answered. Undefined means
  // the query is still loading, and flashing this at someone who HAS
  // onboarded would be worse than showing it a moment late.
  if (!me || me.onboarded_at !== null) return null

  const first = (me.name || "").trim().split(" ")[0]

  return (
    <div role="dialog" aria-modal="true" aria-label="Set up Kliptos"
      style={{
        position: "fixed", inset: 0, zIndex: 100, background: alpha(L.floor, 96),
        display: "flex", alignItems: "center", justifyContent: "center", padding: 24,
        overflowY: "auto", fontFamily: grotesque,
      }}>
      <div style={{ width: "100%", maxWidth: 560, background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 12, padding: 28 }}>
        <p style={{ margin: "0 0 6px", fontFamily: mono, fontSize: 12, color: L.dust }}>
          Two questions · about 10 seconds
        </p>
        <h1 style={{ margin: "0 0 8px", fontSize: 24, fontWeight: 700, letterSpacing: "-0.02em" }}>
          {first ? `Welcome, ${first}.` : "Welcome."} What do you make?
        </h1>
        <p style={{ margin: "0 0 22px", fontSize: 14, lineHeight: 1.55, color: L.ash }}>
          Kliptos watches what&apos;s trending and suggests the format each trend deserves.
          Telling it your niche means the trends you see are yours, not everyone&apos;s.
        </p>

        <div className="grid gap-2 sm:grid-cols-3" style={{ marginBottom: 22 }}>
          {(niches?.items ?? []).map(n => {
            const on = niche === n.key
            return (
              <button key={n.key} onClick={() => setNiche(on ? null : n.key)}
                aria-pressed={on}
                style={{
                  background: on ? L.benchRaised : "transparent",
                  border: `1px solid ${on ? L.make : L.rule}`,
                  color: on ? L.ink : L.ash, fontFamily: grotesque, fontSize: 13.5,
                  fontWeight: on ? 600 : 400, padding: "11px 12px", borderRadius: 8,
                  cursor: "pointer", textAlign: "left",
                }}>
                {n.label}
              </button>
            )
          })}
        </div>

        <div style={{ marginBottom: 24 }}>
          <span style={{ display: "block", marginBottom: 7, fontSize: 12.5, fontWeight: 600, color: L.ash }}>
            What language do you write in?
          </span>
          <select value={language} onChange={e => setLanguage(e.target.value)}
            style={{
              boxSizing: "border-box", width: 240, background: L.floor,
              border: `1px solid ${L.rule}`, borderRadius: 8, color: L.ink,
              fontFamily: grotesque, fontSize: 13.5, padding: "9px 12px", outline: "none",
            }}>
            {(voices?.languages ?? ["English"]).map(l => <option key={l} value={l}>{l}</option>)}
          </select>
          <p style={{ margin: "7px 0 0", fontSize: 12, color: L.dust }}>
            Hindi shorts get Hindi voices and Devanagari captions.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap", borderTop: `1px solid ${L.ruleFaint}`, paddingTop: 18 }}>
          <button
            onClick={() => save.mutate({ ...(niche ? { niche } : {}), language })}
            disabled={save.isPending}
            style={{
              display: "flex", alignItems: "center", gap: 8, background: L.make,
              border: "none", borderRadius: 8, color: "#fff", fontFamily: grotesque,
              fontSize: 14.5, fontWeight: 600, padding: "11px 18px",
              cursor: save.isPending ? "default" : "pointer", opacity: save.isPending ? 0.6 : 1,
            }}>
            {save.isPending ? "Saving…" : "Start creating"} <MdOutlineArrowForward size={17} />
          </button>
          {/* A skip that is remembered, not a dismissal that returns. */}
          <button onClick={() => save.mutate({})} disabled={save.isPending}
            style={{ background: "transparent", border: "none", color: L.dust, fontFamily: grotesque, fontSize: 13, textDecoration: "underline", cursor: "pointer", padding: 0 }}>
            Skip — I&apos;ll explore first
          </button>
          <span style={{ marginLeft: "auto", fontSize: 12, color: L.dust }}>
            You can change both later in Settings.
          </span>
        </div>

        {save.error && (
          <p style={{ margin: "12px 0 0", fontSize: 12.5, color: L.refused }}>
            {(save.error as Error).message}
          </p>
        )}
      </div>
    </div>
  )
}
