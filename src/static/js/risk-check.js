/* Risk Committee Check: a four-question self-assessment. Shows a 0-8 score,
   where the evidence is thin, and how AIRA Nexus answers each gap. The answers
   pre-fill a security review request only if the visitor chooses to send them. */
(function () {
  "use strict";
  var root = document.querySelector("[data-risk]");
  if (!root) return;
  var qs = Array.prototype.slice.call(root.querySelectorAll(".rk-q"));
  var fill = root.querySelector(".rk-fill");
  var scoreEl = root.querySelector(".rk-score");
  var band = root.querySelector(".rk-band");
  var gaps = root.querySelector(".rk-gaps");
  var send = root.querySelector(".tool-send");
  var contact = root.dataset.contact;
  var LABEL = { 2: "Yes, with evidence", 1: "Partly", 0: "Not yet" };
  var CIRC = 2 * Math.PI * 50;
  fill.style.strokeDasharray = CIRC;

  function update() {
    var answers = qs.map(function (q) {
      var on = q.querySelector("input:checked");
      return { q: q.querySelector("legend").textContent, how: q.dataset.answer, v: on ? +on.value : null, el: q };
    });
    var done = answers.filter(function (a) { return a.v !== null; });
    var score = done.reduce(function (s, a) { return s + a.v; }, 0);
    answers.forEach(function (a) { a.el.dataset.state = a.v === null ? "" : ["gap", "part", "ok"][a.v]; });

    scoreEl.textContent = score;
    fill.style.strokeDashoffset = CIRC * (1 - score / 8);
    root.dataset.level = done.length < 4 ? "" : score >= 7 ? "ok" : score >= 4 ? "part" : "gap";

    if (done.length < 4) band.textContent = done.length ? (4 - done.length) + " question" + (done.length === 3 ? "" : "s") + " to go." : "Answer the four questions.";
    else if (score === 8) band.textContent = "Ready for the committee: keep the evidence current as AI use grows.";
    else if (score >= 5) band.textContent = "Close: a few answers would rest on assurances rather than evidence.";
    else band.textContent = "Exposed: the committee would be asked to accept assurances, not evidence.";

    var open = answers.filter(function (a) { return a.v !== null && a.v < 2; });
    gaps.innerHTML = open.map(function (a) {
      return '<li class="' + (a.v ? "part" : "gap") + '"><b>' + a.q + "</b><span>How AIRA Nexus answers it: " + a.how + "</span></li>";
    }).join("");

    var brief = ["Risk Committee Check (self-assessment)", ""].concat(answers.map(function (a, i) {
      return "0" + (i + 1) + " " + a.q + " " + (a.v === null ? "not answered" : LABEL[a.v]);
    }), ["", "Score: " + score + " of 8", "", "We would like a security review of how AIRA Nexus would close these gaps."]);
    send.href = contact + "?topic=" + encodeURIComponent("Request Demo/PoC") + "&brief=" + encodeURIComponent(brief.join("\n"));
  }

  root.addEventListener("change", update);
  root.classList.add("ready");
  update();
})();
