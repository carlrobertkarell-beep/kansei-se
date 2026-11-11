"""Behavior and real-motion evidence for the progressive clinic menu.

All navigation probes use the local checkout and never visit booking providers.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urlsplit


KEYS = ('ultraljud', 'injektioner', 'naprapati', 'kliniken')
DESTINATIONS = {
    'ultraljud': (
        '/ultraljud/axel/', '/ultraljud/kna/', '/ultraljud/hoft-ljumske/',
        '/ultraljud/fot-fotled/', '/ultraljud/#in-2',
    ),
    'injektioner': ('/hyaluronsyra/', '/prp/', '/injektioner/'),
    'naprapati': ('/naprapati/', '/priser/'),
}


def _active(page, key, focus=False):
    page.wait_for_function('''({key, focus}) => {
        const d = document.querySelector('#site-menu');
        const v = d?.querySelector('[data-menu-view="' + key + '"]');
        return d?.open && d.dataset.menuActive === key &&
            d.dataset.menuTransition !== 'true' && v && !v.hidden && !v.inert &&
            (!focus || document.activeElement === v.querySelector('.menu-view-title'));
    }''', arg={'key': key, 'focus': focus}, timeout=5000)
    state = page.locator('#site-menu .menu-view').evaluate_all('''views => views.map(v => ({
        key: v.dataset.menuView, hidden: v.hidden, inert: v.inert
    }))''')
    if len(state) != 5 or any((v['hidden'] or v['inert']) if v['key'] == key
                             else not (v['hidden'] and v['inert']) for v in state):
        raise AssertionError('Inactive menu panes are not both hidden and inert')
    return page.locator(f'#site-menu .menu-view[data-menu-view="{key}"]')


def _geometry(page):
    result = page.locator('#site-menu').evaluate('''d => {
        const within = el => {
            if (!el) return false;
            const r = el.getBoundingClientRect();
            return r.top >= -1 && r.bottom <= innerHeight + 1 &&
                r.left >= -1 && r.right <= innerWidth + 1;
        };
        const touch = el => { const r = el.getBoundingClientRect(); return r.width >= 44 && r.height >= 44; };
        const close = d.querySelector('[data-site-close]');
        const footer = d.querySelector(':scope > .menu-bottom');
        const book = footer?.querySelector('.button');
        return {overflow:d.scrollWidth > d.clientWidth + 3,
            close:within(close) && touch(close), footer:within(footer),
            book:within(book) && touch(book)};
    }''')
    if result['overflow'] or not all(result[k] for k in ('close', 'footer', 'book')):
        raise AssertionError('Progressive menu has overflow or inaccessible fixed controls: ' + str(result))


def _closed(page):
    page.wait_for_function('''() => {
        const d = document.querySelector('#site-menu');
        const b = document.querySelector('button[data-site-menu]');
        return !d?.open && b?.getAttribute('aria-expanded') === 'false' &&
            document.activeElement === b && !document.body.classList.contains('locked');
    }''', timeout=5000)


def _root(page, keys, destinations, fresh=False):
    root = _active(page, 'root')
    buttons = root.locator('button[data-menu-target]')
    if buttons.evaluate_all('els => els.map(el => el.dataset.menuTarget)') != list(keys):
        raise AssertionError('First menu pane does not present exactly the four main choices')
    if not buttons.evaluate_all('''els => els.every(el => {
        const r = el.getBoundingClientRect();
        return r.width >= 44 && r.height >= 44 && el.getClientRects().length;
    })'''):
        raise AssertionError('A primary menu choice has a small or hidden touch target')
    # On portrait phones the first four choices must be visible together.
    if page.viewport_size['height'] >= 500 and not buttons.evaluate_all('''els => els.every(el => {
        const r = el.getBoundingClientRect();
        const footer = document.querySelector('#site-menu > .menu-bottom').getBoundingClientRect();
        const head = document.querySelector('#site-menu .site-menu-head').getBoundingClientRect();
        return r.top >= head.bottom - 1 && r.bottom <= footer.top + 1;
    })'''):
        raise AssertionError('The first menu pane requires portrait scrolling to reach its main choices')
    for href in set(sum(destinations.values(), ())):
        if page.locator(f'#site-menu a[href="{href}"]:visible').count():
            raise AssertionError('Area/detail links clutter the first menu pane')
    if fresh:
        if page.locator('#site-menu .menu-more').evaluate('el => el.open'):
            raise AssertionError('Reopened menu retains its expanded information group')
        if page.locator('#site-menu .site-menu-body').evaluate('el => el.scrollTop') > 1:
            raise AssertionError('Reopened menu retains an old scroll position')
        if root.evaluate('el => el.scrollTop') > 1:
            raise AssertionError('Reopened root pane retains an old scroll position')
    _geometry(page)
    return root


def _tab_loop(page):
    targets = page.locator('#site-menu a[href], #site-menu button:not([disabled]), #site-menu summary, #site-menu [tabindex="0"]')
    indexes = targets.evaluate_all('''els => els.flatMap((el, i) =>
        el.getClientRects().length && el.tabIndex >= 0 && !el.closest('[inert],[hidden]') ? [i] : [])''')
    if not indexes:
        raise AssertionError('Progressive menu has no focusable controls')
    first, last = targets.nth(indexes[0]), targets.nth(indexes[-1])
    first.focus()
    page.keyboard.press('Shift+Tab')
    if not last.evaluate('el => document.activeElement === el'):
        raise AssertionError('Reverse Tab escaped the active menu pane')
    page.keyboard.press('Tab')
    if not first.evaluate('el => document.activeElement === el'):
        raise AssertionError('Tab did not wrap to the first menu control')
    for _ in range(len(indexes) + 1):
        page.keyboard.press('Tab')
        if not page.locator('#site-menu').evaluate('''d =>
            d.contains(document.activeElement) && !document.activeElement.closest('[hidden],[inert]')'''):
            raise AssertionError('Keyboard focus entered an inactive pane or left the menu')


def check_minimal_menu(page, screenshot, keyboard=False, close_button=False, reduced_motion=False):
    keys, destinations = KEYS, DESTINATIONS
    if urlsplit(page.url).port == 4174:
        # Review screenshots also run against the previous production menu.
        if not page.locator('#menu-view-ultraljud a[href="/ultraljud/#in-2"]').count():
            destinations = {**destinations, 'ultraljud': (
                '/ultraljud/axel/', '/ultraljud/kna/', '/ultraljud/')}
        if page.locator('[data-menu-target="hyaluron"]').count():
            keys = ('ultraljud', 'hyaluron', 'naprapati', 'kliniken')
            destinations = {**destinations, 'hyaluron': (
                '/hyaluronsyra/kna/', '/hyaluronsyra/hoft/', '/hyaluronsyra/axel/', '/hyaluronsyra/')}
    opener = page.locator('button[data-site-menu]')
    opener.click(timeout=5000)
    _root(page, keys, destinations, fresh=True)
    if opener.get_attribute('aria-expanded') != 'true':
        raise AssertionError('Progressive menu lacks expanded state')
    if reduced_motion and not page.locator('#site-menu').evaluate('''d =>
        matchMedia('(prefers-reduced-motion: reduce)').matches &&
        getComputedStyle(d).animationName === 'none' &&
        getComputedStyle(d, '::backdrop').animationName === 'none'
    '''):
        raise AssertionError('Progressive menu ignores reduced-motion preference')
    page.screenshot(path=str(screenshot), animations='disabled')
    if keyboard:
        _tab_loop(page)
        for key in keys:
            trigger = page.locator(f'#site-menu button[data-menu-target="{key}"]')
            trigger.click()
            pane = _active(page, key, focus=True)
            _geometry(page)
            if key in destinations:
                links = pane.locator('a[href]')
                if links.evaluate_all('els => els.map(el => el.getAttribute("href"))') != list(destinations[key]):
                    raise AssertionError('Incorrect progressive service destinations: ' + key)
                if not links.evaluate_all('''els => els.every(el => {
                    const r = el.getBoundingClientRect();
                    return r.width >= 44 && r.height >= 44 && !el.closest('[hidden],[inert]');
                })'''):
                    raise AssertionError('A service destination is inaccessible or too small')
            else:
                for href in ('/priser/', '/om-oss/', '/kontakt/', '/patientinformation/'):
                    if pane.locator(f'a[href="{href}"]').count() != 1:
                        raise AssertionError('Missing or duplicated practical menu destination: ' + href)
            if key in ('ultraljud', 'kliniken'):
                page.screenshot(path=str(screenshot.with_name(screenshot.stem + '-' + key + '.png')), animations='disabled')
            if key == 'kliniken':
                summary = pane.locator('.menu-more > summary')
                summary.focus()
                page.keyboard.press('Enter')
                if not summary.evaluate('el => el.parentElement.open'):
                    raise AssertionError('More information does not open from keyboard')
                if pane.locator('a[href="/ultraljud/bilder/"]').count() != 1:
                    raise AssertionError('Patient case library is missing or duplicated')
                last = pane.locator('.menu-more a[href]').last
                last.scroll_into_view_if_needed()
                _geometry(page)
                page.screenshot(path=str(screenshot.with_name(screenshot.stem + '-more.png')), animations='disabled')
            _tab_loop(page)
            back = page.locator('#site-menu button[data-menu-back]:visible')
            if back.count() != 1:
                raise AssertionError('Detail pane lacks one clear back control')
            back.click()
            _active(page, 'root')
            page.wait_for_function('''key => document.activeElement ===
                document.querySelector('#site-menu button[data-menu-target="' + key + '"]')''', arg=key, timeout=5000)
            _root(page, keys, destinations)
            if not trigger.evaluate('''el => {
                const r = el.getBoundingClientRect();
                const view = el.closest('.menu-view').getBoundingClientRect();
                return r.top >= view.top - 1 && r.bottom <= view.bottom + 1;
            }'''):
                raise AssertionError('Back restores focus to a choice outside the visible root pane')
        # Escape closes the entire dialog from a detail pane, not only that pane.
        page.locator('#site-menu button[data-menu-target="kliniken"]').click()
        _active(page, 'kliniken', focus=True)
    page.keyboard.press('Escape')
    _closed(page)
    if keyboard or close_button:
        opener.click()
        _root(page, keys, destinations, fresh=True)
        if close_button:
            page.locator('#site-menu [data-site-close]').click()
        else:
            page.keyboard.press('Escape')
        _closed(page)
    return {'type': 'dialog', 'model': 'progressive', 'keyboard': keyboard, 'close_button': close_button}


def check_minimal_menu_motion(page, output):
    """Probe real normal-motion behavior and preserve an actual interaction video."""
    parsed = urlsplit(page.url)
    if parsed.hostname not in ('127.0.0.1', 'localhost'):
        return {'skipped': 'Normal-motion video is limited to the local checkout'}
    base = parsed.scheme + '://' + parsed.netloc
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    browser = page.context.browser
    context = browser.new_context(
        viewport={'width': 390, 'height': 844}, locale='sv-SE', reduced_motion='no-preference',
        record_video_dir=str(output / 'menu-motion-recording'),
        record_video_size={'width': 390, 'height': 844})
    context.route('**/*', lambda r: r.continue_() if urlsplit(r.request.url).netloc == parsed.netloc else r.abort())
    probe = context.new_page()
    video = probe.video
    samples = []
    errors = []
    probe.on('pageerror', lambda error: errors.append(str(error)[:180]))
    report = {'samples': samples, 'errors': errors}
    probe.expose_function('__recordMinimalFrame', lambda frame: samples.append(frame))

    def arm(selector, label):
        probe.locator(selector).evaluate('''(el, label) => {
            el.addEventListener('click', () => setTimeout(() => {
                const d = document.querySelector('#site-menu');
                window.__recordMinimalFrame({label, open:!!d?.open,
                    opacity:d ? parseFloat(getComputedStyle(d).opacity) : null,
                    path:location.pathname, reduced:matchMedia('(prefers-reduced-motion: reduce)').matches});
            }, 80), {once:true});
        }''', label)

    def sample(label):
        matches = [x for x in samples if x['label'] == label]
        if not matches:
            raise AssertionError('No real animation frame recorded before navigation: ' + label)
        frame = matches[-1]
        if not frame['open'] or frame['reduced'] or not (0 < frame['opacity'] < 1):
            raise AssertionError('Menu skips or instantly finishes its normal-motion animation: ' + str(frame))
        return frame

    def settled_dialog():
        # Filled CSS animations remain in getAnimations() after finishing.
        # Await this snapshot's finished promises rather than an empty list.
        probe.locator('#site-menu').evaluate('''async d => {
            await Promise.all(d.getAnimations().map(a => a.finished.catch(() => {})));
        }''')

    def arm_pane(selector, label, outgoing, incoming):
        probe.locator(selector).evaluate('''(el, args) => {
            el.addEventListener('click', () => {
                const started = performance.now();
                for (const sampleAt of [160, 280]) setTimeout(() => {
                    const d = document.querySelector('#site-menu');
                    const view = key => {
                        const v = d.querySelector('[data-menu-view="' + key + '"]');
                        return {key, hidden:v.hidden, inert:v.inert,
                            opacity:parseFloat(getComputedStyle(v).opacity),
                            hasFocus:v.contains(document.activeElement),
                            animations:v.getAnimations().map(a => {
                                const t = a.effect.getComputedTiming();
                                return {state:a.playState, currentTime:a.currentTime,
                                    duration:t.duration, delay:t.delay, endTime:t.endTime,
                                    progress:t.progress};
                            })};
                    };
                    window.__recordMinimalFrame({label:args.label, sampleAt,
                        elapsed:Math.round(performance.now() - started),
                        open:d.open, active:d.dataset.menuActive,
                        transitioning:d.dataset.menuTransition === 'true',
                        outgoing:view(args.outgoing), incoming:view(args.incoming)});
                }, sampleAt);
            }, {once:true});
        }''', {'label': label, 'outgoing': outgoing, 'incoming': incoming})

    def pane_samples(label):
        frames = [frame for frame in samples if frame['label'] == label]
        if sorted(frame['sampleAt'] for frame in frames) != [160, 280]:
            raise AssertionError('Missing real pane animation frames: ' + label)
        for frame in frames:
            incoming = frame['incoming']
            panes_inert = all(not frame[k]['hidden'] and frame[k]['inert']
                              for k in ('outgoing', 'incoming'))
            moving = any(a['state'] == 'running' and a['progress'] is not None and
                         0 < a['progress'] < 1 for a in incoming['animations'])
            if not (frame['open'] and frame['transitioning'] and panes_inert and moving and
                    frame['active'] == incoming['key'] and not incoming['hasFocus'] and
                    0 < incoming['opacity'] < 1):
                raise AssertionError('Pane change finishes abruptly or enables focus too early: ' + str(frame))

    def visit_and_back(key):
        selector = f'#site-menu button[data-menu-target="{key}"]'
        arm_pane(selector, key + '-forward', 'root', key)
        probe.locator(selector).click()
        _active(probe, key, focus=True)
        pane_samples(key + '-forward')
        probe.wait_for_timeout(1000)
        back = '#site-menu button[data-menu-back]:visible'
        arm_pane(back, key + '-back', key, 'root')
        probe.locator(back).click()
        _active(probe, 'root')
        probe.wait_for_function('''key => document.activeElement ===
            document.querySelector('#site-menu button[data-menu-target="' + key + '"]')''', arg=key)
        pane_samples(key + '-back')
        probe.wait_for_timeout(1000)

    try:
        probe.goto(base + '/', wait_until='load', timeout=45000)
        probe.wait_for_function("() => document.querySelector('#site-menu')?.classList.contains('menu-minimal')")
        denied = probe.locator('[data-statistics="no"]:visible')
        if denied.count():
            denied.click()
        welcome = probe.locator('.home-first-impression')
        if welcome.count():
            probe.wait_for_timeout(750)
            if not welcome.locator('.home-intro-image img').evaluate('''image =>
                getComputedStyle(image).opacity === '1' &&
                getComputedStyle(image).transform === 'none' &&
                getComputedStyle(image.parentElement).opacity === '1'
            '''):
                raise AssertionError('The first photograph is hidden or moves while reading')
            probe.screenshot(path=str(output / 'home-first-impression-normal.png'), animations='allow')
        arm('button[data-site-menu]', 'opening')
        probe.locator('button[data-site-menu]').click()
        probe.wait_for_timeout(80)
        probe.screenshot(path=str(output / 'menu-normal-opening.png'), animations='allow')
        settled_dialog()
        sample('opening')
        _active(probe, 'root')
        probe.wait_for_timeout(1000)
        visit_and_back('ultraljud')
        visit_and_back('injektioner')
        arm('#site-menu [data-site-close]', 'closing')
        probe.locator('#site-menu [data-site-close]').click()
        probe.wait_for_timeout(80)
        probe.screenshot(path=str(output / 'menu-normal-closing.png'), animations='allow')
        _closed(probe)
        sample('closing')
        probe.wait_for_timeout(200)
        # A genuine internal link must keep the dialog open while exiting. This
        # catches the older generic body listener that called native close().
        probe.locator('button[data-site-menu]').click()
        settled_dialog()
        _active(probe, 'root')
        probe.wait_for_timeout(1000)
        probe.locator('#site-menu button[data-menu-target="ultraljud"]').click()
        _active(probe, 'ultraljud', focus=True)
        probe.wait_for_timeout(1000)
        selector = '#site-menu .menu-view[data-menu-view="ultraljud"] a[href="/ultraljud/axel/"]'
        arm(selector, 'internal-link-exit')
        probe.locator(selector).click()
        probe.wait_for_url(base + '/ultraljud/axel/', timeout=15000)
        frame = sample('internal-link-exit')
        if frame['path'] != '/':
            raise AssertionError('Internal navigation starts before the exit animation completes')
        probe.wait_for_timeout(200)
        if errors:
            raise AssertionError('JavaScript error during normal-motion menu probe: ' + '; '.join(errors))
        report['passed'] = True
    finally:
        context.close()
        if video:
            saved = output / 'menu-interaction-mobile.webm'
            shutil.move(video.path(), saved)
            report['video'] = saved.name
            ffmpeg = shutil.which('ffmpeg')
            if ffmpeg:
                converted = output / 'menu-interaction-mobile.mp4'
                try:
                    result = subprocess.run([ffmpeg, '-y', '-loglevel', 'error', '-i', str(saved),
                        '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                        str(converted)], capture_output=True, timeout=30)
                    if result.returncode == 0:
                        report['mp4'] = converted.name
                except (OSError, subprocess.TimeoutExpired):
                    report['mp4_note'] = 'Optional conversion unavailable; original WebM preserved'
        (output / 'menu-motion.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return report
