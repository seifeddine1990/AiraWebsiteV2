"""Build the AIRA Fusion website.

    python build.py            # writes ./public
    python build.py --serve    # builds, then serves ./public on http://localhost:8090

Pages live in src/pages/**.html. Each starts with a small front-matter block:

    ---
    title: Page title
    description: One sentence for search and link previews.
    nav: platform            # which header item is current (optional)
    ---

The header, footer, fonts and meta tags are added here, once, so a nav change is
one edit. Placeholders usable inside pages:

    {{root}}          relative path to the site root ("" or "../"), works on file://
    {{icon:NAME}}     an inline line icon from ICONS below
    {{hex:NAME}}      a product hexagon badge from HEX below
    {{hexfield}}      the decorative hex field used behind CTA bands
    {{cta}}           the standard closing call-to-action band
"""
from __future__ import annotations

import http.server
from html import escape
import os
import re
import shutil
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT = ROOT / "public"
SITE_URL = "https://airafusion.com"
CONTACT_EMAIL = "info@airafusion.com"

# Brand artwork is the approved AIRA Fusion files in src/static/img/brand (never redrawn here).

NAV = [
    ("home", "Home", "index.html"),
    ("nexus", "AIRA Nexus", "nexus.html"),
    ("solutions", "Solutions", "solutions.html"),
    ("security", "Security", "security.html"),
    ("about", "About", "about.html"),
]

