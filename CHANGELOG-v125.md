# Kansei v125 — Local SEO & technical cleanup

Date: 2026-09-09

## Changes
- Strengthened local relevance for **Naprapat + Odenplan + Vasastan + Stockholm** on `/naprapati/`.
- Changed naprapati H1 to **Naprapat vid Odenplan i Vasastan** and rewrote the opening paragraph for local intent without keyword stuffing.
- Updated naprapati title, meta description, Open Graph title/description and breadcrumb label.
- Reworked homepage `MedicalClinic` JSON-LD with stable `@id`, telephone, richer NAP data, area served, service URLs and Person entity references.
- Removed misleading `PhysicalTherapy` specialty from the clinic schema; physiotherapy remains correctly represented through Magnus Wennerlund where relevant.
- Corrected `/kontakt/` structured data: it incorrectly identified itself as the Patientinformation page. It is now a `ContactPage` tied to the Kansei clinic entity.
- Linked Carl-Robert Kårell's Person schema to the clinic entity with a stable `@id`.
- Added **Vasastan** to homepage location copy and meta description.
- Clarified that the site's 301 review count refers to **Bokadirekt**.
- Removed obsolete `<meta name="keywords">`.
- Fixed duplicated `<noscript><noscript>` wrappers across templates.
- Updated sitemap `lastmod` only for materially changed canonical pages.

## Redirect note
The existing legacy alias pages remain `noindex` and client-redirect to their canonical destinations. If the production host supports server rules, replace these with HTTP 301 redirects. GitHub Pages alone does not provide arbitrary redirect rules, so no host-specific redirect file was added.
