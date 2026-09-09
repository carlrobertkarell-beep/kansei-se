# Kansei improvement engine: public safety layer v1

Installed: 2026-09-09. This is the **public, read-only** part of the system.
The analysis engine and all Search Console data belong in a separate PRIVATE repository.
No OpenAI, GSC, Ads or patient-data secrets belong in this public repository.

## What this layer does
- Daily check requested at 04:17 UTC; GitHub schedules can be delayed or disabled after inactivity.
- On pull requests, tests source files before publication; captures candidate and baseline screenshots.
- Checks six public pages on mobile (390 px) and desktop (1440 px): H1, title, booking origin,
  visible images, horizontal overflow, runtime errors and mobile menu expanded state.
- Does not click booking links or submit forms. Third-party requests except web fonts are blocked.
- AI branches `kansei-ai/` are checked against controls from the trusted base revision.
- AI pilot scope: at most two pages, title/description/share metadata only; all other bytes locked.
- Public screenshot artifacts retained for 3 days. No report claiming bookings or Maps rankings.

## IMPORTANT: merge gate is not branch protection
Tests alone do not prevent a direct push to main. The owner must set a branch rule for main:
require pull request + one approval + required check `website-quality` + existing SEO `check`,
require up-to-date branch, disallow force pushes/deletions and review bypass permissions.
No agent token should bypass this rule or have administration/workflows permissions.
This installation does NOT silently change repository administration settings.

## Pilot and proposed future mandate
Initially the private engine creates reviewable metadata PRs; it cannot merge at all.
Automatic production changes are NOT implemented or approved in this pilot.
A later, separately approved tier may publish narrowly defined technical repairs after testing.
Medical statements, prices, services, branding, hours, tracking/consent, booking destinations,
patient applications, account permissions, live Ads offers and advertising budgets always require owner approval.

## Coordination with Ads
No campaign is started, edited or stopped here. Ads decisions and active landing-page locks
belong in the PRIVATE operating brief. Until that list is approved, even metadata PRs require review.
Opening hours are owner-confirmed; do not reopen or change that item.

## Limitations
No Core Web Vitals field measurement, full accessibility certification, medical review,
perceptual screenshot comparison or real booking-confirmation test is implied by a pass.
Failures are visible in GitHub Actions; notification delivery depends on the owner's GitHub settings.
No promise of an unsolicited ChatGPT notification or guaranteed ranking improvement.
