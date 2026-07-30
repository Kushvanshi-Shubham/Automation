# Instagram Setup — exact steps, top to bottom

Follow in order. Steps 1–2 are on your phone/instagram.com, 3–7 on developers.facebook.com.
Total time: ~25 minutes (excluding Meta's review wait).

---

## 1. Make your Instagram a Professional account (2 min)
1. Instagram app → your profile → **☰ menu → Settings and privacy**
2. **Account type and tools → Switch to professional account**
3. Choose **Creator** or **Business** (either works; Business preferred for API)
4. Finish the wizard (category doesn't matter).

## 2. Link Instagram to a Facebook Page (3 min)
The API can only see IG accounts connected to a FB Page.
1. If you don't have a Facebook Page: facebook.com → Menu → Pages → **Create new Page** (name it e.g. "Kliptos", any category) — takes 1 minute.
2. Instagram app → profile → **Edit profile → Page** (under "Profile information", may say "Connect or create") → connect the Page you just made.
   - Alternative path: Facebook Page → Settings → **Linked accounts → Instagram → Connect account**.
3. Verify: your FB Page settings → Linked accounts shows your IG username. ✅

## 3. Create the Meta app (5 min)
1. Go to **developers.facebook.com** → log in with the SAME Facebook account that owns the Page.
2. First time: click **Get Started** and register as a developer (verify phone/email).
3. **My Apps → Create App**
4. Use case: choose **Other** → Next
5. App type: choose **Business** → Next
6. App name: `Kliptos` · contact email: yours → **Create app**

## 4. Add the products (3 min)
On the app dashboard ("Add products to your app"):
1. Find **Facebook Login for Business** → **Set up**
2. Find **Instagram** (or "Instagram Graph API") → **Set up**

## 5. Configure Facebook Login (3 min)
1. Left sidebar → **Facebook Login for Business → Settings**
2. In **Valid OAuth Redirect URIs** add BOTH (second one is for after deployment; placeholder is fine to skip for now):
   ```
   http://localhost:8000/api/instagram/callback
   ```
   ⚠️ If Meta refuses http/localhost here: that's expected on some app types — in that case skip it; local testing then needs the deployed URL anyway (Meta must fetch the video from a public URL regardless).
3. Save changes.

## 6. Get the credentials (1 min)
1. Left sidebar → **App settings → Basic**
2. Copy **App ID** and **App Secret** (click Show)
3. **Send both to me** — I wire them into `.env` (`META_APP_ID`, `META_APP_SECRET`).

## 7. Add yourself as tester = instant testing rights (2 min)
While the app is in **Development Mode**, it can publish to YOUR OWN Instagram without any review:
1. Left sidebar → **App roles → Roles**
2. You're already Administrator (creator) — that's enough. If a friend will test: **Add People → Tester** with their FB account, they accept the invite.
3. Leave the app in Development Mode for now. **Do NOT switch to Live** yet.

## 8. App Review — start it, then forget it (10 min + weeks of waiting)
Needed only to let PUBLIC users (non-testers) connect. Do it in parallel:
1. Left sidebar → **App Review → Permissions and features**
2. Request **Advanced Access** for:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
   - `pages_read_engagement`
   - `business_management`
3. Each asks for a description + screen recording of how Kliptos uses it. Do this AFTER we deploy (you'll record the real flow). For now just note where it lives.
4. Business verification may be requested (business document or website) — handle when asked.

---

## What to send me
| Item | Where it's used |
|:---|:---|
| **App ID** | `META_APP_ID` in `.env` |
| **App Secret** | `META_APP_SECRET` in `.env` |

## Reality reminders
- The final Reel publish needs the rendered video on a **public URL** (Meta downloads it). Localhost cannot serve Meta → the true end-to-end test happens at deployment (or via a tunnel).
- Long-lived tokens last ~60 days; reconnecting refreshes them (auto-refresh comes later).
- Same playbook as YouTube: **`youtube.upload` verification is still pending on your side too.**
