/* MSP Pure Water — UI behaviours (no CRM logic here) */
(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  /* ?static=1 = QA/screenshot mode: no video, no motion, everything revealed */
  var STATIC = /[?&]static=1/.test(location.search); if (STATIC) { reduce = true; document.querySelectorAll(".hero-media video,.phero-media video").forEach(function (sv) { var im = document.createElement("img"); im.src = sv.getAttribute("poster"); im.alt = ""; sv.replaceWith(im); }); }
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
    var sub = btn.nextElementSibling, timer;
    function open(v) { clearTimeout(timer); btn.setAttribute("aria-expanded", v); sub.setAttribute("data-open", v); }
    btn.addEventListener("click", function () { open(btn.getAttribute("aria-expanded") !== "true"); });
    btn.parentElement.addEventListener("mouseenter", function () { open("true"); });
    /* grace period so the pointer can travel into the panel */
    btn.parentElement.addEventListener("mouseleave", function () { clearTimeout(timer); timer = setTimeout(function () { open("false"); }, 320); });
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

  /* Page transitions: short fade out on internal navigation, fade in on load */
  if (!reduce) {
    document.addEventListener("click", function (e) {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var a = e.target.closest("a[href]"); if (!a) return;
      var href = a.getAttribute("href") || "";
      if (a.target === "_blank" || a.hasAttribute("download") || /^(tel:|mailto:|#|javascript:)/.test(href) || a.hasAttribute("data-no-transition")) return;
      var url; try { url = new URL(a.href, location.href); } catch (err) { return; }
      if (url.origin !== location.origin) return;
      if (url.pathname === location.pathname && url.search === location.search && url.hash) return;
      e.preventDefault(); document.body.classList.add("page-leave");
      setTimeout(function () { location.href = url.href; }, 190);
    });
    window.addEventListener("pageshow", function () { document.body.classList.remove("page-leave"); });
  }

  /* Hero video: respect reduced motion + data saver; pause when offscreen */
  var hv = $(".hero-media video");
  $$(".phero-media video").forEach(function (v) {
    if (reduce || (navigator.connection && navigator.connection.saveData)) { v.removeAttribute("autoplay"); v.pause(); var pi = document.createElement("img"); pi.src = v.getAttribute("poster"); pi.alt = ""; v.replaceWith(pi); return; }
    var pp = v.play(); if (pp && pp.catch) pp.catch(function () {});
    if ("IntersectionObserver" in window) new IntersectionObserver(function (es) { es.forEach(function (en) { if (en.isIntersecting) v.play().catch(function () {}); else v.pause(); }); }).observe(v);
  });
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
        '<div class="explorer-actions"><a class="btn btn-gold" href="/preview/find-my-system/" data-intake=\'' + JSON.stringify({ water_problems: [p.label], system_interest: p.interest }).replace(/'/g, "&#39;") + '\' data-intake-via="problem_explorer">Find my system</a>' +
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

  /* System configurator (product buy box) */
  $$("[data-configurator]").forEach(function (box) {
    var cfg = JSON.parse(box.querySelector("script[type='application/json']").textContent);
    var totalEl = box.querySelector("[data-total]"), cta = box.querySelector("[data-cta]"), lineEl = box.querySelector("[data-config-line]");
    function money(n) { return "$" + n.toLocaleString("en-US"); }
    function state() {
      var total = cfg.price, parts = [];
      cfg.options.forEach(function (g) {
        if (g.type === "single") { var r = box.querySelector('input[name="cfg-' + g.key + '"]:checked'); if (r) { var c = g.choices[parseInt(r.value, 10)]; total += c.add; parts.push(c.label); } }
        else { var cb = box.querySelector('input[name="cfg-' + g.key + '"]'); if (cb && cb.checked) { total += g.add; parts.push(g.label); } }
      });
      return { total: total, parts: parts, line: cfg.name + (parts.length ? " + " + parts.join(" + ") : "") + " — " + money(total) + " installed" };
    }
    function render() {
      var s = state(); if (totalEl) totalEl.textContent = money(s.total); if (lineEl) lineEl.textContent = s.parts.length ? s.parts.join(" · ") : "Standard configuration";
      if (cta) { cta.setAttribute("href", "/preview/schedule/?system=" + encodeURIComponent(cfg.id)); cta.textContent = "Schedule installation · " + money(s.total); }
      if (window.MSPIntake) window.MSPIntake.setPreset({ system_interest: cfg.interest, water_source: cfg.water_source || "", system_id: cfg.id, system_config: s.line });
    }
    box.addEventListener("change", render);
    if (cta) cta.addEventListener("click", function () { render(); if (window.MSPTrack) window.MSPTrack.event("schedule_click", { label: "configurator", system: cfg.id, total: state().total }); });
    render();
  });
  /* Gallery thumbs */
  $$(".gallery").forEach(function (g) { var main = g.querySelector(".main img"); g.querySelectorAll(".thumbs button").forEach(function (b) { b.addEventListener("click", function () { main.src = b.getAttribute("data-src"); main.alt = b.getAttribute("data-alt") || ""; g.querySelectorAll(".thumbs button").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); }); }); }); });
  /* Schedule page: show chosen configuration */
  $$("[data-config-summary]").forEach(function (el) {
    var pre = (window.MSPIntake && window.MSPIntake.preset()) || {}; var q = new URLSearchParams(location.search);
    if (pre.system_config) { el.setAttribute("data-show", "true"); el.querySelector(".cs-line").textContent = pre.system_config; }
    else if (q.get("system")) { el.setAttribute("data-show", "true"); el.querySelector(".cs-line").textContent = q.get("system").replace(/-/g, " "); }
  });

  /* System carousel */
  $$("[data-carousel]").forEach(function (c) {
    c.classList.add("js");
    var slides = $$(".slide", c), dots = $$("[data-slide]", c), cur = $("[data-current]", c), i = 0;
    function show(n, focus) {
      i = (n + slides.length) % slides.length;
      slides.forEach(function (s, k) { s.setAttribute("data-active", k === i ? "true" : "false"); });
      dots.forEach(function (d, k) { d.setAttribute("aria-selected", k === i ? "true" : "false"); });
      if (cur) cur.textContent = i + 1;
      if (focus) { try { slides[i].querySelector("h3").setAttribute("tabindex", "-1"); slides[i].querySelector("h3").focus({ preventScroll: true }); } catch (e) {} }
    }
    $("[data-prev]", c).addEventListener("click", function () { show(i - 1, true); });
    $("[data-next]", c).addEventListener("click", function () { show(i + 1, true); });
    dots.forEach(function (d) { d.addEventListener("click", function () { show(parseInt(d.getAttribute("data-slide"), 10), true); }); });
    c.addEventListener("keydown", function (e) { if (e.key === "ArrowRight") { show(i + 1, true); } else if (e.key === "ArrowLeft") { show(i - 1, true); } });
    /* deep link: /city-water-filtration/#dual-tank-city */
    var h = (location.hash || "").slice(1); slides.forEach(function (s, k) { if (s.id === h) show(k, false); });
    window.addEventListener("hashchange", function () { var hh = location.hash.slice(1); slides.forEach(function (s, k) { if (s.id === hh) show(k, false); }); });
  });

  /* Current year */
  $$("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();
