/* Pilot Fit Scorer: score up to three candidate use cases from 1 to 5 on the
   six pilot criteria, rank them, flag weak spots, and send the shortlist to the
   contact form. Scores stay in this browser (localStorage) until sent. */
(function () {
  "use strict";
  var root = document.querySelector("[data-scorer]");
  if (!root) return;
  var KEY = "aira-pilot-scorer";
  var LETTERS = ["A", "B", "C"];
  var items = Array.prototype.slice.call(root.querySelectorAll(".sc-criteria li"));
  var crits = items.map(function (li) {
    return { id: li.dataset.crit, name: li.querySelector("b").textContent, good: li.querySelector(".sc-q span").textContent };
  });
  var tabs = Array.prototype.slice.call(root.querySelectorAll(".sc-cand"));
  var nameInput = root.querySelector("#sc-name");
  var rank = root.querySelector(".sc-rank");
  var advice = root.querySelector(".sc-advice");
  var send = root.querySelector(".tool-send");
  var contact = root.dataset.contact;
  var current = 0;

  function blank() { return LETTERS.map(function () { return { name: "", scores: {} }; }); }
  var state = blank();
  try {
    var saved = JSON.parse(localStorage.getItem(KEY));
    if (Array.isArray(saved) && saved.length === 3) state = saved;
  } catch (_) { /* storage may be blocked */ }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (_) {} }

  // Build the 1-5 radio groups once.
  items.forEach(function (li, i) {
    var set = li.querySelector("fieldset");
    for (var v = 1; v <= 5; v++) {
      var label = document.createElement("label");
      label.innerHTML = '<input type="radio" name="sc-' + crits[i].id + '" value="' + v + '"><span>' + v + "</span>";
      set.appendChild(label);
    }
    set.addEventListener("change", function (e) {
      state[current].scores[crits[i].id] = +e.target.value;
      update();
    });
  });

  function total(c) { return crits.reduce(function (sum, k) { return sum + (c.scores[k.id] || 0); }, 0); }
  function scored(c) { return crits.filter(function (k) { return c.scores[k.id]; }).length; }
  function label(i) { return state[i].name.trim() || "Candidate " + LETTERS[i]; }
  function verdict(t) {
    if (t >= 25) return { cls: "good", text: "Strong first pilot" };
    if (t >= 19) return { cls: "mid", text: "Workable: tighten the weak spots" };
    return { cls: "low", text: "Refine before piloting" };
  }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  function showCandidate(i, focus) {
    current = i;
    tabs.forEach(function (t, k) {
      t.setAttribute("aria-selected", k === i ? "true" : "false");
      t.tabIndex = k === i ? 0 : -1;
    });
    if (focus) tabs[i].focus();
    nameInput.value = state[i].name;
    nameInput.placeholder = "e.g. " + ["KYC document review for corporate onboarding", "Credit proposal drafting for relationship managers", "Policy Q&A for branch staff"][i];
    items.forEach(function (li, k) {
      var v = state[i].scores[crits[k].id];
      li.querySelectorAll("input").forEach(function (inp) { inp.checked = +inp.value === v; });
    });
  }

  function update() {
    tabs.forEach(function (t, i) {
      t.querySelector(".sc-cname").textContent = label(i);
      t.querySelector(".sc-ctotal").textContent = total(state[i]);
    });
    var list = state.map(function (c, i) { return { i: i, t: total(c), n: scored(c) }; })
      .filter(function (c) { return c.n > 0; })
      .sort(function (a, b) { return b.t - a.t || b.n - a.n; });

    rank.innerHTML = list.length ? list.map(function (c, pos) {
      var done = c.n === crits.length, v = verdict(c.t);
      return '<li class="' + (pos === 0 && done ? "top" : "") + '"><div class="sc-rhead"><span>' + LETTERS[c.i] + "</span><b>" + esc(label(c.i)) +
        "</b><em>" + c.t + "<small>/30</small></em></div><i class=\"sc-bar\"><i style=\"width:" + (c.t / 30 * 100) + '%"></i></i>' +
        (done ? '<span class="sc-pill ' + v.cls + '">' + v.text + "</span>" : '<span class="sc-pill">' + c.n + " of 6 scored</span>") + "</li>";
    }).join("") : '<li class="sc-empty">Score a candidate to see it ranked here.</li>';

    var best = list.filter(function (c) { return c.n === crits.length; })[0];
    if (best) {
      var c = state[best.i];
      var weak = crits.filter(function (k) { return c.scores[k.id] <= 2; });
      var tie = list.filter(function (x) { return x.n === crits.length && x.t === best.t; }).length > 1;
      advice.innerHTML = "<p><b>Start with " + esc(label(best.i)) + ".</b> " +
        (tie ? "It is tied on total; prefer the candidate with the clearer owner and the more contained risk. " : "") +
        (weak.length ? "Before scoping, strengthen:</p><ul>" + weak.map(function (k) {
          return "<li><b>" + k.name + " (" + c.scores[k.id] + "/5)</b>" + k.good + "</li>";
        }).join("") + "</ul>" : "No criterion scores below three: a good shape for a first pilot.</p>");
    } else {
      advice.innerHTML = list.length ? "<p>Score all six criteria for a candidate to get a recommendation.</p>" : "";
    }

    var lines = ["Pilot Fit Scorer results", ""];
    list.forEach(function (x) {
      var c = state[x.i];
      lines.push(LETTERS[x.i] + ". " + label(x.i) + ": " + x.t + "/30" + (x.n === crits.length ? " (" + verdict(x.t).text + ")" : " (" + x.n + " of 6 scored)"));
      lines.push("   " + crits.map(function (k) { return k.name + " " + (c.scores[k.id] || "-"); }).join(", "));
    });
    send.href = contact + "?topic=" + encodeURIComponent("Request Demo/PoC") + "&brief=" + encodeURIComponent(list.length ? lines.join("\n") : "I would like to scope a pilot.");
    save();
  }

  tabs.forEach(function (t, k) {
    t.addEventListener("click", function () { showCandidate(k); });
    t.addEventListener("keydown", function (e) {
      var d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (!d) return;
      e.preventDefault();
      showCandidate((current + d + 3) % 3, true);
    });
  });
  nameInput.addEventListener("input", function () { state[current].name = nameInput.value; update(); });
  root.querySelector(".sc-reset").addEventListener("click", function () {
    state = blank();
    showCandidate(0);
    update();
  });

  root.classList.add("ready");
  showCandidate(0);
  update();
})();
