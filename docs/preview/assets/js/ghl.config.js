/* =====================================================================
   MSP PURE WATER — GOHIGHLEVEL INTEGRATION CONFIG (single source of truth)
   ---------------------------------------------------------------------
   Everything the site needs to talk to GoHighLevel lives in this file.
   Replace the *_HERE placeholders with real values from the MSP Pure Water
   GoHighLevel sub-account. Nothing else in the site has to change.

   NEVER put a private API key or auth token in this file. It ships to the
   browser. Direct API calls belong behind a server-side proxy (see
   INTEGRATION.md → "Future API integration").
   ===================================================================== */
window.MSP_GHL = {

  /* Sub-account (location) ID. Found in GHL → Settings → Business Profile. */
  locationId: "GHL_LOCATION_ID_HERE",   /* optional; found in GHL → Settings → Business Profile */

  /* -------------------------------------------------------------------
     LEAD SUBMISSION — how the native Find My System intake reaches GHL.
     mode:
       "webhook"  Recommended first implementation. Create a GHL Workflow
                  with the trigger "Inbound Webhook", copy its URL here.
                  The site POSTs JSON (see INTEGRATION.md → payload) and
                  the workflow creates/updates the contact, opportunity,
                  tags and notifications.
       "embed"    Shows the official GHL form (formEmbedUrl) inside the
                  branded wrapper instead of the native intake. Use if
                  you prefer GHL to own the fields entirely.
       "api"      Reserved. POSTs the same payload to apiProxyUrl — a
                  server-side endpoint that calls the GHL API with a
                  private key. Site code needs no change to switch.
     ------------------------------------------------------------------- */
  lead: {
    mode: "webhook",
    webhookUrl: "GHL_INBOUND_WEBHOOK_URL_HERE",
    formId: "GHL_FORM_ID_HERE",
    formEmbedUrl: "GHL_FORM_EMBED_URL_HERE",      /* e.g. https://api.leadconnectorhq.com/widget/form/XXXX */
    apiProxyUrl: "",
    /* OR paste the complete GHL embed code (the <iframe …> plus its <script>)
       here as one string. When set, it is used as-is and formEmbedUrl is ignored. */
    embedHtml: "",
    /* Optional bot protection. Leave empty to rely on honeypot + timing. */
    turnstileSiteKey: ""
  },

  /* -------------------------------------------------------------------
     CONTACT US FORM — the /contact/ page.
     GHL → Sites → Forms → (your Contact form) → Integrate → Embed.
     EITHER paste the whole embed code into embedHtml (easiest),
     OR copy just the iframe's src into formEmbedUrl.
     ------------------------------------------------------------------- */
  contact: {
    formName: "MSP - New Contact Form",
    formId: "V32gATfTfG9ZQh3MNXJX",
    formEmbedUrl: "https://api.homeservicehub.app/widget/form/V32gATfTfG9ZQh3MNXJX",
    /* Official embed code pasted from GHL (white-label domain api.homeservicehub.app). */
    embedHtml: "<iframe src=\"https://api.homeservicehub.app/widget/form/V32gATfTfG9ZQh3MNXJX\" style=\"width:100%;height:100%;border:none;border-radius:3px\" id=\"inline-V32gATfTfG9ZQh3MNXJX\" data-layout=\"{'id':'INLINE'}\" data-trigger-type=\"alwaysShow\" data-trigger-value=\"\" data-activation-type=\"alwaysActivated\" data-activation-value=\"\" data-deactivation-type=\"neverDeactivate\" data-deactivation-value=\"\" data-form-name=\"MSP - New Contact Form\" data-height=\"1453\" data-layout-iframe-id=\"inline-V32gATfTfG9ZQh3MNXJX\" data-form-id=\"V32gATfTfG9ZQh3MNXJX\" data-cookie-consent=\"true\" data-cookie-consent-provider=\"auto\" title=\"MSP - New Contact Form\"></iframe><script src=\"https://api.homeservicehub.app/js/form_embed.js\"></script>",
    height: 1453
  },


  /* -------------------------------------------------------------------
     SCHEDULING — the ONE MSP Pure Water consultation calendar.
     Every "Schedule Online" CTA on the site resolves to this calendar.
     calendarEmbedUrl: GHL → Calendars → (calendar) → Share → Embed link
       e.g. https://api.leadconnectorhq.com/widget/booking/XXXXXXXX
     thankYouPath: set the SAME path as the calendar's "Custom thank-you
       page" (Calendar → Settings → Confirmation) so booked visitors land
       on the branded confirmation screen.
     ------------------------------------------------------------------- */
  calendar: {
    calendarId: "BNcToWKbTUgDdLhuc4cW",
    calendarEmbedUrl: "https://api.homeservicehub.app/widget/booking/BNcToWKbTUgDdLhuc4cW",
    /* OR paste the complete calendar embed code (<iframe …> + <script>) here. */
    embedHtml: "",
    thankYouPath: "/booked/",
    /* Query-string prefill keys the GHL booking widget understands. */
    prefill: { first_name: "first_name", last_name: "last_name", email: "email", phone: "phone" }
  },

  /* -------------------------------------------------------------------
     CUSTOM FIELD MAPPING — payload key → GHL custom field key.
     Create these fields in GHL → Settings → Custom Fields (Contact).
     Keys are the GHL "unique key" (fieldKey). Adjust if you name them
     differently in GHL; the site's payload keys stay the same.
     ------------------------------------------------------------------- */
  customFields: {
    water_source:        "contact.water_source",
    water_problems:      "contact.water_problems",
    system_interest:     "contact.system_interest",
    system_id:           "contact.system_id",
    system_config:       "contact.system_configuration",
    bathrooms:           "contact.bathrooms",
    household_size:      "contact.household_size",
    existing_equipment:  "contact.existing_equipment",
    customer_notes:      "contact.customer_notes",
    lead_source:         "contact.lead_source",
    website_entry_page:  "contact.website_entry_page",
    landing_page:        "contact.landing_page",
    referrer:            "contact.referrer",
    utm_source:          "contact.utm_source",
    utm_medium:          "contact.utm_medium",
    utm_campaign:        "contact.utm_campaign",
    utm_content:         "contact.utm_content",
    utm_term:            "contact.utm_term",
    gclid:               "contact.gclid",
    fbclid:              "contact.fbclid"
  },

  /* Pipeline names are configured INSIDE GoHighLevel workflows, not here.
     These labels only document the intended behaviour for the team. */
  pipeline: {
    name: "MSP Pure Water — Website Leads",
    stages: { new: "New Website Lead", booked: "Appointment Scheduled" }
  },

  /* Tags the webhook workflow should apply (documentation for the GHL build). */
  tags: {
    base: ["Website Lead"],
    bySource: { "City Water": "City Water", "Well Water": "Well Water" },
    byInterest: { "Reverse Osmosis": "RO Interest", "Whole Home Filtration": "Whole Home Interest" }
  },

  /* -------------------------------------------------------------------
     ANALYTICS — the site pushes every event to window.dataLayer.
     Paste a GTM container ID to load Google Tag Manager, or leave empty
     and read dataLayer from any tag manager you already have.
     ------------------------------------------------------------------- */
  analytics: {
    gtmId: "",
    ga4Id: ""
  },

  /* Consent copy shown under every phone/email field. Edit to match the
     SMS consent language configured in GHL. */
  consent: {
    text: "By submitting, you agree MSP Pure Water may call, text or email you about your request. Message and data rates may apply. Reply STOP to opt out at any time. See our Privacy Policy.",
    smsOptInLabel: "Yes, text me appointment updates and reminders."
  }
};
