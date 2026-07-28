"use client"

import { motion } from "framer-motion"
import { signIn } from "next-auth/react"
import Link from "next/link"
import { useState } from "react"
import { Loader2 } from "lucide-react"

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
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-6 relative overflow-hidden font-sans text-zinc-50">
      <div className="absolute top-1/4 -left-1/4 w-1/2 h-1/2 bg-violet-600/20 blur-[100px] rounded-full pointer-events-none" />
      <div className="absolute bottom-1/4 -right-1/4 w-1/2 h-1/2 bg-blue-600/20 blur-[100px] rounded-full pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md p-8 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-xl relative z-10 shadow-2xl"
      >
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center font-bold text-2xl shadow-[0_0_15px_rgba(139,92,246,0.5)] mx-auto mb-4">
            K
          </div>
          <h1 className="text-2xl font-bold mb-2">Sign in to Kliptos</h1>
          <p className="text-zinc-400 text-sm">Automate your YouTube Shorts journey.</p>
        </div>

        <button
          onClick={handleGoogleSignIn}
          disabled={isLoading}
          className="w-full py-4 px-6 rounded-xl bg-white text-zinc-950 font-medium hover:bg-zinc-200 transition-colors flex items-center justify-center gap-3 mb-6 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
          )}
          {isLoading ? "Signing in…" : "Continue with Google"}
        </button>

        <p className="text-center text-sm text-zinc-500">
          By signing in, you agree to our Terms of Service and Privacy Policy.
        </p>

        <div className="mt-8 pt-6 border-t border-white/10 text-center">
          <Link href="/" className="text-sm text-zinc-400 hover:text-white transition-colors">
            &larr; Back to home
          </Link>
        </div>
      </motion.div>
    </div>
  )
}