# 24px line icons, stroke drawn by CSS (.icon svg)
ICONS = {
    "shield": '<path d="M12 3 4.5 6v5.5c0 4.6 3.1 8.3 7.5 9.5 4.4-1.2 7.5-4.9 7.5-9.5V6L12 3Z"/><path d="m8.8 12.2 2.2 2.2 4.3-4.6"/>',
    "lock": '<rect x="5" y="10.5" width="14" height="10" rx="2.2"/><path d="M8 10.5V7.8a4 4 0 0 1 8 0v2.7"/><path d="M12 14.5v2.5"/>',
    "id": '<circle cx="12" cy="8.5" r="3.6"/><path d="M4.8 20c.9-3.6 3.8-5.8 7.2-5.8s6.3 2.2 7.2 5.8"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="m10.9 12.1 8.1-8.1"/><path d="m16 7 2.5 2.5"/><path d="m14 9 1.8 1.8"/>',
    "policy": '<path d="M7 3.5h7.5L19 8v12.5H7z"/><path d="M14.5 3.5V8H19"/><path d="M10 12.5h6M10 16h6"/><path d="M4.5 7v13.5"/>',
    "filter": '<path d="M4 5h16l-6.2 7.4V19l-3.6 1.5v-8.1z"/>',
    "cpu": '<rect x="6.5" y="6.5" width="11" height="11" rx="2"/><path d="M9.5 3v3.5M14.5 3v3.5M9.5 17.5V21M14.5 17.5V21M3 9.5h3.5M3 14.5h3.5M17.5 9.5H21M17.5 14.5H21"/><rect x="10" y="10" width="4" height="4" rx=".6"/>',
    "pulse": '<path d="M3 12h4l2.5-6 5 12 2.5-6h4"/>',
    "chain": '<rect x="3" y="9" width="8" height="6" rx="3"/><rect x="13" y="9" width="8" height="6" rx="3"/><path d="M9 12h6"/>',
    "server": '<rect x="4" y="4" width="16" height="7" rx="1.8"/><rect x="4" y="13" width="16" height="7" rx="1.8"/><path d="M8 7.5h.01M8 16.5h.01M12 7.5h5M12 16.5h5"/>',
    "cloud": '<path d="M7 18.5a4.5 4.5 0 0 1-.6-8.96A6 6 0 0 1 18 9.5a4.5 4.5 0 0 1-.5 9z"/>',
    "airgap": '<rect x="3" y="7" width="7" height="10" rx="1.6"/><rect x="14" y="7" width="7" height="10" rx="1.6"/><path d="M10.8 12h.6M12.4 12h.6"/>',
    "door": '<path d="M5 20.5V4.5a1 1 0 0 1 1-1h9.5v17"/><path d="M15.5 3.5 19 5v15.5h-3.5"/><path d="M12.5 12h.01"/><path d="M3 20.5h18"/>',
    "flow": '<rect x="3" y="3.5" width="6" height="5" rx="1.2"/><rect x="15" y="9.5" width="6" height="5" rx="1.2"/><rect x="3" y="15.5" width="6" height="5" rx="1.2"/><path d="M9 6h3a2 2 0 0 1 2 2v2.5h1M9 18h3a2 2 0 0 0 2-2v-2.5"/>',
    "doc": '<path d="M6.5 3.5h7L18 8v12.5H6.5z"/><path d="M13.5 3.5V8H18"/><path d="M9.5 13h5.5M9.5 16.5h3.5"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6"/><path d="m15 15 5 5"/>',
    "users": '<circle cx="9" cy="8.5" r="3.2"/><path d="M3 19.5c.7-3.2 3-5 6-5s5.3 1.8 6 5"/><path d="M15.5 5.6a3.2 3.2 0 0 1 0 5.8M17.5 14.8c1.8.7 3 2.3 3.5 4.7"/>',
    "check": '<circle cx="12" cy="12" r="8.5"/><path d="m8.3 12.3 2.5 2.5 4.9-5.2"/>',
    "coins": '<ellipse cx="10" cy="6.5" rx="6" ry="2.5"/><path d="M4 6.5v4c0 1.4 2.7 2.5 6 2.5s6-1.1 6-2.5v-4"/><path d="M8 15.8c.6.1 1.3.2 2 .2 3.3 0 6-1.1 6-2.5"/><path d="M4 10.5v4c0 1.1 1.6 2 4 2.3"/><path d="M17 11.5c1.9.4 3 1.2 3 2.1v4c0 1.4-2.7 2.5-6 2.5-1.6 0-3.1-.3-4.2-.7"/>',
    "eye": '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="3"/>',
    "layers": '<path d="m12 3.5 8.5 4.5-8.5 4.5L3.5 8z"/><path d="m3.5 12 8.5 4.5 8.5-4.5"/><path d="m3.5 16 8.5 4.5 8.5-4.5"/>',
    "bank": '<path d="M3.5 9 12 4l8.5 5"/><path d="M5 9.5v8M9.5 9.5v8M14.5 9.5v8M19 9.5v8"/><path d="M3 20h18"/>',
    "gov": '<path d="M12 3.5v3"/><path d="M8.5 6.5h7"/><path d="M5 11a7 7 0 0 1 14 0"/><path d="M4 11h16M6 11v7M10 11v7M14 11v7M18 11v7M3 20.5h18"/>',
    "shieldcheck": '<path d="M12 3 4.5 6v5.5c0 4.6 3.1 8.3 7.5 9.5 4.4-1.2 7.5-4.9 7.5-9.5V6L12 3Z"/>',
    "health": '<path d="M12 20s-7.5-4.4-7.5-10A4.3 4.3 0 0 1 12 7.3 4.3 4.3 0 0 1 19.5 10c0 5.6-7.5 10-7.5 10Z"/><path d="M8 12.5h2l1.2-2.5 1.8 4 1.2-1.5H16"/>',
    "spark": '<path d="M12 3.5v4M12 16.5v4M3.5 12h4M16.5 12h4M6 6l2.6 2.6M15.4 15.4 18 18M6 18l2.6-2.6M15.4 8.6 18 6"/>',
    "route": '<circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="6" r="2.5"/><path d="M8.5 18H15a3 3 0 0 0 0-6H9a3 3 0 0 1 0-6h6.5"/>',
    "approve": '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="m8.3 12.3 2.5 2.5 4.9-5.2"/>',
    "db": '<ellipse cx="12" cy="6" rx="7" ry="2.8"/><path d="M5 6v12c0 1.5 3.1 2.8 7 2.8s7-1.3 7-2.8V6"/><path d="M5 12c0 1.5 3.1 2.8 7 2.8s7-1.3 7-2.8"/>',
    "terminal": '<rect x="3" y="4.5" width="18" height="15" rx="2.2"/><path d="m7 10 3 2.5L7 15M12.5 15.5H17"/>',
}

