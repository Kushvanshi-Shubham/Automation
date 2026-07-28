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
        const res = await fetch(`${API_URL}/auth/google`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id_token: account.id_token }),
        })
        if (!res.ok) {
          throw new Error(`Backend token exchange failed: ${res.status}`)
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
