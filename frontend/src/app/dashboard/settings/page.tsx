"use client"

/**
 * Settings — connected accounts and your own API keys. Themed, Material
 * icons, plain words. All connect/disconnect flows unchanged.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useSearchParams } from "next/navigation"
import { Suspense, useState } from "react"
import {
  MdOutlineCheckCircle, MdOutlineDeleteOutline, MdOutlineErrorOutline,
  MdOutlineKey, MdOutlineLiveTv, MdOutlinePhotoCamera,
} from "react-icons/md"
import { fetchApi } from "@/lib/api-client"
import { L, mono, grotesque, alpha } from "@/lib/line/tokens"

interface Channel {
  id: string
  youtube_channel_id: string | null
  channel_name: string | null
  is_active: boolean | null
  created_at: string | null
}

const card: React.CSSProperties = { background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 10 }
const sectionHead: React.CSSProperties = {
  padding: "14px 18px", borderBottom: `1px solid ${L.ruleFaint}`, display: "flex",
  alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap",
}
const rowStyle: React.CSSProperties = {
  padding: "13px 18px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12,
}
const primaryBtn = (disabled = false): React.CSSProperties => ({
  display: "flex", alignItems: "center", gap: 7, background: L.make, border: "none", color: "#fff",
  fontFamily: grotesque, fontSize: 13, fontWeight: 600, padding: "9px 14px", borderRadius: 8,
  cursor: disabled ? "default" : "pointer", opacity: disabled ? 0.5 : 1,
})
const trashBtn: React.CSSProperties = {
  background: "none", border: "none", color: "var(--k-dust)", cursor: "pointer", padding: 6, borderRadius: 6,
}
const banner = (color: string): React.CSSProperties => ({
  border: `1px solid ${alpha(color, 30)}`, background: alpha(color, 7), borderRadius: 8,
  padding: "11px 14px", fontSize: 13.5, color: L.ink, display: "flex", alignItems: "center", gap: 8,
})

export default function SettingsPage() {
  return (
    <Suspense fallback={<div style={{ ...card, height: 160, maxWidth: 720, opacity: 0.5 }} />}>
      <SettingsContent />
    </Suspense>
  )
}

function SettingsContent() {
  const searchParams = useSearchParams()
  const ytConnected = searchParams.get("yt_connected")
  const ytError = searchParams.get("yt_error")
  const igConnected = searchParams.get("ig_connected")
  const igError = searchParams.get("ig_error")
  const queryClient = useQueryClient()

  const { data: channels, isLoading } = useQuery<Channel[]>({
    queryKey: ["channels"],
    queryFn: () => fetchApi("/channels"),
  })

  const connect = useMutation({
    mutationFn: () => fetchApi("/channels/connect"),
    onSuccess: (data: { auth_url: string }) => {
      window.location.href = data.auth_url
    },
  })

  const disconnect = useMutation({
    mutationFn: (channelId: string) => fetchApi(`/channels/${channelId}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["channels"] }),
  })

  return (
    <div style={{ maxWidth: 720, fontFamily: grotesque, display: "flex", flexDirection: "column", gap: 18, paddingBottom: 24 }}>
      <div>
        <h1 style={{ margin: "0 0 4px", fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>Settings</h1>
        <p style={{ margin: 0, fontSize: 14, color: L.ash }}>Connected accounts and your own API keys.</p>
      </div>

      {ytConnected && (
        <div style={banner(L.ready)}>
          <MdOutlineCheckCircle size={17} color={L.ready} /> YouTube channel &quot;{ytConnected}&quot; connected.
        </div>
      )}
      {ytError && (
        <div style={banner(L.refused)}>
          <MdOutlineErrorOutline size={17} color={L.refused} /> YouTube connection failed: {ytError.replaceAll("_", " ")}
        </div>
      )}
      {igConnected && (
        <div style={banner(L.ready)}>
          <MdOutlineCheckCircle size={17} color={L.ready} /> Instagram @{igConnected} connected.
        </div>
      )}
      {igError && (
        <div style={banner(L.refused)}>
          <MdOutlineErrorOutline size={17} color={L.refused} /> Instagram connection failed: {igError.replaceAll("_", " ")}
        </div>
      )}

      {/* YouTube */}
      <section style={{ ...card, overflow: "hidden" }}>
        <div style={sectionHead}>
          <div>
            <h2 style={{ margin: 0, display: "flex", alignItems: "center", gap: 8, fontSize: 15, fontWeight: 650 }}>
              <MdOutlineLiveTv size={18} color={L.refused} /> YouTube channels
            </h2>
            <p style={{ margin: "3px 0 0", fontSize: 12.5, color: L.dust }}>Where your shorts get published</p>
          </div>
          <button onClick={() => connect.mutate()} disabled={connect.isPending} style={primaryBtn(connect.isPending)}>
            {connect.isPending ? "Opening…" : "Connect a channel"}
          </button>
        </div>
        {isLoading && <div style={{ ...rowStyle, fontSize: 13, color: L.dust }}>Loading…</div>}
        {!isLoading && (channels ?? []).length === 0 && (
          <div style={{ ...rowStyle, fontSize: 13, lineHeight: 1.5, color: L.ash }}>
            No channel connected yet — connect one and finished shorts publish straight from the preview page.
          </div>
        )}
        {(channels ?? []).map(channel => (
          <div key={channel.id} style={{ ...rowStyle, borderTop: `1px solid ${L.ruleFaint}` }}>
            <div style={{ minWidth: 0 }}>
              <p style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>{channel.channel_name ?? "Unnamed channel"}</p>
              <p style={{ margin: "2px 0 0", fontFamily: mono, fontSize: 11.5, color: L.dust }}>{channel.youtube_channel_id}</p>
            </div>
            <button onClick={() => disconnect.mutate(channel.id)} disabled={disconnect.isPending}
              title="Disconnect" style={trashBtn}>
              <MdOutlineDeleteOutline size={18} />
            </button>
          </div>
        ))}
      </section>

      <InstagramSection />

      <ApiKeysSection />
    </div>
  )
}

