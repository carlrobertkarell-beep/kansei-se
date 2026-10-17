"""Browser tests against checkout files. All third-party requests are stubbed."""
from pathlib import Path
from urllib.parse import urlsplit,unquote
from playwright.sync_api import sync_playwright
import json,mimetypes,re
ROOT=Path(__file__).resolve().parents[2]
OUT=Path('/tmp/kansei-visibility-artifacts');OUT.mkdir(exist_ok=True)
ORIGIN='https://www.kansei.se'
checks=[]

def setup(browser,viewport=None,seed=None):
    context=browser.new_context(viewport=viewport or {'width':1280,'height':900},locale='sv-SE',reduced_motion='reduce')
    seen=[]
    def route(r):
        u=urlsplit(r.request.url)
        if u.hostname in ['kansei.se','www.kansei.se']:
            p=(ROOT/unquote(u.path).lstrip('/')).resolve()
            if not p.is_relative_to(ROOT):r.abort();return
            if p.is_dir():p=p/'index.html'
            if p.is_file():r.fulfill(path=str(p),content_type=mimetypes.guess_type(p.name)[0] or 'application/octet-stream')
            else:r.fulfill(status=404,body='not found')
        else:
            if 'googletagmanager.com' in (u.hostname or '') or 'google-analytics.com' in (u.hostname or ''):seen.append(r.request.url)
            r.fulfill(status=200,body='',content_type='application/javascript' if r.request.resource_type=='script' else 'text/plain')
    context.route('**/*',route)
    context.add_init_script("document.addEventListener('click',e=>{const a=e.target.closest('a');if(a&&/bokadirekt/.test(a.href))e.preventDefault();},true);")
    if seed:context.add_init_script(seed)
    return context,context.new_page(),seen

def events(page,name=None):
    return page.evaluate("name=>(window.dataLayer||[]).map(x=>Array.from(x)).filter(x=>x[0]==='event'&&(!name||x[1]===name))",name)

