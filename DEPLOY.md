# Put MSP Water Report online (permanent free website)

This makes your app live at a real URL like **https://msp-water-report.onrender.com**,
always on — even when your Mac is off. It's two one-time steps: get the code on GitHub,
then connect it to Render (a free host). About 10–15 minutes total.

Everything in the code is already prepared for this (production server, security PIN,
and the Render config). You just click through the two accounts.

---

## Step 1 — Put the code on GitHub (use the free GitHub Desktop app)

1. Download **GitHub Desktop**: https://desktop.github.com → install it.
2. Open it and **sign in** (create a free GitHub account if you don't have one).
3. Top menu: **File → Add Local Repository…**
4. Choose this folder: `…/Claude/Water Report` and click **Add Repository**.
   (It's already set up as a repository, so it'll just appear.)
5. Click **Publish repository** (top right).
   - **Keep "Keep this code private" CHECKED.**
   - Click **Publish Repository**.

Your code is now safely on GitHub. (Whenever you change something later, GitHub Desktop
shows the change — type a short note and click **Commit**, then **Push**.)

---

## Step 2 — Turn it into a live website on Render (free)

1. Go to **https://render.com** → **Get Started** → **Sign in with GitHub** (free).
2. Click **New +** → **Blueprint**.
3. Pick your **water-report** repository from the list → **Connect**.
4. Render reads the included `render.yaml` automatically and sets everything up.
   It will ask you to enter one value:
   - **ADMIN_PIN** — type a PIN you'll remember (e.g. a 4–6 digit code). This is what
     locks the **Settings** page so the public can't change your branding.
5. Click **Apply** / **Create**. Wait ~3–5 minutes for the first build.
6. When it's done, Render shows your live URL, e.g. **https://msp-water-report.onrender.com**.
   Open it — it works from any computer or phone. 🎉

---

## Good to know

- **Free tier sleeps when idle.** After ~15 minutes of no use, the first visit takes
  ~30–50 seconds to wake up, then it's instant. To keep it always-instant, Render's
  paid tier is about $7/month (optional).
- **Your branding is built in.** The company name, phone (952-952-6206),
  email (info@msppurewaterco.com), website, products and BBB Accredited Dealer badge
  all come from `config.json`, which is part of the code — so they're correct and
  permanent on the live site.
- **To use your real logo on the live site:** put your logo image in this folder named
  exactly `logo.png`, then in GitHub Desktop click **Commit** → **Push**. Render
  re-deploys automatically and the logo appears on every report.
- **Changing branding later:** edit it in the **Settings** page on the live site (enter
  your ADMIN_PIN). On the free tier those live edits reset if the service restarts — for
  a permanent change, edit `config.json` (or add `logo.png`) here and Push from GitHub
  Desktop. (On a paid tier with a persistent disk, live edits stick.)
- **Who can use it:** anyone with the link can generate a report (great as a lead magnet).
  Only people with the ADMIN_PIN can change settings. Want the whole site password-
  protected (rep-only) or on your own domain like **report.msppurewaterco.com**? Just ask.

---

## Optional — your own domain (report.msppurewaterco.com)

In Render: open your service → **Settings → Custom Domains → Add** `report.msppurewaterco.com`.
Render shows you a CNAME record; add it at whoever manages your domain (where you bought
msppurewaterco.com). It goes live in a few minutes to an hour.
