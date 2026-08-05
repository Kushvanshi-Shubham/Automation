import { getSession } from "next-auth/react"

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"

/** Media files come as local paths (/media/…, dev) or absolute object-storage
 * URLs (prod). Always run video/image URLs through this. */
export function mediaUrl(pathOrUrl: string): string {
  if (/^https?:\/\//.test(pathOrUrl)) return pathOrUrl
  return `${API_BASE_URL.replace(/\/api\/?$/, "")}${pathOrUrl}`
}

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
    // The API writes plain-English `detail` messages — show those, not
    // "API Error 409: {json}". Fall back to a human line per status.
    const raw = await response.text()
    let message = ""
    try {
      const parsed = JSON.parse(raw)
      const detail = parsed?.detail
      message = typeof detail === "string" ? detail
        : Array.isArray(detail) ? (detail[0]?.msg ?? "")  // pydantic validation
        : ""
    } catch {
      message = raw.slice(0, 200)
    }
    if (!message) {
      message = response.status === 401 ? "Your session expired — sign in again."
        : response.status === 402 ? "You don't have enough credits for that."
        : response.status === 404 ? "That item no longer exists."
        : response.status === 409 ? "That's already in progress."
        : response.status === 429 ? "Slow down a moment and try again."
        : response.status >= 500 ? "Something broke on our side. Try again in a moment."
        : `Request failed (${response.status}).`
    }
    throw new Error(message)
  }

  if (response.status === 204) return null
  return response.json()
}
