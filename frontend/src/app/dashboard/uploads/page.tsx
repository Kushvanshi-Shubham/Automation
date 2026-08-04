"use client"

/**
 * Publish list — everything published, scheduled, or on its way out.
 * Themed; polling and statuses unchanged.
 */
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { MdOutlineOpenInNew } from "react-icons/md"
import { fetchApi } from "@/lib/api-client"
import { L, grotesque, alpha } from "@/lib/line/tokens"

interface UploadVideo {
  id: string
  status: string
  title: string | null
  scheduled_at: string | null
  published_at: string | null
  created_at: string | null
}

const STATUS: Record<string, { label: string; color: string }> = {
  published: { label: "Live on your channel", color: L.live },
  scheduled: { label: "Scheduled", color: L.working },
  publishing: { label: "Uploading…", color: L.working },
  upload_failed: { label: "Upload failed", color: L.refused },
}

const card: React.CSSProperties = { background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 10 }

export default function UploadsPage() {
  const { data, isLoading } = useQuery<UploadVideo[]>({
    queryKey: ["uploads"],
    queryFn: () => fetchApi("/uploads"),
    refetchInterval: q => (q.state.data ?? []).some(v => v.status === "publishing") ? 5000 : false,
  })

  const uploads = data ?? []

  return (
    <div style={{ maxWidth: 860, fontFamily: grotesque, display: "flex", flexDirection: "column", gap: 18, paddingBottom: 24 }}>
      <div>
        <h1 style={{ margin: "0 0 4px", fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>Publish list</h1>
        <p style={{ margin: 0, fontSize: 14, color: L.ash }}>Everything published, scheduled, or on its way to a platform.</p>
      </div>

      {isLoading && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {Array.from({ length: 3 }).map((_, i) => <div key={i} style={{ ...card, height: 70, opacity: 0.5 }} />)}
        </div>
      )}

      {!isLoading && uploads.length === 0 && (
        <div style={{ ...card, padding: "30px 26px", maxWidth: 640 }}>
          <h3 style={{ margin: "0 0 6px", fontSize: 16, fontWeight: 600 }}>Nothing published yet</h3>
          <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.6, color: L.ash, maxWidth: "52ch" }}>
            When a finished short goes to YouTube or Instagram — now or on a schedule — it shows up
            here with its live status. Render one and hit Publish on the preview page.
          </p>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {uploads.map(video => {
          const st = STATUS[video.status] ?? STATUS.publishing
          return (
            <div key={video.id} style={{ ...card, padding: "14px 18px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
              <div style={{ minWidth: 0 }}>
                <p style={{ margin: 0, fontSize: 14.5, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {video.title ?? "Untitled short"}
                </p>
                <p style={{ margin: "3px 0 0", fontSize: 12, color: L.dust }}>
                  {video.status === "scheduled" && video.scheduled_at
                    ? `Goes public ${new Date(video.scheduled_at).toLocaleString()}`
                    : video.published_at
                      ? `Published ${new Date(video.published_at).toLocaleString()}`
                      : ""}
                </p>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexShrink: 0 }}>
                <span style={{ fontSize: 11.5, fontWeight: 600, color: st.color, border: `1px solid ${alpha(st.color, 35)}`, padding: "3px 9px", borderRadius: 5, whiteSpace: "nowrap" }}>
                  {st.label}
                </span>
                <Link href={`/dashboard/preview/${video.id}`} title="Open preview"
                  style={{ display: "flex", color: L.dust, padding: 5 }}>
                  <MdOutlineOpenInNew size={17} />
                </Link>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
