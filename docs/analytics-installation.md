# Pending GA4 installation

Prepared for verified Kansei GA4 property 417935074.
The numeric property ID is not a Google tag ID.

No clinic page includes the new files. Nothing in this draft enables tracking.

Before installation:
1. Obtain the G-… measurement ID from the web stream in property 417935074.
   Verify the stream URL is kansei.se, rather than a Framer preview.
2. Disable Enhanced Measurement for this stream. Automatic site-search, form
   and link events must not send user-entered health information or raw URLs.
3. Replace the old /cookie/ redirect with a clinic-style explanation of Google
   Analytics, optional consent, cookies, retention and withdrawal.
4. Add the verified ID in a kansei-ga4 meta tag and the local CSS/deferred JS
   to public clinic-site pages. Exclude Reda, patient apps and previews.
5. Verify consent, clean payloads, revocation, responsive layout and actual
   collection in GA4 Realtime/DebugView before publication.

The bridge blocks Google requests until explicit analytics consent.
Preference is saved for 180 days. Ads and Google signals are disabled.
Query strings and fragments are removed from page URLs; referrers are reduced
to origins. No patient input, service choice or audience field is sent.
A booking_click is intent, never a completed booking.

Sources:
- https://support.google.com/analytics/answer/9539598
- https://developers.google.com/analytics/devguides/collection/ga4/views
- https://support.google.com/analytics/answer/6366371
- https://support.google.com/analytics/answer/13297105
- https://www.pts.se/internet-och-telefoni/kakor-cookies/

Prototype assertions do not prove third-party collection. Actual Google stream
settings and requests must be verified with the correct ID before activation.
