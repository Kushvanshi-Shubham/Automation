import type { Metadata } from "next"
import LegalPage from "@/components/legal-page"

export const metadata: Metadata = { title: "Terms of Service — Kliptos" }

export default function TermsPage() {
  return (
    <LegalPage title="Terms of Service" updated="3 August 2026">
      <section>
        <h2>1. What Kliptos is</h2>
        <p>
          Kliptos (&quot;we&quot;, &quot;us&quot;) is a software service that helps creators produce short-form
          videos: it surfaces trending topics, generates editable scripts with AI, renders videos with
          voice, captions, licensed stock footage and music, and can publish them to platforms you
          connect (such as YouTube). By creating an account you agree to these terms.
        </p>
      </section>

      <section>
        <h2>2. Your account</h2>
        <ul>
          <li>You sign in with Google. You are responsible for activity on your account.</li>
          <li>You must be at least 13 years old (or the minimum age in your country) to use Kliptos.</li>
          <li>We may suspend accounts that abuse the service, attempt to circumvent limits, or violate these terms.</li>
        </ul>
      </section>

      <section>
        <h2>3. Credits</h2>
        <ul>
          <li>Rendering videos consumes credits. The credit price of an action is always shown before you confirm it.</li>
          <li>Script-only generations are free within a daily limit.</li>
          <li>If a render fails on our side, the credits are refunded to your balance automatically.</li>
          <li>Free signup credits have no cash value. Purchased credits are governed by the <a href="/refunds">Refund Policy</a>.</li>
        </ul>
      </section>

      <section>
        <h2>4. Your content and responsibilities</h2>
        <ul>
          <li>You own the videos you create. We claim no ownership of your outputs.</li>
          <li>Scripts are AI-generated drafts — <strong>you are the editor and publisher</strong>. You are responsible for reviewing content before publishing and for its accuracy and legality.</li>
          <li>Media you upload (for example podcast recordings used by Clips) must be content you own or have rights to.</li>
          <li>You are responsible for complying with the rules of platforms you publish to, including YouTube&apos;s policies on disclosing altered or synthetic content where required.</li>
          <li>You may not use Kliptos to create content that is illegal, infringes others&apos; rights, or is designed to deceive (including impersonation of real people).</li>
        </ul>
      </section>

      <section>
        <h2>5. Third-party services</h2>
        <p>
          Kliptos uses YouTube API Services. By connecting a YouTube channel you also agree to the{" "}
          <a href="https://www.youtube.com/t/terms" target="_blank" rel="noopener noreferrer">YouTube Terms of Service</a>{" "}
          and the <a href="https://policies.google.com/privacy" target="_blank" rel="noopener noreferrer">Google Privacy Policy</a>.
          You can revoke Kliptos&apos;s access to your Google data at any time at{" "}
          <a href="https://security.google.com/settings/security/permissions" target="_blank" rel="noopener noreferrer">security.google.com/settings</a>{" "}
          or by disconnecting the channel in Settings. Stock footage and photos are provided under the Pexels
          license; background music is used under its respective licenses with attribution added automatically
          where required.
        </p>
      </section>

      <section>
        <h2>6. Bring-your-own API keys</h2>
        <p>
          You may add your own AI-provider keys (Gemini, OpenAI, Hugging Face). Usage against your own keys is
          billed to you directly by that provider under their terms; keep your keys secure and within the
          provider&apos;s usage policies. Keys are stored encrypted and are never displayed back once saved.
        </p>
      </section>

      <section>
        <h2>7. Service quality</h2>
        <p>
          We aim for high availability but Kliptos is provided &quot;as is&quot; without warranties. AI models and
          third-party APIs can fail or produce imperfect output; our responsibility for a failed render is limited
          to the automatic credit refund. To the maximum extent permitted by law, our total liability is limited to
          the amount you paid us in the three months before the claim.
        </p>
      </section>

      <section>
        <h2>8. Changes and termination</h2>
        <p>
          We may update these terms; material changes will be announced in the app. You can stop using Kliptos and
          request account deletion at any time. These terms are governed by the laws of India, with courts at
          Varanasi, Uttar Pradesh having jurisdiction.
        </p>
      </section>
    </LegalPage>
  )
}
