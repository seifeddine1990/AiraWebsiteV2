/* AIRA Fusion website — progressive enhancement only. Every page reads fine without it. */
(function () {
  "use strict";
  var doc = document.documentElement;
  doc.classList.remove("no-js");
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Header ---------- */
  var header = document.querySelector(".site-header");
  function onScroll() { if (header) header.classList.toggle("scrolled", window.scrollY > 12); }
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  var toggle = document.querySelector(".nav-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var open = document.body.classList.toggle("nav-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.querySelectorAll(".nav-links a").forEach(function (a) {
      a.addEventListener("click", function () { document.body.classList.remove("nav-open"); toggle.setAttribute("aria-expanded", "false"); });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && document.body.classList.contains("nav-open")) {
        document.body.classList.remove("nav-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });
  }

  /* ---------- Reveal on scroll ---------- */
  var revs = document.querySelectorAll(".rev");
  if ("IntersectionObserver" in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    revs.forEach(function (el) { io.observe(el); });
  } else {
    revs.forEach(function (el) { el.classList.add("in"); });
  }

  document.querySelectorAll("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });

  /* ---------- Light ribbons: silk-like bundles of thin lines drifting slowly ---------- */
  function runWhenVisible(el, draw) {
    var raf = 0, on = false;
    function loop(t) { draw(t / 1000); if (on) raf = requestAnimationFrame(loop); }
    if (reduce || !("IntersectionObserver" in window)) { draw(4); return; }
    new IntersectionObserver(function (en) {
      var v = en[0].isIntersecting;
      if (v && !on) { on = true; raf = requestAnimationFrame(loop); }
      else if (!v && on) { on = false; cancelAnimationFrame(raf); }
    }).observe(el);
  }
  function fitCanvas(c) {
    var dpr = Math.min(window.devicePixelRatio || 1, 2), w = c.clientWidth, h = c.clientHeight;
    if (c.width !== Math.round(w * dpr) || c.height !== Math.round(h * dpr)) { c.width = Math.round(w * dpr); c.height = Math.round(h * dpr); }
    var ctx = c.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx: ctx, w: w, h: h };
  }
  document.querySelectorAll("canvas.waves").forEach(function (c) {
    if (!c.getContext) return;
    var hero = c.getAttribute("data-variant") === "hero";
    var ribbons = hero ? [
      // sweeps from the upper left edge down across the bottom
      { fn: function (u, t) { return 0.98 - 0.66 * Math.exp(-u * 2.4) + 0.035 * Math.sin(u * 5 + t * 0.45); }, spread: 0.2, k: 7, ph: 0, n: 34, a: 0.5, col: "30,140,255" },
      { fn: function (u, t) { return 0.9 + 0.05 * Math.sin(u * 3.2 - t * 0.35) - 0.08 * u; }, spread: 0.12, k: 5, ph: 2, n: 26, a: 0.42, col: "0,190,255" }
    ] : [
      { fn: function (u, t) { return 0.95 - 0.5 * Math.exp(-u * 2.8) + 0.03 * Math.sin(u * 4 + t * 0.4); }, spread: 0.18, k: 6, ph: 1, n: 28, a: 0.38, col: "30,140,255" }
    ];
    runWhenVisible(c, function (t) {
      var f = fitCanvas(c), ctx = f.ctx, W = f.w, H = f.h;
      ctx.clearRect(0, 0, W, H);
      ctx.globalCompositeOperation = "lighter";
      ctx.lineWidth = 1;
      ribbons.forEach(function (r) {
        for (var i = 0; i < r.n; i++) {
          var m = i / (r.n - 1) - 0.5, edge = 1 - Math.min(1, Math.abs(m) * 1.8);
          var alpha = r.a * (0.18 + 0.82 * edge * edge);
          ctx.strokeStyle = "rgba(" + r.col + "," + alpha.toFixed(3) + ")";
          ctx.beginPath();
          for (var x = -20; x <= W + 20; x += 14) {
            var u = x / W;
            var spread = r.spread * H * (0.3 + 0.7 * (0.5 + 0.5 * Math.sin(u * r.k + t * 0.35 + r.ph)));
            var y = r.fn(u, t) * H + m * spread + Math.sin(u * 9 + t * 0.8 + i * 0.21) * H * 0.006;
            if (x === -20) ctx.moveTo(x, y); else ctx.lineTo(x, y);
          }
          ctx.stroke();
        }
      });
      ctx.globalCompositeOperation = "source-over";
    });
  });

  /* ---------- Globe: a dotted night-side earth (real coastlines) with glowing arcs ---------- */
  var globe = document.querySelector("canvas.globe");
  if (globe && globe.getContext) {
    var mask = null;
    try {
      var raw = atob(window.AIRA_LANDMASK || "");
      mask = new Uint8Array(raw.length);
      for (var mi = 0; mi < raw.length; mi++) mask[mi] = raw.charCodeAt(mi);
    } catch (e) { mask = null; }
    function isLand(latDeg, lonDeg) {
      if (!mask || !mask.length) return false;
      var r = Math.min(179, Math.max(0, Math.floor(90 - latDeg))), c = Math.min(359, Math.max(0, Math.floor(lonDeg + 180)));
      var i = r * 360 + c;
      return (mask[i >> 3] >> (i & 7)) & 1;
    }
    var D2R = Math.PI / 180;
    function toXYZ(latDeg, lonDeg) {
      var la = latDeg * D2R, lo = lonDeg * D2R;
      return { x: Math.cos(la) * Math.cos(lo), y: Math.sin(la), z: -Math.cos(la) * Math.sin(lo) };
    }
    // Dot field: an even Fibonacci lattice, tagged land or ocean from the mask
    var pts = [], N = 9000, golden = Math.PI * (3 - Math.sqrt(5));
    for (var gi = 0; gi < N; gi++) {
      var gy = 1 - (gi / (N - 1)) * 2, lat = Math.asin(gy) / D2R, lon = ((golden * gi / D2R) % 360) - 180;
      var p = toXYZ(lat, lon);
      p.land = isLand(lat, lon);
      var hs = Math.sin(gi * 12.9898 + 78.233) * 43758.5453; p.lit = p.land && (hs - Math.floor(hs)) < 0.07;
      pts.push(p);
    }
    // Financial and government hubs, joined by arcs (decorative, not office locations)
    var hubs = [[25.2, 55.3], [51.5, -0.1], [40.7, -74.0], [1.35, 103.8], [50.1, 8.7], [24.7, 46.7], [22.3, 114.2], [19.1, 72.9], [35.7, 139.7], [48.9, 2.35]].map(function (h) { return toXYZ(h[0], h[1]); });
    var links = [[0, 1], [0, 3], [0, 5], [0, 7], [1, 2], [4, 0], [3, 6], [6, 8], [9, 0]];
    var tilt = 0.36, rot0 = -2.25;
    function proj(p, rot, cx, cy, R, lift) {
      var x = p.x * Math.cos(rot) + p.z * Math.sin(rot), z = -p.x * Math.sin(rot) + p.z * Math.cos(rot), y = p.y;
      var y2 = y * Math.cos(tilt) - z * Math.sin(tilt), z2 = y * Math.sin(tilt) + z * Math.cos(tilt);
      lift = lift || 1;
      return { x: cx + x * R * lift, y: cy - y2 * R * lift, z: z2 };
    }
    runWhenVisible(globe, function (t) {
      var f = fitCanvas(globe), ctx = f.ctx, W = f.w, H = f.h, R = Math.min(W, H) * 0.42, cx = W / 2, cy = H / 2, rot = rot0 + t * 0.045;
      ctx.clearRect(0, 0, W, H);
      var atm = ctx.createRadialGradient(cx, cy, R * 0.94, cx, cy, R * 1.2);
      atm.addColorStop(0, "rgba(0,150,255,.42)"); atm.addColorStop(0.4, "rgba(0,120,255,.14)"); atm.addColorStop(1, "rgba(0,80,255,0)");
      ctx.fillStyle = atm; ctx.beginPath(); ctx.arc(cx, cy, R * 1.2, 0, Math.PI * 2); ctx.fill();
      var body = ctx.createRadialGradient(cx - R * 0.35, cy - R * 0.35, R * 0.1, cx, cy, R);
      body.addColorStop(0, "#0c2c5e"); body.addColorStop(0.7, "#061633"); body.addColorStop(1, "#030b1c");
      ctx.fillStyle = body; ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.fill();
      for (var i = 0; i < pts.length; i++) {
        var p = pts[i], q = proj(p, rot, cx, cy, R);
        if (q.z < 0) continue;
        var s = 0.55 + q.z * 0.95;
        if (p.lit) { ctx.fillStyle = "rgba(200,244,255," + (0.5 + 0.5 * q.z).toFixed(2) + ")"; ctx.fillRect(q.x - s, q.y - s, s * 2, s * 2); }
        else if (p.land) { ctx.fillStyle = "rgba(56,168,255," + (0.28 + 0.62 * q.z).toFixed(2) + ")"; ctx.fillRect(q.x - s / 2, q.y - s / 2, s * 1.25, s * 1.25); }
        else if (i % 3 === 0) { ctx.fillStyle = "rgba(40,105,210," + (0.05 + 0.12 * q.z).toFixed(2) + ")"; ctx.fillRect(q.x, q.y, 1, 1); }
      }
      ctx.lineWidth = 1.2;
      links.forEach(function (l, li) {
        var a = hubs[l[0]], b = hubs[l[1]], p1 = proj(a, rot, cx, cy, R), p2 = proj(b, rot, cx, cy, R);
        if (p1.z < 0.02 || p2.z < 0.02) return;
        var mid = { x: a.x + b.x, y: a.y + b.y, z: a.z + b.z }, ml = Math.sqrt(mid.x * mid.x + mid.y * mid.y + mid.z * mid.z) || 1;
        var span = Math.acos(Math.max(-1, Math.min(1, a.x * b.x + a.y * b.y + a.z * b.z)));
        var m = proj({ x: mid.x / ml, y: mid.y / ml, z: mid.z / ml }, rot, cx, cy, R, 1 + span * 0.28);
        var fade = Math.min(p1.z, p2.z) * 2.5, alpha = Math.min(0.6, fade);
        ctx.strokeStyle = "rgba(0,207,255," + alpha.toFixed(2) + ")";
        ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.quadraticCurveTo(m.x, m.y, p2.x, p2.y); ctx.stroke();
        var u = (t * 0.28 + li * 0.37) % 1, bx = (1 - u) * (1 - u) * p1.x + 2 * (1 - u) * u * m.x + u * u * p2.x, by = (1 - u) * (1 - u) * p1.y + 2 * (1 - u) * u * m.y + u * u * p2.y;
        ctx.fillStyle = "rgba(210,248,255," + Math.min(1, fade).toFixed(2) + ")"; ctx.beginPath(); ctx.arc(bx, by, 2, 0, Math.PI * 2); ctx.fill();
      });
      hubs.forEach(function (h) {
        var q = proj(h, rot, cx, cy, R);
        if (q.z < 0.02) return;
        ctx.fillStyle = "rgba(0,207,255," + (0.25 * q.z).toFixed(2) + ")"; ctx.beginPath(); ctx.arc(q.x, q.y, 6, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "rgba(220,250,255," + (0.6 + 0.4 * q.z).toFixed(2) + ")"; ctx.beginPath(); ctx.arc(q.x, q.y, 2.2, 0, Math.PI * 2); ctx.fill();
      });
      var limb = ctx.createRadialGradient(cx, cy, R * 0.86, cx, cy, R);
      limb.addColorStop(0, "rgba(0,160,255,0)"); limb.addColorStop(1, "rgba(80,200,255,.42)");
      ctx.fillStyle = limb; ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.fill();
    });
  }

  /* ---------- Plane diagram: highlight a product, show its line ---------- */
  var plane = document.querySelector(".plane");
  if (plane && plane.querySelectorAll(".node").length) {
    var pnodes = plane.querySelectorAll(".node"), caption = document.querySelector("[data-plane-caption]");
    var idx = 0, timer;
    function show(i) {
      pnodes.forEach(function (n, j) { n.classList.toggle("on", j === i); });
      if (caption) caption.innerHTML = pnodes[i].getAttribute("data-say");
    }
    function cycle() { show(idx); idx = (idx + 1) % pnodes.length; }
    pnodes.forEach(function (n, j) {
      function select() { clearInterval(timer); show(j); }
      function resume() {
        clearInterval(timer);
        idx = (j + 1) % pnodes.length;
        if (!reduce && !plane.contains(document.activeElement) && !plane.matches(":hover")) timer = setInterval(cycle, 3200);
      }
      n.addEventListener("mouseenter", select);
      n.addEventListener("mouseleave", resume);
      n.addEventListener("focus", select);
      n.addEventListener("blur", resume);
    });
    plane.addEventListener("mouseleave", function () {
      clearInterval(timer);
      if (!reduce && !plane.contains(document.activeElement)) timer = setInterval(cycle, 3200);
    });
    cycle();
    if (!reduce) timer = setInterval(cycle, 3200);
  }

  /* ---------- Request lifecycle ---------- */
  var lc = document.querySelector(".lifecycle");
  if (lc) {
    var steps = lc.querySelectorAll(".lc-step"), beam = lc.querySelector(".beam"), log = lc.querySelector(".lc-log");
    var lines = [];
    steps.forEach(function (s) { lines.push(s.getAttribute("data-log")); });
    var cur = -1, lcTimer = null;
    function tick() {
      cur++;
      if (cur >= steps.length) {
        clearInterval(lcTimer); lcTimer = null;
        setTimeout(function () { cur = -1; steps.forEach(function (s) { s.classList.remove("on"); }); if (beam) beam.style.width = "0"; if (log) log.innerHTML = ""; lcTimer = setInterval(tick, 1100); }, 3600);
        return;
      }
      steps[cur].classList.add("on");
      if (beam) beam.style.width = (cur / (steps.length - 1) * 92) + "%";
      if (log) {
        var rows = lines.slice(Math.max(0, cur - 3), cur + 1);
        log.innerHTML = rows.join("<br>");
      }
    }
    if (reduce) { steps.forEach(function (s) { s.classList.add("on"); }); if (log) log.innerHTML = lines.slice(-4).join("<br>"); }
    else if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (en) {
        if (en[0].isIntersecting && !lcTimer && cur === -1) lcTimer = setInterval(tick, 1100);
      }, { threshold: 0.35 }).observe(lc);
    }
  }

  /* ---------- Audit chain: real SHA-256, tamper to break verification ---------- */
  function sha256(ascii) {
    function rr(v, a) { return (v >>> a) | (v << (32 - a)); }
    var mp = Math.pow, max = mp(2, 32), res = "", words = [], bl = ascii.length * 8, i, j;
    var h = sha256.h = sha256.h || [], k = sha256.k = sha256.k || [], pl = k.length, ic = {};
    for (var c = 2; pl < 64; c++) { if (!ic[c]) { for (i = 0; i < 313; i += c) ic[i] = c; h[pl] = (mp(c, .5) * max) | 0; k[pl++] = (mp(c, 1 / 3) * max) | 0; } }
    var H = h.slice(0, 8);
    ascii += "\x80"; while (ascii.length % 64 - 56) ascii += "\x00";
    for (i = 0; i < ascii.length; i++) { j = ascii.charCodeAt(i); words[i >> 2] |= j << ((3 - i) % 4) * 8; }
    words[words.length] = ((bl / max) | 0); words[words.length] = bl;
    for (j = 0; j < words.length;) {
      var w = words.slice(j, j += 16), old = H; H = H.slice(0, 8);
      for (i = 0; i < 64; i++) {
        var w15 = w[i - 15], w2 = w[i - 2], a = H[0], e = H[4];
        var t1 = H[7] + (rr(e, 6) ^ rr(e, 11) ^ rr(e, 25)) + ((e & H[5]) ^ ((~e) & H[6])) + k[i] +
          (w[i] = (i < 16) ? w[i] : (w[i - 16] + (rr(w15, 7) ^ rr(w15, 18) ^ (w15 >>> 3)) + w[i - 7] + (rr(w2, 17) ^ rr(w2, 19) ^ (w2 >>> 10))) | 0);
        var t2 = (rr(a, 2) ^ rr(a, 13) ^ rr(a, 22)) + ((a & H[1]) ^ (a & H[2]) ^ (H[1] & H[2]));
        H = [(t1 + t2) | 0].concat(H); H[4] = (H[4] + t1) | 0;
      }
      for (i = 0; i < 8; i++) H[i] = (H[i] + old[i]) | 0;
    }
    for (i = 0; i < 8; i++) for (j = 3; j + 1; j--) { var b = (H[i] >> (j * 8)) & 255; res += ((b < 16) ? 0 : "") + b.toString(16); }
    return res;
  }
  var chainEl = document.querySelector("[data-chain]");
  if (chainEl) {
    var events = [
      { ev: "run.started", who: "analyst@bank", obj: "Customer Onboarding Review" },
      { ev: "policy.allowed", who: "gateway", obj: "endpoint kyc-review · model allow-list" },
      { ev: "guardrail.redacted", who: "gateway", obj: "PII · 2 fields masked" },
      { ev: "approval.granted", who: "officer@bank", obj: "review shared to case file" },
      { ev: "run.completed", who: "runtime", obj: "cost 0.041 · 6 nodes" }
    ];
    var tampered = -1, statusEl = document.querySelector("[data-chain-status]"), btn = document.querySelector("[data-chain-tamper]");
    function render() {
      var prev = "0".repeat(64), valid = true, html = "";
      // the stored hashes are computed from the ORIGINAL payloads; tampering changes the payload but not the stored hash
      var stored = [], p = "0".repeat(64);
      events.forEach(function (e) { var hh = sha256(p + "|" + e.ev + "|" + e.who + "|" + e.obj); stored.push(hh); p = hh; });
      events.forEach(function (e, i) {
        var payload = i === tampered ? { ev: e.ev, who: e.who, obj: e.obj.replace(/\d/, "9") + " (edited)" } : e;
        var recomputed = sha256(prev + "|" + payload.ev + "|" + payload.who + "|" + payload.obj);
        var ok = valid && recomputed === stored[i];
        if (!ok) valid = false;
        var cls = "blk" + (i === tampered ? " tampered" : (!ok ? " invalid" : ""));
        html += '<div class="' + cls + '"><div><div class="ev">' + payload.ev + '</div><div class="obj">' + payload.obj + '</div></div>' +
          '<div class="ph">prev ' + prev.slice(0, 10) + '…</div>' +
          '<div class="h">hash ' + stored[i].slice(0, 10) + '…</div></div>';
        prev = stored[i];
      });
      chainEl.innerHTML = html;
      if (statusEl) {
        statusEl.classList.toggle("broken", !valid);
        statusEl.textContent = valid ? "Chain verified · 5 of 5 entries" : "Verification failed at entry " + (tampered + 1);
      }
      if (btn) btn.innerHTML = tampered < 0 ? "Try to edit an entry <span class=\"arr\">→</span>" : "Restore the record";
    }
    render();
    if (btn) btn.addEventListener("click", function () { tampered = tampered < 0 ? 2 : -1; render(); });
  }

  /* ---------- Catalogue filter buttons ---------- */
  document.querySelectorAll("[data-tabs]").forEach(function (group) {
    var tabs = group.querySelectorAll(".tab"), target = document.querySelector(group.getAttribute("data-tabs"));
    tabs.forEach(function (t) {
      t.addEventListener("click", function () {
        tabs.forEach(function (x) { x.setAttribute("aria-pressed", x === t ? "true" : "false"); });
        var f = t.getAttribute("data-filter");
        target.querySelectorAll("[data-sector]").forEach(function (card) {
          card.hidden = !(f === "all" || card.getAttribute("data-sector").indexOf(f) > -1);
        });
      });
    });
  });

  /* ---------- Live policy stream (illustrative governed events) ---------- */
  var stream = document.querySelector("[data-stream] .s-rows");
  if (stream) {
    var ic = {
      id: '<circle cx="12" cy="8.5" r="3.6"/><path d="M4.8 20c.9-3.6 3.8-5.8 7.2-5.8s6.3 2.2 7.2 5.8"/>',
      filter: '<path d="M4 5h16l-6.2 7.4V19l-3.6 1.5v-8.1z"/>',
      policy: '<path d="M7 3.5h7.5L19 8v12.5H7z"/><path d="M14.5 3.5V8H19"/><path d="M10 12.5h6M10 16h6"/>',
      cpu: '<rect x="6.5" y="6.5" width="11" height="11" rx="2"/><path d="M9.5 3v3.5M14.5 3v3.5M9.5 17.5V21M14.5 17.5V21M3 9.5h3.5M3 14.5h3.5M17.5 9.5H21M17.5 14.5H21"/>',
      approve: '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="m8.3 12.3 2.5 2.5 4.9-5.2"/>',
      chain: '<rect x="3" y="9" width="8" height="6" rx="3"/><rect x="13" y="9" width="8" height="6" rx="3"/><path d="M9 12h6"/>'
    };
    var feed = [
      ["id", "Identity verified", "analyst@bank · SSO + MFA", "ok", "allow"],
      ["policy", "AI Endpoint policy", "kyc-review · model allow-list", "ok", "pass"],
      ["filter", "PII redacted before the call", "2 fields masked", "info", "redact"],
      ["cpu", "Routed to local model", "your GPUs · 1.8 s", "info", "run"],
      ["approve", "Approval requested", "credit memo · level 2", "warn", "hold"],
      ["chain", "Audit entry sealed", "hash-chained · WORM", "ok", "sealed"],
      ["filter", "Prompt injection blocked", "external document", "warn", "block"],
      ["policy", "Budget within limit", "38% of monthly cap", "ok", "pass"]
    ];
    var k = 0;
    function push() {
      var f = feed[k++ % feed.length], row = document.createElement("div");
      row.className = "s-row";
      row.innerHTML = '<span class="glow-icon"><svg viewBox="0 0 24 24" aria-hidden="true">' + ic[f[0]] + '</svg></span><div><b>' + f[1] + '</b><small>' + f[2] + '</small></div><span class="st ' + f[3] + '">' + f[4] + '</span>';
      stream.insertBefore(row, stream.firstChild);
      while (stream.children.length > 5) stream.removeChild(stream.lastChild);
    }
    for (var s0 = 0; s0 < 5; s0++) push();
    if (!reduce) setInterval(push, 2200);
  }
})();
