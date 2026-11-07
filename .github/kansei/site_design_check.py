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
    return styles
