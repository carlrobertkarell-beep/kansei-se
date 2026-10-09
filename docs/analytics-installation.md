# GA4 installation

Prepared for verified Kansei GA4 property 417935074.
Owner-supplied screenshot identifies web stream 6422923083 and measurement ID G-F1EVW66L9S. The screenshot initially showed Enhanced Measurement enabled. The owner confirmed it switched OFF on 9 October 2026.

The installation includes the verified tag ID and consent bridge on 131 public clinic pages, plus a /cookie/ information page. Publication and actual collection are verified separately from local prototype checks.

Configuration and verification:
1. Owner has supplied the stream measurement ID. Confirm the stream belongs to the intended Kansei web property.
2. Keep Enhanced Measurement disabled for this stream. Automatic site-search, form
   and link events must not send user-entered health information or raw URLs.
3. Cookie information and an accessible accept/reject banner are prepared.
4. ID and assets are included only on indexable public clinic-site pages. Reda, patient apps, noindex previews and the 404 page are excluded.
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
