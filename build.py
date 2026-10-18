"""Build the AIRA Fusion website.

    python build.py            # writes ./public
    python build.py --serve    # builds, then serves ./public on http://localhost:8090

Pages live in src/pages/**.html. Each starts with a small front-matter block:

    ---
    title: Page title
    description: One sentence for search and link previews.
    nav: platform            # which header item is current (optional)
    scripts: tour, gateway-sim   # page-specific scripts in static/js (optional)
    ---

The header, footer, fonts and meta tags are added here, once, so a nav change is
one edit. Placeholders usable inside pages:

    {{root}}          relative path to the site root ("" or "../"), works on file://
    {{icon:NAME}}     an inline line icon from ICONS below
    {{hex:NAME}}      a product hexagon badge from HEX below
    {{hexfield}}      the decorative hex field used behind CTA bands
    {{cta}}           the standard closing call-to-action band
    {{tour}}          the interactive AIRA Nexus product tour (TOURS below)
    {{photo:NAME}}    a tinted photo fading in behind a hero or CTA (add ":lazy" below the fold)
    {{band:NAME}}     a photo band across the top of a card
"""
from __future__ import annotations

import http.server
import hashlib
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
    ("insights", "Insights", "insights/index.html"),
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


# Interactive product tour: the executive briefing deck's product tours, one tab per product.
# Pins are percentages of the screenshot; each callout matches the pin with the same number.
TOURS = [
    dict(id="home", name="Home", role="01 · Consume", icon="producthub",
         hex="hub", kind='Consume',
         summary='Where every employee uses AI. Ask for answers; Work for objectives. One inbox for approvals, running and failed work, with AI Solutions a click away.',
         features=['<b>Ask</b>: governed chat across approved models, grounded in knowledge, with citations and abstention', '<b>Work</b>: give AIRA an objective and follow it through approvals to a result', '<b>Knowledge Hub</b>: access curated enterprise knowledge collections, from policies to compliance guidance, with collection-level permissions and answers grounded in source material', '<b>Document Insights</b>: upload, OCR and chat with a document', '<b>The AI Solution catalog</b>, with a run page for each type and replayable run history'],
         title=("One front door", "for every employee."),
         lead="The live product: the same screen your staff open on day one. Ask for answers, give Work an objective, and find approvals, knowledge and AI Solutions in one place.",
         shots=[dict(src="tour-aira-home.jpg", url="home.bank.local/chat", alt="AIRA Home: the Ask screen with pending actions and approved assistants",
                     pins=[(32, 80), (49, 75), (34, 46), (12, 42)])],
         points=[("Approved assistants only", "Staff pick from the assistants and agents the bank has published."),
                 ("Governed, encrypted, audited", "Every prompt passes policy before a model sees it."),
                 ("Work waits for you", "Approvals and runs that need a person, in one inbox."),
                 ("Knowledge one click away", "Collections, documents and AI Solutions in the same place.")]),
    dict(id="studio", name="Studio", role="02 · Create", icon="productstudio",
         hex="studio", kind='Create',
         summary='Where teams build. One path from idea to production: Build &rarr; Configure &rarr; Assign AI &rarr; Test &rarr; Evaluate &rarr; Publish. What a builder tests in Studio is exactly what Runtime runs.',
         features=['Four kinds of capability: AI Assistant, AI Agent, AI Flow and AI Solution', 'A Solution Advisor that drafts a capability from a plain-language description', 'Typed-node workflow canvas: prompt, knowledge, HTTP, code, database, agent, MCP tool, branching, error handling and subflows', 'Prompt Lab, a run debugger, and evaluation scenario libraries graded by programmatic checks plus an LLM judge', 'Templates, data sources, an encrypted connections vault and MCP servers'],
         title=("Start from", "banking templates."),
         lead="Copy a template, wire in your knowledge and systems, and publish, with sign-off designed in. What a builder tests in Studio is exactly what Runtime runs.",
         shots=[dict(src="tour-aira-studio-1.jpg", url="studio.bank.local/templates", alt="AIRA Studio: the template gallery",
                     pins=[(19, 33.3), (72.6, 54.4)]),
                dict(src="tour-aira-studio-2.jpg", url="Workflow · Corporate Credit Review", alt="AIRA Studio: a corporate credit review workflow with an approval step",
                     pins=[(71, 16)], inset=True)],
         points=[("Templates for the bank", "Policy and compliance, client onboarding, credit proposals and research agents."),
                 ("Credit proposal, drafted", "Financials in; policy exceptions, covenants and a committee memo out."),
                 ("Approval is a step", "The credit committee signs off inside the workflow, before anything is recorded.")]),
    dict(id="gateway", name="Gateway", role="03 · Govern access", icon="productgateway",
         hex="gateway", kind='Unified access',
         summary='One controlled, audited entry point for on-premises and cloud LLMs, agents and AI Solutions. AIRA Nexus Runtime and external applications access the same governed catalog through application subscriptions.',
         features=['<b>One catalog</b>: approved LLMs, agents and AI Solutions for Nexus and external applications', '<b>Application subscriptions</b>: subscribe to catalog offerings with controlled access grants and limits', '<b>Policy controls</b>: models, fallbacks, routing, guardrails, data policy and security level', '<b>Audited access</b>: identity-bound requests, usage tracking and a record of every call'],
         title=("Every model call,", "on one screen."),
         lead="The live state of the model plane: traffic, errors, spend and policy, per time window, through one governed door to every model.",
         shots=[dict(src="tour-aira-gateway.jpg", url="gateway.bank.local/overview", alt="AIRA Gateway: overview of requests, errors, cost, budgets and policy blocks",
                     pins=[(19.4, 37.5), (79.5, 37.5), (39.5, 51), (59.5, 66.7)])],
         points=[("Traffic and errors", "Requests, failures and latency for every AI endpoint."),
                 ("Policy blocks", "Requests stopped by policy: counted, never silent."),
                 ("Budgets before overspend", "Limits per team, key and application, flagged early."),
                 ("Operator queue", "Requests, subscriptions and models that need a decision.")]),
    dict(id="runtime", name="Runtime", role="04 · Execute", icon="productruntime",
         hex="runtime", kind='Execute',
         summary='Where published capabilities run. Runtime deploys versions, governs execution and gives your team full control over environments on Kubernetes and OpenShift. Access to models, agents and AI Solutions is controlled through AIRA Gateway.',
         features=['<b>Environment control</b>: manage environments, versioned deployments and schedules on Kubernetes and OpenShift', '<b>Governed access</b>: each deployed capability uses its own identity and access grants through Gateway', '<b>Execution governance</b>: approvals, run history and a durable record of every execution', 'Triggers in and deliveries out with retry; usage and cost per deployment', 'Tenant isolation enforced in the database'],
         title=("Published once,", "live by environment."),
         lead="What Studio publishes, Runtime runs: versioned, approved and isolated per environment.",
         shots=[dict(src="tour-aira-runtime.jpg", url="runtime.bank.local/published", alt="AIRA Runtime: published AI Solutions with versions and environments",
                     pins=[(64.7, 36), (31, 57), (47.5, 36), (88, 20.5)])],
         points=[("Live where it is approved", "Each version is promoted per environment: test, then production."),
                 ("Arabic and English", "An Arabic credit memo runs beside its English twin."),
                 ("Workflows and apps", "Every kind of AI Solution, versioned the same way."),
                 ("Move by bundle", "Import a release bundle from another estate.")]),
    dict(id="signal", name="Signal", role="05 · Observe", icon="productsignal",
         hex="signal", kind='Observe',
         summary='One answer to "what is our AI doing?" Signal observes runs, cost and health across the estate, and gives investigators the thread to pull when something looks wrong.',
         features=['Overview of AI Solution runs, failure rate, node latency and spend, from one hour to ninety days', 'Activity, LLM activity, journeys, flagged events and incidents', 'Health of AI Solutions, knowledge, the workflow engine, the platform and the estate', 'Cost, spend and security views, with export'],
         title=("Evidence your auditors", "can verify."),
         lead="Every action lands in a hash-chained ledger, checked in place and exported in one click.",
         shots=[dict(src="tour-aira-signal.jpg", url="signal.bank.local/audit", alt="AIRA Signal: the audit log with chain verification and evidence export",
                     pins=[(33.5, 30.5), (17.5, 44.4), (80.5, 55.5), (79.5, 30.5)])],
         points=[("Chain verified", "Any alteration breaks the hash chain, and the screen says so."),
                 ("Filter by who and what", "Person, action, product and resource."),
                 ("Patterns at a glance", "The most frequent actions in the window."),
                 ("Evidence export", "Download the audit evidence for an examiner.")]),
    dict(id="data", name="Data", role="06 · Connect", icon="productdata",
         hex="data", kind='Connect',
         summary='The governed data plane. Connect enterprise systems, ingest documents exactly once, and keep every extraction reviewable against the content it came from.',
         features=['Governed connectivity to PostgreSQL, SQL Server, MySQL, Oracle and IBM Db2, read-only by default, every query audited', 'Idempotent ingestion jobs that report incomplete attempts and never create duplicates', 'Document review bound to the content hash and the extractor version', 'A bounded tabular extraction service for CSV, TSV and JSON'],
         title=("Feed AI from your systems,", "governed."),
         lead="The governed data plane: connect enterprise systems, ingest documents exactly once, and keep every extraction reviewable against the content it came from.",
         diagram=True, pins=[(27.3, 16.5), (37.5, 50), (50, 29.6), (27.3, 78)],
         points=[("Governed connectivity", "PostgreSQL, SQL Server, MySQL, Oracle and IBM Db2: read-only by default, every query audited."),
                 ("Ingested exactly once", "Idempotent jobs report incomplete attempts and never create duplicates."),
                 ("Review bound to the source", "Each review is tied to the content hash and the extractor version."),
                 ("Tabular extraction", "A bounded service for CSV, TSV and JSON.")]),
]

