# Clinic booking measurement

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
