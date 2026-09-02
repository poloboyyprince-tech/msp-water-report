# MSP Pure Water — GoHighLevel Integration Guide

GoHighLevel (GHL) is the CRM, scheduling, automation and notification system
of record for this website. The site is the conversion front end; GHL owns
every contact, opportunity and appointment. ScheduleDrop is a manual downstream
handoff triggered from GHL. Nothing on the site stores leads or bookings.

## 1. Where everything lives

| What | File |
|---|---|
| Every GHL setting (IDs, embed URLs, field map, consent copy, analytics IDs) | `src/config/ghl.config.js` → shipped as `/assets/js/ghl.config.js` |
| CRM submission logic (webhook / embed / api), calendar + form wrappers | `src/js/ghl-adapter.js` (`window.MSPCRM`) |
| Find My System wizard (presentation only, calls `MSPCRM.submitLead`) | `src/js/find-my-system.js` |
| Analytics events + UTM / lead-source attribution | `src/js/tracking.js` (`window.MSPTrack`) |
| UI behaviours, water-source pre-selection, confirmation pages | `src/js/ui.js` |
| Page templates / components (`GHLCalendar`, `GHLBookingConfirmation`, …) | `build.py` |

Edit only `ghl.config.js` to go live. No UI component contains a GHL ID.

## 2. Go-live checklist (paste these values)

1. **`locationId`** – GHL → Settings → Business Profile → Location ID.
2. **Lead intake (`lead.mode: "webhook"`)** – GHL → Automation → Workflows → Create →
   trigger **Inbound Webhook**. Copy the webhook URL into `lead.webhookUrl`.
   Send one test submission from `/find-my-system/` (on localhost the page
   shows an integration-readiness banner) so GHL learns the payload fields, then
   map them in the workflow (section 4).
   *If your host blocks cross-origin POSTs to the webhook*, set
   `lead.mode: "api"` and point `lead.apiProxyUrl` at a tiny serverless relay
   that forwards the JSON to the webhook (or to the GHL API with a private key).
   No site code changes.
3. **Calendar** – GHL → Calendars → the MSP consultation calendar → Share →
   **Embed link** (`https://api.leadconnectorhq.com/widget/booking/…`) →
   `calendar.calendarEmbedUrl`. Also paste the calendar ID into `calendar.calendarId`.
   In that calendar's settings set **Custom thank-you page** to
   `https://msppurewaterco.com/booked/` so booked visitors land on the branded
   confirmation screen (`calendar.thankYouPath`).
4. **Optional official form embed** – if you would rather GHL render the intake
   fields, set `lead.mode: "embed"` and paste the form's embed URL
   (`https://api.leadconnectorhq.com/widget/form/…`) into `lead.formEmbedUrl`.
   Add `<div data-ghl-form class="ghl-wrap"></div>` where you want it; the
   wrapper handles loading state, height and fallback.
5. **Analytics** – paste a GTM container ID into `analytics.gtmId` (or read
   `window.dataLayer` from your existing tag). Events are listed in section 8.
6. Rebuild (`python3 build.py`) and deploy `dist/`.

Where the placeholders appear in the built site: only inside
`/assets/js/ghl.config.js`. Public pages never print a placeholder; when a
value is missing the calendar wrapper shows a branded "call or text" fallback
and the wizard shows a call-to-phone message instead of a false success.
Developers see the readiness banner on `localhost` or with `?msp-debug=1`.

## 3. Customer journey → GHL objects

```
Visitor → water-source card / problem explorer (pre-fills intake)
       → FIND MY SYSTEM (5 steps) → POST JSON → Inbound Webhook workflow
            → contact created/updated, custom fields, tags, opportunity
            → internal "NEW WEBSITE LEAD" notification, customer confirmation
       → /thank-you/ shows the GHL calendar with name/phone/email pre-filled
       → appointment booked in the MSP calendar (GHL owns availability)
            → "APPOINTMENT BOOKED" workflow: stage update, confirmations,
               internal notification, ScheduleDrop handoff task
       → calendar redirects to /booked/ (branded confirmation, appointment_booked event)
```
"Schedule Online" everywhere → `/schedule/` → the same calendar embed.
"Claim Your Best Price" → `/best-price-guarantee/#claim` → same wizard with
`inquiry_type = "Best Price Guarantee Inquiry"` so the workflow can tag and route it.

## 4. Webhook payload → custom fields

The site POSTs this JSON (`Content-Type: application/json`). Create matching
**Contact custom fields** in GHL (Settings → Custom Fields) and map them in the
webhook workflow's *Create/Update Contact* action.

| Payload key | GHL field | Notes |
|---|---|---|
| first_name, last_name, phone, email | standard | |
| city, postal_code, state (MN), country (US) | standard address | |
| water_source | Water Source (dropdown: City Water / Well Water / Not Sure) | |
| water_problems | Water Problems (text; comma-separated) | |
| system_interest | System Interest (dropdown) | |
| bathrooms, household_size | Bathrooms, Household Size | optional |
| existing_equipment | Existing Equipment | optional |
| customer_notes | Customer Notes | optional |
| sms_consent | SMS Consent (Yes/No) | drive DND / SMS opt-in from this |
| inquiry_type | Inquiry Type | "Find My System" or "Best Price Guarantee Inquiry" |
| lead_source | Lead Source | Google Ads / Google Organic / Google Business Profile / Facebook / Instagram / Direct / Referral / Campaign: … |
| website_entry_page, landing_page, referrer | Website Entry Page, Landing Page, Referrer | |
| utm_source, utm_medium, utm_campaign, utm_content, utm_term | UTM * | first-touch, persisted in the browser |
| gclid, fbclid | GCLID, FBCLID | |
| tags | (use in Add Tag action) | "Website Lead, City Water, RO Interest" etc. |
| submission_id, submitted_at, page | | duplicate protection / audit |

