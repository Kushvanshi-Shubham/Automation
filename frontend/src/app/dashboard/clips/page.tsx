"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Clock, Loader2, Scissors, Trash2, UploadCloud } from "lucide-react"
import { useRef, useState } from "react"
import { API_BASE_URL, fetchApi } from "@/lib/api-client"
import { getSession } from "next-auth/react"

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

export default function ClipsPage() {
  const queryClient = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

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

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Clips</h1>
        <p className="text-zinc-400 mt-1">
          Upload your podcast, stream or long video — AI finds the best moments to clip. Your footage, your rights.
        </p>
      </div>

      {/* Upload zone */}
      <label className="block cursor-pointer">
        <input
          ref={fileRef}
          type="file"
          accept=".mp4,.mov,.webm,.mkv,.mp3,.m4a,.wav"
          className="hidden"
          onChange={e => e.target.files?.[0] && upload(e.target.files[0])}
        />
        <div className="rounded-2xl border-2 border-dashed border-white/10 hover:border-violet-500/40 bg-zinc-900/50 p-10 text-center transition-colors">
          {uploading ? (
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
              <p className="text-sm text-zinc-400">Uploading…</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <UploadCloud className="w-8 h-8 text-zinc-500" />
              <p className="font-medium">Drop your video or click to upload</p>
              <p className="text-xs text-zinc-500">mp4 / mov / webm / mkv / mp3 / m4a / wav · up to 500MB · max 10 uploads</p>
            </div>
          )}
        </div>
      </label>
      {uploadError && <p className="text-sm text-rose-400">{uploadError}</p>}

      {/* Assets */}
      {isLoading && <div className="h-28 rounded-2xl bg-zinc-900 border border-white/5 animate-pulse" />}

      <div className="space-y-4">
        {(assets ?? []).map(asset => (
          <div key={asset.id} className="rounded-2xl bg-zinc-900 border border-white/5 overflow-hidden">
            <div className="px-5 py-4 flex items-center justify-between gap-4 border-b border-white/5">
              <div className="min-w-0">
                <p className="font-medium truncate">{asset.filename}</p>
                <p className="text-xs text-zinc-500 mt-0.5">
                  {asset.kind}
                  {asset.duration ? ` · ${fmtTime(asset.duration)}` : ""}
                  {asset.size_bytes ? ` · ${(asset.size_bytes / 1024 / 1024).toFixed(1)}MB` : ""}
                </p>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className={`px-2.5 py-1 rounded-md text-xs font-medium border ${
                  asset.status === "ready"
                    ? "bg-emerald-400/10 text-emerald-400 border-emerald-400/20"
                    : asset.status === "failed"
                      ? "bg-rose-400/10 text-rose-400 border-rose-400/20"
                      : "bg-blue-400/10 text-blue-400 border-blue-400/20"
                }`}>
                  {asset.status === "processing" || asset.status === "uploaded" ? (
                    <span className="flex items-center gap-1.5"><Loader2 className="w-3 h-3 animate-spin" /> Analyzing…</span>
                  ) : asset.status}
                </span>
                <button
                  onClick={() => remove.mutate(asset.id)}
                  className="p-2 rounded-lg text-zinc-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                  title="Delete upload"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {asset.status === "failed" && (
              <p className="px-5 py-3 text-xs text-rose-400">{asset.error_message}</p>
            )}

            {asset.status === "ready" && (asset.highlights ?? []).length === 0 && (
              <p className="px-5 py-3 text-sm text-zinc-500">No strong clip moments found in this file.</p>
            )}

            {(asset.highlights ?? []).map((h, i) => (
              <div key={i} className="px-5 py-3 flex items-center justify-between gap-4 border-t border-white/5">
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{h.title}</p>
                  <p className="text-xs text-zinc-500 mt-0.5 flex items-center gap-2">
                    <Clock className="w-3 h-3" /> {fmtTime(h.start)}–{fmtTime(h.end)} ({Math.round(h.end - h.start)}s)
                    <span className="text-zinc-600">· {h.reason}</span>
                  </p>
                </div>
                <button
                  disabled
                  title="Clip rendering ships next"
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs font-medium text-zinc-500 cursor-not-allowed flex-shrink-0"
                >
                  <Scissors className="w-3.5 h-3.5" /> Create clip (soon)
                </button>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
