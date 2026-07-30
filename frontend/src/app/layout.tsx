import type { Metadata } from "next"
import { Inter, Geist } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import Providers from "@/components/providers"
import { cn } from "@/lib/utils";

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });

const inter = Inter({ subsets: ["latin"] })

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Kliptos — Turn Trends Into Shorts, Automatically",
    template: "%s · Kliptos",
  },
  description:
    "Kliptos finds trending topics in your niche, writes the script with AI, renders a captioned 9:16 short with voice and music, and publishes it to YouTube — in minutes, not hours.",
  keywords: [
    "AI shorts generator", "faceless YouTube channel", "YouTube Shorts automation",
    "AI video generator", "trending topics", "Reels automation", "AI script writer",
    "content automation", "short form video tool",
  ],
  applicationName: "Kliptos",
  authors: [{ name: "Kliptos" }],
  openGraph: {
    type: "website",
    url: SITE_URL,
    siteName: "Kliptos",
    title: "Kliptos — Turn Trends Into Shorts, Automatically",
    description:
      "Trending topics → AI script → rendered short with captions & music → published to YouTube. Start free.",
    images: [{ url: "/og.png", width: 1200, height: 630, alt: "Kliptos — AI Shorts Automation" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Kliptos — Turn Trends Into Shorts, Automatically",
    description:
      "Trending topics → AI script → rendered short with captions & music → published to YouTube. Start free.",
    images: ["/og.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, "max-video-preview": -1, "max-image-preview": "large" },
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning className={cn("font-sans", geist.variable)}>
      <body className={`${inter.className} bg-zinc-950 text-zinc-50 min-h-screen antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          disableTransitionOnChange
        >
          <Providers>{children}</Providers>
        </ThemeProvider>
      </body>
    </html>
  )
}