DATA_DIAGRAM = """<svg class="data-diagram" viewBox="0 0 960 540" role="img" aria-label="Diagram: enterprise systems and documents flow through AIRA Data into knowledge collections, reviewed extractions and the audit trail">
<defs><linearGradient id="dd-core" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#10275A"/><stop offset="1" stop-color="#0A1A3A"/></linearGradient></defs>
<rect width="960" height="540" fill="#F7F9FD"/>
<g class="dd-wires" fill="none">
<path id="dd-s1" d="M262 122 C330 122 320 270 380 270"/><path id="dd-s2" d="M262 222 C330 222 330 270 380 270"/>
<path id="dd-s3" d="M262 322 C330 322 330 270 380 270"/><path id="dd-s4" d="M262 422 C330 422 320 270 380 270"/>
<path id="dd-o1" d="M580 270 C640 270 630 162 698 162"/><path id="dd-o2" d="M580 270 L698 270"/><path id="dd-o3" d="M580 270 C640 270 630 378 698 378"/>
</g>
<g class="dd-flow" fill="#2F86FF">
<circle r="4"><animateMotion dur="2.6s" repeatCount="indefinite"><mpath href="#dd-s1"/></animateMotion></circle>
<circle r="4"><animateMotion dur="2.6s" begin=".6s" repeatCount="indefinite"><mpath href="#dd-s2"/></animateMotion></circle>
<circle r="4"><animateMotion dur="2.6s" begin="1.2s" repeatCount="indefinite"><mpath href="#dd-s3"/></animateMotion></circle>
<circle r="4"><animateMotion dur="2.6s" begin="1.8s" repeatCount="indefinite"><mpath href="#dd-s4"/></animateMotion></circle>
<circle r="4"><animateMotion dur="2s" begin=".3s" repeatCount="indefinite"><mpath href="#dd-o1"/></animateMotion></circle>
<circle r="4"><animateMotion dur="2s" begin="1s" repeatCount="indefinite"><mpath href="#dd-o2"/></animateMotion></circle>
<circle r="4"><animateMotion dur="2s" begin="1.6s" repeatCount="indefinite"><mpath href="#dd-o3"/></animateMotion></circle>
</g>
<g class="dd-box"><rect x="42" y="90" width="220" height="64" rx="14"/><rect x="42" y="190" width="220" height="64" rx="14"/><rect x="42" y="290" width="220" height="64" rx="14"/><rect x="42" y="390" width="220" height="64" rx="14"/>
<rect x="698" y="130" width="220" height="64" rx="14"/><rect x="698" y="238" width="220" height="64" rx="14"/><rect x="698" y="346" width="220" height="64" rx="14"/></g>
<g class="dd-k"><text x="62" y="116">DATABASES</text><text x="62" y="216">DATABASES</text><text x="62" y="316">CONTENT</text><text x="62" y="416">FILES</text>
<text x="718" y="156">KNOWLEDGE</text><text x="718" y="264">REVIEW</text><text x="718" y="372">EVIDENCE</text></g>
<g class="dd-t"><text x="62" y="140">PostgreSQL · SQL Server</text><text x="62" y="240">Oracle · IBM Db2 · MySQL</text><text x="62" y="340">Documents &amp; scans</text><text x="62" y="440">CSV · TSV · JSON</text>
<text x="718" y="180">Governed collections</text><text x="718" y="288">Reviewed extractions</text><text x="718" y="396">Audit trail</text></g>
<rect x="380" y="160" width="200" height="220" rx="22" fill="url(#dd-core)"/>
<text class="dd-ck" x="480" y="204" text-anchor="middle">06 · CONNECT</text>
<text class="dd-ct" x="480" y="240" text-anchor="middle">AIRA Data</text>
<g class="dd-cl" text-anchor="middle"><text x="480" y="284">Read-only by default</text><text x="480" y="312">Ingested exactly once</text><text x="480" y="340">Hash-bound review</text></g>
</svg>"""


