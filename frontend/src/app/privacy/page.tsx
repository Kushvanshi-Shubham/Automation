import type { Metadata } from "next"
import LegalPage from "@/components/legal-page"

export const metadata: Metadata = { title: "Privacy Policy — Kliptos" }

export default function PrivacyPage() {
  return (
    <LegalPage title="Privacy Policy" updated="3 August 2026">
      <section>
        <h2>1. What we collect</h2>
        <ul>
          <li><strong>Account data</strong>: your name, email and avatar from Google Sign-In.</li>
          <li><strong>Connected platforms</strong>: OAuth tokens for channels you connect (e.g. YouTube). Tokens are encrypted at rest and used only to perform the actions you request, such as uploading your video.</li>
          <li><strong>Your content</strong>: scripts, rendered videos, and media files you upload for clipping (plus their transcripts).</li>
          <li><strong>Your API keys</strong> (optional): provider keys you add are encrypted at rest and never shown back or shared.</li>
          <li><strong>Usage data</strong>: renders, credits, and basic logs needed to run and secure the service (including IP addresses for rate limiting).</li>
        </ul>
      </section>

      <section>
        <h2>2. How we use it</h2>
        <p>
          Only to provide Kliptos: generating your scripts, rendering your videos, publishing where you ask us to,
          preventing abuse, and improving the product. <strong>We do not sell your data.</strong> We do not use your
          content or your Google user data to train AI models.
        </p>
      </section>

      <section>
        <h2>3. Google user data (Limited Use disclosure)</h2>
        <p>
          Kliptos&apos;s use and transfer of information received from Google APIs adheres to the{" "}
          <a href="https://developers.google.com/terms/api-services-user-data-policy" target="_blank" rel="noopener noreferrer">
            Google API Services User Data Policy
          </a>, including the Limited Use requirements. YouTube tokens are used solely to list your channel and
          upload/schedule the videos you explicitly choose to publish. You can revoke access at any time at{" "}
          <a href="https://security.google.com/settings/security/permissions" target="_blank" rel="noopener noreferrer">
            security.google.com/settings
          </a>{" "}
          or in Kliptos Settings.
        </p>
      </section>

      <section>
        <h2>4. Processors we rely on</h2>
        <p>
          To generate and render content, the relevant parts of your input are processed by: Google (Gemini,
          YouTube API), OpenAI, Hugging Face (only if selected or as fallback), Pexels (stock media search),
          and Microsoft (neural text-to-speech). Hosting and infrastructure providers store data on our behalf.
          Each processor receives only what it needs for its task.
        </p>
      </section>

      <section>
        <h2>5. Retention and deletion</h2>
        <ul>
          <li>Rendered videos and uploads are kept so you can access them; you can delete them in the app at any time.</li>
          <li>Deleting an upload also deletes its transcript and highlights.</li>
          <li>To delete your entire account and data, email <a href="mailto:support@kliptos.app">support@kliptos.app</a> — we complete deletion within 30 days.</li>
        </ul>
      </section>

      <section>
        <h2>6. Cookies</h2>
        <p>
          We use only essential cookies: your login session. No advertising or cross-site tracking cookies.
        </p>
      </section>

      <section>
        <h2>7. Your rights</h2>
        <p>
          You may request access to, correction of, or deletion of your personal data. Indian users: this policy is
          designed to align with the Digital Personal Data Protection Act, 2023; our grievance contact is{" "}
          <a href="mailto:support@kliptos.app">support@kliptos.app</a>. We respond within the timelines the law requires.
        </p>
      </section>

      <section>
        <h2>8. Changes</h2>
        <p>Material changes to this policy will be announced in the app before they take effect.</p>
      </section>
    </LegalPage>
  )
}