Key names in `ghl.config.js → customFields` document the intended GHL field
keys; rename there if you name fields differently.

## 5. Pipeline

Pipeline **MSP Pure Water — Website Leads** (create in GHL → Opportunities).
Stages, configured inside GHL workflows (not hard-coded on the site):

- **New Website Lead** ← set by Workflow 1
- **Appointment Scheduled** ← set by Workflow 2
- further stages (Consultation Done, Installed, Lost…) are free to add.

## 6. Workflows

**Workflow 1 — New Website Lead** · Trigger: Inbound Webhook (section 2)
1. Create/Update Contact (map fields above).
2. Add tags: `Website Lead`; `City Water` or `Well Water` from Water Source;
   `RO Interest` when System Interest = Reverse Osmosis; `Whole Home Interest`
   when Whole Home Filtration; `Best Price` when inquiry_type is the guarantee.
3. Create/Update Opportunity in the pipeline, stage **New Website Lead**,
   source = Lead Source.
4. Internal notification (section 7, "NEW MSP PURE WATER WEBSITE LEAD").
5. Customer confirmation (email; SMS only if SMS Consent = Yes) with the
   booking link `https://msppurewaterco.com/schedule/`.
6. Wait 30 min → if no appointment → go to Workflow 3.

**Workflow 2 — Appointment Booked** · Trigger: Appointment status = Confirmed
(or Booked) on the MSP consultation calendar
1. Update opportunity stage → **Appointment Scheduled**; add tag `Appointment Booked`.
2. Customer confirmation (email + SMS if consented) with date/time and reschedule link.
3. Internal notification (section 7, "NEW MSP PURE WATER APPOINTMENT").
4. **Create Task** assigned to the owner: *"Enter this appointment into
   ScheduleDrop"* with the same details, due in 1 hour.
5. Reminders 24 h and 2 h before; reschedule/cancel handled by the calendar.

**Workflow 3 — Lead Did Not Book** · Trigger: from Workflow 1 wait step, or
tag `Website Lead` without an appointment after 30 min
- SMS/email nudge with the booking link (respect SMS Consent), retry at 1 day
  and 3 days, then hand to manual follow-up. The website plays no role here.

**Workflow 4 — Appointment Reminders / Status** · standard GHL calendar
automations: confirmation, 24 h / 2 h reminders, no-show handling, internal
status changes.

## 7. Internal notification templates

Send to the owner by SMS + email (and Slack/Teams if used). Contact link:
`https://app.gohighlevel.com/v2/location/{{location.id}}/contacts/detail/{{contact.id}}`

```
NEW MSP PURE WATER WEBSITE LEAD
Customer: {{contact.first_name}} {{contact.last_name}}
Phone: {{contact.phone}}   Email: {{contact.email}}   City: {{contact.city}}
Water Source: {{contact.water_source}}
Water Problems: {{contact.water_problems}}
System Interest: {{contact.system_interest}}
Inquiry: {{contact.inquiry_type}}
Source: {{contact.lead_source}} ({{contact.utm_campaign}})
Open contact: <link above>
```

```
NEW MSP PURE WATER APPOINTMENT
Customer: {{contact.first_name}} {{contact.last_name}}   Phone: {{contact.phone}}
City: {{contact.city}}
Appointment: {{appointment.start_time}}
Water Source: {{contact.water_source}}   Problems: {{contact.water_problems}}
System Interest: {{contact.system_interest}}   Lead Source: {{contact.lead_source}}
ACTION REQUIRED: Review this appointment and enter the required information into ScheduleDrop.
Open contact: <link above>
```

## 8. Analytics events (window.dataLayer)

`phone_click`, `schedule_click`, `find_my_system_opened`,
`find_my_system_started`, `find_my_system_completed`, `lead_form_submitted`,
`lead_form_error`, `calendar_viewed`, `appointment_booked`,
`city_water_selected`, `well_water_selected`, `drinking_water_selected`,
`ro_selected`, `pricing_viewed`, `system_comparison_used`,
`best_price_guarantee_cta`. Each carries `page_path` plus context (`via`,
`label`, `water_source`, `system_interest`, `mode`). `appointment_booked` fires
on `/booked/` (calendar thank-you redirect) and, best-effort, when the embedded
calendar posts a booking message. Turn on console logging with `?msp-debug=1`.

## 9. Future API integration

Presentation and submission are already separated. To move from the inbound
webhook to a direct API integration: build a server endpoint that receives the
same payload, calls the GHL Contacts / Opportunities / Appointments APIs with a
private key, and set `lead.mode: "api"` + `lead.apiProxyUrl`. The wizard,
calendar wrapper and tracking need no changes. Never put an API key in the
browser bundle.

## 10. Acceptance test

Run the 21-step test from the project brief after pasting real values:
incognito → select water source → problems → Find My System → submit → check
contact, custom fields, UTM, opportunity, internal notification → continue to
calendar → book → check appointment on calendar, linked contact, stage,
booking notification, ScheduleDrop task, customer confirmation, `/booked/`.
Use `?utm_source=test&utm_medium=qa&utm_campaign=acceptance` on the first URL
to verify attribution retention.
