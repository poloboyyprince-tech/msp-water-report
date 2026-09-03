/* MSP Pure Water — GoHighLevel adapter (CRM submission + scheduling)
   ---------------------------------------------------------------
   Presentation components never talk to GHL directly. They call:
     MSPCRM.submitLead(payload)            -> Promise<{ok, mode, error}>
     MSPCRM.renderCalendar(el, prefill)    -> official GHL calendar embed
     MSPCRM.renderForm(el)                 -> official GHL form embed
     MSPCRM.calendarUrl(prefill)           -> booking URL with prefill
     MSPCRM.status()                       -> integration readiness
   Swap lead.mode in ghl.config.js between webhook / embed / api without
   touching any UI code. */
(function () {
  "use strict";
  var C = window.MSP_GHL || {};
  var PH = /_HERE$|^$/;                                 /* placeholder detector */
  function set(v) { return typeof v === "string" && !PH.test(v); }
  var GHL_EMBED_JS = "https://link.msgsndr.com/js/form_embed.js";

  function status() {
    var lead = C.lead || {}, cal = C.calendar || {};
    var leadReady = lead.mode === "webhook" ? set(lead.webhookUrl) : lead.mode === "embed" ? set(lead.formEmbedUrl) : lead.mode === "api" ? set(lead.apiProxyUrl) : false;
    return {
      locationId: set(C.locationId), leadMode: lead.mode, leadReady: leadReady,
      calendarReady: set(cal.calendarEmbedUrl), analytics: !!(C.analytics && (C.analytics.gtmId || C.analytics.ga4Id))
    };
  }

  /* ---- Session hand-off between intake, calendar and confirmation ---- */
  var SKEY = "msp_lead";
  function saveLead(p) { try { sessionStorage.setItem(SKEY, JSON.stringify(p)); } catch (e) {} }
  function loadLead() { try { return JSON.parse(sessionStorage.getItem(SKEY) || "null"); } catch (e) { return null; } }

  /* ---- Payload normalisation: one shape, every backend ---- */
  function buildPayload(data) {
    var attr = (window.MSPTrack && window.MSPTrack.attribution()) || {};
    var p = {
      first_name: data.first_name || "", last_name: data.last_name || "", phone: data.phone || "", email: data.email || "",
      city: data.city || "", postal_code: data.zip || "", state: "MN", country: "US",
      water_source: data.water_source || "", water_problems: (data.water_problems || []).join(", "),
      system_interest: data.system_interest || "", bathrooms: data.bathrooms || "", household_size: data.household_size || "",
      existing_equipment: data.existing_equipment || "", customer_notes: data.notes || "",
      sms_consent: data.sms_consent ? "Yes" : "No",
      system_id: data.system_id || "", system_config: data.system_config || "",
      lead_source: data.lead_source || attr.lead_source || "Direct", inquiry_type: data.inquiry_type || "Find My System",
      website_entry_page: attr.website_entry_page || "", landing_page: attr.landing_page || "", referrer: attr.referrer || "",
      utm_source: attr.utm_source || "", utm_medium: attr.utm_medium || "", utm_campaign: attr.utm_campaign || "",
      utm_content: attr.utm_content || "", utm_term: attr.utm_term || "", gclid: attr.gclid || "", fbclid: attr.fbclid || "",
      submitted_at: new Date().toISOString(), page: location.href, submission_id: data.submission_id || ""
    };
    /* Tags the workflow may apply (documentation; the workflow decides). */
    var tags = (C.tags && C.tags.base ? C.tags.base.slice() : []);
    if (C.tags && C.tags.bySource && C.tags.bySource[p.water_source]) tags.push(C.tags.bySource[p.water_source]);
    if (C.tags && C.tags.byInterest && C.tags.byInterest[p.system_interest]) tags.push(C.tags.byInterest[p.system_interest]);
    p.tags = tags.join(",");
    return p;
  }

  function post(url, payload) {
    var ctrl = ("AbortController" in window) ? new AbortController() : null;
    var t = setTimeout(function () { if (ctrl) ctrl.abort(); }, 15000);
    return fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload), signal: ctrl ? ctrl.signal : undefined })
      .then(function (r) { clearTimeout(t); if (!r.ok) throw new Error("HTTP " + r.status); return r; });
  }

  /* submitLead never resolves ok:true unless the endpoint accepted the POST. */
  function submitLead(data) {
    var lead = C.lead || {}, st = status();
    var payload = buildPayload(data);
    saveLead(payload);
    if (!st.leadReady) {
      return Promise.resolve({ ok: false, mode: lead.mode, error: "not_configured", payload: payload });
    }
    var url = lead.mode === "api" ? lead.apiProxyUrl : lead.webhookUrl;
    return post(url, payload).then(function () { return { ok: true, mode: lead.mode, payload: payload }; })
      .catch(function (err) { return { ok: false, mode: lead.mode, error: err && err.message || "network", payload: payload }; });
  }

  /* ---- Scheduling ---- */
  function calendarUrl(prefill) {
    var cal = C.calendar || {}; if (!set(cal.calendarEmbedUrl)) return "";
    var lead = prefill || loadLead() || {}; var map = cal.prefill || {};
    try { var pre = JSON.parse(sessionStorage.getItem("msp_intake") || "{}"); ["water_source", "system_interest", "system_config"].forEach(function (k) { if (!lead[k] && pre[k]) lead[k] = pre[k]; }); } catch (e) {}
    var q = [];
    ["first_name", "last_name", "email", "phone"].forEach(function (k) { if (lead[k]) q.push(encodeURIComponent(map[k] || k) + "=" + encodeURIComponent(lead[k])); });
    /* Pass intake context along so it can be read from the appointment/contact. */
    ["water_source", "system_interest", "system_config", "water_problems", "city", "lead_source", "utm_source", "utm_medium", "utm_campaign"].forEach(function (k) { if (lead[k]) q.push(encodeURIComponent(k) + "=" + encodeURIComponent(lead[k])); });
    return cal.calendarEmbedUrl + (cal.calendarEmbedUrl.indexOf("?") > -1 ? "&" : "?") + q.join("&");
  }

  function loadEmbedScript() {
    if (document.querySelector('script[src="' + GHL_EMBED_JS + '"]')) return;
    var s = document.createElement("script"); s.src = GHL_EMBED_JS; s.async = true; document.head.appendChild(s);
  }

  function fallback(el, kind) {
    var phone = el.getAttribute("data-phone") || "(952) 952-6206", tel = el.getAttribute("data-tel") || "+19529526206";
    el.setAttribute("data-state", "fallback");
    el.innerHTML = '<div class="ghl-fallback"><h3>' + (kind === "calendar" ? "Online booking is opening soon." : "Online intake is opening soon.") +
      '</h3><p>Call or text and we’ll get you on the schedule right away. We’ll answer within 24 hours.</p>' +
      '<a class="phone" href="tel:' + tel + '">' + phone + '</a>' +
      '<a class="btn btn-navy" href="/preview/schedule/">Schedule page</a></div>';
  }

  function renderCalendar(el, prefill) {
    var url = calendarUrl(prefill);
    if (!url) { fallback(el, "calendar"); return false; }
    el.setAttribute("data-state", "loading");
    el.innerHTML = '<div class="ghl-loading"><span class="spinner"></span>Loading available times…</div>' +
      '<iframe src="' + url + '" title="Schedule your MSP Pure Water consultation" loading="lazy" scrolling="no" ' +
      'id="msp-ghl-calendar" style="min-height:760px"></iframe>';
    var f = el.querySelector("iframe");
    f.addEventListener("load", function () { el.setAttribute("data-state", "ready"); if (window.MSPTrack) window.MSPTrack.once("calendar_viewed", { calendar: (C.calendar || {}).calendarId }); });
    loadEmbedScript();
    /* Best-effort booking detection from the widget; the reliable path is the
       calendar's custom thank-you redirect to /booked/ (see INTEGRATION.md). */
    window.addEventListener("message", function (ev) {
      if (!/leadconnectorhq|msgsndr|gohighlevel/.test(ev.origin || "")) return;
      var d = ev.data; var s = typeof d === "string" ? d : JSON.stringify(d || {});
      if (/book(ed|ing)[-_ ]?(success|confirm)|appointment[-_ ]?(booked|created)/i.test(s)) {
        if (window.MSPTrack) window.MSPTrack.once("appointment_booked", { via: "widget_message" });
        el.dispatchEvent(new CustomEvent("msp:booked", { bubbles: true }));
      }
    });
    return true;
  }

  function renderForm(el) {
    var lead = C.lead || {};
    if (!set(lead.formEmbedUrl)) { fallback(el, "form"); return false; }
    el.setAttribute("data-state", "loading");
    el.innerHTML = '<div class="ghl-loading"><span class="spinner"></span>Loading…</div>' +
      '<iframe src="' + lead.formEmbedUrl + '" title="MSP Pure Water intake form" loading="lazy" scrolling="no" id="msp-ghl-form" style="min-height:900px"></iframe>';
    el.querySelector("iframe").addEventListener("load", function () { el.setAttribute("data-state", "ready"); });
    loadEmbedScript();
    return true;
  }

  /* Developer readiness banner: only on localhost or with ?msp-debug=1 */
  function devBanner() {
    var show = /localhost|127\.0\.0\.1/.test(location.hostname) || (window.MSPTrack && window.MSPTrack.debug);
    document.querySelectorAll(".dev-banner").forEach(function (b) {
      if (!show) return; var st = status();
      b.setAttribute("data-show", "true");
      b.innerHTML = "<b>Integration readiness</b> (visible only on localhost / ?msp-debug=1) &mdash; " +
        "Location ID: " + (st.locationId ? "set" : "<code>GHL_LOCATION_ID_HERE</code>") + " &middot; Lead (" + st.leadMode + "): " + (st.leadReady ? "ready" : "<code>placeholder</code>") +
        " &middot; Calendar: " + (st.calendarReady ? "ready" : "<code>GHL_CALENDAR_EMBED_URL_HERE</code>") + " &middot; Analytics: " + (st.analytics ? "configured" : "dataLayer only") +
        ". Edit <code>assets/js/ghl.config.js</code>.";
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", devBanner); else devBanner();

  window.MSPCRM = { submitLead: submitLead, buildPayload: buildPayload, renderCalendar: renderCalendar, renderForm: renderForm, calendarUrl: calendarUrl, status: status, loadLead: loadLead, saveLead: saveLead };
})();
