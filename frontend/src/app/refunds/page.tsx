import type { Metadata } from "next"
import LegalPage from "@/components/legal-page"

export const metadata: Metadata = { title: "Refund Policy — Kliptos" }

export default function RefundsPage() {
  return (
    <LegalPage title="Refund & Cancellation Policy" updated="3 August 2026">
      <section>
        <h2>1. Failed renders — automatic, always</h2>
        <p>
          If a video render fails for any reason on our side, the credits it consumed are refunded to your
          balance <strong>automatically and immediately</strong>. No ticket needed.
        </p>
      </section>

      <section>
        <h2>2. Purchased credit packs</h2>
        <ul>
          <li><strong>Unused packs</strong>: refundable in full within 7 days of purchase if none of the pack&apos;s credits have been spent.</li>
          <li><strong>Partially used packs</strong>: the unused portion is refundable within 7 days of purchase, calculated at the pack&apos;s per-credit price.</li>
          <li><strong>Consumed credits</strong> are not refundable — each render&apos;s credit price is shown before you confirm it, and you review the script before rendering.</li>
          <li>Free signup or promotional credits have no cash value and are not refundable.</li>
        </ul>
      </section>

      <section>
        <h2>3. Subscriptions (when available)</h2>
        <ul>
          <li>Cancel anytime; your plan stays active until the end of the paid period, and you are not charged again.</li>
          <li>If you cancel within 48 hours of a renewal and have not used that period&apos;s credits, we refund the renewal on request.</li>
        </ul>
      </section>

      <section>
        <h2>4. How refunds are paid</h2>
        <p>
          Approved refunds are returned to the original payment method within <strong>5–7 business days</strong>{" "}
          (processing time depends on your bank or payment provider). To request one, email{" "}
          <a href="mailto:support@kliptos.app">support@kliptos.app</a> from your account email with the payment
          reference — we respond within 2 business days.
        </p>
      </section>

      <section>
        <h2>5. Fair use</h2>
        <p>
          We reserve the right to refuse refunds where we detect abuse (for example, repeated purchase–consume–refund
          patterns). Nothing in this policy limits rights you have under applicable consumer-protection law.
        </p>
      </section>
    </LegalPage>
  )
}