# Product hexagon badges: a small pointy-top hex with a product glyph.
HEX_GLYPH = {
    "hub": '<path d="m19 31 13-12 13 12M23 28v16h18V28M29 44V34h6v10"/>',
    "studio": '<rect x="19" y="20" width="10" height="9" rx="2"/><rect x="35" y="35" width="10" height="9" rx="2"/><path d="M29 24.5h8a3 3 0 0 1 3 3V35M19 40h10M24 35v10"/>',
    "gateway": '<circle cx="22" cy="24" r="4"/><circle cx="42" cy="40" r="4"/><path d="M26 24h2a4 4 0 0 1 4 4v8a4 4 0 0 0 4 4h2m-3-3 3 3-3 3"/>',
    "runtime": '<circle cx="32" cy="32" r="9.5"/><circle cx="32" cy="32" r="3"/><path d="M32 29V18M34.35 30.13l8.6-6.86M34.92 32.67l10.73 2.45M33.3 34.7l4.77 9.91M30.7 34.7l-4.77 9.91M29.08 32.67l-10.73 2.45M29.65 30.13l-8.6-6.86"/>',
    "signal": '<rect x="19" y="21" width="26" height="19" rx="3"/><path d="M28 45h8M32 40v5M23 32h4l3-6 4 10 3-5h4"/>',
    "data": '<ellipse cx="29" cy="23" rx="8" ry="3"/><path d="M21 23v14c0 1.7 3.6 3 8 3M37 23v8M21 30c0 1.7 3.6 3 8 3s8-1.3 8-3M29 40h8M37 36v8h4"/><circle cx="44" cy="44" r="3"/><circle cx="40" cy="34" r="3"/>',
    "console": '<rect x="22" y="23" width="20" height="18" rx="2.5"/><path d="M22 28.5h20M26 34h7"/>',
}


def hexbadge(name: str) -> str:
    pts = "32,5 55.4,18.5 55.4,45.5 32,59 8.6,45.5 8.6,18.5"
    return (
        f'<svg class="p-hex" viewBox="0 0 64 64" aria-hidden="true">'
        f'<defs><linearGradient id="hx-{name}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#00CFFF"/><stop offset="1" stop-color="#006CFF"/></linearGradient></defs>'
        f'<polygon points="{pts}" fill="#0a2244" stroke="url(#hx-{name})" stroke-width="2.2" stroke-linejoin="round"/>'
        f'<g fill="none" stroke="#bfefff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{HEX_GLYPH[name]}</g></svg>'
    )


def icon(name: str) -> str:
    if name.startswith("product"):
        return f'<svg viewBox="16 16 32 32" aria-hidden="true">{HEX_GLYPH[name[7:]]}</svg>'
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


def hexfield() -> str:
    import math
    cells = []
    s = 34
    hw = s * math.sqrt(3)
    for r in range(-1, 9):
        for c in range(-1, 8):
            cx = c * hw + (hw / 2 if r % 2 else 0)
            cy = r * s * 1.5
            d = math.hypot(cx - 260, cy - 240)
            op = max(0.0, 1 - d / 300)
            if op <= 0.02:
                continue
            pts = " ".join(f"{cx + (s - 3) * math.cos(math.radians(60 * i - 90)):.1f},{cy + (s - 3) * math.sin(math.radians(60 * i - 90)):.1f}" for i in range(6))
            hot = (r * 7 + c * 3) % 11 == 0
            stroke = "#00CFFF" if hot else "#6fbfff"
            cells.append(f'<polygon points="{pts}" fill="{"rgba(0,207,255,.08)" if hot else "none"}" stroke="{stroke}" stroke-opacity="{op * (0.9 if hot else 0.35):.2f}" stroke-width="1"/>')
    return f'<svg class="hexfield" viewBox="0 0 520 480" aria-hidden="true">{"".join(cells)}</svg>'


def _hexpts(cx: float, cy: float, r: float) -> str:
    import math
    return " ".join(f"{cx + r * math.cos(math.radians(60 * i - 90)):.1f},{cy + r * math.sin(math.radians(60 * i - 90)):.1f}" for i in range(6))


PLANE_NODES = [
    ("Home", "Consume", "<b>AIRA Home</b> &mdash; Ask and Work for every employee: grounded answers with citations, documents and the AI Solution catalog."),
    ("Studio", "Create", "<b>AIRA Studio</b> &mdash; build, test, evaluate and publish assistants, agents, flows and AI Solutions."),
    ("Gateway", "Unified access", "<b>AIRA Gateway</b> &mdash; one governed catalog for LLMs, agents and AI Solutions, with application subscriptions, policy controls and audit."),
    ("Runtime", "Execute", "<b>AIRA Runtime</b> &mdash; deploys and executes capabilities with environment control on Kubernetes and OpenShift, using governed access through Gateway."),
    ("Signal", "Observe", "<b>AIRA Signal</b> &mdash; runs, latency, spend, flagged events and health, across the whole estate."),
    ("Data", "Connect", "<b>AIRA Data</b> &mdash; governed sources, ingestion, extraction and document review. Read-only by default."),
]