def tour() -> str:
    tabs, panels = [], []
    for i, t in enumerate(TOURS):
        pid = t["id"]
        tabs.append(
            f'<button class="tour-tab" type="button" role="tab" id="tt-{pid}" aria-controls="{pid}" '
            f'aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}">'
            f'<span class="tt-ico">{{{{icon:{t["icon"]}}}}}</span><span class="tt-txt"><small>{t["role"]}</small><b>AIRA {t["name"]}</b></span></button>')
        points = "".join(
            f'<li><button type="button" class="tour-point" data-pin="{n}"><b>{n}</b><span><strong>{head}</strong>{body}</span>'
            f'<i class="tp-bar" aria-hidden="true"></i></button></li>'
            for n, (head, body) in enumerate(t["points"], 1))

        def pin(k: int, x: float, y: float) -> str:
            return (f'<button type="button" class="pin" data-pin="{k}" style="--x:{x}%;--y:{y}%" '
                    f'aria-label="Point {k}: {t["points"][k - 1][0]}">{k}</button>')

        stage = []
        if t.get("diagram"):
            pins = "".join(pin(k, x, y) for k, (x, y) in enumerate(t["pins"], 1))
            stage.append(f'<figure class="shot shot-diagram"><div class="sb"><i></i><i></i><i></i><span>AIRA Data · how it works</span></div>'
                         f'<div class="shot-view"><div class="shot-canvas">{DATA_DIAGRAM}<span class="spot" aria-hidden="true"></span>{pins}</div></div></figure>')
        n = 0
        for sh in t.get("shots", []):
            pins = ""
            for x, y in sh["pins"]:
                n += 1
                pins += pin(n, x, y)
            inset = sh.get("inset")
            stage.append(
                f'<figure class="shot{" shot-inset" if inset else ""}"><div class="sb"><i></i><i></i><i></i><span>{sh["url"]}</span>'
                f'<button type="button" class="shot-zoom" aria-label="Enlarge screenshot"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"/></svg></button></div>'
                f'<div class="shot-view"><div class="shot-canvas"><img src="{{{{root}}}}img/product/{sh["src"]}" alt="{sh["alt"]}" '
                f'loading="lazy" decoding="async" width="{1800 if inset else 1920}" height="{375 if inset else 1080}">'
                f'<span class="spot" aria-hidden="true"></span>{pins}</div></div></figure>')
        has_inset = any(sh.get("inset") for sh in t.get("shots", []))
        head, tail = t["title"]
        features = "".join(f"<li>{f}</li>" for f in t["features"])
        # The panel id is the product id, so nexus.html#gateway opens the Gateway tab.
        panels.append(
            f'<div class="tour-panel" role="tabpanel" id="{pid}" aria-labelledby="tt-{pid}">'
            f'<div class="tour-copy"><span class="micro accent">AIRA {t["name"]} · {t["kind"]}</span>'
            f'<h3>{head} <span class="grad">{tail}</span></h3><p class="lead">{t["lead"]}</p>'
            f'<ol class="tour-points">{points}</ol></div>'
            f'<div class="tour-stage{" has-inset" if has_inset else ""}">{"".join(stage)}</div>'
            f'<div class="tour-more"><div class="tm-head">{{{{hex:{t["hex"]}}}}}<div><h4>What AIRA {t["name"]} does</h4>'
            f'<p>{t["summary"]}</p></div></div><ul class="tm-list">{features}</ul></div></div>')
    return (f'<div class="tour" data-tour><div class="tour-bar"><div class="tour-tabs" role="tablist" aria-label="AIRA Nexus products">{"".join(tabs)}</div>'
            f'<button type="button" class="tour-play" aria-pressed="true" hidden><span class="tp-on">Pause tour</span><span class="tp-off">Play tour</span></button></div>'
            f'{"".join(panels)}</div>'
            f'<dialog class="tour-lightbox" aria-label="Enlarged screenshot"><button type="button" class="tl-close" aria-label="Close">&times;</button><div class="tl-body"></div></dialog>')

