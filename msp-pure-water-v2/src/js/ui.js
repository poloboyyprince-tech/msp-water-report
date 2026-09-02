/* MSP Pure Water — UI behaviours (no CRM logic here) */
(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  /* ?static=1 = QA/screenshot mode: no video, no motion, everything revealed */
  var STATIC = /[?&]static=1/.test(location.search); if (STATIC) { reduce = true; var sv = document.querySelector(".hero-media video"); if (sv) { var im = document.createElement("img"); im.src = sv.getAttribute("poster"); im.alt = ""; sv.replaceWith(im); } }
  var $ = function (s, r) { return (r || document).querySelector(s); }, $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* Announcement bar */
  var ann = $(".announce"); if (ann) { try { if (sessionStorage.getItem("msp_ann") === "1") ann.hidden = true; } catch (e) {} var x = $(".x", ann); if (x) x.addEventListener("click", function () { ann.hidden = true; try { sessionStorage.setItem("msp_ann", "1"); } catch (e) {} }); }

  /* Header: transparent over hero */
  var header = $(".header");
  if (header && header.classList.contains("over-hero")) {
    var onScroll = function () { header.classList.toggle("is-scrolled", window.scrollY > 40); }; onScroll(); window.addEventListener("scroll", onScroll, { passive: true });
  }
  /* Desktop dropdowns */
  $$(".nav [aria-haspopup]").forEach(function (btn) {
    var sub = btn.nextElementSibling;
    function open(v) { btn.setAttribute("aria-expanded", v); sub.setAttribute("data-open", v); }
    btn.addEventListener("click", function () { open(btn.getAttribute("aria-expanded") !== "true"); });
    btn.parentElement.addEventListener("mouseenter", function () { open("true"); });
    btn.parentElement.addEventListener("mouseleave", function () { open("false"); });
    btn.parentElement.addEventListener("focusout", function (e) { if (!btn.parentElement.contains(e.relatedTarget)) open("false"); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") open("false"); });
  });
  /* Mobile nav */
  var mnav = $(".mnav"), burger = $(".burger");
  if (mnav && burger) {
    var last;
    function toggle(v) { mnav.setAttribute("data-open", v); burger.setAttribute("aria-expanded", v); document.body.style.overflow = v === "true" ? "hidden" : ""; if (v === "true") { last = document.activeElement; $(".mnav .x").focus(); } else if (last) last.focus(); }
    burger.addEventListener("click", function () { toggle("true"); });
    $(".mnav .x").addEventListener("click", function () { toggle("false"); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && mnav.getAttribute("data-open") === "true") toggle("false"); });
  }

  /* Reveal on scroll */
  var rev = $$(".reveal");
  if (rev.length && !reduce && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) { es.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } }); }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    rev.forEach(function (el) { io.observe(el); });
  } else rev.forEach(function (el) { el.classList.add("in"); });

  /* Parallax (2 depths, transform only, never scroll-jacks) */
  var px = $$("[data-parallax]");
  if (px.length && !reduce) {
    var raf = false;
    function tick() { raf = false; var vh = window.innerHeight; px.forEach(function (el) { var r = el.getBoundingClientRect(); if (r.bottom < 0 || r.top > vh) return; var p = (r.top + r.height / 2 - vh / 2) / vh; el.style.transform = "translate3d(0," + (p * parseFloat(el.getAttribute("data-parallax") || 40) * -1).toFixed(1) + "px,0)"; }); }
    window.addEventListener("scroll", function () { if (!raf) { raf = true; requestAnimationFrame(tick); } }, { passive: true }); tick();
  }

  /* Hero video: respect reduced motion + data saver; pause when offscreen */
  var hv = $(".hero-media video");
  if (hv) {
    var saver = navigator.connection && navigator.connection.saveData;
    if (reduce || saver) { hv.removeAttribute("autoplay"); hv.pause(); hv.setAttribute("data-paused", "true"); }
    else { var p = hv.play(); if (p && p.catch) p.catch(function () {}); }
    var tg = $(".video-toggle");
    if (tg) tg.addEventListener("click", function () { if (hv.paused) { hv.play(); tg.textContent = "Pause video"; } else { hv.pause(); tg.textContent = "Play video"; } });
    if (tg && (reduce || saver)) tg.textContent = "Play video";
    if ("IntersectionObserver" in window) new IntersectionObserver(function (es) { es.forEach(function (en) { if (hv.getAttribute("data-paused")) return; if (en.isIntersecting) hv.play().catch(function () {}); else hv.pause(); }); }).observe(hv);
  }

  /* Water source cards & any [data-intake] element seed the Find My System state */
  document.addEventListener("click", function (e) {
    var el = e.target.closest("[data-intake]"); if (!el || !window.MSPIntake) return;
    try { var obj = JSON.parse(el.getAttribute("data-intake")); window.MSPIntake.setPreset(obj);
      if (window.MSPTrack && obj.water_source) window.MSPTrack.event(obj.water_source === "Well Water" ? "well_water_selected" : obj.water_source === "City Water" ? "city_water_selected" : "drinking_water_selected", { via: el.getAttribute("data-intake-via") || "card" });
      if (window.MSPTrack && obj.system_interest === "Reverse Osmosis") window.MSPTrack.event("ro_selected", { via: el.getAttribute("data-intake-via") || "card" });
    } catch (err) {}
  }, true);

  /* Problem explorer */
  var ex = $("[data-explorer]");
  if (ex) {
    var data = JSON.parse($("#explorer-data").textContent), panel = $(".explorer-panel", ex), chips = $$(".chip", ex);
    function show(id) {
      var p = data[id]; if (!p) return;
      chips.forEach(function (c) { c.setAttribute("aria-selected", c.getAttribute("data-id") === id ? "true" : "false"); });
      panel.innerHTML = '<span class="tag">' + p.tag + "</span><h3>" + p.label + "</h3><dl><div><dt>What causes it</dt><dd>" + p.cause + "</dd></div><div><dt>How MSP approaches it</dt><dd>" + p.approach + "</dd></div><div><dt>Which systems may apply</dt><dd><div class=\"syslinks\">" +
        p.systems.map(function (s) { return '<a href="' + s.href + '">' + s.name + " &middot; $" + s.price + "</a>"; }).join("") + "</dd></div></dl>" +
        '<div class="explorer-actions"><a class="btn btn-gold" href="/find-my-system/" data-intake=\'' + JSON.stringify({ water_problems: [p.label], system_interest: p.interest }).replace(/'/g, "&#39;") + '\' data-intake-via="problem_explorer">Find my system</a>' +
        (p.href ? '<a class="btn btn-outline on-light" href="' + p.href + '">Read more</a>' : "") + "</div>";
      panel.setAttribute("data-current", id);
    }
    chips.forEach(function (c) { c.addEventListener("click", function () { show(c.getAttribute("data-id")); }); });
    var initial = (location.hash || "").replace("#problem-", ""); show(data[initial] ? initial : chips[0].getAttribute("data-id"));
  }

  /* Thank-you / schedule pages: render the GHL calendar with prefill */
  $$("[data-ghl-calendar]").forEach(function (el) { if (window.MSPCRM) window.MSPCRM.renderCalendar(el); });
  $$("[data-ghl-form]").forEach(function (el) { if (window.MSPCRM) window.MSPCRM.renderForm(el); });
  var lead = window.MSPCRM && window.MSPCRM.loadLead();
  $$("[data-lead-name]").forEach(function (el) { if (lead && lead.first_name) el.textContent = lead.first_name; });
  $$("[data-lead-summary]").forEach(function (el) { if (!lead) { el.hidden = true; return; } el.innerHTML = "<div><b>Your water</b>" + (lead.water_source || "—") + "</div><div><b>Experiencing</b>" + (lead.water_problems || "—") + "</div><div><b>Interested in</b>" + (lead.system_interest || "—") + "</div>"; });

  /* Booking confirmation page */
  var booked = $("[data-booked]");
  if (booked) {
    var q = function (n) { var m = new RegExp("[?&]" + n + "=([^&#]*)").exec(location.search); return m ? decodeURIComponent(m[1].replace(/\+/g, " ")) : ""; };
    var name = q("first_name") || q("name") || (lead && lead.first_name) || "";
    var date = q("date") || q("appointment_date") || q("start_date") || "", time = q("time") || q("appointment_time") || q("start_time") || "";
    $$("[data-booked-name]").forEach(function (el) { el.textContent = name ? name + ", you’re scheduled." : "You’re scheduled."; });
    var d = $("[data-booked-date]"), t = $("[data-booked-time]");
    if (d) d.textContent = date || "See your confirmation email"; if (t) t.textContent = time || "See your confirmation email";
    if (window.MSPTrack) window.MSPTrack.once("appointment_booked", { via: "thank_you_page" });
    try { sessionStorage.setItem("msp_booked", "1"); } catch (e) {}
  }
  document.addEventListener("msp:booked", function () { var s = $("[data-booked-inline]"); if (s) { s.hidden = false; s.scrollIntoView({ behavior: reduce ? "auto" : "smooth" }); } });

  /* Current year */
  $$("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();
