"""Check the shared clinic typography and touch targets on representative pages."""

SERVICE_PATHS = frozenset((
    '/', '/ultraljud/', '/hyaluronsyra/', '/injektioner/', '/prp/', '/naprapati/',
))

DESIGN_PATHS = SERVICE_PATHS | {
    '/om-oss/', '/kontakt/', '/priser/', '/en/', '/fragor-och-svar/', '/hjalp-mig-boka/',
    '/kunskapsbank/', '/ultraljud/bilder/', '/ultraljud/bursit-axel/',
    '/hyaluronsyra/film/',
    '/blogg/prp-eller-hyaluronsyra-vid-knaartros/',
}


def check_site_design(page, path):
    styles = page.evaluate("""checkBooking => {
        const primary = checkBooking && document.querySelector(
            'main a:is(.button-dark,.btn-teal)[href*="bokadirekt.se/"]'
        );
        const headings = document.querySelectorAll(
            'main h1, main h2:not(:where(nav *, dialog *, [role="dialog"] *, .knowledge-result *)), ' +
            '.footer-cta h2, body.clinic-heading-style :is(h1, h2)'
        );
        const bookingRect = primary && primary.getBoundingClientRect();
        return {
            headings: Array.from(headings, heading => {
                const {fontFamily, fontStyle, fontWeight} = getComputedStyle(heading);
                return {
                    text: heading.textContent.trim(),
                    font: fontFamily.split(',')[0].trim().replace(/^["']|["']$/g, '').toLowerCase(),
                    style: fontStyle,
                    weight: fontWeight,
                };
            }),
            bodyFont: getComputedStyle(document.body).fontFamily,
            booking: bookingRect && {width: bookingRect.width, height: bookingRect.height},
        };
    }""", path in SERVICE_PATHS)

    mismatches = [
        heading for heading in styles['headings']
        if (heading['font'], heading['style'], heading['weight']) != ('georgia', 'normal', '400')
    ]
    if not styles['headings'] or mismatches:
        raise AssertionError(f"Clinic headings do not use the shared upright serif: {mismatches}")
    if 'sans-serif' not in styles['bodyFont'].lower():
        raise AssertionError(f"Clinic body lost its sans serif: {styles['bodyFont']!r}")
    if path in SERVICE_PATHS:
        booking = styles['booking']
        if not booking or min(booking.values()) < 44:
            raise AssertionError(f"Primary booking action is smaller than 44 × 44 px: {booking}")
    disclosure_selectors = {
        '/hyaluronsyra/': '.ha-faq summary, #fordjupning summary',
        '/ultraljud/': '.ultrasound-booking-report > summary',
    }
    if path in disclosure_selectors:
        markers = page.locator(disclosure_selectors[path]).evaluate_all("""summaries => summaries.map(summary => {
            const marker = getComputedStyle(summary, '::after');
            const rect = summary.getBoundingClientRect();
            const text = document.createRange();
            text.selectNodeContents(summary);
            const textEnd = Math.max(...Array.from(text.getClientRects(), line => line.right));
            return {
                display: getComputedStyle(summary).display,
                marker: marker.content,
                markerWidth: parseFloat(marker.width),
                freeSpace: rect.right - textEnd,
            };
        })""")
        if not markers or any(
            item['display'] != 'flex' or item['marker'] != '"+"'
            or not 0 < item['markerWidth'] <= item['freeSpace']
            for item in markers
        ):
            raise AssertionError(f"Disclosure label overlaps the right-hand marker: {markers}")
    return styles
