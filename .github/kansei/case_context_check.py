"""Exercise the patient entrance, clinical key and real reader links in all cases."""
from case_story_check import STORY_PATHS

CONTEXT_PATHS = STORY_PATHS + ('/ultraljud/kna/',)


def check_context(page, path, output, label):
    summary=page.locator('[data-case-context=summary]')
    decision=page.locator('[data-case-context=decision]')
    if summary.count()!=1 or decision.count()!=1:
        raise AssertionError('Case context missing or duplicated')
    if not summary.evaluate('(e)=>e.getBoundingClientRect().width>=document.documentElement.clientWidth-3'):
        raise AssertionError('Case entrance inherits a narrow legacy text-column width')
    if summary.locator('.case-context-goals li').count()!=3:
        raise AssertionError('Every case needs its own everyday activities')
    if decision.locator('.case-context-related article').count()!=2:
        raise AssertionError('Case has no two contextual comparison routes')
    if decision.locator('.case-context-faq details').count()!=2:
        raise AssertionError('Case-specific questions missing')
    if decision.locator('a[href="/naprapati/"]').count()!=1:
        raise AssertionError('Case does not explain its rehabilitation route')
    if path=='/ultraljud/kna/' and decision.locator('a[href="/hyaluronsyra/kna/"]').count()!=1:
        raise AssertionError('Knee OA context does not reach the hyaluron explanation')
    for link in summary.locator('a[href^="#"]').all():
        if page.locator(link.get_attribute('href')).count()!=1:
            raise AssertionError('Patient entrance has a missing or duplicate target')
    media=decision.locator('[data-case-view]')
    media.click()
    tab=media.get_attribute('data-case-tab')
    if tab and page.locator('#'+tab).get_attribute('aria-selected')!='true':
        raise AssertionError('Clinical key opens the wrong image or film')
    for details in decision.locator('details').all():
        details.locator('summary').click()
        if details.get_attribute('open') is None:raise AssertionError('Case question does not open')
        details.locator('summary').click()
    if label!='compact':
        slug=path.strip('/').replace('/','-')
        for name,element in [('entrance',summary),('decision',decision)]:
            element.scroll_into_view_if_needed()
            element.screenshot(path=str(output/f'context-{slug}-{label}-{name}.png'),animations='disabled',style='body>header,body>a[href="#main"]{visibility:hidden!important}')
    return {'patient_entrance':'Passed','clinical_key_and_reader':'Passed','case_questions':'Passed','related_cases':2}
