# Kansei v126 — 404, legacy URLs and regression checks

Date: 2026-09-09

## Published changes
- Replaced the automatic homepage redirect in `404.html` with a responsive, accessible error page, useful navigation and direct booking. No automatic redirect or homepage canonical; includes `noindex`.
- Shortened `/mot-vart-team/` and `/team-kansei/` to point directly to `/om-oss/`, removing the intermediate `/team/` hop.
- Kept the existing `/kontakt/contact-v1/` and `/kliniken/odenplan/` destinations at `/kontakt/`, with descriptive fallback links, viewport metadata and explicit noindex.
- Removed `/reda/` from the public sitemap because that patient-program page already carries `noindex`. Its access flow and noindex directive remain unchanged.
- Added read-only GitHub Actions checks for JSON-LD syntax, sitemap/canonical consistency, internal HTML link targets and the changed redirects.
- After a successful GitHub Pages deployment, the checks also verify the public HTTP 404 and the four legacy HTML redirects, with bounded retries for CDN propagation.

## Scope and limitations
- These are immediate HTML refresh redirects, not custom HTTP 301 rules. Existing Pages hosting and domain settings are unchanged.
- No changes to business name, service names, prices, opening hours, clinical claims, analytics or booking destinations.
- The current visible opening hours and homepage schema agree (weekdays 08–19, weekends 10–15), but the clinic owner still needs to confirm that these are the actual reception hours and match Google Business Profile.
- Passing JSON parsing is not full Schema.org or Google rich-result validation. These checks do not establish indexing, rankings, bookings, Core Web Vitals or medical accuracy.
- Missing-page status is verified using an actual nonexistent public URL, not by visiting `/404.html` directly.
