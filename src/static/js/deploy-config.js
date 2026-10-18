/* Deployment choices update the perimeter diagram and enquiry summary. */
(function () {
  "use strict";
  var root = document.querySelector("[data-deploy-config]");
  if (!root) return;
  var map = root.querySelector(".dc-map");
  var list = root.querySelector(".dc-check ul");
  var send = root.querySelector(".tool-send");
  var contact = root.dataset.contact;
  var hybrid = root.querySelector('input[name="dc-models"][value="hybrid"]');
  var WHERE = { onprem: "Your data centre", cloud: "Your private cloud", airgap: "Your isolated network" };

  function chips(a) { return a.map(function (x) { return "<span>" + x + "</span>"; }).join(""); }
  function row(k, items, cls) { return '<div class="dc-row ' + (cls || "") + '"><span class="dc-k">' + k + '</span><div class="dc-chips">' + chips(items) + "</div></div>"; }
  function get(name) { var el = root.querySelector('input[name="' + name + '"]:checked'); return el ? el.value : null; }

  function update() {
    var where = get("dc-where");
    var air = where === "airgap";
    hybrid.disabled = air;
    hybrid.closest("label").classList.toggle("off", air);
    if (air && hybrid.checked) root.querySelector('input[name="dc-models"][value="local"]').checked = true;
    var models = get("dc-models"), obs = root.querySelector('input[name="dc-obs"]').checked;

    var html = '<div class="dc-perimeter" data-where="' + where + '"><div class="dc-plabel"><i></i>' + WHERE[where] + "</div>" +
      row("Access", ["Single sign-on", "Access controls"]) +
      row("AIRA Nexus", ["Home", "Studio", "Gateway", "Runtime", "Signal", "Data", "Console"], "core") +
      row("Private AI", ["Your models", "Your data"]) +
      row("Foundation", ["Container platform", "Secure storage"]) +
      (obs ? row("Monitoring", ["Health", "Activity", "Alerts"], "added") : "") +
      "</div>";
    if (models === "hybrid") {
      html += '<div class="dc-egress on"><span class="dc-line"></span><div><b>Approved cloud models</b><span>Connected through AIRA Gateway, with your access keys.</span></div></div>';
    } else {
      html += '<div class="dc-egress ' + (air ? "cut" : "none") + '"><span class="dc-line"></span><div><b>' + (air ? "No outbound connection" : "No cloud model calls") + "</b><span>" +
        (air ? "AI stays inside your isolated network." : "AI runs within your environment.") + "</span></div></div>";
    }
    map.innerHTML = html;

    var check = [
      "Hosted in " + WHERE[where].toLowerCase(),
      models === "hybrid" ? "Private AI with approved cloud access" : "Private AI within your environment",
      "Shared identity and access controls"
    ];
    check.push(obs ? "Operational monitoring included" : "Operational monitoring optional");
    list.innerHTML = check.map(function (c) { return "<li>" + c + "</li>"; }).join("");

    var brief = ["Deployment Configurator", "",
      "Where: " + WHERE[where],
      "Models: " + (models === "hybrid" ? "local and approved cloud models" : "local models only"),
      "Operational monitoring: " + (obs ? "yes" : "no"), "",
      "We would like to discuss this deployment."];
    send.href = contact + "?topic=" + encodeURIComponent("Request Demo/PoC") + "&brief=" + encodeURIComponent(brief.join("\n"));
  }

  root.addEventListener("change", update);
  root.classList.add("ready");
  update();
})();
