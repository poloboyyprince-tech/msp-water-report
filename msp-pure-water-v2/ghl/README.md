# GHL funnel pages (paste-ready)

## vsl-page.html — "Digital Marketing" funnel → Offer step (the VSL page)

One self-contained block built from the live site's design tokens (`src/css/site.css`).
Top to bottom: logo (left) + phone (right) · headline · subheadline · 16:9 video
frame · gold "Click to Book a Free Water Test Today" button · "Book Your In-Home
Appointment" details · GHL booking calendar (Free Water Test, id oMIy60l9ixISaEpJBkYb).

### Put it into GoHighLevel (about 5 minutes)

1. GHL → **Sites → Funnels → Digital Marketing**. Click the **Offer** step, then **Edit**.
2. Clear the template: hover each section on the canvas, click its **trash** icon,
   confirm. Repeat until the canvas is empty. (Layers panel, left toolbar, lists them.)
3. Click **+ Add Section** → choose **Full Width**.
4. Inside it click **+ Add Row** → **1 column**.
5. Inside the row click **+ Add Element** → scroll to **Custom JS/HTML** (under
   "Misc" / "Custom") and drop it in.
6. Click the new element → in the right panel click **Open Code Editor**.
   Open `vsl-page.html`, **select all, copy, paste** it in, click **Yes, save**.
7. Still on the element: **Advanced** → set all Margin and Padding to **0**.
   Click the **Row**, then the **Section**, and zero their padding too.
8. Click the **page settings** (gear/"Page" at the top or bottom-left) → **Background**
   → color **#0B1426**. Font settings can stay; the block loads its own fonts.
9. Find the comment `[VSL EMBED CODE HERE]` inside `<div class="vsl">` in the code
   editor and paste the video embed (`<iframe …>` or `<video …>`) there.
   The frame is 16:9 and fills it automatically.
10. **Save** (top right), then **Preview** on desktop and phone, then **Publish**.
11. Funnel → **Settings** → attach a domain so the page gets a real URL
    (it currently only exists at the api.homeservicehub.app preview link).

### The "Free Water Test" calendar (already created — Settings → Calendars)
- Id `oMIy60l9ixISaEpJBkYb`, slug `msp-free-water-test`, type **Simple calendar (event)**.
  Personal/round-robin types inherit the user's Mon–Fri availability and hide Saturdays.
- 60-min appointments, slot interval 120 min, Mon–Sat 12:00–7:00 PM
  → exactly 12:00, 2:00, 4:00 and 6:00 PM. Sundays closed.
- Minimum notice **16 hours** (noon must be booked by 8 PM the night before).
- Auto-confirm on; thank-you message tells them MSP will call/text to confirm.
- Optional: Calendar → Customizations → primary colour #C9A84C to match the page.
