# Clinic booking measurement

## Current release — 31 October 2026

The owner approved service-level booking measurement and the five conversion
improvements on 31 October. This section supersedes the older payload exclusions
below only for the fixed service-category event names described here.

Public clinic pages now load `assets/clinic.20261031.js` and
`assets/analytics.20261031.js`. The measurement version is `20261031`.
The bridge still sends `booking_click` exactly once per eligible click. This
remains the single existing booking-intent key event. One additional event
identifies the actual destination's broad service category:

| Event | Meaning |
| --- | --- |
| `booking_naprapathy_click` | Naprapatbehandling, service ID 3263299 |
| `booking_ultrasound_click` | Muskuloskeletalt ultraljud, service ID 1946824 |
| `booking_hyaluron_click` | Sinovial or Sinogel service; no product/body-area split |
| `booking_prp_click` | PRP/ACP, service ID 3409514 |
| `booking_consultation_click` | Injektionskonsultation, service ID 3409513 |
| `booking_wellness_click` | Friskvård, service ID 1952697 |
| `booking_general_click` | Profile/general booking link; service not yet chosen |

These are website-sent custom events, so their event-name reports do not need a
new Admin custom dimension. Do **not** mark the service events as additional key
events or add their counts to `booking_click`: that would double-count one click.
They do not confirm the final appointment, treatment or completed booking.

Classification uses verified destination service IDs, never the page's topic,
link text, arbitrary data attributes or the booking guide's symptom answers.
Unknown destinations remain `general`. The existing `placement` custom dimension
also accepts `price_list`, `article_visit`, `case_card` and `service_card`.

The expanded statistics are disclosed on `/cookie/` and in the consent banner.
Version 2 of the consent choice requires a new explicit opt-in from previous
visitors. Rejection and withdrawal keep all Google measurement disabled. No
patient/form data, body area, diagnosis, raw booking URL or product is sent.

Validation: `node tests/booking-services.cjs` runs the actual consent bridge with
stubbed Google calls. This proves dispatch/consent behaviour, not live ingestion.
Check event reports after real consented traffic arrives. Historical events are
not backfilled. Production QA must not create fake patient clicks in GA4.

Verified Bokadirekt calendar URLs on 31 October: Naprapatbehandling 3263299,
PRP/ACP 3409514, Friskvårdsbehandling 1952697 and Injektionskonsultation 3409513;
the existing ultrasound/Sinovial/Sinogel direct destinations are reused.

Source: https://developers.google.com/analytics/devguides/collection/ga4/events

## Earlier measurement history

The clinic runtime prepares `kansei:booking-intent` DOM events for clicks to the
clinic's Bokadirekt profile and existing service URLs. A click is booking intent,
not a completed booking. This code does not collect or transmit analytics, set
cookies, read referrers or persist selections. `window.KanseiMeasure` defaults to
unset; events require its explicit value `true`.

An analytics integration must enable this switch only after any applicable
consent, reset it when consent is withdrawn, and attach its own event listener.
Do not add patient data, symptoms, query strings, full destination URLs or health
selections. No analytics provider is configured by this change.

Event detail is limited to `event: booking_click`, service (`ultrasound`,
`hyaluron`, `prp`, `general`), audience (`clinician`, `visitor`), placement
(`header`, `footer`, `guide`, `menu`, `content`), and version `business-v2`.
Audience reflects the clinician-labelled booking link, not a verified identity.
Service reflects the information page or link; it does not confirm which
service a visitor finally books on Bokadirekt.

AI acquisition needs multiple sources of evidence: referrals reported by patients
or referring clinicians, and attributed sessions where an analytics provider
actually supplies those data. Missing referrers mean referral reports alone
cannot measure all AI visits. Do not treat Search Console web traffic as all AI
traffic or present a local DOM event as a recorded conversion.

The clinician page copy action copies clinic facts only. It never asks for patient
inputs or transmits a referral. Contact and secure transfer of patient documents
must be agreed with the clinic separately.


## Visibility measurement update — 16 October 2026

See `visibility-measurement-2026-10-16.md` for the newer bridge, version 20261016, strict referral groups and explicit exclusion of review/profile links from booking_click. The same GA4 property and consent choice are reused; do not add another tag. Browser tests use stubbed third parties and do not by themselves verify actual GA4 collection.

## Booking funnel reporting — 25 October 2026

The current public-page bridge is `assets/analytics.20261017.js`. Its
`measurement_version` remains `20261016`; the filename is not a new measurement
definition. `assets/clinic.20261008.js` classifies the link placement and emits
the in-memory intent. The Google payload includes only the allowlisted public
page fields plus `placement`, `referral_group` and `measurement_version`.
The internal `service` and `audience` fields are not sent to Google.

Register these existing parameters in GA4 Admin as **event-scoped custom
dimensions** before reporting their breakdowns:

| Display name | Event parameter | Allowed values |
| --- | --- | --- |
| Booking link placement | `placement` | `header`, `footer`, `guide`, `menu`, `content` |
| Referral group | `referral_group` | `chatgpt`, `perplexity`, `copilot`, `gemini`, `google`, `bing`, `other`, `unknown` |
| Measurement version | `measurement_version` | Version emitted by the bridge |

The website does not register account definitions. The GA4 Admin read on
25 October returned no registered custom definitions. Account-side setup is
not complete until the correct property's authenticated Admin screen or API
confirms it. A sign-in wall blocks the setup; it is not evidence that a
definition was created. Registration does not reconstruct historical reports.

Use complete, equal date windows with the same channel and device filters:

| Stage | Measure | Interpretation |
| --- | --- | --- |
| Google result | Search Console clicks and impressions | Search visibility and traffic; not website sessions or booking outcomes |
| Website visit | GA4 users and sessions | Consent-based sample; not all visitors |
| Booking intent | Users or sessions with `booking_click` | People or sessions that followed a booking link; report event count separately because repeated clicks can occur |
| Confirmed booking | Verified aggregate from Bokadirekt | A separate outcome; currently unavailable to the website bridge |

For a website click-through rate, divide **users with a booking click** by
**users in the same filtered population**. Do not divide raw click events by
users or mix Search Console clicks with GA4 sessions. A click's public page
path identifies where the link was clicked, not necessarily the original
landing page or the service finally booked.

No booking-completed, purchase or appointment-confirmed event is implemented.
Do not create such an event from a link click, page return or assumed outcome.
Until a supported Bokadirekt integration is verified, compare website intent
with a separate aggregate of confirmed bookings. Do not transfer patient
identities, health selections or booking records to GA4 for reconciliation.

The browser checks intercept all third-party requests. They verify consent,
one event per eligible click, existing placements and payload exclusions; they
do not verify Google ingestion, account configuration or booking completion.
