"use client"

/**
 * Footage — upload your own long video, the best moments are found for
 * you, one click cuts each into a short. Also feeds Create (scenes can
 * play your footage) and Your styles (teach from reels). Themed.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useRef, useState } from "react"
import {
  MdOutlineContentCut, MdOutlineDeleteOutline, MdOutlineFileUpload, MdOutlineSchedule,
} from "react-icons/md"
import { API_BASE_URL, fetchApi } from "@/lib/api-client"
import { getSession } from "next-auth/react"
import { L, mono, grotesque, alpha } from "@/lib/line/tokens"

interface Highlight {
  start: number
  end: number
  title: string
  reason: string
}

interface AssetItem {
  id: string
  filename: string
  kind: string
  size_bytes: number | null
  duration: number | null
  status: string
  error_message: string | null
  highlights: Highlight[] | null
  created_at: string | null
}

function fmtTime(s: number) {
  const m = Math.floor(s / 60)
  return `${m}:${String(Math.floor(s % 60)).padStart(2, "0")}`
}

const card: React.CSSProperties = { background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 10 }
const label: React.CSSProperties = { fontSize: 12.5, fontWeight: 600, color: L.ash }
const field: React.CSSProperties = {
  boxSizing: "border-box", background: L.floor, border: `1px solid ${L.rule}`,
  borderRadius: 8, color: L.ink, fontFamily: grotesque, fontSize: 13.5, padding: "9px 12px", outline: "none",
}

export default function ClipsPage() {
  const queryClient = useQueryClient()
  const router = useRouter()
  const fileRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [clipError, setClipError] = useState<string | null>(null)
  const [creatingKey, setCreatingKey] = useState<string | null>(null)
  const [captionStyle, setCaptionStyle] = useState("classic")
  const [aspectRatio, setAspectRatio] = useState("9:16")

  const { data: captionStyles } = useQuery<{ items: { key: string; label: string; desc: string }[] }>({
    queryKey: ["caption-styles"],
    queryFn: () => fetchApi("/pipeline/caption-styles"),
    staleTime: Infinity,
  })
  const { data: aspectRatios } = useQuery<{ items: { key: string; label: string }[] }>({
    queryKey: ["aspect-ratios"],
    queryFn: () => fetchApi("/pipeline/aspect-ratios"),
    staleTime: Infinity,
  })

  const createClip = useMutation({
    mutationFn: (p: { assetId: string; h: Highlight }) =>
      fetchApi(`/media-assets/${p.assetId}/clips`, {
        method: "POST",
        body: JSON.stringify({
          start: p.h.start,
          end: p.h.end,
          title: p.h.title,
          caption_style: captionStyle,
          aspect_ratio: aspectRatio,
        }),
      }) as Promise<{ video_id: string; job_id: string }>,
    onMutate: (p) => {
      setClipError(null)
      setCreatingKey(`${p.assetId}:${p.h.start}`)
    },
    onSuccess: (data) => router.push(`/dashboard/preview/${data.video_id}?job=${data.job_id}`),
    onError: (e) => {
      setClipError((e as Error).message)
      setCreatingKey(null)
    },
  })

  const { data: assets, isLoading } = useQuery<AssetItem[]>({
    queryKey: ["media-assets"],
    queryFn: () => fetchApi("/media-assets"),
    refetchInterval: q =>
      (q.state.data ?? []).some(a => ["uploaded", "processing"].includes(a.status)) ? 5000 : false,
  })

  const remove = useMutation({
    mutationFn: (id: string) => fetchApi(`/media-assets/${id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["media-assets"] }),
  })

  const upload = async (file: File) => {
    setUploading(true)
    setUploadError(null)
    try {
      const session = await getSession()
      const form = new FormData()
      form.append("file", file)
      const resp = await fetch(`${API_BASE_URL}/media-assets`, {
        method: "POST",
        headers: { Authorization: `Bearer ${session?.backendToken ?? ""}` },
        body: form,
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err.detail ?? `Upload failed (${resp.status})`)
      }
      queryClient.invalidateQueries({ queryKey: ["media-assets"] })
    } catch (e) {
      setUploadError((e as Error).message)
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ""
    }
  }

  const statusChip = (status: string) => {
    const s = status === "ready" ? { text: "Ready", color: L.ready }
      : status === "failed" ? { text: "Failed", color: L.refused }
      : { text: "Analyzing…", color: L.working }
    return (
      <span style={{ fontSize: 11.5, fontWeight: 600, color: s.color, border: `1px solid ${alpha(s.color, 35)}`, padding: "3px 9px", borderRadius: 5, whiteSpace: "nowrap" }}>
        {s.text}
      </span>
    )
  }

  return (
    <div style={{ maxWidth: 860, fontFamily: grotesque, display: "flex", flexDirection: "column", gap: 18, paddingBottom: 24 }}>
      <div>
        <h1 style={{ margin: "0 0 4px", fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>Footage</h1>
        <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6, color: L.ash, maxWidth: "66ch" }}>
          Upload your podcast, stream or long video — the best moments are found for you, and one click
          cuts each into a captioned short. Your uploads also power{" "}
          <Link href="/dashboard/studio" style={{ color: L.make }}>Create</Link> (scenes can play your
          footage) and <Link href="/dashboard/styles" style={{ color: L.make }}>Your styles</Link>.
          Your footage, your rights.
        </p>
      </div>

      {/* Upload zone */}
      <label style={{ display: "block", cursor: "pointer" }}>
        <input
          ref={fileRef}
          type="file"
          accept=".mp4,.mov,.webm,.mkv,.mp3,.m4a,.wav"
          style={{ display: "none" }}
          onChange={e => e.target.files?.[0] && upload(e.target.files[0])}
        />
        <div style={{
          border: `2px dashed ${uploading ? alpha(L.make, 50) : L.rule}`, borderRadius: 12,
          background: L.bench, padding: "34px 20px", textAlign: "center",
        }}>
          <MdOutlineFileUpload size={30} color={uploading ? L.make : L.dust} style={{ display: "block", margin: "0 auto 8px" }} />
          <p style={{ margin: "0 0 4px", fontSize: 14.5, fontWeight: 600 }}>
            {uploading ? "Uploading…" : "Drop your video here or click to upload"}
          </p>
          <p style={{ margin: 0, fontSize: 12, color: L.dust }}>
            mp4 / mov / webm / mkv / mp3 / m4a / wav · up to 500MB · max 10 uploads
          </p>
        </div>
      </label>
      {uploadError && <p style={{ margin: 0, fontSize: 13, color: L.refused }}>{uploadError}</p>}
      {clipError && <p style={{ margin: 0, fontSize: 13, color: L.refused }}>{clipError}</p>}

      {/* Clip render settings — applied to every "Cut this clip" */}
      <div style={{ ...card, padding: "13px 16px", display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, flex: 1, minWidth: 220 }}>
          <span style={label}>Captions</span>
          <select value={captionStyle} onChange={e => setCaptionStyle(e.target.value)} style={{ ...field, flex: 1 }}>
            {(captionStyles?.items ?? [{ key: "classic", label: "Classic Bold", desc: "" }]).map(s => (
              <option key={s.key} value={s.key}>{s.label}</option>
            ))}
          </select>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={label}>Aspect</span>
          <div style={{ display: "flex", gap: 5 }}>
            {(aspectRatios?.items ?? [{ key: "9:16", label: "Vertical" }]).map(a => (
              <button key={a.key} onClick={() => setAspectRatio(a.key)}
                style={{
                  background: aspectRatio === a.key ? alpha(L.make, 8) : L.floor,
                  border: `1px solid ${aspectRatio === a.key ? alpha(L.make, 45) : L.rule}`,
                  color: L.ink, fontFamily: mono, fontSize: 12, fontWeight: 600,
                  padding: "7px 11px", borderRadius: 7, cursor: "pointer",
                }}>
                {a.key}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Assets */}
      {isLoading && <div style={{ ...card, height: 110, opacity: 0.5 }} />}

      {!isLoading && (assets ?? []).length === 0 && (
        <div style={{ ...card, padding: "28px 26px" }}>
          <h2 style={{ margin: "0 0 6px", fontSize: 16, fontWeight: 600 }}>No footage yet</h2>
          <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.6, color: L.ash, maxWidth: "56ch" }}>
            Upload anything you have the rights to — a podcast episode, a stream VOD, an old long-form
            video. It gets transcribed automatically, the strongest 15–60 second moments are suggested,
            and each one is a single click from becoming a captioned short.
          </p>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {(assets ?? []).map(asset => (
          <div key={asset.id} style={{ ...card, overflow: "hidden" }}>
            <div style={{ padding: "13px 18px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, borderBottom: `1px solid ${L.ruleFaint}` }}>
              <div style={{ minWidth: 0 }}>
                <p style={{ margin: 0, fontSize: 14.5, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{asset.filename}</p>
                <p style={{ margin: "2px 0 0", fontSize: 12, color: L.dust }}>
                  {asset.kind}
                  {asset.duration ? <> · <span style={{ fontFamily: mono }}>{fmtTime(asset.duration)}</span></> : ""}
                  {asset.size_bytes ? <> · <span style={{ fontFamily: mono }}>{(asset.size_bytes / 1024 / 1024).toFixed(1)}MB</span></> : ""}
                </p>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
                {statusChip(asset.status)}
                <button onClick={() => remove.mutate(asset.id)} title="Delete upload"
                  style={{ background: "none", border: "none", color: L.dust, cursor: "pointer", padding: 5 }}>
                  <MdOutlineDeleteOutline size={18} />
                </button>
              </div>
            </div>

            {asset.status === "failed" && (
              <p style={{ margin: 0, padding: "11px 18px", fontSize: 12.5, color: L.refused }}>{asset.error_message}</p>
            )}

            {asset.status === "ready" && (asset.highlights ?? []).length === 0 && (
              <p style={{ margin: 0, padding: "11px 18px", fontSize: 13, color: L.ash }}>
                No strong clip moments found in this file — you can still use it scene-by-scene in Create.
              </p>
            )}

            {(asset.highlights ?? []).map((h, i) => (
              <div key={i} style={{ padding: "11px 18px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, borderTop: i > 0 ? `1px solid ${L.ruleFaint}` : "none" }}>
                <div style={{ minWidth: 0 }}>
                  <p style={{ margin: 0, fontSize: 13.5, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{h.title}</p>
                  <p style={{ margin: "3px 0 0", display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: L.dust }}>
                    <MdOutlineSchedule size={13} />
                    <span style={{ fontFamily: mono }}>{fmtTime(h.start)}–{fmtTime(h.end)}</span>
                    ({Math.round(h.end - h.start)}s) · {h.reason}
                  </p>
                </div>
                <button
                  onClick={() => createClip.mutate({ assetId: asset.id, h })}
                  disabled={asset.kind !== "video" || createClip.isPending}
                  title={asset.kind !== "video" ? "Audio-only uploads can't be clipped yet" : "Render this moment as a captioned short (1 credit)"}
                  style={{
                    display: "flex", alignItems: "center", gap: 6, flexShrink: 0,
                    background: asset.kind !== "video" ? "transparent" : L.make,
                    border: asset.kind !== "video" ? `1px solid ${L.rule}` : "none",
                    color: asset.kind !== "video" ? L.dust : "#fff",
                    fontFamily: grotesque, fontSize: 12.5, fontWeight: 600,
                    padding: "8px 13px", borderRadius: 7,
                    cursor: asset.kind !== "video" || createClip.isPending ? "default" : "pointer",
                    opacity: createClip.isPending && creatingKey !== `${asset.id}:${h.start}` ? 0.55 : 1,
                  }}>
                  <MdOutlineContentCut size={15} />
                  {creatingKey === `${asset.id}:${h.start}` ? "Starting…" : "Cut this clip · 1 credit"}
                </button>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
