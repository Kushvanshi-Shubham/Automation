import { getSession } from "next-auth/react"

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers)
  headers.set("Content-Type", "application/json")

  // Client-side: read the backend token from the NextAuth session (httpOnly
  // session cookie holds it; it is never persisted to localStorage).
  if (typeof window !== "undefined") {
    const session = await getSession()
    if (session?.backendToken) {
      headers.set("Authorization", `Bearer ${session.backendToken}`)
    }
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`API Error ${response.status}: ${errorText}`)
  }

  if (response.status === 204) return null
  return response.json()
}
