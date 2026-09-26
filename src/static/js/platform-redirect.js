// Keep saved product links working after consolidating the platform under Nexus.
(function () {
  var hash = window.location.hash;
  if (hash === "#hub") hash = "#home";
  if (hash === "#solutions") hash = "#products";
  window.location.replace("nexus.html" + window.location.search + hash);
})();
