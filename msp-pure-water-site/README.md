# MSP Pure Water — static replica

A static copy of the Amboras-built site, captured from the live preview tunnel
on 2026-08-28. All 17 real pages are reproduced with content **byte-for-byte
identical** to the original's rendered DOM (verified by automated text diff).

## Run locally

    python3 -m http.server 8931 --directory msp-pure-water-site

Then open http://localhost:8931/ — or use the `msp-site` entry in
`.claude/launch.json`.

## How it was built

The original is a Next.js dev server. Pages were rendered with headless Chrome
(`--dump-dom`) so client-rendered content — product specs, prices, variant
options — is captured as real markup. Only mechanical transforms were applied:

- `/_next/image?url=…` → local `assets/img/…`
- internal routes → `.html`
- Next.js runtime scripts dropped
- fonts and stylesheet pulled local (stylesheet is the original, unmodified,
  except font URLs)

Header, `<main>` and footer markup are copied through untouched.

## What `assets/site.js` does

The original relies on React for interactivity. This script restores only what
the original does — it adds nothing:

- **Scroll reveals.** The stylesheet ships `.reveal` / `.reveal-left` /
  `.reveal-right` at `opacity: 0`, painting them only once `.visible` is added.
  React did that with an IntersectionObserver. Without it every section below
  the hero stays permanently invisible (29 such elements on the homepage, 17 on
  About).
- **Collapsible panels** — FAQ and product-page accordions.
- **Announcement bar dismiss.**
- **Product option selection.**

## Known gaps (not defects in this copy)

**Faithful reproductions of original bugs:**

- 20 routes are linked in the nav/footer but were never built by Amboras and
  404 on the original: `/accessibility`, `/uv-water-purification`, and all 18
  `/service-areas/<city>` pages. They 404 here too.
- `/products` shows "No products available yet" — it does on the original too.

**Cannot be reproduced statically:**

- **The scheduler wizard** (`/schedule`) renders step 1 exactly, but advancing
  through system → date → time → details is React state backed by Amboras's
  server. A static file cannot process a booking. To go live with a working
  scheduler you need either the real Next.js app or the form wired to a service
  (Formspree, a CRM endpoint, etc.).
- **The header hamburger** is currently inert. Whether it opens a menu on a
  healthy original was never established — the preview tunnel stopped hydrating
  (HMR WebSocket failures) before it could be observed.
- **The cookie consent banner** appears on the original but is injected by
  React after load; its markup was not captured.

## Assets

5 product/brand images + 1 placeholder, 5 woff2 files (Cinzel, Josefin Sans —
both open-licensed). Nothing loads from a third-party host, so the site works
fully offline.
