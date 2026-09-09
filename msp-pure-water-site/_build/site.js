/* MSP Pure Water — static behaviour (replaces the original React interactivity) */
(function () {
  "use strict";

  /* Never let a stale scroll-lock survive a navigation or a half-open drawer. */
  document.body.style.overflow = "";

  /* ---- FAQ / disclosure accordions -------------------------------------- */
  document.querySelectorAll("button").forEach(function (btn) {
    var panel = btn.nextElementSibling;
    if (!panel || !panel.classList.contains("overflow-hidden")) return;
    if (!/max-h-0/.test(panel.className)) return;
    var icon = btn.querySelector("svg");
    btn.setAttribute("aria-expanded", "false");
    btn.addEventListener("click", function () {
      var open = panel.classList.toggle("max-h-0");
      var isOpen = !open;
      panel.style.maxHeight = isOpen ? panel.scrollHeight + 32 + "px" : "";
      btn.setAttribute("aria-expanded", String(isOpen));
      if (icon) icon.classList.toggle("rotate-45", isOpen);
    });
  });

  /* ---- Announcement bar dismiss ----------------------------------------- */
  var dismiss = document.querySelector('[aria-label="Dismiss announcement"]');
  if (dismiss) {
    dismiss.addEventListener("click", function () {
      var bar = dismiss.closest("div");
      if (bar) bar.style.display = "none";
    });
  }

  /* ---- Mobile drawer ----------------------------------------------------- */
  var drawer = document.getElementById("mobile-drawer");
  var opener = document.querySelector('[aria-label="Open menu"]');
  function setDrawer(open) {
    if (!drawer) return;
    drawer.classList.toggle("hidden", !open);
    // Only lock scrolling while the drawer is genuinely open.
    document.body.style.overflow = open && !drawer.classList.contains("hidden") ? "hidden" : "";
  }
  if (opener) opener.addEventListener("click", function () { setDrawer(true); });
  if (drawer) {
    drawer.querySelectorAll("[data-drawer-close]").forEach(function (el) {
      el.addEventListener("click", function () { setDrawer(false); });
    });
    drawer.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () { setDrawer(false); });
    });
  }
  window.addEventListener("pageshow", function () {
    setDrawer(false);
    document.body.style.overflow = "";
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") setDrawer(false);
  });

  /* ---- Cookie consent ---------------------------------------------------- */
  var banner = document.getElementById("cookie-banner");
  var KEY = "msp-cookie-choice";
  function stored() { try { return localStorage.getItem(KEY); } catch (e) { return "seen"; } }
  function remember(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
  if (banner && !stored()) {
    setTimeout(function () { banner.classList.remove("hidden"); }, 900);
    banner.querySelectorAll("[data-cookie]").forEach(function (b) {
      b.addEventListener("click", function () {
        remember(b.getAttribute("data-cookie"));
        banner.classList.add("hidden");
      });
    });
  }

  /* ---- Header condense on scroll ----------------------------------------- */
  var header = document.querySelector("header");
  if (header) {
    var onScroll = function () {
      var y = window.scrollY > 40;
      header.classList.toggle("bg-background/95", y);
      header.classList.toggle("bg-background/60", !y);
      header.classList.toggle("shadow-lg", y);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }


  /* ---- Product variant selection + price ---------------------------------- */
  var vroot = document.querySelector("[data-variants]");
  if (vroot) {
    var VARIANTS = {};
    try { VARIANTS = JSON.parse(vroot.getAttribute("data-variants")); } catch (e) {}
    var groups = {};
    vroot.querySelectorAll("[data-opt]").forEach(function (btn) {
      var g = btn.getAttribute("data-opt");
      (groups[g] = groups[g] || []).push(btn);
    });
    var chosen = {};
    Object.keys(groups).forEach(function (g) {
      chosen[g] = groups[g][0].getAttribute("data-val");
    });
    var priceEl = vroot.querySelector("[data-price]");
    function norm(v) { return String(v).replace(/\s*\(\+\$[\d,]+\)\s*$/, "").trim(); }
    function refresh() {
      var keys = Object.keys(groups).sort(function (a, b) { return a - b; });
      var combo = keys.map(function (g) { return norm(chosen[g]); }).join(" / ");
      var price = VARIANTS[combo];
      if (price === undefined) price = VARIANTS[keys.map(function(g){return chosen[g];}).join(" / ")];
      if (price === undefined && keys.length === 1) price = VARIANTS[norm(chosen[keys[0]])];
      if (price !== undefined && priceEl) priceEl.textContent = price;
      keys.forEach(function (g) {
        var lbl = vroot.querySelector('[data-optlabel="' + g + '"]');
        if (lbl) lbl.textContent = chosen[g];
        groups[g].forEach(function (btn) {
          var on = btn.getAttribute("data-val") === chosen[g];
          btn.classList.toggle("border-accent", on);
          btn.classList.toggle("bg-accent", on);
          btn.classList.toggle("text-accent-foreground", on);
          btn.classList.toggle("font-semibold", on);
          btn.classList.toggle("border-border", !on);
          btn.classList.toggle("hover:border-accent/60", !on);
        });
      });
    }
    Object.keys(groups).forEach(function (g) {
      groups[g].forEach(function (btn) {
        btn.addEventListener("click", function () {
          chosen[g] = btn.getAttribute("data-val");
          refresh();
        });
      });
    });
    refresh();
  }


  /* ---- Scheduling wizard --------------------------------------------------- */
  var dataEl = document.getElementById("sched-data");
  if (dataEl) {
    var SYS = {};
    try { SYS = JSON.parse(dataEl.textContent); } catch (e) {}
    var state = { water: null, system: null, price: null, date: "", window: "", name: "", phone: "", addr: "" };
    var LABELS = ["Water", "System", "Time", "Details", "Confirm"];
    var steps = document.getElementById("sched-steps");

    function show(n) {
      document.querySelectorAll("[data-step]").forEach(function (s) {
        s.hidden = Number(s.getAttribute("data-step")) !== n;
      });
      if (steps) {
        steps.innerHTML = LABELS.map(function (l, i) {
          var on = i + 1 === n, done = i + 1 < n;
          return '<li class="px-2 py-1 rounded ' +
            (on ? "text-accent font-semibold" : done ? "text-foreground/60" : "text-muted-foreground/40") +
            '">' + l + "</li>";
        }).join('<li class="text-muted-foreground/30">&#183;</li>');
      }
      window.scrollTo({ top: 0, behavior: "smooth" });
    }

    document.querySelectorAll("[data-water]").forEach(function (b) {
      b.addEventListener("click", function () {
        state.water = b.getAttribute("data-water");
        var list = document.getElementById("sys-list");
        list.innerHTML = (SYS[state.water] || []).map(function (s) {
          return '<button type="button" class="glass-card-hover rounded-xl p-5 text-left w-full flex items-center justify-between gap-4" data-sys="' +
            s[0] + '" data-price="' + s[1] + '"><span class="font-heading font-bold text-foreground">' + s[0] +
            '</span><span class="text-accent font-heading font-bold whitespace-nowrap">' + s[1] + "</span></button>";
        }).join("");
        list.querySelectorAll("[data-sys]").forEach(function (sb) {
          sb.addEventListener("click", function () {
            state.system = sb.getAttribute("data-sys");
            state.price = sb.getAttribute("data-price");
            show(3);
          });
        });
        show(2);
      });
    });

    document.querySelectorAll("[data-back]").forEach(function (b) {
      b.addEventListener("click", function () { show(Number(b.getAttribute("data-back"))); });
    });

    document.querySelectorAll(".win-btn").forEach(function (b) {
      b.addEventListener("click", function () {
        state.window = b.getAttribute("data-window");
        document.querySelectorAll(".win-btn").forEach(function (o) {
          var on = o === b;
          o.classList.toggle("border-accent", on);
          o.classList.toggle("bg-accent", on);
          o.classList.toggle("text-accent-foreground", on);
          o.classList.toggle("border-border", !on);
        });
      });
    });

    var to4 = document.getElementById("to-4");
    if (to4) to4.addEventListener("click", function () {
      state.date = (document.getElementById("sched-date") || {}).value || "";
      if (!state.date || !state.window) { alert("Please pick a date and an arrival window."); return; }
      show(4);
    });

    var to5 = document.getElementById("to-5");
    if (to5) to5.addEventListener("click", function () {
      state.name = (document.getElementById("f-name") || {}).value || "";
      state.phone = (document.getElementById("f-phone") || {}).value || "";
      state.addr = (document.getElementById("f-addr") || {}).value || "";
      if (!state.name || !state.phone) { alert("Please add your name and a phone number so we can confirm."); return; }
      var rows = [["Water", state.water === "well" ? "Well water" : "City water"],
                  ["System", state.system], ["Price", state.price],
                  ["Date", state.date], ["Arrival", state.window],
                  ["Name", state.name], ["Phone", state.phone], ["Address", state.addr || "—"]];
      document.getElementById("summary").innerHTML = rows.map(function (r) {
        return '<div class="flex justify-between gap-4 border-b border-accent/10 pb-2"><dt class="text-muted-foreground">' +
          r[0] + '</dt><dd class="text-foreground font-medium text-right">' + r[1] + "</dd></div>";
      }).join("");
      var msg = "Installation request — " + state.system + " (" + state.price + "). " +
        state.date + ", " + state.window + ". " + state.name + ", " + state.phone +
        (state.addr ? ", " + state.addr : "") + ".";
      var sms = document.getElementById("send-sms");
      var mail = document.getElementById("send-mail");
      if (sms) sms.href = "sms:9529526206?&body=" + encodeURIComponent(msg);
      if (mail) mail.href = "mailto:info@msppurewaterco.com?subject=" +
        encodeURIComponent("Installation request — " + state.system) + "&body=" + encodeURIComponent(msg);
      show(5);
    });

    show(1);
  }

  /* ---- Smooth in-page anchors -------------------------------------------- */
  document.querySelectorAll('a[href*="#"]').forEach(function (a) {
    var hash = a.getAttribute("href").split("#")[1];
    if (!hash) return;
    a.addEventListener("click", function (e) {
      var t = document.getElementById(hash);
      if (!t) return;
      e.preventDefault();
      setDrawer(false);
      t.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
})();
