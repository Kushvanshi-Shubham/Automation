/**
 * THE LINE — design tokens (docs/design/01-DIRECTION.md §7).
 * The interface is the factory floor. Color = state, never decoration.
 * Violet appears ONLY on the object being made / the commit action.
 */
export const L = {
  floor: "#0B0C0E",
  bench: "#131519",
  benchRaised: "#1A1D22",
  rule: "#2A2E35",
  ruleFaint: "#1E2126",

  ink: "#E8EAED",
  ash: "#8A8F98",
  dust: "#565B64",

  make: "#8B5CF6",     // the object / the commit — nowhere else
  ready: "#3FBF7F",    // awaiting you / live-ok
  working: "#D9A353",  // tungsten — in flight
  live: "#58A6FF",     // on air
  refused: "#D25353",  // the siding
} as const

export const grotesque = "var(--font-archivo), Archivo, system-ui, sans-serif"
export const mono = "var(--font-jetbrains), 'JetBrains Mono', ui-monospace, monospace"

/** Motion law: nothing fades — things travel along the line axis. */
export const MOTION = {
  feedback: 0.12,
  travel: 0.24,
  station: 0.48,
  ease: [0.32, 0.72, 0.24, 1] as [number, number, number, number],
}

/** Instrument label — the mono micro-type used across all telemetry. */
export const tele = (color: string = L.ash, ls = "0.1em"): React.CSSProperties => ({
  fontFamily: mono,
  fontSize: 10,
  letterSpacing: ls,
  color,
})
