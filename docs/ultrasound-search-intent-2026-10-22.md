# Ultrasound: symptoms, examinations and original cases

The ultrasound section has 40 active pages and seven retained redirect aliases.
This update keeps existing URLs and assigns each active page a clear purpose:

- The examination hub and ten regional pages explain a visit in Stockholm,
  its scope, current price, booking and relevant symptom guides.
- Sixteen focused examination pages answer a specific question about a tendon,
  nerve, swelling or other structure. Patient terms such as hopparknä and
  hälsporre appear with the anatomical names.
- The image library and twelve case or combined case/examination pages explain
  the clinic's original evidence. They support the examination pages without
  repeating the same broad search title on every case.

The full page mapping, titles and descriptions are in
`.github/kansei/content/ultrasound-search-intent.20261022.json`.
Regenerate the static pages using
`python3 .github/kansei/improve_ultrasound_search.py` (standard library only).

## Symptom route

The new guide `/kunskapsbank/kna/ont-pa-utsidan-av-knat/` distinguishes a symptom
question from an examination request. It describes running-related symptoms,
injury and swelling, clinical assessment, ultrasound limits and appropriate
care. It links to the original IT-band case and the regional knee examination.
The knee hub, knowledge index, running-knee article, case and ultrasound hub
link back to it with descriptive anchor text.

The guide provides a clinical-assessment booking and a separate diagnostic
ultrasound booking with their existing prices and scope. It does not assume
that every person with pain needs imaging or an injection. Urgent-care advice
uses 1177, and imaging limitations use ACR/RSNA. No patient history or outcome
was invented for this guide.

## Discovery and booking

Nine regional pages now provide early symptom links. Eight receive a closing
booking choice; the shoulder and knee pages already have booking sections.
Four previously brief regional pages receive specific FAQs. FAQ JSON-LD is
generated from visible questions and answers. The image library links directly
to the existing ultrasound service, with price, duration and clinic location.

The current canonical host, sitemap, consent bridge, service destinations,
prices, original media, reader geometry and finding coordinates are retained.
Sitemap dates change only for edited pages. Copyright organization references
are consolidated in structured data. Decorative layers retain empty alt text
because the original image and surrounding explanation already describe them.

No paid search, account permissions, analytics configuration or external
outreach changes are part of this release. Private Search Console and Analytics
exports remain outside this public repository. Booking-link clicks are not
confirmed bookings, and a published/indexable page is not proof of Google
indexing or a ranking gain.

## Verification

- Static SEO, sitemap, structured-data syntax, clinic visibility and internal
  targets; FAQ parity and local fragment targets on the edited pages.
- All existing ultrasound media and alternatives compared with the base revision.
- Mobile and desktop checks of symptom navigation, new guide, directory search,
  direct service destinations, overflow, runtime errors and unchanged readers.
- Existing repository regression checks before merge; live file verification
  and sitemap submission after deployment.

Google guidance: [Search Essentials](https://developers.google.com/search/docs/essentials),
[helpful content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content),
[descriptive internal links](https://developers.google.com/search/docs/crawling-indexing/links-crawlable).
