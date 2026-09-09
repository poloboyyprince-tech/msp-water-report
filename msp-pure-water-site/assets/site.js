/* Restores the interactions React provided on the original site.
   Nothing here adds behaviour the original does not have - notably the
   header hamburger, which is inert on the Amboras build too. */
(function () {
  "use strict";

  /* Collapsible panels: FAQ questions and the product-page accordions.
     Markup pattern: <button>…</button><div class="… max-h-0">…</div> */
  document.querySelectorAll("button").forEach(function (btn) {
    var panel = btn.nextElementSibling;
    if (!panel || !panel.classList.contains("overflow-hidden")) return;
    var chevron = btn.querySelector("svg");
    var open = !/max-h-0/.test(panel.className);
    btn.setAttribute("aria-expanded", String(open));
    btn.addEventListener("click", function () {
      open = !open;
      panel.classList.toggle("max-h-0", !open);
      panel.style.maxHeight = open ? panel.scrollHeight + 32 + "px" : "";
      btn.setAttribute("aria-expanded", String(open));
      if (chevron) chevron.classList.toggle("rotate-180", open);
    });
  });


  /* Scroll reveals. The stylesheet ships .reveal/.reveal-left/.reveal-right at
     opacity 0 and only paints them once .visible is added - React did that with
     an IntersectionObserver, so without this every section below the hero stays
     invisible. Anything already on screen is revealed immediately. */
  var reveals = document.querySelectorAll(".reveal, .reveal-left, .reveal-right");
  if (reveals.length) {
    if (!("IntersectionObserver" in window)) {
      reveals.forEach(function (el) { el.classList.add("visible"); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            e.target.classList.add("visible");
            io.unobserve(e.target);
          }
        });
      }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });
      reveals.forEach(function (el) {
        var r = el.getBoundingClientRect();
        if (r.top < window.innerHeight && r.bottom > 0) el.classList.add("visible");
        else io.observe(el);
      });
    }
  }

  /* Announcement bar dismiss */
  var dismiss = document.querySelector('[aria-label="Dismiss announcement"]');
  if (dismiss) {
    dismiss.addEventListener("click", function () {
      var bar = dismiss.parentElement;
      if (bar) bar.style.display = "none";
    });
  }

  /* Product option selection. The original swaps the highlighted button and
     the "Type — X" label; price is identical across variants except on the
     dual-tank system, whose add-on prices are read from data-variants. */
  var priceEl = document.querySelector("[data-price]");
  var groups = {};
  document.querySelectorAll("[data-opt]").forEach(function (b) {
    (groups[b.getAttribute("data-opt")] = groups[b.getAttribute("data-opt")] || []).push(b);
  });
  Object.keys(groups).forEach(function (g) {
    groups[g].forEach(function (btn) {
      btn.addEventListener("click", function () {
        groups[g].forEach(function (o) {
          var on = o === btn;
          o.classList.toggle("border-accent", on);
          o.classList.toggle("bg-accent", on);
          o.classList.toggle("text-accent-foreground", on);
          o.classList.toggle("font-semibold", on);
          o.classList.toggle("border-border", !on);
        });
        var lbl = document.querySelector('[data-optlabel="' + g + '"]');
        if (lbl) lbl.textContent = btn.getAttribute("data-val") || btn.textContent.trim();
      });
    });
  });
})();
