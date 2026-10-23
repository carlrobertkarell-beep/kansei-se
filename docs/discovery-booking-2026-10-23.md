# Connect established guides to original cases and the right visit

The owner authorized implementation of the indexing, examination-page and
naprapathy work on 23 October 2026, including measurement. The established
guides already link to examination topics. This release adds concise routes
to original cases, films and the information needed before booking.

## Changes

- The homepage links directly to the knee-calcification, shoulder-bursa and
  lateral-hip cases, and to the knee hyaluron service.
- The ultrasound hub and regional knee/shoulder pages expose selected cases
  as ordinary, visible HTML links. Relevant established guides connect to
  complementary cases without changing their clinical advice.
- Knee hyaluron has direct routes to the actual procedure film, product film
  and preparation/aftercare information. Existing prices and direct-booking
  destinations are preserved.
- Naprapathy gains symptom-guide routes, clear Odenplan/Vasastan location
  information and a practical location FAQ.
- Visible new visit-choice FAQs and existing FAQ structured data agree.
  Sitemap modification dates change only for edited pages.

No new URLs, redirects, medical claims about treatment efficacy, patient
histories, outcomes, opening hours or advertising changes are introduced.
Readers, finding coordinates, original images and video files are unchanged.
Private Search Console and GA4 exports remain outside the public repository.

## Measurement and access

The existing GSC Wizard tracker has been expanded to cover the current
ultrasound and hyaluron URLs, naprapathy and the new lateral-knee guide.
This tracks indexing; it does not request indexing or prove a ranking change.
The existing consent-based `booking_click` event is working. Booking intent
is not a completed booking, and no analytics/consent configuration was changed.

The public Google Maps listing displayed `Medicinsk klinik` and an HTTP
website address during this review. Owner-side primary and additional
categories must be checked before any category change. No public suggestion
or owner profile edit has been submitted from an unsigned-in session.
Individual Search Console indexing requests likewise require an authenticated
owner session; the URL Inspection API is read-only for this purpose.

## Validation

Static SEO, internal targets, FAQ parity and existing media preservation are
checked before publication. The existing CI exercises the new visible routes,
location block and expandable visit answers at desktop, mobile and compact
widths. Candidate screenshots are reviewed before merging. After deployment,
public files are compared to the approved source and the changed sitemap is
submitted once.

References: [Google's crawl guidance](https://developers.google.com/search/docs/crawling-indexing/troubleshoot-crawling-errors),
[requesting recrawls](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl),
[local ranking guidance](https://support.google.com/business/answer/7091).
