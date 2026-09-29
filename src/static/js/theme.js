/* Apply the saved palette before the body renders. Storage is optional. */
(function () {
  "use strict";
  var root = document.documentElement;
  var sheet = document.getElementById("light-theme");
  var theme = root.getAttribute("data-default-theme") === "dark" ? "dark" : "light";
  var button;
  try {
    var saved = localStorage.getItem("aira-theme");
    if (saved === "light" || saved === "dark") theme = saved;
  } catch (_) { /* Private browsing and local-file previews may block storage. */ }

  function apply(value) {
    theme = value;
    root.setAttribute("data-theme", theme);
    sheet.media = theme === "light" ? "all" : "not all";
    document.querySelector('meta[name="theme-color"]').content = theme === "light" ? "#f0f6fa" : "#040d1c";
    if (button) {
      var next = theme === "light" ? "dark" : "light";
      button.setAttribute("aria-label", "Switch to " + next + " mode");
      button.querySelector("span").textContent = next === "dark" ? "Dark mode" : "Light mode";
    }
  }
  apply(theme);
  document.addEventListener("DOMContentLoaded", function () {
    button = document.querySelector(".theme-toggle");
    apply(theme);
    button.hidden = false;
    button.addEventListener("click", function () {
      apply(theme === "light" ? "dark" : "light");
      try { localStorage.setItem("aira-theme", theme); } catch (_) {}
    });
  });
})();
