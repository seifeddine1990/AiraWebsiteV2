/* Deployment Configurator: pick where AIRA Nexus runs, the model mix, the
   platform and monitoring; the perimeter diagram and checklist update to match.
   Everything shown comes from the published deployment specifications. */
(function () {
  "use strict";
  var root = document.querySelector("[data-deploy-config]");
  if (!root) return;
  var map = root.querySelector(".dc-map");
  var list = root.querySelector(".dc-check ul");
  var send = root.querySelector(".tool-send");
  var contact = root.dataset.contact;
  var hybrid = root.querySelector('input[name="dc-models"][value="hybrid"]');
  var WHERE = { onprem: "On-premises · your data centre", cloud: "Private cloud · your tenancy", airgap: "Air-gapped · isolated network" };

  function chips(a) { return a.map(function (x) { return "<span>" + x + "</span>"; }).join(""); }
  function row(k, items, cls) { return '<div class="dc-row ' + (cls || "") + '"><span class="dc-k">' + k + '</span><div class="dc-chips">' + chips(items) + "</div></div>"; }
  function get(name) { var el = root.querySelector('input[name="' + name + '"]:checked'); return el ? el.value : null; }

  function update() {
    var where = get("dc-where");
    var air = where === "airgap";
    hybrid.disabled = air;
    hybrid.closest("label").classList.toggle("off", air);
    if (air && hybrid.checked) root.querySelector('input[name="dc-models"][value="local"]').checked = true;
    var models = get("dc-models"), ocp = get("dc-platform") === "ocp", obs = root.querySelector('input[name="dc-obs"]').checked;

    var html = '<div class="dc-perimeter" data-where="' + where + '"><div class="dc-plabel"><i></i>' + WHERE[where] + "</div>" +
      row("Identity", ["Keycloak SSO", "OIDC &amp; SAML", "TOTP MFA"]) +
      row("AIRA Nexus", ["Home", "Studio", "Gateway", "Runtime", "Signal", "Data", "Console"], "core") +
      row("Local models", ["Ollama · CPU or GPU", "vLLM · GPU", "SGLang · GPU"]) +
      row("Data stores", ["PostgreSQL", "Redis", "Qdrant", "MinIO", "Temporal"]) +
      row("Platform", [ocp ? "OpenShift overlay" : "Kubernetes · base &amp; overlays", "Hostname-routed ingress", "TLS at your edge"]) +
      (obs ? row("Monitoring", ["Prometheus", "Grafana", "Loki", "Tempo", "Alertmanager"], "added") : "") +
      "</div>";
    if (models === "hybrid") {
      html += '<div class="dc-egress on"><span class="dc-line"></span><div><b>Approved cloud models</b><span>OpenAI, Anthropic, Google Gemini, Mistral, Cohere or any OpenAI-compatible endpoint, called through AIRA Gateway with your keys</span></div></div>';
    } else {
      html += '<div class="dc-egress ' + (air ? "cut" : "none") + '"><span class="dc-line"></span><div><b>' + (air ? "No outbound connection" : "No cloud model calls") + "</b><span>" +
        (air ? "Fully isolated: no telemetry, no phone-home, no activation server" : "Every model runs on your hardware; no telemetry or phone-home") + "</span></div></div>";
    }
    map.innerHTML = html;

    var check = [
      ocp ? "An OpenShift cluster, deployed with the OpenShift overlay" : "A Kubernetes cluster, deployed with the base and overlays",
      "Hostname-routed ingress, with TLS terminated at your edge",
      "Single sign-on through Keycloak (OIDC and SAML) across every product",
      "Self-hosted PostgreSQL, Redis, Qdrant, MinIO and Temporal",
      "Hardware for local inference: Ollama runs on CPU or GPU; vLLM and SGLang need GPUs",
      "Models declared in configuration, never auto-detected"
    ];
    if (models === "hybrid") check.push("Your own keys for the cloud providers you approve, and outbound access from the Gateway to those providers only");
    if (air) check.push("A route to bring container images, model weights and release bundles into the isolated network");
    check.push("An offline, signed licence: no activation server");
    if (obs) check.push("The optional Prometheus, Grafana, Loki, Tempo and Alertmanager overlay");
    check.push("Backup, restore-verify and a documented restore drill");
    list.innerHTML = check.map(function (c) { return "<li>" + c + "</li>"; }).join("");

    var brief = ["Deployment Configurator", "",
      "Where: " + WHERE[where],
      "Models: " + (models === "hybrid" ? "local and approved cloud models" : "local models only"),
      "Platform: " + (ocp ? "OpenShift" : "Kubernetes"),
      "Monitoring overlay: " + (obs ? "yes" : "no"), "",
      "We would like to discuss this deployment."];
    send.href = contact + "?topic=" + encodeURIComponent("Request Demo/PoC") + "&brief=" + encodeURIComponent(brief.join("\n"));
  }

  root.addEventListener("change", update);
  root.classList.add("ready");
  update();
})();