CTA = """
<section class="section tight">
  <div class="wrap">
    <div class="cta-band rev">
      {{photo:hand:lazy}}
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
      <img class="word" src="{{{{root}}}}img/brand/aira-wordmark-navy.png" alt="AIRA Fusion" width="106" height="35">
    </a>
    <button class="nav-toggle" aria-label="Menu" aria-controls="primary-navigation" aria-expanded="false"><i></i></button>
    <ul class="nav-links" id="primary-navigation">
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
          <img class="word" src="{{{{root}}}}img/brand/aira-wordmark-navy.png" alt="AIRA Fusion" width="106" height="35">
        </a>
        <div class="domain">airafusion.com</div>
        <p>Artificial Intelligence Research &amp; Application. An enterprise AI company making AI secure, regulated and reliable for banks, governments and regulated enterprises.</p>
        <div class="tag">Secure &bull; Regulated &bull; Reliable</div>
      </div>
      <div class="foot-col"><h5>AIRA Fusion</h5>
        <a href="{{{{root}}}}insights/index.html">Insights</a><a href="{{{{root}}}}about.html">About us</a><a href="{{{{root}}}}about.html#principles">Principles</a><a href="{{{{root}}}}contact.html">Contact</a></div>
      <div class="foot-col"><h5>AIRA Nexus</h5>
        <a href="{{{{root}}}}nexus.html">Overview</a><a href="{{{{root}}}}nexus.html#products">Six products</a><a href="{{{{root}}}}nexus.html#doors">Architecture</a><a href="{{{{root}}}}nexus.html#deploy">Specifications</a></div>
      <div class="foot-col"><h5>Trust</h5>
        <a href="{{{{root}}}}security.html">Security &amp; governance</a><a href="{{{{root}}}}security.html#audit">Tamper-evident audit</a><a href="{{{{root}}}}security.html#assurance">Assurance status</a><a href="{{{{root}}}}security.html#review">Security review pack</a></div>
      <div class="foot-col"><h5>Work with us</h5>
        <a href="{{{{root}}}}solutions.html">Solutions</a><a href="{{{{root}}}}solutions.html#catalogue">Use-case catalogue</a><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></div>
    </div>
    <div class="foot-bottom">
      <span>&copy; <span data-year>2026</span> AIRA Fusion. AIRA Nexus is the flagship platform of AIRA Fusion.</span>
      <span class="powered">Powered by <b>Al Ahd Al Rasekh for Artificial Intelligence LLC</b> &middot; Jordan</span>
    </div>
  </div>
</footer>
"""


