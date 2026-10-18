/* Gateway Simulator: walks one request through identity, model access, data
   policy, budget, approval and routing, then appends a chained audit entry.
   Rules are illustrative; in AIRA Gateway they are the customer's policies. */
(function () {
  "use strict";
  var root = document.querySelector("[data-gateway-sim]");
  if (!root) return;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var form = root.querySelector(".gs-controls");
  var text = root.querySelector(".gs-text");
  var stepsEl = root.querySelector(".gs-steps");
  var outcome = root.querySelector(".gs-outcome");
  var audit = root.querySelector(".gs-audit");

  var WHO = {
    analyst: { name: "Credit analyst", via: "Signed in through SSO with MFA · role: credit-analyst", team: "Credit risk", budget: "61% of the team's monthly budget used", models: ["private", "cloud"], requests: ["summary", "reply", "approve"] },
    branch: { name: "Branch employee", via: "Signed in through SSO with MFA · role: branch-staff", team: "Retail branches", budget: "38% of the team's monthly budget used", models: ["private"], requests: ["reply"] },
    app: { name: "Mobile banking app", via: "Application key for the “Customer reply assistant” subscription", team: "Mobile app subscription", budget: "1,240 of 5,000 daily requests used", models: ["private"], requests: ["reply"], pinned: true }
  };
  var REQ = {
    summary: { label: "credit file summary", text: "Summarise the credit file for Al-Noor Trading LLC, customer ID 448812, signatory national ID 9871034521, and list any covenant breaches.",
      pii: [["448812", "[CUSTOMER_ID]"], ["9871034521", "[NATIONAL_ID]"]], denyWhy: "Credit files are limited to credit roles." },
    reply: { label: "customer reply", text: "Draft a reply to Rania Haddad explaining the new card fee schedule, in Arabic and English.",
      pii: [["Rania Haddad", "[CUSTOMER_NAME]"]] },
    approve: { label: "facility increase", text: "Increase the facility for Al-Noor Trading LLC by JOD 250,000 and record it in core banking.",
      pii: [], action: true, denyWhy: "Facility changes are limited to credit roles." }
  };

  var entry = 48212, prev = "9f3a61c0b27d4e15";
  function hash(s) {
    // Two FNV-1a passes give a short, stable demo fingerprint (not a cryptographic hash).
    var out = "";
    [2166136261, 33554467].forEach(function (seed) {
      var h = seed >>> 0;
      for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
      out += ("0000000" + h.toString(16)).slice(-8);
    });
    return out;
  }
  function esc(s) { return s.replace(/[&<>]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); }
  function val(name) { return form.querySelector('input[name="' + name + '"]:checked').value; }

  function plan() {
    var who = WHO[val("gs-who")], reqKey = val("gs-req"), req = REQ[reqKey], model = val("gs-model");
    var steps = [], stop = null, masked = false, held = false;
    var shown = esc(req.text);
    req.pii.forEach(function (p) { shown = shown.replace(p[0], '<mark>' + esc(p[0]) + "</mark>"); });

    steps.push({ k: "Identity", s: "pass", d: who.via });

    if (who.requests.indexOf(reqKey) < 0) {
      stop = { s: "block", d: who.pinned ? "Not in this application's subscription: it may only call the Customer reply assistant." : req.denyWhy };
      steps.push({ k: "Access policy", s: "block", d: stop.d });
    } else if (who.models.indexOf(model) < 0 && !who.pinned) {
      stop = { s: "block", d: "The approved cloud model is not enabled for this role." };
      steps.push({ k: "Access policy", s: "block", d: stop.d });
    } else if (who.pinned && model === "cloud") {
      steps.push({ k: "Access policy", s: "transform", d: "Allowed. The subscription pins this offering to the private model, so the cloud choice is overridden." });
      model = "private";
    } else {
      steps.push({ k: "Access policy", s: "pass", d: "Allowed: " + who.name.toLowerCase() + " may send a " + req.label + " to the " + (model === "cloud" ? "approved cloud model" : "private model") + "." });
    }

    if (!stop) {
      if (req.pii.length && model === "cloud") {
        masked = true;
        var out = esc(req.text);
        req.pii.forEach(function (p) { out = out.replace(p[0], '<mark class="masked">' + p[1] + "</mark>"); });
        shown = out;
        steps.push({ k: "Data policy & guardrails", s: "transform", d: req.pii.length + " identifier" + (req.pii.length > 1 ? "s" : "") + " masked before the request leaves your perimeter." });
      } else if (req.pii.length) {
        steps.push({ k: "Data policy & guardrails", s: "pass", d: "Identifiers stay inside your perimeter on the private model: no masking needed. Guardrails passed." });
      } else {
        steps.push({ k: "Data policy & guardrails", s: "pass", d: "No personal data detected. Guardrails passed." });
      }
      steps.push({ k: "Budget", s: "pass", d: who.team + ": " + who.budget + "." });
      if (req.action) {
        held = true;
        steps.push({ k: "Approval gate", s: "hold", d: "A facility change needs a credit committee approver. The run is paused and the approver notified." });
      } else {
        steps.push({ k: "Approval gate", s: "skip", d: "Not a consequential action: no approval needed." });
      }
      steps.push(held
        ? { k: "Route", s: "hold", d: "Waiting for approval before anything is recorded in core banking." }
        : { k: "Route", s: "pass", d: model === "cloud" ? "Sent to the approved cloud provider with your organisation's key. Fallback: the private model." : "Sent to the private model inside your perimeter. Fallback: a second private replica." });
    } else {
      ["Data policy & guardrails", "Budget", "Approval gate", "Route"].forEach(function (k) { steps.push({ k: k, s: "skip", d: "Not reached." }); });
    }

    var result = stop ? { cls: "block", t: "Blocked by policy", d: stop.d }
      : held ? { cls: "hold", t: "Held for human approval", d: "Nothing changes until the approver signs off, and the sign-off is recorded with their name." }
      : masked ? { cls: "transform", t: "Delivered with masking", d: "The model never saw the customer identifiers." }
      : { cls: "pass", t: "Delivered", d: "Answered under policy, within budget." };
    return { who: who, req: req, model: model, shown: shown, steps: steps, result: result };
  }

  var timers = [];
  function run() {
    timers.forEach(clearTimeout);
    timers = [];
    var p = plan();
    text.innerHTML = p.shown;
    stepsEl.innerHTML = p.steps.map(function (st, i) {
      return '<li data-s="' + st.s + '"><span class="gs-dot">' + (i + 1) + '</span><div><b>' + st.k + "</b><span>" + st.d + "</span></div></li>";
    }).join("");
    outcome.className = "gs-outcome";
    outcome.innerHTML = "";
    audit.textContent = "";
    var items = stepsEl.children, delay = reduce ? 0 : 420;
    Array.prototype.forEach.call(items, function (li, i) {
      timers.push(setTimeout(function () { li.classList.add("on"); }, delay * (i + 1)));
    });
    timers.push(setTimeout(function () {
      outcome.className = "gs-outcome show " + p.result.cls;
      outcome.innerHTML = "<b>" + p.result.t + "</b><span>" + p.result.d + "</span>";
      entry += 1;
      var record = [entry, p.who.name, p.req.label, p.result.t, prev].join("|");
      var next = hash(record);
      audit.innerHTML = "<b>Audit entry #" + entry.toLocaleString("en") + "</b> " + esc(p.who.name) + " · " + p.req.label + " · " + p.result.t.toLowerCase() +
        '<br><span>previous ' + prev.slice(0, 8) + "… → this entry " + next.slice(0, 8) + "…</span>" +
        (p.result.cls === "block" ? "<em>Denied requests are recorded too.</em>" : "");
      prev = next;
    }, delay * (items.length + 1)));
  }

  form.addEventListener("submit", function (e) { e.preventDefault(); run(); });
  form.addEventListener("change", run);
  root.querySelector(".gs-run").addEventListener("click", run);
  root.classList.add("ready");
  // Show the first request statically; animate only when the visitor interacts.
  var first = plan();
  text.innerHTML = first.shown;
  stepsEl.innerHTML = first.steps.map(function (st, i) {
    return '<li class="gs-wait"><span class="gs-dot">' + (i + 1) + "</span><div><b>" + st.k + "</b><span>Waiting for a request.</span></div></li>";
  }).join("");
  outcome.className = "gs-outcome show idle";
  outcome.innerHTML = "<b>Ready</b><span>Choose who is asking, the request and the model, then send it through the Gateway.</span>";
})();
