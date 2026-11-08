"""Check the shared clinic typography and touch targets on representative pages."""

SERVICE_PATHS = frozenset((
    '/', '/ultraljud/', '/hyaluronsyra/', '/injektioner/', '/prp/', '/naprapati/',
))

DESIGN_PATHS = SERVICE_PATHS | {
    '/om-oss/', '/kontakt/', '/fragor-och-svar/', '/hjalp-mig-boka/',
    '/kunskapsbank/', '/ultraljud/bilder/', '/ultraljud/bursit-axel/',
    '/blogg/prp-eller-hyaluronsyra-vid-knaartros/',
}


def check_site_design(page, path):
    styles = page.evaluate("""checkBooking => {
        const title = document.querySelector('main h1');
        const primary = checkBooking && document.querySelector(
            'main a:is(.button-dark,.btn-teal)[href*="bokadirekt.se/"]'
        );
        const firstFont = el => getComputedStyle(el).fontFamily
            .split(',')[0].trim().replace(/^["']|["']$/g, '').toLowerCase();
        const bookingRect = primary && primary.getBoundingClientRect();
        return {
            titleFont: title && firstFont(title),
            bodyFont: getComputedStyle(document.body).fontFamily,
            booking: bookingRect && {width: bookingRect.width, height: bookingRect.height},
        };
    }""", path in SERVICE_PATHS)

    if styles['titleFont'] != 'georgia':
        raise AssertionError(f"Clinic H1 lost its shared serif: {styles['titleFont']!r}")
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
