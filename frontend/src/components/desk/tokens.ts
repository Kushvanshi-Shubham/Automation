/** Kliptos design system — from the Claude Design handoff (violet/blue on near-black). */
export const T = {
  bg: "#0A0B10",
  panel: "#121419",
  head: "#191C24",
  rule: "#262A35",
  strong: "#343A48",
  text: "#E9EAEF",
  body: "#B0B4C0",
  dim: "#8A8F9E",
  faint: "#5F6472",
  signal: "#9B6BF2",   // violet — primary action
  signalHi: "#B995F7",
  working: "#D9A94E",  // amber — in flight
  ready: "#4FB08A",    // green — awaiting you
  live: "#4F8FF0",     // blue — published
  failed: "#D9566A",   // red — refused
  idle: "#6E7484",
} as const

export const mono = "var(--font-jetbrains), 'JetBrains Mono', monospace"
export const sans = "var(--font-archivo), Archivo, system-ui, sans-serif"

/** Monospace micro-label style used everywhere in the system. */
export const microLabel = (color: string = T.dim, tracking = "0.1em") => ({
  fontFamily: mono,
  fontSize: "10px",
  letterSpacing: tracking,
  color,
}) as React.CSSProperties