def canonical_url(meta: dict, rel: str) -> str:
    return f"{SITE_URL}/{meta.get('canonical', rel)}".replace("/index.html", "/")


def indexable(rel: str) -> bool:
    return rel != "404.html" and not rel.startswith("_")


def page(meta: dict, body: str, rel: str, default_theme: str = "light") -> str:
    title = meta.get("title", "AIRA Fusion")
    full_title = title if "AIRA" in title else f"{title} | AIRA Fusion"
    full_title = escape(full_title, quote=True)
    desc = escape(meta.get("description", ""), quote=True)
    canon = escape(canonical_url(meta, rel), quote=True)
    robots = '<meta name="robots" content="noindex">' if not indexable(rel) else ""
    # Page-specific scripts from front matter, e.g. "scripts: tour, gateway-sim".
    page_scripts = "".join(f'<script src="{{{{root}}}}js/{name.strip()}.js" defer></script>\n'
                           for name in meta.get("scripts", "").split(",") if name.strip())
    return f"""<!DOCTYPE html>
<html lang="en" class="no-js" data-default-theme="{default_theme}" data-theme="{default_theme}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="{'#f0f6fa' if default_theme == 'light' else '#040d1c'}">{robots}
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
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{{{{root}}}}css/site.css">
<link rel="stylesheet" href="{{{{root}}}}css/glow.css">
<link rel="stylesheet" href="{{{{root}}}}css/briefing.css">
<link id="light-theme" rel="stylesheet" href="{{{{root}}}}css/light.css" media="{'all' if default_theme == 'light' else 'not all'}">
<script src="{{{{root}}}}js/theme.js"></script>
</head>
<body>
{header(meta.get("nav", ""))}
<main id="main">
{body}
</main>
{FOOTER}
<button class="theme-toggle" type="button" aria-label="Switch color theme" hidden>
  <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M20 15.5A8.5 8.5 0 0 1 8.5 4 8.5 8.5 0 1 0 20 15.5Z"/></svg>
  <span>Dark mode</span>
</button>
<script src="{{{{root}}}}js/site.js" defer></script>
{page_scripts}<script src="{{{{root}}}}js/aira-config.js" defer></script>
<script src="{{{{root}}}}js/aira-email.js" defer></script>
<script src="{{{{root}}}}js/aira-contact.js" defer></script>
</body>
</html>
"""


FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def render(text: str, root: str) -> str:
    # every inner-page hero gets the flowing light waves (replacing the old hex field)
    text = text.replace('<section class="page-hero bg-grid">\n  {{hexfield}}\n', '<section class="page-hero">\n  <canvas class="waves" aria-hidden="true"></canvas>\n')
    text = re.sub(r'<section class="page-hero bg-grid"(.*?)>', r'<section class="page-hero"\1>\n  <canvas class="waves" aria-hidden="true"></canvas>', text)
    text = text.replace("{{cta}}", CTA).replace("{{hexfield}}", hexfield())
    text = text.replace("{{tour}}", tour())
    # Briefing photography: a tinted photo fading in from the right, or a band across the top of a card.
    text = re.sub(r"\{\{photo:([a-z]+)(:lazy)?\}\}", lambda m: (
        f'<div class="photo-bleed" aria-hidden="true"><img src="{{{{root}}}}img/photos/{m.group(1)}.jpg" alt="" '
        + ('loading="lazy" ' if m.group(2) else 'fetchpriority="high" ') + 'decoding="async"></div>'), text)
    text = re.sub(r"\{\{band:([a-z]+)\}\}", lambda m: (
        f'<div class="photo-band" aria-hidden="true"><img src="{{{{root}}}}img/photos/{m.group(1)}.jpg" alt="" loading="lazy" decoding="async"></div>'), text)
    text = text.replace("{{plane}}", plane()).replace("{{doors}}", doors())
    text = re.sub(r"\{\{icon:([a-z]+)\}\}", lambda m: icon(m.group(1)), text)
    text = re.sub(r"\{\{hex:([a-z]+)\}\}", lambda m: hexbadge(m.group(1)), text)
    text = text.replace("{{email}}", CONTACT_EMAIL)
    # Use the supplied wordmark for each surface; never recolor the logo artwork.
    text = re.sub(r'<img\b[^>]*src="[^"]*aira-wordmark-navy\.png"[^>]*>',
                  lambda m: m.group(0) + m.group(0).replace("aira-wordmark-navy.png", "aira-wordmark-white.png"), text)
    # Content versions keep a release's CSS and JavaScript in sync with its HTML.
    def version_asset(match: re.Match) -> str:
        asset = match.group(2)
        version = hashlib.sha256((SRC / "static" / asset).read_bytes()).hexdigest()[:12]
        return f'{match.group(1)}="{{{{root}}}}{asset}?v={version}"'
    text = re.sub(r'(href|src)="\{\{root\}\}((?:css|js)/[^"?]+\.(?:css|js))"', version_asset, text)
    return text.replace("{{root}}", root)


def build() -> None:
    # empty the output folder but keep the folder itself (a preview server may be serving from it)
    OUT.mkdir(exist_ok=True)
    for child in OUT.iterdir():
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    shutil.copytree(SRC / "static", OUT, dirs_exist_ok=True)
    count = 0
    urls = []
    home = FM.match((SRC / "pages" / "index.html").read_text(encoding="utf-8"))
    theme_flag = re.search(r"^default_theme:\s*(\S+)\s*$", home.group(1), re.M) if home else None
    default_theme = theme_flag.group(1) if theme_flag else "light"
    if default_theme not in ("light", "dark"):
        sys.exit("index.html default_theme must be light or dark")
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
        html = render(page(meta, raw, rel, default_theme), root)
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
