import NextAuth from "next-auth"
import Google from "next-auth/providers/google"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"

declare module "next-auth" {
  interface Session {
    backendToken?: string
  }
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [Google],
  session: { strategy: "jwt" },
  pages: {
    signIn: "/sign-in",
  },
  callbacks: {
    async jwt({ token, account }) {
      // On initial sign-in, exchange the Google ID token for a Kliptos API token.
      if (account?.id_token) {
        // The API is on a sleeping free tier: a cold start can take ~50s, so
        // give it room but still fail rather than hang the whole callback.
        let res: Response
        try {
          res = await fetch(`${API_URL}/auth/google`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id_token: account.id_token }),
            signal: AbortSignal.timeout(25_000),
          })
        } catch (cause) {
          // Anything thrown here surfaces as a bare CallbackRouteError, so say
          // which URL was unreachable — that is the whole diagnosis next time.
          throw new Error(`Backend unreachable at ${API_URL}/auth/google`, { cause })
        }
        if (!res.ok) {
          // A 401 here almost always means the backend's GOOGLE_CLIENT_ID does
          // not match this app's AUTH_GOOGLE_ID, so the token's audience fails
          // verification. Include the body; the status alone says nothing.
          const detail = await res.text().catch(() => "")
          throw new Error(
            `Backend token exchange failed: ${res.status} ${detail.slice(0, 200)}`,
          )
        }
        const data = await res.json()
        token.backendToken = data.access_token
      }
      return token
    },
    async session({ session, token }) {
      session.backendToken = token.backendToken as string | undefined
      return session
    },
  },
})
