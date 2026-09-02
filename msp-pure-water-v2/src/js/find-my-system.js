/* MSP Pure Water — FIND MY SYSTEM progressive intake (presentation only)
   Renders into any element with [data-fms]. Submission goes through
   MSPCRM.submitLead(); success is only shown when the CRM accepted it. */
(function () {
  "use strict";
  var STEPS = [
    { key: "water_source", title: "What type of water does your home use?", hint: "Most Twin Cities homes are on city water. If you pay a water bill, it’s city water.", type: "single", cls: "three",
      options: ["City Water", "Well Water", "Not Sure"] },
    { key: "water_problems", title: "What are you experiencing?", hint: "Choose everything that applies.", type: "multi", cls: "",
      options: ["Hard Water", "White Scale", "Spots on Dishes", "Dry Skin / Hair", "Chlorine Taste / Smell", "Iron Staining", "Metallic Taste", "Rotten Egg / Sulfur Odor", "Manganese", "Sediment", "Drinking Water Concerns", "Other", "Not Sure"] },
    { key: "system_interest", title: "What are you interested in?", hint: "Not sure? Pick the last option and we’ll recommend.", type: "single", cls: "",
      options: ["Whole Home Filtration", "Water Softening", "Well Water Treatment", "Reverse Osmosis", "Complete System", "Not Sure / Recommend Something"] },
    { key: "contact", title: "Where should we send your recommendation?", hint: "We’ll match your answers to the right system and reach out the same day.", type: "contact" },
    { key: "details", title: "Anything that helps us size it right?", hint: "Optional. Skip if you’d rather cover it on the call.", type: "details" }
  ];
  var PRESET_KEY = "msp_intake";
  function preset() { try { return JSON.parse(sessionStorage.getItem(PRESET_KEY) || "{}"); } catch (e) { return {}; } }
  function setPreset(obj) { var p = preset(); Object.keys(obj).forEach(function (k) { p[k] = obj[k]; }); try { sessionStorage.setItem(PRESET_KEY, JSON.stringify(p)); } catch (e) {} }
  window.MSPIntake = { preset: preset, setPreset: setPreset };

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function uid() { return "msp-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8); }

  function build(root) {
    var state = { step: 0, data: { water_problems: [] }, started: Date.now(), submitting: false, sid: uid() };
    var pre = preset();
    if (pre.water_source) state.data.water_source = pre.water_source;
    if (pre.water_problems && pre.water_problems.length) state.data.water_problems = pre.water_problems.slice();
    if (pre.system_interest) state.data.system_interest = pre.system_interest;
    if (pre.inquiry_type) state.data.inquiry_type = pre.inquiry_type;
    var startAt = parseInt(root.getAttribute("data-start") || "0", 10); if (startAt) state.step = Math.min(startAt, STEPS.length - 1);
    var consent = (window.MSP_GHL && window.MSP_GHL.consent) || {};

    function progress() { return '<div class="fms-progress" aria-hidden="true">' + STEPS.map(function (_, i) { return '<i class="' + (i <= state.step ? "on" : "") + '"></i>'; }).join("") + "</div>"; }
    function optionsHtml(st) {
      var name = st.key, multi = st.type === "multi";
      return '<div class="opts ' + st.cls + '" role="group" aria-label="' + esc(st.title) + '">' + st.options.map(function (o) {
        var checked = multi ? state.data.water_problems.indexOf(o) > -1 : state.data[name] === o;
        return '<label class="opt"><input type="' + (multi ? "checkbox" : "radio") + '" name="' + name + '" value="' + esc(o) + '"' + (checked ? " checked" : "") + '> <span>' + esc(o) + "</span></label>";
      }).join("") + "</div>";
    }
    function field(id, label, type, extra, req) {
      return '<div class="field" data-field="' + id + '"><label for="fms-' + id + '">' + label + (req ? "" : ' <span class="muted">(optional)</span>') + '</label>' +
        '<input id="fms-' + id + '" name="' + id + '" type="' + type + '" ' + (extra || "") + (req ? " required" : "") + ' value="' + esc(state.data[id] || "") + '"><span class="err">' + (req ? "Please enter " + label.toLowerCase() + "." : "") + "</span></div>";
    }
    function contactHtml() {
      return '<div class="fields-2">' + field("first_name", "First name", "text", 'autocomplete="given-name"', true) + field("last_name", "Last name", "text", 'autocomplete="family-name"', true) + "</div>" +
        '<div class="fields-2">' + field("phone", "Phone number", "tel", 'autocomplete="tel" inputmode="tel"', true) + field("email", "Email", "email", 'autocomplete="email" inputmode="email"', true) + "</div>" +
        '<div class="fields-2">' + field("city", "City", "text", 'autocomplete="address-level2"', true) + field("zip", "ZIP code", "text", 'autocomplete="postal-code" inputmode="numeric" pattern="[0-9]{5}" maxlength="5"', true) + "</div>" +
        '<div class="hp" aria-hidden="true"><label>Company <input type="text" name="company_website" tabindex="-1" autocomplete="off"></label></div>' +
        '<div class="consent"><label><input type="checkbox" name="sms_consent"' + (state.data.sms_consent ? " checked" : "") + '> <span>' + esc(consent.smsOptInLabel || "Yes, text me appointment updates.") + '</span></label>' +
        esc(consent.text || "") + ' <a href="/privacy/" class="link">Privacy Policy</a></div>';
    }
    function detailsHtml() {
      var sel = function (id, label, opts) { return '<div class="field"><label for="fms-' + id + '">' + label + ' <span class="muted">(optional)</span></label><select id="fms-' + id + '" name="' + id + '"><option value="">Select</option>' + opts.map(function (o) { return '<option' + (state.data[id] === o ? " selected" : "") + ">" + esc(o) + "</option>"; }).join("") + "</select></div>"; };
      return '<div class="fields-2">' + sel("bathrooms", "Bathrooms", ["1", "1.5", "2", "2.5", "3", "3.5", "4+"]) + sel("household_size", "People in household", ["1", "2", "3", "4", "5", "6+"]) + "</div>" +
        sel("existing_equipment", "Existing water treatment equipment", ["None", "Water softener", "Iron filter", "Reverse osmosis", "Whole-home filter", "Not sure"]) +
        '<div class="field"><label for="fms-notes">Anything else? <span class="muted">(optional)</span></label><textarea id="fms-notes" name="notes" rows="3" maxlength="1000">' + esc(state.data.notes || "") + "</textarea></div>";
    }
    function summary() {
      var d = state.data;
      return '<div class="summary-box"><div><b>Your water</b>' + esc(d.water_source || "—") + "</div><div><b>Experiencing</b>" + esc(d.water_problems.length ? d.water_problems.join(", ") : "—") + "</div><div><b>Interested in</b>" + esc(d.system_interest || "—") + "</div></div>";
    }
    function render() {
      var st = STEPS[state.step], last = state.step === STEPS.length - 1;
      var body = st.type === "contact" ? contactHtml() : st.type === "details" ? summary() + detailsHtml() : optionsHtml(st);
      root.innerHTML = '<form class="fms" novalidate aria-live="polite">' + progress() +
        '<div class="fms-step" data-active="true"><p class="kicker">Find My System &middot; Step ' + (state.step + 1) + " of " + STEPS.length + "</p><h3>" + esc(st.title) + '</h3><p class="hint">' + esc(st.hint) + "</p>" + body + "</div>" +
        '<div class="fms-status" role="alert"></div>' +
        '<div class="fms-nav">' + (state.step > 0 ? '<button type="button" class="btn btn-outline on-light" data-back>Back</button>' : '<span></span>') +
        '<button type="submit" class="btn btn-gold btn-lg" data-next>' + (last ? "Send my request" : st.type === "contact" ? "Continue" : "Continue") + "</button></div></form>";
      var first = root.querySelector("input,select,button[data-next]"); if (first && state.step > 0) { try { first.focus({ preventScroll: true }); } catch (e) {} }
      root.querySelector("form").addEventListener("submit", next);
      var back = root.querySelector("[data-back]"); if (back) back.addEventListener("click", function () { collect(); state.step--; render(); });
      if (state.step === 0 && window.MSPTrack) window.MSPTrack.once("find_my_system_started", { entry: location.pathname });
    }
    function collect() {
      var form = root.querySelector("form"), st = STEPS[state.step];
      if (st.type === "multi") { state.data.water_problems = Array.prototype.map.call(form.querySelectorAll('input[name="water_problems"]:checked'), function (i) { return i.value; }); }
      else if (st.type === "single") { var r = form.querySelector('input[name="' + st.key + '"]:checked'); state.data[st.key] = r ? r.value : ""; }
      else { Array.prototype.forEach.call(form.querySelectorAll("input,select,textarea"), function (i) { if (!i.name) return; if (i.name === "company_website") { state.hp = i.value; return; } state.data[i.name] = i.type === "checkbox" ? i.checked : i.value.trim(); }); }
    }
    function validate() {
      var st = STEPS[state.step], form = root.querySelector("form"), ok = true, status = root.querySelector(".fms-status"); status.removeAttribute("data-kind");
      if (st.type === "single" && !state.data[st.key]) { status.textContent = "Please choose an option to continue."; status.setAttribute("data-kind", "error"); return false; }
      if (st.type === "multi" && !state.data.water_problems.length) { status.textContent = "Choose at least one, or “Not Sure”."; status.setAttribute("data-kind", "error"); return false; }
      if (st.type === "contact") {
        form.querySelectorAll(".field[data-field]").forEach(function (f) {
          var i = f.querySelector("input"), v = i.value.trim(), bad = false;
          if (i.required && !v) bad = true;
          if (i.type === "email" && v && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)) bad = true;
          if (i.type === "tel" && v && v.replace(/\D/g, "").length < 10) bad = true;
          if (i.name === "zip" && v && !/^\d{5}$/.test(v)) bad = true;
          f.classList.toggle("invalid", bad); if (bad) ok = false;
        });
        if (!ok) { status.textContent = "Please check the highlighted fields."; status.setAttribute("data-kind", "error"); }
      }
      return ok;
    }
    function next(e) {
      e.preventDefault(); if (state.submitting) return;
      collect(); if (!validate()) return;
      if (state.step === 0 && window.MSPTrack) window.MSPTrack.event(state.data.water_source === "Well Water" ? "well_water_selected" : state.data.water_source === "City Water" ? "city_water_selected" : "water_source_not_sure", { via: "find_my_system" });
      if (state.step === 2 && state.data.system_interest === "Reverse Osmosis" && window.MSPTrack) window.MSPTrack.event("ro_selected", { via: "find_my_system" });
      setPreset({ water_source: state.data.water_source, water_problems: state.data.water_problems, system_interest: state.data.system_interest });
      if (state.step < STEPS.length - 1) { state.step++; render(); return; }
      submit();
    }
    function submit() {
      var form = root.querySelector("form"), status = root.querySelector(".fms-status"), btn = root.querySelector("[data-next]");
      if (state.hp) { return; }                                                                     /* honeypot filled = bot */
      if (Date.now() - state.started < 3000) { status.textContent = "Please take a moment to review your answers."; status.setAttribute("data-kind", "error"); return; }
      state.submitting = true; btn.setAttribute("aria-disabled", "true"); btn.innerHTML = '<span class="spinner"></span> Sending…';
      status.removeAttribute("data-kind");
      state.data.submission_id = state.sid;
      window.MSPCRM.submitLead(state.data).then(function (res) {
        if (res.ok) {
          if (window.MSPTrack) { window.MSPTrack.event("find_my_system_completed", { water_source: state.data.water_source, system_interest: state.data.system_interest }); window.MSPTrack.event("lead_form_submitted", { mode: res.mode, inquiry_type: state.data.inquiry_type || "Find My System" }); }
          location.assign("/thank-you/");
          return;
        }
        state.submitting = false; btn.removeAttribute("aria-disabled"); btn.textContent = "Try again";
        if (res.error === "not_configured") {
          status.innerHTML = "Online intake isn’t live yet. Call or text <a href=\"tel:+19529526206\"><b>(952) 952-6206</b></a> and we’ll take it from here, or <a href=\"/schedule/\" class=\"link\">pick a time online</a>.";
          status.setAttribute("data-kind", "info");
        } else {
          status.innerHTML = "We couldn’t send that just now. Please try again, or call or text <a href=\"tel:+19529526206\"><b>(952) 952-6206</b></a>.";
          status.setAttribute("data-kind", "error");
        }
        if (window.MSPTrack) window.MSPTrack.event("lead_form_error", { error: res.error, mode: res.mode });
      });
    }
    render();
  }

  function init() { document.querySelectorAll("[data-fms]").forEach(build); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
