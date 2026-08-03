/**
 * Kliptos design tokens — themed via CSS variables (light + dark values in
 * globals.css). Color = state, never decoration; violet appears only on the
 * object being made / the commit action.
 */
export const L = {
  floor: "var(--k-floor)",
  bench: "var(--k-bench)",
  benchRaised: "var(--k-bench-raised)",
  rule: "var(--k-rule)",
  ruleFaint: "var(--k-rule-faint)",

  ink: "var(--k-ink)",
  ash: "var(--k-ash)",
  dust: "var(--k-dust)",

  make: "var(--k-make)",
  ready: "var(--k-ready)",
  working: "var(--k-working)",
  live: "var(--k-live)",
  refused: "var(--k-refused)",
} as const

export const grotesque = "var(--font-archivo), Archivo, system-ui, sans-serif"
export const mono = "var(--font-jetbrains), 'JetBrains Mono', ui-monospace, monospace"

/** Motion law: entrances only, short; nothing blocks navigation. */
export const MOTION = {
  feedback: 0.12,
  travel: 0.18,
  ease: [0.32, 0.72, 0.24, 1] as [number, number, number, number],
}

/** Instrument label — mono micro-type, reserved for real telemetry. */
export const tele = (color: string = L.ash, ls = "0.1em"): React.CSSProperties => ({
  fontFamily: mono,
  fontSize: 10,
  letterSpacing: ls,
  color,
})

/** Translucent variant of a themed token (CSS var-safe). */
export const alpha = (color: string, pct: number) => `color-mix(in srgb, ${color} ${pct}%, transparent)`
