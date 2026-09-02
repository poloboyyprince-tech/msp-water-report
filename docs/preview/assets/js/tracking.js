/* MSP Pure Water — AnalyticsTracking + lead attribution
   Every conversion event goes to window.dataLayer (GTM/GA4 compatible),
   plus gtag()/fbq() when those globals exist. Attribution is captured on
   first landing and attached to every CRM submission. */
(function () {
  "use strict";
  var cfg = (window.MSP_GHL && window.MSP_GHL.analytics) || {};
  var dl = (window.dataLayer = window.dataLayer || []);
  var DEBUG = /[?&]msp-debug=1/.test(location.search) || localStorage.getItem("msp_debug") === "1";
  if (/[?&]msp-debug=1/.test(location.search)) { try { localStorage.setItem("msp_debug", "1"); } catch (e) {} }

  /* ---------- Attribution (first-touch, persisted) ---------- */
  var KEY = "msp_attr";
  function qs(name) { var m = new RegExp("[?&]" + name + "=([^&#]*)").exec(location.search); return m ? decodeURIComponent(m[1].replace(/\+/g, " ")) : ""; }
  function leadSource(a) {
    var ref = (a.referrer || "").toLowerCase(), src = (a.utm_source || "").toLowerCase(), med = (a.utm_medium || "").toLowerCase();
    if (a.gclid || (src === "google" && /cpc|ppc|paid/.test(med))) return "Google Ads";
    if (/gbp|gmb|google[-_ ]?business|business\.google/.test(src + " " + med + " " + (a.utm_campaign || "") + " " + ref)) return "Google Business Profile";
    if (a.fbclid || /facebook|instagram|^fb$|^ig$|meta/.test(src) || /facebook\.|instagram\.|fb\.com|l\.facebook/.test(ref)) return "Facebook / Instagram";
    if (src === "google" || /google\./.test(ref)) return "Google Organic";
    if (src) return "Campaign: " + a.utm_source + (a.utm_medium ? " / " + a.utm_medium : "");
    if (!ref) return "Direct";
    return "Referral";
  }
  function capture() {
    var existing = null;
    try { existing = JSON.parse(localStorage.getItem(KEY) || "null"); } catch (e) {}
    var a = {
      utm_source: qs("utm_source"), utm_medium: qs("utm_medium"), utm_campaign: qs("utm_campaign"),
      utm_content: qs("utm_content"), utm_term: qs("utm_term"), gclid: qs("gclid"), fbclid: qs("fbclid"),
      landing_page: location.href.split("#")[0],
      referrer: (document.referrer && document.referrer.indexOf(location.host) === -1) ? document.referrer : "",
      first_seen: new Date().toISOString()
    };
    var hasCampaign = a.utm_source || a.gclid || a.fbclid;
    if (existing && !hasCampaign) { a = existing; }               /* keep first touch */
    else if (existing && hasCampaign) { a.first_seen = existing.first_seen; a.website_entry_page = existing.website_entry_page; }
    a.website_entry_page = a.website_entry_page || a.landing_page;
    a.lead_source = leadSource(a);
    try { localStorage.setItem(KEY, JSON.stringify(a)); } catch (e) {}
    return a;
  }
  var attr = capture();

  /* ---------- Events ---------- */
  function event(name, props) {
    var payload = Object.assign({ event: name, page_path: location.pathname }, props || {});
    dl.push(payload);
    try { if (typeof window.gtag === "function" && cfg.ga4Id) window.gtag("event", name, props || {}); } catch (e) {}
    try { if (typeof window.fbq === "function") window.fbq("trackCustom", name, props || {}); } catch (e) {}
    if (DEBUG) console.log("[MSP track]", name, props || {});
  }
  var fired = {};
  function once(name, props) { if (fired[name]) return; fired[name] = true; event(name, props); }

  /* Optional GTM loader (only when an ID is configured). */
  if (cfg.gtmId) {
    dl.push({ "gtm.start": new Date().getTime(), event: "gtm.js" });
    var s = document.createElement("script"); s.async = true;
    s.src = "https://www.googletagmanager.com/gtm.js?id=" + encodeURIComponent(cfg.gtmId);
    document.head.appendChild(s);
  }

  /* Auto-binding of common interactions. */
  function bind() {
    document.addEventListener("click", function (e) {
      var a = e.target.closest("a,button"); if (!a) return;
      var href = a.getAttribute("href") || "";
      var t = a.getAttribute("data-track");
      if (t) { event(t, { label: a.getAttribute("data-track-label") || a.textContent.trim().slice(0, 60) }); }
      else if (/^tel:/.test(href)) { event("phone_click", { label: a.textContent.trim().slice(0, 40) }); }
      else if (/\/schedule\/?(\?|#|$)/.test(href)) { event("schedule_click", { label: a.textContent.trim().slice(0, 40) }); }
      else if (/\/find-my-system\/?(\?|#|$)/.test(href) || a.hasAttribute("data-fms-open")) { event("find_my_system_opened", { label: a.textContent.trim().slice(0, 40) }); }
      else if (/best-price/.test(href) || a.hasAttribute("data-bpg")) { event("best_price_guarantee_cta", {}); }
    }, true);

    /* Viewport-based events */
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          var n = en.target.getAttribute("data-view-event"); if (n) once(n, { section: en.target.id || "" });
          io.unobserve(en.target);
        });
      }, { threshold: 0.35 });
      document.querySelectorAll("[data-view-event]").forEach(function (el) { io.observe(el); });
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bind); else bind();

  window.MSPTrack = { event: event, once: once, attribution: function () { return attr; }, debug: DEBUG };
})();
