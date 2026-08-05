# Pricing

## Plans
| Plan | US | India | Credits/mo | What it actually gives |
|:---|:---|:---|:---|:---|
| Free | $0 | ₹0 | 3 | 720p, **watermark**, 45s max, stock footage + edge-tts, 5 free scripts/day, no publishing (download & post yourself) |
| Pro | $19 | ₹499 | 50 | **No watermark**, 1080p, 3-min shorts, publish + schedule, standing orders, teach-a-style, your footage in scenes, brand kit, priority queue, BYO keys |
| Studio | $49 | ₹1,299 | 150 | Everything in Pro + premium AI engines unlocked, multiple channels, bulk queue |
| Top-up | $5/10cr | ₹149/10cr | — | Prepaid balance for heavy months |

India is deliberate regional pricing (~⅓ of US, Decision #10), **not** a currency conversion — the landing page says so explicitly.

Enforced by `app/services/plans.py`; the paywall is off until billing ships (`PLAN_ENFORCEMENT_ENABLED=false`), so beta users are served Pro-level features and admins always get Studio.

## Why Pro is worth paying for
Seven of Pro's upgrades cost us **nothing** to serve — no watermark, 1080p, longer videos, brand kit, priority queue, publishing, autopilot. That's the margin engine: the perceived jump is large, the marginal cost is zero. The expensive upgrades (premium voice, AI B-roll, avatars) are metered in credits instead of bundled.

## Credit costs come from real cost, not vibes
`app/services/credits.py`: `credits = ceil(real_cost_usd × MARGIN ÷ CREDIT_PRICE_USD)`, MARGIN = 2.0, floor 1.

| Engine | Real cost | Credits | Note |
|:---|:---|:---|:---|
| Stock footage + edge-tts (narrated/visual/clip) | ~$0.002 | 1 | script tokens + ~3 min CPU + R2 storage |
| AI images (≈6 slides, Gemini) | ~$0.20 | 4 | was mispriced at 2 |
| Premium voice (ElevenLabs/Cartesia, 60s) | ~$0.15 | 3 | not wired yet |
| HeyGen avatar (60s) | ~$0.50 | 10 | scaffold shipped, needs owner's key |
| Veo Fast 60s | ~$8.50 | 170 | **was 25–30 in the old plan — a ₹450 loss per render in India** |

**The trap we removed:** a credit is worth ~$0.38 to a US subscriber but only ~$0.11 to an Indian one, while engine costs are global. Pricing off the *lowest* credit value ($0.10) means no render can lose money in any region — US subscribers simply get extra margin, and top-up credits (₹14.9 ≈ $0.17 each) are more profitable than subscription credits.

A 170-credit Veo render is intentionally out of reach of a ₹499 monthly allowance; that lane is meant to be bought with a top-up, which is exactly how an $8.50 render should feel.

## Real economics today
Every lane in production is near-free: Pexels API (free), edge-tts (free), Whisper (local CPU), Gemini Flash (fractions of a cent), R2 (zero egress). A stock short costs ≈ **$0.002**, so 50 Pro renders ≈ ₹9 against ₹499 revenue. See `/api/billing/economics` (owner-only) for live numbers.

Payment rails: Stripe (US/global) + Razorpay w/ UPI (India). GST invoicing needed for India. Prepaid top-up preferred over postpaid metering — RBI e-mandate rules make variable recurring charges painful, and prepaid can never go unpaid.

Links: [[Home]] · [[Unit Economics]] · [[Decisions]] · [[AI Content System]]
