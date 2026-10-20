"""Playback and readable-caption checks for the shared film player."""
from __future__ import annotations

FILM_DURATIONS = {
    '/hyaluronsyra/': 67.1,
    '/hyaluronsyra/film/': 67.1,
    '/hyaluronsyra/ultraljudsvagledd-injektion/': 70,
    '/hyaluronsyra/sinovial-sinogel/': 79.166667,
    '/hyaluronsyra/sinovial-sinogel/film/': 79.166667,
}
FILM_PATHS = tuple(FILM_DURATIONS)


def check_film_captions(page, path, output, viewport):
    video = page.locator('video.film-player')
    if video.count() != 1:
        raise AssertionError('Expected one shared film player')
    video.evaluate('(v) => { v.muted = true; v.preload = "auto"; v.load(); }')
    page.wait_for_function("""() => {
        const v = document.querySelector('video.film-player');
        const t = v.querySelector('track[kind="captions"]');
        return v.readyState >= 2 && t.readyState === 2 &&
            t.track.mode === 'showing' && t.track.cues.length > 0;
    }""", timeout=20000)
    expected_duration = FILM_DURATIONS[path]
    duration = video.evaluate('(v) => v.duration')
    if abs(duration - expected_duration) > .1:
        raise AssertionError('Unexpected film duration')

    # Start playback normally; the CI static server does not support byte-range seeking.
    video.evaluate('(v) => v.play()')
    page.wait_for_function("""() => {
        const v = document.querySelector('video.film-player');
        return !v.paused && v.querySelector('track[kind="captions"]').track.activeCues.length > 0;
    }""")
    video.evaluate('(v) => v.pause()')
    video.scroll_into_view_if_needed()
    page.wait_for_timeout(100)

    mobile = viewport != 'desktop'
    state = page.evaluate("""() => {
        const v = document.querySelector('video.film-player');
        const t = v.querySelector('track[kind="captions"]').track;
        const b = v.nextElementSibling;
        const s = getComputedStyle(b), vr = v.getBoundingClientRect(), br = b.getBoundingClientRect();
        return {visible:!b.hidden, text:b.textContent,
            expected:[...t.activeCues].map(c=>c.text.replace(/<[^>]*>/g,'').replace(/\\s+/g,' ').trim()).join(' '),
            font:parseFloat(s.fontSize), outside:v.classList.contains('film-captions-outside'),
            below:br.top >= vr.bottom-1, width:br.width, videoWidth:vr.width,
            overflow:b.scrollWidth > b.clientWidth+1, mode:t.mode};
    }""")
    if mobile:
        if not state['visible'] or not state['outside'] or not state['below']:
            raise AssertionError('Mobile captions do not sit below the video')
        if state['font'] < 17 or state['overflow'] or abs(state['width']-state['videoWidth']) > 1:
            raise AssertionError('Mobile captions are too small or overflow')
        if not state['text'] or state['text'] != state['expected']:
            raise AssertionError('Displayed captions do not match the current speech cue')
    elif state['visible'] or state['outside'] or state['mode'] != 'showing':
        raise AssertionError('Desktop native captions are not available')

    slug = path.strip('/').replace('/', '-')
    video.locator('..').screenshot(path=str(output/f'{slug}-{viewport}-captions.png'),
        animations='disabled', style='body>header,body>a[href="#main"]{visibility:hidden!important}')

    # The native CC menu remains authoritative, including while playback is paused.
    video.evaluate('(v) => { v.querySelector(\'track[kind="captions"]\').track.mode = "disabled"; }')
    page.wait_for_function("() => document.querySelector('.film-live-captions').hidden")
    video.evaluate('(v) => { v.querySelector(\'track[kind="captions"]\').track.mode = "showing"; }')
    if mobile:
        page.wait_for_function("() => !document.querySelector('.film-live-captions').hidden")

    # Fullscreen must restore the native caption layer instead of leaving it transparent.
    if mobile and path != '/hyaluronsyra/':
        video.evaluate('(v) => v.requestFullscreen()')
        page.wait_for_function("() => document.fullscreenElement === document.querySelector('video.film-player')")
        page.wait_for_function("() => document.querySelector('.film-live-captions').hidden && !document.querySelector('video.film-player').classList.contains('film-captions-outside')")
        if video.evaluate('(v) => v.querySelector(\'track[kind="captions"]\').track.mode') != 'showing':
            raise AssertionError('Fullscreen lost native captions')
        page.evaluate('document.exitFullscreen()')
        page.wait_for_function("() => !document.fullscreenElement && !document.querySelector('.film-live-captions').hidden")

    return {'duration': duration, 'caption_font_px': state['font'] if mobile else 'native',
        'playback': 'passed', 'sync_and_cc': 'passed', 'fullscreen': 'passed' if mobile and path != '/hyaluronsyra/' else 'native'}
