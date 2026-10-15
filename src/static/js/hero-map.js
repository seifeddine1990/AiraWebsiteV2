/* Home hero platform map: cycles through the six capabilities, lighting the
   node and its wire and naming the governance step under the core. Hovering a
   node takes over; the pointer tilts the map. Reduced motion shows it still. */
(function () {
  "use strict";
  var map = document.querySelector("[data-hero-map]");
  if (!map) return;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var svg = map.querySelector(".platform-wires");
  var nodes = Array.prototype.slice.call(map.querySelectorAll(".platform-node"));
  var status = map.querySelector(".pm-status span");
  var order = [1, 2, 4, 6, 5, 3];
  var step = 0, timer = null, hover = false;

  function light(n) {
    nodes.forEach(function (node) { node.classList.toggle("on", +node.dataset.node === n); });
    map.querySelectorAll(".pm-live use").forEach(function (w) { w.classList.toggle("on", +w.dataset.wire === n); });
    var node = map.querySelector('[data-node="' + n + '"]');
    if (status && node) {
      status.parentNode.classList.remove("swap");
      void status.parentNode.offsetWidth;
      status.textContent = node.dataset.status;
      status.parentNode.classList.add("swap");
    }
  }

  function cycle() { step = (step + 1) % order.length; light(order[step]); }
  function run() { clearInterval(timer); timer = (reduce || hover || document.hidden) ? null : setInterval(cycle, 2600); }

  nodes.forEach(function (node) {
    node.addEventListener("mouseenter", function () {
      hover = true; run();
      var n = +node.dataset.node;
      step = order.indexOf(n);
      light(n);
    });
    node.addEventListener("mouseleave", function () { hover = false; run(); });
  });
  document.addEventListener("visibilitychange", run);

  if (reduce) {
    if (svg && svg.pauseAnimations) svg.pauseAnimations();
  } else if (window.matchMedia("(hover: hover) and (min-width: 821px)").matches) {
    var visual = map.closest(".hf-visual") || map;
    var frame = 0;
    visual.addEventListener("mousemove", function (e) {
      var r = visual.getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(function () {
        map.style.setProperty("--ry", (x * 8).toFixed(2) + "deg");
        map.style.setProperty("--rx", (-y * 6).toFixed(2) + "deg");
      });
    });
    visual.addEventListener("mouseleave", function () {
      map.style.setProperty("--ry", "0deg");
      map.style.setProperty("--rx", "0deg");
    });
  }

  map.classList.add("live");
  light(order[0]);
  run();
})();