def plane() -> str:
    import math
    parts = ['<svg viewBox="0 0 600 600" role="img" aria-label="AIRA Nexus: six products around one governed core">',
             '<defs><linearGradient id="pgrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#00CFFF"/><stop offset="1" stop-color="#006CFF"/></linearGradient>'
             '<radialGradient id="pcore" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#0a6cff" stop-opacity=".35"/><stop offset="1" stop-color="#0a6cff" stop-opacity="0"/></radialGradient></defs>',
             '<circle cx="300" cy="300" r="290" fill="url(#pcore)"/>',
             '<circle class="orbit" cx="300" cy="300" r="215"/>',
             '<circle class="orbit dash" cx="300" cy="300" r="262"/>',
             '<circle class="orbit" cx="300" cy="300" r="120" opacity=".7"/>',
             f'<polygon points="{_hexpts(300, 300, 150)}" fill="none" stroke="rgba(0,207,255,.14)" stroke-width="1"/>']
    pos = []
    for i in range(6):
        a = math.radians(60 * i - 90)
        pos.append((300 + 215 * math.cos(a), 300 + 215 * math.sin(a)))
    for i, (x, y) in enumerate(pos):
        parts.append(f'<line class="spoke" x1="300" y1="300" x2="{x:.1f}" y2="{y:.1f}"/>')
        parts.append(f'<path class="pulse" d="M{x:.1f},{y:.1f} L300,300" style="animation-delay:{i * 0.6:.1f}s"/>')
    parts.append('<image href="{{root}}img/brand/aira-icon-512.png" x="222" y="222" width="156" height="156"/>')
    for i, ((x, y), (name, sub, say)) in enumerate(zip(pos, PLANE_NODES)):
        parts.append(f'<g class="node" data-say="{say}" tabindex="0"><polygon class="node-hex" points="{_hexpts(x, y, 58)}"/>'
                     f'<text x="{x:.1f}" y="{y + 1:.1f}">{name}</text><text class="sub" x="{x:.1f}" y="{y + 19:.1f}">{sub}</text></g>')
    parts.append("</svg>")
    return "".join(parts)


def doors() -> str:
    return """<svg viewBox="0 0 1000 570" role="img" aria-label="AIRA Nexus Platform contains AIRA Home, a central AIRA Gateway, approved LLM access and AIRA Runtime. AIRA Home and external application users connect through Gateway to approved LLMs and Runtime.">
<defs><marker id="gateway-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#00CFFF"/></marker></defs>
<rect class="perimeter" x="14" y="16" width="972" height="408" rx="20"/>
<text class="lbl" x="40" y="54">AIRA Nexus Platform</text>
<text class="tiny" x="40" y="80">One platform &middot; shared identity, governance and audit</text>
<rect class="box" x="40" y="184" width="230" height="120" rx="14"/>
<text class="lbl" x="62" y="220">AIRA Home</text>
<text class="tiny" x="62" y="250">Your teams &middot; Ask &amp; Work</text>
<text class="tiny" x="62" y="276">Knowledge &amp; AI Solutions</text>
<path marker-end="url(#gateway-arrow)" class="wire flow" d="M270 244 H360"/>
<rect class="box door" x="360" y="134" width="290" height="224" rx="4"/>
<text class="lbl" x="384" y="172">AIRA Gateway</text>
<text class="sub" x="384" y="202">One governed entry point</text>
<text class="tiny" x="384" y="238">Catalog &middot; subscriptions &middot; access</text>
<text class="tiny" x="384" y="268">Routing &middot; fallbacks &middot; guardrails</text>
<text class="tiny" x="384" y="298">Data policy &middot; security &middot; limits</text>
<text class="tiny" x="384" y="328">Every request controlled &amp; audited</text>
<path marker-end="url(#gateway-arrow)" class="wire flow" d="M650 202 H682 V172 H716"/>
<path marker-end="url(#gateway-arrow)" class="wire flow" d="M650 288 H682 V320 H716"/>
<rect class="box" x="716" y="112" width="244" height="120" rx="14"/>
<text class="lbl" x="738" y="148">Approved LLMs</text>
<text class="tiny" x="738" y="178">On-premises &middot; cloud</text>
<text class="tiny" x="738" y="204">Your models &middot; your keys</text>
<rect class="box" x="716" y="260" width="244" height="120" rx="14"/>
<text class="lbl" x="738" y="296">AIRA Runtime</text>
<text class="tiny" x="738" y="326">Agents &amp; AI Solutions</text>
<text class="tiny" x="738" y="352">Execution &amp; environment control</text>
<text class="tiny" x="40" y="402">Studio &middot; Data &middot; Signal &middot; Console support the platform</text>
<rect class="ext" x="40" y="452" width="230" height="100" rx="14"/>
<text class="lbl" x="62" y="486">External app users</text>
<text class="tiny" x="62" y="516">Subscribed applications &amp; APIs</text>
<path marker-end="url(#gateway-arrow)" class="wire flow" d="M270 502 H505 V358"/>
</svg>"""


