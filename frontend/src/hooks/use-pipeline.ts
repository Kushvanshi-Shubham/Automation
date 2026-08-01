"use client"

import { getSession } from "next-auth/react"
import { useEffect, useState } from "react"
import { API_BASE_URL } from "@/lib/api-client"

// ws(s)://host derived from the API URL (strip protocol + trailing /api)
const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws").replace(/\/api\/?$/, "")

export interface PipelineState {
  status: "idle" | "running" | "completed" | "failed"
  stage: string
  progress: number
  error: string | null
  isConnected: boolean
}

export function usePipeline(jobId: string | null) {
  const [state, setState] = useState<PipelineState>({
    status: "idle",
    stage: "initializing",
    progress: 0,
    error: null,
    isConnected: false,
  })

  useEffect(() => {
    if (!jobId) return

    let ws: WebSocket
    let reconnectTimeout: ReturnType<typeof setTimeout>
    let cancelled = false

    const connect = async () => {
      // The progress stream is authenticated: pass the backend token.
      const session = await getSession()
      if (cancelled) return
      const token = session?.backendToken ?? ""
      ws = new WebSocket(`${WS_BASE_URL}/ws/pipeline/${jobId}?token=${encodeURIComponent(token)}`)

      ws.onopen = () => {
        setState((s) => ({ ...s, isConnected: true }))
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setState((s) => ({
            ...s,
            status: data.status || s.status,
            stage: data.stage || s.stage,
            progress: data.progress ?? s.progress,
            error: data.error || s.error,
          }))
        } catch (err) {
          console.error("Failed to parse websocket message", err)
        }
      }

      ws.onclose = () => {
        setState((s) => ({ ...s, isConnected: false }))
        // Auto-reconnect after 3 seconds
        reconnectTimeout = setTimeout(connect, 3000)
      }

      ws.onerror = (error) => {
        console.error("Websocket error", error)
        ws.close()
      }
    }

    connect()

    return () => {
      cancelled = true
      clearTimeout(reconnectTimeout)
      if (ws) ws.close()
    }
  }, [jobId])

  return state
}
