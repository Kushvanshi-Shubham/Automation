/**
 * THE LINE — stencil pictograms. One style only: 1.5px technical line,
 * square caps, miter joints — drawn like equipment markings on a factory
 * floor. No emoji anywhere in chrome (design law).
 */

type P = { size?: number; color?: string; className?: string }

function Stencil({ size = 16, color = "currentColor", className, children }: P & { children: React.ReactNode }) {
  return (
    <svg
      width={size} height={size} viewBox="0 0 16 16" fill="none" className={className}
      stroke={color} strokeWidth="1.5" strokeLinecap="square" strokeLinejoin="miter" aria-hidden
    >
      {children}
    </svg>
  )
}

/** ① SIGNAL — a blip on the scope: ranging ticks + contact. */
export const StSignal = (p: P) => (
  <Stencil {...p}>
    <circle cx="8" cy="8" r="6.2" strokeDasharray="2.4 3.2" />
    <circle cx="9.5" cy="6.5" r="1.6" fill="currentColor" stroke="none" />
  </Stencil>
)

/** ② DESK — the script bench: surface and legs. */
export const StDesk = (p: P) => (
  <Stencil {...p}>
    <path d="M1.5 6.5h13" />
    <path d="M3.5 6.5v6M12.5 6.5v6" />
    <path d="M5.5 3.5h5" />
  </Stencil>
)

/** ③ STAGE — a film frame on the light table. */
export const StStage = (p: P) => (
  <Stencil {...p}>
    <rect x="2.5" y="3.5" width="11" height="9" />
    <path d="M5 3.5v9M11 3.5v9" strokeWidth="1" />
  </Stencil>
)

/** ④ RAIL — a reel at the gate. */
export const StRail = (p: P) => (
  <Stencil {...p}>
    <path d="M1.5 12.5h13" />
    <circle cx="8" cy="7.5" r="3.6" />
    <circle cx="8" cy="7.5" r="0.9" fill="currentColor" stroke="none" />
    <path d="M3 12.5v2M13 12.5v2" strokeWidth="1" />
  </Stencil>
)

/** ⑤ AIR — the mast, transmitting. */
export const StAir = (p: P) => (
  <Stencil {...p}>
    <path d="M8 14V6" />
    <path d="M5 14h6" />
    <path d="M4.5 4.5a5 5 0 0 1 7 0" strokeWidth="1.2" />
    <path d="M2.8 2.8a7.4 7.4 0 0 1 10.4 0" strokeWidth="1.2" />
    <circle cx="8" cy="6" r="1.1" fill="currentColor" stroke="none" />
  </Stencil>
)

/** VAULT — the footage drawer. */
export const StVault = (p: P) => (
  <Stencil {...p}>
    <rect x="2.5" y="2.5" width="11" height="11" />
    <path d="M2.5 7.5h11" />
    <path d="M6.5 5h3M6.5 10.5h3" strokeWidth="1.2" />
  </Stencil>
)

/** CONSOLE — service toggles. */
export const StConsole = (p: P) => (
  <Stencil {...p}>
    <path d="M3.5 2.5v11M8 2.5v11M12.5 2.5v11" strokeWidth="1.2" />
    <rect x="2" y="8.5" width="3" height="2.6" fill="currentColor" stroke="none" />
    <rect x="6.5" y="4" width="3" height="2.6" fill="currentColor" stroke="none" />
    <rect x="11" y="10" width="3" height="2.6" fill="currentColor" stroke="none" />
  </Stencil>
)

/** The reel — the object being made. */
export const StReel = (p: P) => (
  <Stencil {...p}>
    <circle cx="8" cy="8" r="5.6" />
    <circle cx="8" cy="8" r="1" fill="currentColor" stroke="none" />
    <path d="M8 2.4v2.2M8 11.4v2.2M2.4 8h2.2M11.4 8h2.2" strokeWidth="1.2" />
  </Stencil>
)

/** The siding — refused work, shunted with its refund. */
export const StSiding = (p: P) => (
  <Stencil {...p}>
    <path d="M1.5 5.5h8" />
    <path d="M6 5.5l6 6h2.5" />
    <path d="M11 3l3 3-3 3" strokeWidth="0" fill="none" />
  </Stencil>
)

/** Numeral stamp — painted-floor station number. */
export function StationNumeral({ n, size = 120, color }: { n: number; size?: number; color: string }) {
  return (
    <span
      aria-hidden
      style={{
        fontFamily: "var(--font-archivo), Archivo, sans-serif",
        fontWeight: 700,
        fontSize: size,
        lineHeight: 1,
        color: "transparent",
        WebkitTextStroke: `1.5px ${color}`,
        letterSpacing: "-0.04em",
        userSelect: "none",
      }}
    >
      {"0" + n}
    </span>
  )
}
