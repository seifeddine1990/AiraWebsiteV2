/* Product tour: tabs per product, numbered callouts linked to screenshot pins,
   a spotlight that follows the active point, autoplay while visible, and an
   enlarged view. Without JavaScript every panel stays visible. */
(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var STEP = 4600;

  document.querySelectorAll("[data-tour]").forEach(function (tour) {
    var tabs = Array.prototype.slice.call(tour.querySelectorAll(".tour-tab"));
    var panels = tabs.map(function (t) { return document.getElementById(t.getAttribute("aria-controls")); });
    var playBtn = tour.querySelector(".tour-play");
    var lightbox = tour.nextElementSibling && tour.nextElementSibling.matches(".tour-lightbox") ? tour.nextElementSibling : null;
    var current = 0, point = 1, timer = null;
    var playing = !reduce, visible = false, hovered = false;
    tour.style.setProperty("--step", STEP + "ms");

    function pointsOf(panel) { return panel.querySelectorAll(".tour-point"); }

    function activate(n) {
      var panel = panels[current];
      point = n;
      panel.querySelectorAll(".tour-point").forEach(function (b) {
        var on = +b.dataset.pin === n;
        b.classList.toggle("on", on);
        b.setAttribute("aria-current", on ? "step" : "false");
        if (on) { var bar = b.querySelector(".tp-bar"); bar.style.animation = "none"; void bar.offsetWidth; bar.style.animation = ""; }
      });
      panel.querySelectorAll(".shot-view").forEach(function (view) {
        var pin = view.querySelector('.pin[data-pin="' + n + '"]');
        view.querySelectorAll(".pin").forEach(function (p) { p.classList.toggle("on", p === pin); });
        view.classList.toggle("focus", !!pin);
        view.closest(".shot").classList.toggle("lead", !!pin);
        if (pin) {
          var x = pin.style.getPropertyValue("--x"), y = pin.style.getPropertyValue("--y");
          view.style.setProperty("--sx", x);
          view.style.setProperty("--sy", y);
        }
      });
    }

    function select(i, focus) {
      current = (i + tabs.length) % tabs.length;
      tabs.forEach(function (t, k) {
        var on = k === current;
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
        panels[k].hidden = !on;
      });
      if (focus) tabs[current].focus();
      activate(1);
    }

    function tick() {
      var count = pointsOf(panels[current]).length;
      if (point < count) activate(point + 1);
      else select(current + 1);
    }

    function sync() {
      var run = playing && visible && !hovered && !document.hidden;
      tour.classList.toggle("paused", !run);
      clearInterval(timer);
      timer = run ? setInterval(tick, STEP) : null;
      if (playBtn) playBtn.setAttribute("aria-pressed", playing ? "true" : "false");
    }

    function stop() { playing = false; sync(); }

    // Product links such as nexus.html#gateway open that product's tab.
    function fromHash(scroll) {
      var k = panels.findIndex(function (p) { return "#" + p.id === window.location.hash; });
      if (k < 0) return;
      select(k);
      stop();
      if (scroll) tour.scrollIntoView({ block: "start" });
    }
    function remember(k) {
      if (history.replaceState) history.replaceState(null, "", "#" + panels[k].id);
    }

    tabs.forEach(function (t, k) {
      t.addEventListener("click", function () { select(k); stop(); remember(k); });
      t.addEventListener("keydown", function (e) {
        var key = e.key, next = null;
        if (key === "ArrowRight" || key === "ArrowDown") next = current + 1;
        else if (key === "ArrowLeft" || key === "ArrowUp") next = current - 1;
        else if (key === "Home") next = 0;
        else if (key === "End") next = tabs.length - 1;
        if (next === null) return;
        e.preventDefault();
        select(next, true);
        stop();
        remember(current);
      });
    });

    panels.forEach(function (panel) {
      panel.addEventListener("click", function (e) {
        var target = e.target.closest(".tour-point, .pin");
        if (target) { activate(+target.dataset.pin); stop(); return; }
        var zoom = e.target.closest(".shot-zoom");
        if (zoom && lightbox) open(zoom.closest(".shot"));
      });
      panel.addEventListener("mouseover", function (e) {
        var target = e.target.closest(".tour-point, .pin");
        if (target && +target.dataset.pin !== point) activate(+target.dataset.pin);
      });
    });

    if (playBtn) {
      playBtn.hidden = reduce;
      playBtn.addEventListener("click", function () { playing = !playing; sync(); });
    }
    tour.addEventListener("mouseenter", function () { hovered = true; sync(); });
    tour.addEventListener("mouseleave", function () { hovered = false; sync(); });
    document.addEventListener("visibilitychange", sync);

    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        visible = entries[0].isIntersecting;
        sync();
      }, { threshold: 0.35 }).observe(tour);
    } else {
      visible = true;
    }

    function open(shot) {
      var body = lightbox.querySelector(".tl-body");
      var copy = shot.querySelector(".shot-view").cloneNode(true);
      copy.classList.remove("focus");
      copy.querySelectorAll(".pin").forEach(function (p) { p.tabIndex = -1; p.setAttribute("aria-hidden", "true"); });
      body.innerHTML = "";
      body.appendChild(copy);
      stop();
      if (lightbox.showModal) lightbox.showModal(); else lightbox.setAttribute("open", "");
    }
    if (lightbox) {
      lightbox.querySelector(".tl-close").addEventListener("click", function () { lightbox.close(); });
      lightbox.addEventListener("click", function (e) { if (e.target === lightbox) lightbox.close(); });
    }

    if (reduce) tour.querySelectorAll("svg").forEach(function (s) { if (s.pauseAnimations) s.pauseAnimations(); });
    tour.classList.add("ready");
    select(0);
    fromHash(true);
    window.addEventListener("hashchange", function () { fromHash(true); });
    sync();
  });
})();
