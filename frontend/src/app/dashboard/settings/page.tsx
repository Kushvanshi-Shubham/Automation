"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { CheckCircle2, Loader2, Trash2, Tv } from "lucide-react"
import { useSearchParams } from "next/navigation"
import { Suspense } from "react"
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
    <Suspense fallback={<div className="h-40 rounded-2xl bg-zinc-900 border border-white/5 animate-pulse max-w-2xl" />}>
      <SettingsContent />
    </Suspense>
  )
}

function SettingsContent() {
  const searchParams = useSearchParams()
  const ytConnected = searchParams.get("yt_connected")
  const ytError = searchParams.get("yt_error")
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

      <section className="rounded-2xl bg-zinc-900 border border-white/5 overflow-hidden">
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
    </div>
  )
}
