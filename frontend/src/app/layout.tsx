import type { Metadata } from "next"
import { Inter, Geist, Archivo, JetBrains_Mono } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import Providers from "@/components/providers"
import { cn } from "@/lib/utils";

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });

const inter = Inter({ subsets: ["latin"] })

// THE LINE design system: one grotesque for statements, one instrument
// mono for telemetry (docs/design/01-DIRECTION.md §5).
const archivo = Archivo({ subsets: ["latin"], weight: ["400", "600", "700"], variable: "--font-archivo" })
const jetbrains = JetBrains_Mono({ subsets: ["latin"], weight: ["400", "700"], variable: "--font-jetbrains" })

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
    <html lang="en" suppressHydrationWarning className={cn("font-sans", geist.variable, archivo.variable, jetbrains.variable)}>
      {/* suppressHydrationWarning: browser extensions inject attributes into <body> pre-hydration */}
      {/* Background/ink come from the design tokens, not hardcoded zinc — otherwise
          light mode shows black on overscroll and on pages shorter than the viewport. */}
      <body
        suppressHydrationWarning
        className={`${inter.className} min-h-screen antialiased`}
        style={{ background: "var(--k-floor)", color: "var(--k-ink)" }}
      >
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
