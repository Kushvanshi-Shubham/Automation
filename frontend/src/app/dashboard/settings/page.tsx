"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { CheckCircle2, KeyRound, Loader2, Trash2, Tv } from "lucide-react"
import { useSearchParams } from "next/navigation"
import { Suspense, useState } from "react"
import { fetchApi } from "@/lib/api-client"

interface Channel {
  id: string
  youtube_channel_id: string | null
  channel_name: string | null
  is_active: boolean | null
  created_at: string | null
}

export default function SettingsPage() {
  return (
    <Suspense fallback={<div className="h-40 rounded-2xl bg-zinc-900/60 backdrop-blur-md border border-white/10 animate-pulse max-w-2xl" />}>
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
    <div className="max-w-2xl space-y-8 pb-12">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-zinc-400 mt-1">Connected accounts and preferences.</p>
      </div>

      {ytConnected && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" /> YouTube channel &quot;{ytConnected}&quot; connected successfully.
        </div>
      )}
      {ytError && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
          YouTube connection failed: {ytError.replaceAll("_", " ")}
        </div>
      )}
      {igConnected && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" /> Instagram &quot;@{igConnected}&quot; connected successfully.
        </div>
      )}
      {igError && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
          Instagram connection failed: {igError.replaceAll("_", " ")}
        </div>
      )}

      <section className="rounded-2xl bg-zinc-900/60 backdrop-blur-md border border-white/10 overflow-hidden">
        <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
              <Tv className="w-5 h-5 text-rose-500" />
            </div>
            <div>
              <h2 className="font-semibold">YouTube Channels</h2>
              <p className="text-xs text-zinc-500">Where your shorts get published</p>
            </div>
          </div>
          <button
            onClick={() => connect.mutate()}
            disabled={connect.isPending}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 text-sm font-medium text-white disabled:opacity-60"
          >
            {connect.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Tv className="w-4 h-4" />}
            Connect Channel
          </button>
        </div>

        <div className="divide-y divide-white/5">
          {isLoading && <div className="p-6 text-sm text-zinc-500">Loading...</div>}
          {!isLoading && (channels ?? []).length === 0 && (
            <div className="p-6 text-sm text-zinc-500">
              No channels connected yet. Connect one to publish directly from Kliptos.
            </div>
          )}
          {(channels ?? []).map(channel => (
            <div key={channel.id} className="px-6 py-4 flex items-center justify-between">
              <div>
                <p className="font-medium text-sm">{channel.channel_name ?? "Unnamed channel"}</p>
                <p className="text-xs text-zinc-500">{channel.youtube_channel_id}</p>
              </div>
              <button
                onClick={() => disconnect.mutate(channel.id)}
                disabled={disconnect.isPending}
                className="p-2 rounded-lg text-zinc-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                title="Disconnect"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
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
    <section className="rounded-2xl bg-zinc-900/60 backdrop-blur-md border border-white/10 overflow-hidden">
      <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-pink-500/10 border border-pink-500/20 flex items-center justify-center text-base">
            📸
          </div>
          <div>
            <h2 className="font-semibold">Instagram Accounts</h2>
            <p className="text-xs text-zinc-500">Publish Reels via the official Instagram API (Business/Creator account required)</p>
          </div>
        </div>
        <button
          onClick={() => connect.mutate()}
          disabled={!status?.enabled || connect.isPending}
          title={!status?.enabled ? "Instagram app not configured yet — coming with deployment" : undefined}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-pink-600 to-rose-600 text-sm font-medium text-white disabled:opacity-40"
        >
          {connect.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : "📸"}
          Connect Instagram
        </button>
      </div>

      <div className="divide-y divide-white/5">
        {!status?.enabled && (
          <div className="p-6 text-sm text-zinc-500">
            Instagram publishing activates once the Meta app is configured (in progress — requires Meta App Review).
          </div>
        )}
        {status?.enabled && (accounts ?? []).length === 0 && (
          <div className="p-6 text-sm text-zinc-500">
            No Instagram account connected. Your IG must be a Business/Creator account linked to a Facebook Page.
          </div>
        )}
        {(accounts ?? []).map(a => (
          <div key={a.id} className="px-6 py-4 flex items-center justify-between">
            <div>
              <p className="font-medium text-sm">@{a.username ?? "unknown"}</p>
              <p className="text-xs text-zinc-500">{a.ig_user_id}</p>
            </div>
            <button
              onClick={() => disconnect.mutate(a.id)}
              disabled={disconnect.isPending}
              className="p-2 rounded-lg text-zinc-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
              title="Disconnect"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </section>
  )
}

const PROVIDERS = [
  { key: "gemini", label: "Gemini", hint: "aistudio.google.com — free tier available" },
  { key: "openai", label: "OpenAI", hint: "platform.openai.com — paid account" },
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
    <section className="rounded-2xl bg-zinc-900/60 backdrop-blur-md border border-white/10 overflow-hidden">
      <div className="px-6 py-4 border-b border-white/5 flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
          <KeyRound className="w-5 h-5 text-violet-400" />
        </div>
        <div>
          <h2 className="font-semibold">Your AI API Keys</h2>
          <p className="text-xs text-zinc-500">
            Bring your own keys — scripts generate on your quota. Keys are encrypted and never shown again.
          </p>
        </div>
      </div>

      <div className="divide-y divide-white/5">
        {PROVIDERS.map(p => {
          const masked = saved.get(p.key)
          return (
            <div key={p.key} className="px-6 py-4">
              <div className="flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <p className="font-medium text-sm">{p.label}</p>
                  <p className="text-xs text-zinc-500">{p.hint}</p>
                </div>

                {masked ? (
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-md">
                      {masked} ✓
                    </span>
                    <button
                      onClick={() => remove.mutate(p.key)}
                      disabled={remove.isPending}
                      className="p-2 rounded-lg text-zinc-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                      title="Remove key"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 flex-1 max-w-sm">
                    <input
                      type="password"
                      value={drafts[p.key] ?? ""}
                      onChange={e => setDrafts(prev => ({ ...prev, [p.key]: e.target.value }))}
                      placeholder={`Paste your ${p.label} key`}
                      className="flex-1 bg-black/20 border border-white/10 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-violet-500/50"
                    />
                    <button
                      onClick={() => { setSavingProvider(p.key); save.mutate({ provider: p.key, key: drafts[p.key] ?? "" }) }}
                      disabled={(drafts[p.key] ?? "").length < 10 || savingProvider === p.key}
                      className="px-4 py-2 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 text-sm font-medium text-white disabled:opacity-50 flex items-center gap-1.5"
                    >
                      {savingProvider === p.key ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                      Save
                    </button>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {save.error && (
        <div className="px-6 pb-4">
          <p className="text-xs text-rose-400">{(save.error as Error).message}</p>
        </div>
      )}
    </section>
  )
}