CTA = """
<section class="section tight">
  <div class="wrap">
    <div class="cta-band rev">
      {{hexfield}}
      <span class="eyebrow">Start with one workload</span>
      <h2 class="mt-s">Prove it on your infrastructure, against your own criteria.</h2>
      <p class="lead">A scoped pilot runs AIRA Nexus inside your perimeter, on your models and your data, with success criteria written down before we start. Your security team reviews the real system, not a slide.</p>
      <div class="ctas">
        <a class="btn btn-primary" href="{{root}}contact.html">Request a briefing <span class="arr">&rarr;</span></a>

      </div>
    </div>
  </div>
</section>
"""


def header(nav: str) -> str:
    items = []
    for key, label, href in NAV:
        cur = ' aria-current="page"' if key == nav else ""
        items.append(f'<li><a class="nl" href="{{{{root}}}}{href}"{cur}>{label}</a></li>')
    return f"""<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <nav class="nav wrap" aria-label="Main">
    <a class="brand" href="{{{{root}}}}index.html" aria-label="AIRA Fusion home">
      <img class="mark" src="{{{{root}}}}img/brand/aira-icon-192.png" alt="" width="40" height="40">
      <img class="word" src="{{{{root}}}}img/brand/aira-wordmark-white.png" alt="AIRA Fusion" width="106" height="35">
    </a>
    <button class="nav-toggle" aria-label="Menu" aria-expanded="false"><i></i></button>
    <ul class="nav-links">
      {''.join(items)}
      <li class="nav-cta"><a class="btn btn-outline btn-sm" href="{{{{root}}}}contact.html">Contact us</a></li>
    </ul>
  </nav>
</header>
"""


FOOTER = f"""
<footer class="site-footer">
  <div class="wrap">
    <div class="foot-grid">
      <div class="foot-brand">
        <a class="brand" href="{{{{root}}}}index.html" aria-label="AIRA Fusion home">
          <img class="mark" src="{{{{root}}}}img/brand/aira-icon-192.png" alt="" width="40" height="40">
          <img class="word" src="{{{{root}}}}img/brand/aira-wordmark-white.png" alt="AIRA Fusion" width="106" height="35">
        </a>
        <div class="domain">airafusion.com</div>
        <p>Artificial Intelligence Research &amp; Application. An enterprise AI company making AI secure, regulated and reliable for banks, governments and regulated enterprises.</p>
        <div class="tag">Secure &bull; Regulated &bull; Reliable</div>
      </div>
      <div class="foot-col"><h5>AIRA Fusion</h5>
        <a href="{{{{root}}}}about.html">About us</a><a href="{{{{root}}}}about.html#principles">Principles</a><a href="{{{{root}}}}insights/index.html">Insights</a><a href="{{{{root}}}}contact.html">Contact</a></div>
      <div class="foot-col"><h5>AIRA Nexus</h5>
        <a href="{{{{root}}}}nexus.html">Overview</a><a href="{{{{root}}}}nexus.html#products">Six products</a><a href="{{{{root}}}}nexus.html#doors">Architecture</a><a href="{{{{root}}}}nexus.html#deploy">Specifications</a></div>
      <div class="foot-col"><h5>Trust</h5>
        <a href="{{{{root}}}}security.html">Security &amp; governance</a><a href="{{{{root}}}}security.html#audit">Tamper-evident audit</a><a href="{{{{root}}}}security.html#assurance">Assurance status</a><a href="{{{{root}}}}security.html#review">Security review pack</a></div>
      <div class="foot-col"><h5>Work with us</h5>
        <a href="{{{{root}}}}solutions.html">Solutions</a><a href="{{{{root}}}}solutions.html#catalogue">Use-case catalogue</a><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></div>
    </div>
    <div class="foot-bottom">
      <span>&copy; <span data-year>2026</span> AIRA Fusion. AIRA Nexus is the flagship platform of AIRA Fusion.</span>
      <span class="mono">airafusion.com</span>
    </div>
  </div>
</footer>
"""