interface IgAccount {
  id: string
  ig_user_id: string
  username: string | null
  is_active: boolean | null
}

function InstagramSection() {
  const queryClient = useQueryClient()
  const { data: status } = useQuery<{ enabled: boolean }>({
    queryKey: ["ig-status"],
    queryFn: () => fetchApi("/instagram/status"),
    staleTime: Infinity,
  })
  const { data: accounts } = useQuery<IgAccount[]>({
    queryKey: ["ig-accounts"],
    queryFn: () => fetchApi("/instagram"),
    enabled: status?.enabled === true,
  })

  const connect = useMutation({
    mutationFn: () => fetchApi("/instagram/connect"),
    onSuccess: (data: { auth_url: string }) => { window.location.href = data.auth_url },
  })
  const disconnect = useMutation({
    mutationFn: (id: string) => fetchApi(`/instagram/${id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ig-accounts"] }),
  })

  return (
    <section style={{ ...card, overflow: "hidden" }}>
      <div style={sectionHead}>
        <div>
          <h2 style={{ margin: 0, display: "flex", alignItems: "center", gap: 8, fontSize: 15, fontWeight: 650 }}>
            <MdOutlinePhotoCamera size={18} color={L.live} /> Instagram accounts
          </h2>
          <p style={{ margin: "3px 0 0", fontSize: 12.5, color: L.dust }}>
            Publish Reels via the official Instagram API (Business or Creator account required)
          </p>
        </div>
        <button onClick={() => connect.mutate()} disabled={!status?.enabled || connect.isPending}
          title={!status?.enabled ? "Instagram app not configured yet — coming with deployment" : undefined}
          style={primaryBtn(!status?.enabled || connect.isPending)}>
          {connect.isPending ? "Opening…" : "Connect Instagram"}
        </button>
      </div>
      {!status?.enabled && (
        <div style={{ ...rowStyle, fontSize: 13, lineHeight: 1.5, color: L.ash }}>
          Instagram publishing switches on once the Meta app is configured (in progress — needs Meta App Review).
        </div>
      )}
      {status?.enabled && (accounts ?? []).length === 0 && (
        <div style={{ ...rowStyle, fontSize: 13, lineHeight: 1.5, color: L.ash }}>
          No Instagram account connected. Your account must be Business or Creator, linked to a Facebook Page.
        </div>
      )}
      {(accounts ?? []).map(a => (
        <div key={a.id} style={{ ...rowStyle, borderTop: `1px solid ${L.ruleFaint}` }}>
          <div style={{ minWidth: 0 }}>
            <p style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>@{a.username ?? "unknown"}</p>
            <p style={{ margin: "2px 0 0", fontFamily: mono, fontSize: 11.5, color: L.dust }}>{a.ig_user_id}</p>
          </div>
          <button onClick={() => disconnect.mutate(a.id)} disabled={disconnect.isPending}
            title="Disconnect" style={trashBtn}>
            <MdOutlineDeleteOutline size={18} />
          </button>
        </div>
      ))}
    </section>
  )
}

const PROVIDERS = [
  { key: "gemini", label: "Gemini", hint: "aistudio.google.com — free tier available" },
  { key: "openai", label: "OpenAI", hint: "platform.openai.com — paid account" },
  { key: "huggingface", label: "Hugging Face", hint: "huggingface.co/settings/tokens — open models (Llama & more)" },
  { key: "heygen", label: "HeyGen", hint: "app.heygen.com — for the AI presenter (your avatar & voice), coming soon" },
  { key: "cartesia", label: "Cartesia", hint: "cartesia.ai — studio-grade voices incl. Hindi; your key means no extra credits" },
  { key: "elevenlabs", label: "ElevenLabs", hint: "elevenlabs.io — studio-grade voices and voice cloning (key starts with sk_)" },
]

function ApiKeysSection() {
  const queryClient = useQueryClient()
  const { data } = useQuery<{ items: { provider: string; masked: string }[] }>({
    queryKey: ["api-keys"],
    queryFn: () => fetchApi("/settings/api-keys"),
  })
  const [drafts, setDrafts] = useState<Record<string, string>>({})
  const [savingProvider, setSavingProvider] = useState<string | null>(null)

  const save = useMutation({
    mutationFn: ({ provider, key }: { provider: string; key: string }) =>
      fetchApi("/settings/api-keys", { method: "PUT", body: JSON.stringify({ provider, key }) }),
    onSuccess: (_d, vars) => {
      setDrafts(prev => ({ ...prev, [vars.provider]: "" }))
      queryClient.invalidateQueries({ queryKey: ["api-keys"] })
      queryClient.invalidateQueries({ queryKey: ["llm-models"] })
    },
    onSettled: () => setSavingProvider(null),
  })

  const remove = useMutation({
    mutationFn: (provider: string) => fetchApi(`/settings/api-keys/${provider}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] })
      queryClient.invalidateQueries({ queryKey: ["llm-models"] })
    },
  })

  const saved = new Map((data?.items ?? []).map(i => [i.provider, i.masked]))

  return (
    <section style={{ ...card, overflow: "hidden" }}>
      <div style={{ ...sectionHead, justifyContent: "flex-start" }}>
        <div>
          <h2 style={{ margin: 0, display: "flex", alignItems: "center", gap: 8, fontSize: 15, fontWeight: 650 }}>
            <MdOutlineKey size={18} color={L.make} /> Your API keys
          </h2>
          <p style={{ margin: "3px 0 0", fontSize: 12.5, color: L.dust }}>
            Bring your own keys — scripts generate on your quota. Keys are encrypted and never shown again.
          </p>
        </div>
      </div>

      {PROVIDERS.map(p => {
        const masked = saved.get(p.key)
        return (
          <div key={p.key} style={{ ...rowStyle, borderTop: `1px solid ${L.ruleFaint}`, flexWrap: "wrap" }}>
            <div style={{ minWidth: 160 }}>
              <p style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>{p.label}</p>
              <p style={{ margin: "2px 0 0", fontSize: 12, color: L.dust }}>{p.hint}</p>
            </div>

            {masked ? (
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontFamily: mono, fontSize: 11.5, color: L.ready, border: `1px solid ${alpha(L.ready, 30)}`, padding: "4px 10px", borderRadius: 6 }}>
                  {masked}
                </span>
                <button onClick={() => remove.mutate(p.key)} disabled={remove.isPending}
                  title="Remove key" style={trashBtn}>
                  <MdOutlineDeleteOutline size={18} />
                </button>
              </div>
            ) : (
              <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1, maxWidth: 380 }}>
                <input
                  type="password"
                  value={drafts[p.key] ?? ""}
                  onChange={e => setDrafts(prev => ({ ...prev, [p.key]: e.target.value }))}
                  placeholder={`Paste your ${p.label} key`}
                  style={{
                    flex: 1, boxSizing: "border-box", background: L.floor, border: `1px solid ${L.rule}`,
                    borderRadius: 8, color: L.ink, fontFamily: mono, fontSize: 13, padding: "9px 12px", outline: "none",
                  }}
                />
                <button
                  onClick={() => { setSavingProvider(p.key); save.mutate({ provider: p.key, key: drafts[p.key] ?? "" }) }}
                  disabled={(drafts[p.key] ?? "").length < 10 || savingProvider === p.key}
                  style={primaryBtn((drafts[p.key] ?? "").length < 10 || savingProvider === p.key)}>
                  {savingProvider === p.key ? "Checking…" : "Save"}
                </button>
              </div>
            )}
          </div>
        )
      })}

      {save.error && (
        <p style={{ margin: 0, padding: "0 18px 14px", fontSize: 12.5, color: L.refused }}>
          {(save.error as Error).message}
        </p>
      )}
    </section>
  )
}