def record(name):checks.append(name);print('PASS:',name)
with sync_playwright() as pw:
    browser=pw.chromium.launch()
    c,p,seen=setup(browser)
    p.goto(ORIGIN+'/?private=NEVER_SEND_THIS#SECRET_FRAGMENT',referer='https://chatgpt.com/c/SECRET_CONVERSATION?secret=NEVER_SEND_THIS')
    p.locator('[data-statistics="yes"]').wait_for()
    p.wait_for_timeout(150)
    assert seen==[] and events(p)==[]
    assert p.evaluate("sessionStorage.getItem('kansei-referral-v1')") is None
    p.locator('a[data-measure="booking_click"]').first.click()
    assert events(p)==[]
    record('No Google requests, source storage or booking events before consent')
    p.locator('[data-statistics="yes"]').click()
    p.wait_for_timeout(100)
    assert len(seen)==1 and len(events(p,'page_view'))==1
    assert events(p,'page_view')[0][2]['referral_group']=='chatgpt'
    assert events(p,'page_view')[0][2]['page_location']==ORIGIN+'/'
    assert events(p,'page_view')[0][2]['page_referrer']=='https://chatgpt.com/'
    assert 'SECRET' not in json.dumps(events(p)) and 'NEVER_SEND_THIS' not in json.dumps(events(p))
    record('One page view after consent; domain-only referrer and no URL query, fragment or conversation ID')
    p.locator('a[data-measure="booking_click"]').first.click()
    assert len(events(p,'booking_click'))==1
    ignored=p.locator('a[data-measure="ignore"]')
    assert ignored.count()>0
    ignored.first.evaluate('(a)=>a.click()')
    assert len(events(p,'booking_click'))==1
    record('Booking link counts once; non-booking and review link does not count')
    p.goto(ORIGIN+'/naprapati/',referer=ORIGIN+'/')
    p.wait_for_function("(window.dataLayer||[]).some(x=>x[0]==='event')")
    assert events(p,'page_view')[0][2]['referral_group']=='chatgpt'
    record('Consent-based source group survives internal navigation')
    p.locator('.kansei-statistics-settings').click()
    p.locator('[data-statistics="no"]').click()
    before=len(events(p));calls=len(seen)
    p.locator('a[data-measure="booking_click"]').first.click()
    assert len(events(p))==before and len(seen)==calls
    assert p.evaluate("sessionStorage.getItem('kansei-referral-v1')") is None
    assert p.evaluate("window['ga-disable-G-F1EVW66L9S']") is True
    record('Consent withdrawal stops measurement and removes source storage')
    c.close()
    seed="localStorage.setItem('kansei-statistics-v1',JSON.stringify({allowed:true,at:Date.now()}));"
    for ref,expected in [('https://www.perplexity.ai/search/PRIVATE','perplexity'),('https://copilot.microsoft.com/','copilot'),('https://gemini.google.com/app/PRIVATE','gemini'),('https://www.google.se/search?q=PRIVATE','google'),('https://www.bing.com/search?q=PRIVATE','bing'),('https://chatgpt.com.attacker.invalid/','other')]:
        c,p,_=setup(browser,seed=seed)
        p.goto(ORIGIN+'/naprapati/',referer=ref)
        p.wait_for_function("(window.dataLayer||[]).some(x=>x[0]==='event')")
        assert events(p,'page_view')[0][2]['referral_group']==expected
        assert 'PRIVATE' not in json.dumps(events(p))
        c.close()
    record('Six source-domain classification cases; no fake AI attribution from a lookalike hostname')
    expired=seed+"sessionStorage.setItem('kansei-referral-v1',JSON.stringify({group:'chatgpt',at:Date.now()-31*60000}));"
    c,p,_=setup(browser,seed=expired)
    p.goto(ORIGIN+'/naprapati/',referer=ORIGIN+'/')
    p.wait_for_function("(window.dataLayer||[]).some(x=>x[0]==='event')")
    assert events(p,'page_view')[0][2]['referral_group']=='unknown'
    c.close();record('Expired source group is not reused')
    for width,label in [(320,'compact'),(390,'mobile'),(1280,'desktop')]:
        c,p,_=setup(browser,{'width':width,'height':900})
        for path,name in [('/','home'),('/naprapati/','naprapati'),('/ultraljud/','ultraljud'),('/cookie/','cookie')]:
            p.goto(ORIGIN+path)
            if p.locator('[data-statistics="no"]:visible').count():p.locator('[data-statistics="no"]').click()
            p.wait_for_timeout(120)
            assert p.locator('h1').count()==1
            assert p.locator('#site-menu .menu-secondary a[href="/ultraljud/bilder/"]').count()==1
            width_now=p.evaluate('document.documentElement.scrollWidth')
            assert width_now<=width+2,(path,label,width_now,width)
            p.screenshot(path=str(OUT/f'{name}-{label}.png'))
            footer=p.locator('.footer-utilities')
            assert footer.locator('a[href="https://www.instagram.com/kansei.se/"]').count()==1
            assert footer.locator('a[href="https://www.facebook.com/kanseirehabcenter/"]').count()==1
            settings=footer.locator('.kansei-statistics-settings')
            assert settings.count()==1
            footer.scroll_into_view_if_needed()
            footer.screenshot(path=str(OUT/f'footer-{name}-{label}.png'))
            if name=='home':
                settings.focus()
                p.keyboard.press('Enter')
                assert p.locator('.kansei-statistics').is_visible()
                assert p.locator('[data-statistics="no"]').evaluate('el=>el===document.activeElement')
                p.locator('[data-statistics="no"]').click()
                assert settings.evaluate('el=>el===document.activeElement')
            if name=='cookie':
                p.locator('#statistik-kallgrupp').screenshot(path=str(OUT/f'cookie-source-{label}.png'))
        p.goto(ORIGIN+'/naprapati/')
        p.locator('[data-site-menu]').first.click()
        assert p.locator('#site-menu').is_visible()
        p.screenshot(path=str(OUT/f'menu-{label}.png'))
        c.close()
    record('Desktop/mobile layout without horizontal overflow; static image-library menu link remains single after JavaScript')
    browser.close()
(OUT/'checks.json').write_text(json.dumps({'checks':checks,'all_passed':True,'scope':'Local checkout with third parties stubbed. Does not verify actual GA4 collection, live deployments or rankings.'},ensure_ascii=False,indent=2))
print('BROWSER TESTS COMPLETE:',len(checks))
