"use client"

/**
 * Sign in / sign up — one door.
 *
 * Google OAuth has no separate registration step: the first sign-in
 * creates the account and grants the free credits. So this page has to
 * speak to BOTH audiences, or a new visitor reads "sign in" as
 * "members only" and leaves.
 */
import { signIn } from "next-auth/react"
import Link from "next/link"
import { useState } from "react"
import { MdOutlineArrowBack, MdOutlineCheck } from "react-icons/md"
import { L, grotesque, mono } from "@/lib/line/tokens"

const INCLUDED = [
  "3 credits to make your first Shorts",
  "5 free scripts every day",
  "Trends, your own script, a link, or your own footage",
]

export default function SignInPage() {
  const [isLoading, setIsLoading] = useState(false)

  const handleGoogleSignIn = async () => {
    setIsLoading(true)
    try {
      await signIn("google", { redirectTo: "/dashboard" })
    } catch {
      setIsLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: "100vh", background: L.floor, color: L.ink, fontFamily: grotesque,
      display: "flex", alignItems: "center", justifyContent: "center", padding: 24,
    }}>
      <div style={{ width: "100%", maxWidth: 420 }}>
        <div style={{ textAlign: "center", marginBottom: 26 }}>
          {/* eslint-disable-next-line @next/next/no-img-element -- small static brand asset */}
          <img src="/brand/kliptos-logo-2k.jpeg" alt="Kliptos"
            style={{ width: 44, height: 44, borderRadius: 11, objectFit: "cover", border: `1px solid ${L.rule}`, margin: "0 auto 14px", display: "block" }} />
          <h1 style={{ margin: "0 0 6px", fontSize: 25, fontWeight: 700, letterSpacing: "-0.02em" }}>
            Create your account
          </h1>
          <p style={{ margin: 0, fontSize: 14, lineHeight: 1.55, color: L.ash }}>
            Continue with Google — if you&apos;ve been here before, the same button signs you in.
          </p>
        </div>

        <div style={{ background: L.bench, border: `1px solid ${L.rule}`, borderRadius: 12, padding: 24 }}>
          <button
            onClick={handleGoogleSignIn}
            disabled={isLoading}
            style={{
              width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: 10,
              background: L.make, border: "none", borderRadius: 9, color: "#fff",
              fontFamily: grotesque, fontSize: 15, fontWeight: 600, padding: "13px 18px",
              cursor: isLoading ? "default" : "pointer", opacity: isLoading ? 0.6 : 1,
            }}>
            {!isLoading && (
              <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden>
                <path fill="#fff" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#fff" opacity=".9" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#fff" opacity=".75" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#fff" opacity=".9" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
            )}
            {isLoading ? "Opening Google…" : "Continue with Google"}
          </button>

          <p style={{ margin: "12px 0 0", fontSize: 12, color: L.dust, textAlign: "center" }}>
            No card needed · <span style={{ fontFamily: mono }}>3</span> free credits to start
          </p>

          <ul style={{ margin: "20px 0 0", padding: "18px 0 0", borderTop: `1px solid ${L.ruleFaint}`, listStyle: "none", display: "flex", flexDirection: "column", gap: 10 }}>
            {INCLUDED.map(item => (
              <li key={item} style={{ display: "flex", alignItems: "flex-start", gap: 9, fontSize: 13.5, lineHeight: 1.5, color: L.ash }}>
                <MdOutlineCheck size={16} color={L.ready} style={{ flexShrink: 0, marginTop: 2 }} />
                {item}
              </li>
            ))}
          </ul>
        </div>

        <p style={{ margin: "16px 0 0", fontSize: 12, lineHeight: 1.6, color: L.dust, textAlign: "center" }}>
          By continuing you agree to our{" "}
          <Link href="/terms" style={{ color: L.ash }}>Terms</Link> and{" "}
          <Link href="/privacy" style={{ color: L.ash }}>Privacy Policy</Link>.
        </p>

        <div style={{ marginTop: 22, textAlign: "center" }}>
          <Link href="/" style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 13, color: L.ash, textDecoration: "none" }}>
            <MdOutlineArrowBack size={15} /> Back to home
          </Link>
        </div>
      </div>
    </div>
  )
}