def canonical_url(meta: dict, rel: str) -> str:
    return f"{SITE_URL}/{meta.get('canonical', rel)}".replace("/index.html", "/")


def indexable(rel: str) -> bool:
    return rel != "404.html" and not rel.startswith("_")


def page(meta: dict, body: str, rel: str) -> str:
    title = meta.get("title", "AIRA Fusion")
    full_title = title if "AIRA" in title else f"{title} | AIRA Fusion"
    full_title = escape(full_title, quote=True)
    desc = escape(meta.get("description", ""), quote=True)
    canon = escape(canonical_url(meta, rel), quote=True)
    robots = '<meta name="robots" content="noindex">' if not indexable(rel) else ""
    return f"""<!DOCTYPE html>
<html lang="en" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#07192B">{robots}
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="AIRA Fusion">
<meta property="og:title" content="{full_title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{SITE_URL}/img/og-card.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="32x32" href="{{{{root}}}}favicon.png">
<link rel="apple-touch-icon" href="{{{{root}}}}apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Montserrat:wght@300;400;500;600;700;800&family=Michroma&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{{{{root}}}}css/site.css">
<link rel="stylesheet" href="{{{{root}}}}css/glow.css">
</head>
<body>
{header(meta.get("nav", ""))}
<main id="main">
{body}
</main>
{FOOTER}
<script src="{{{{root}}}}js/site.js" defer></script>
</body>
</html>
"""


FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def render(text: str, root: str) -> str:
    # every inner-page hero gets the flowing light waves (replacing the old hex field)
    text = text.replace('<section class="page-hero bg-grid">\n  {{hexfield}}\n', '<section class="page-hero">\n  <canvas class="waves" aria-hidden="true"></canvas>\n')
    text = re.sub(r'<section class="page-hero bg-grid"(.*?)>', r'<section class="page-hero"\1>\n  <canvas class="waves" aria-hidden="true"></canvas>', text)
    text = text.replace("{{cta}}", CTA).replace("{{hexfield}}", hexfield())
    text = text.replace("{{plane}}", plane()).replace("{{doors}}", doors())
    text = re.sub(r"\{\{icon:([a-z]+)\}\}", lambda m: icon(m.group(1)), text)
    text = re.sub(r"\{\{hex:([a-z]+)\}\}", lambda m: hexbadge(m.group(1)), text)
    text = text.replace("{{email}}", CONTACT_EMAIL)
    return text.replace("{{root}}", root)


def build() -> None:
    # empty the output folder but keep the folder itself (a preview server may be serving from it)
    OUT.mkdir(exist_ok=True)
    for child in OUT.iterdir():
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    shutil.copytree(SRC / "static", OUT, dirs_exist_ok=True)
    count = 0
    urls = []
    for src in sorted((SRC / "pages").rglob("*.html")):
        rel = src.relative_to(SRC / "pages").as_posix()
        raw = src.read_text(encoding="utf-8")
        m = FM.match(raw)
        meta = {}
        if m:
            for line in m.group(1).splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            raw = raw[m.end():]
        depth = rel.count("/")
        root = "/" if rel == "404.html" else "../" * depth
        html = render(page(meta, raw, rel), root)
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        if indexable(rel) and canonical_url(meta, rel) == canonical_url({}, rel):
            urls.append(canonical_url(meta, rel))
        count += 1
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{escape(u)}</loc></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    leftovers = [p for p in OUT.rglob("*.html") if "{{" in p.read_text(encoding="utf-8")]
    if leftovers:
        sys.exit(f"unresolved placeholders in: {', '.join(str(p.relative_to(OUT)) for p in leftovers)}")
    print(f"built {count} pages -> {OUT}")


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        os.chdir(OUT)
        port = 8090
        with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
            print(f"serving http://localhost:{port}")
            httpd.serve_forever()
