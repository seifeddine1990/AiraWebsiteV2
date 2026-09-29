# Website review — 2026-09-29

Local review of the generated site, using Microsoft Edge in headless mode.

## Checks completed

- Build: all 13 HTML pages generated successfully.
- Static validation: 483 local references, section anchors, unique IDs, image alt attributes, form labels and CSS/JavaScript content versions passed.
- Search validation: 11 canonical sitemap URLs, metadata, exclusions and robots policies passed.
- Browser sweep: 12 content pages at 320, 390, 768, 1024 and 1440 pixels (60 page/viewport combinations). No detected horizontal overflow, missing images or captured JavaScript errors.
- Text contrast screening: no remaining failures for directly rendered text on solid backgrounds. This custom check skips gradient backgrounds and is not a full accessibility audit.
- Interactions: mobile menu open/close and Escape focus restoration; every catalogue filter; assurance disclosure; invalid and valid contact fields; legacy platform/hub redirect; diagram keyboard focus, last-to-first cycling and reduced-motion behavior; homepage content without JavaScript.
- Contact handler: recipient, subject, body fields, newlines and special-character encoding tested in an isolated JavaScript context. No email sent and no external mail application opened.
- Original brand image files remain unchanged.

## Fixes made

- Prevented the Nexus diagram from cycling past its final node; added keyboard focus behavior and kept reduced-motion previews paused after hovering.
- Added Escape handling and a controlled-navigation association to the mobile menu, plus visible mobile navigation when JavaScript is unavailable.
- Replaced tab semantics on catalogue filters with labelled toggle-button semantics that match their behavior.
- Darkened small accent and footer text to maintain contrast against the new blue-gray surfaces.
- Added content hashes to CSS/JavaScript URLs so revised assets invalidate cached versions.
- Removed a redundant nginx asset Cache-Control header that prevented inherited security headers from applying to that location. The existing expires directive still provides caching.

## Repeatable checks

```sh
python build.py
python tools/check_site.py
python tools/check_search.py
node tools/check_contact.cjs
node --check src/static/js/site.js
git diff --check
```

Browser audit scripts, JSON results and screenshots from this session are in `tmp/`.

## Limits

Docker's engine was unavailable, so container startup, nginx runtime configuration, deployed response headers, and production 404 routing were not verified. The local Python preview server does not implement nginx's headers or custom error routing. Firefox, Safari, physical devices, screen-reader behavior, external destinations, and real email-client delivery were not tested. No changes were deployed.
