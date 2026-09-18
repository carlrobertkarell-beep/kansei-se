"""Patient workflow regression checks. Only fictional data and an intercepted API."""
import base64
import re
import functools
import json
import os
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / 'reda2-test-results'
RESULTS.mkdir(exist_ok=True)
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass
server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
ORIGIN = f'http://127.0.0.1:{server.server_port}'
FIXTURE = {
    'userId': 'fictional-user', 'patient': {'id': 'fictional-patient', 'display_name': 'Testpersonen'},
    'plan': {'id': 'fictional-plan', 'version': 3, 'status': 'active', 'activated_at': '2026-09-01T10:00:00Z', 'payload': {
        'goal': 'Klara trappan hemma', 'context': {'goalProfile': 'daily', 'capacity': 'supported', 'stage': 'build', 'equipment': 'home'},
        'schedule': {'days': [1,3,5]},
        'exercises': [
            {'id': 'chair', 'name': 'Uppresning från stol', 'variantId': 'supported', 'side': 'simultaneous', 'motionKey': 'chair', 'dose': {'sets': 2, 'reps': 8, 'rest': 0}, 'instruction': 'Res dig lugnt med stöd från stolen.'},
            {'id': 'extension', 'name': 'Benspark från stol', 'variantId': 'seated', 'side': 'both', 'motionKey': 'extension', 'dose': {'sets': 2, 'reps': 8, 'rest': 0}, 'instruction': 'Sträck ett knä i taget.'},
            {'id': 'calf', 'name': 'Tåhävning med stöd', 'variantId': 'supported', 'side': 'simultaneous', 'motionKey': 'calf', 'dose': {'sets': 1, 'reps': 8, 'rest': 0}, 'instruction': 'Lyft hälarna lugnt.'}
        ]}}, 'sessions': [], 'responses': [], 'reflections': [], 'responseError': False, 'reflectionError': False,
}
MOCK = r'''
const clone=x=>JSON.parse(JSON.stringify(x));
const store=window.__fixture;window.__saves=[];window.__failSaves=false;window.__saveDelay=0;
export const db={auth:{onAuthStateChange(){}}};
export async function currentUser(){return {id:store.userId,email:'fictional@example.test'}}
export async function patientBootstrap(){return clone(store)}
export async function evaluateProgression(){return {code:'no_frame',applied:false}}
export async function saveSession(planId,s){
 window.__saves.push(clone({planId,...s}));if(window.__saveDelay)await new Promise(r=>setTimeout(r,window.__saveDelay));
 if(window.__failSaves)throw Error('Simulated connection loss');
 let row=store.sessions.find(r=>r.client_session_id===s.clientSessionId);
 if(row?.completed_at){if(JSON.stringify(row.payload.exercises)!==JSON.stringify(s.payload.exercises))throw Error('Closed session immutable');return row.id}
 if(!row){row={id:'server-'+s.clientSessionId,client_session_id:s.clientSessionId,plan_id:planId,plan_version:store.plan.version};store.sessions.push(row)}
 Object.assign(row,{status:s.status,started_at:s.startedAt,completed_at:s.completedAt,payload:clone(s.payload)});return row.id;
}
export async function submitSessionReflection(sid,rid,answers){const s=store.sessions.find(s=>s.id===sid);const r={id:rid,session_id:sid,plan_id:s.plan_id,plan_version:s.plan_version,created_at:new Date().toISOString(),answers};store.reflections.push(r);return clone(r)}
export async function signOut(){}
export async function sendPatientMagicLink(){}
'''

def inline_html():
    # Offline rendering for environments that prohibit browser navigation.
    # Import maps resolve only local repository bytes; no production calls.
    modules={}
    def load_module(path):
        key='reda-test:'+path
        if key in modules:return key
        modules[key]=''
        source=MOCK if path.split('?')[0]=='reda-2/secure-browser.mjs' else (ROOT/path.split('?')[0]).read_text()
        def dependency(m):
            spec=m.group(2)
            if not spec.startswith('.'):raise ValueError('Unexpected module dependency: '+spec)
            target=str(Path(path.split('?')[0]).parent/spec)
            return m.group(1)+load_module(target)+m.group(3)
        source=re.sub(r"((?:from\s*|import\s*)['\"])(\.{1,2}/[^'\"]+)(['\"])",dependency,source)
        modules[key]='data:text/javascript;base64,'+base64.b64encode(source.encode()).decode()
        return key
    html=(ROOT/'reda-2/patient.html').read_text()
    def style(m):
        path=m.group(1).split('?')[0]
        file=ROOT/path.lstrip('/') if path.startswith('/') else ROOT/'reda-2'/path
        return '<style>'+file.read_text()+'</style>'
    html=re.sub(r'<link rel="stylesheet" href="([^"]+)"\s*/?>',style,html)
    def script(m):
        attrs,body=m.groups();src=re.search(r'src="([^"]+)"',attrs)
        if not src:return m.group(0)
        path=src.group(1);path=path.lstrip('/') if path.startswith('/') else 'reda-2/'+path
        if 'type="module"' in attrs:return '<script type="module">import '+json.dumps(load_module(path))+';</script>'
        return '<script>'+(ROOT/path.split('?')[0]).read_text()+'</script>'
    html=re.sub(r'<script([^>]*)>(.*?)</script>',script,html,flags=re.S)
    imports='<script type="importmap">'+json.dumps({'imports':modules})+'</script>'
    shim='<script>if(!crypto.randomUUID){let n=0;crypto.randomUUID=()=>"00000000-0000-4000-8000-"+String(++n).padStart(12,"0")}</script>'
    return html.replace('<head>','<head>'+imports+shim,1)

def run():
    with sync_playwright() as pw:
        executable = os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE')
        browser = pw.chromium.launch(headless=True, **({'executable_path': executable} if executable else {}))
        def page_for(width=390, height=844, dark=False, fixture=None):
            context=browser.new_context(viewport={'width':width,'height':height}, reduced_motion='reduce')
            context.set_default_timeout(8000)
            context.add_init_script('window.__fixture='+json.dumps(fixture or FIXTURE)+';')
            def route(r):
                if '/reda-2/secure-browser.mjs' in r.request.url:r.fulfill(status=200,content_type='text/javascript',body=MOCK)
                elif r.request.url.startswith(ORIGIN):r.continue_()
                else:r.abort()
            context.route('**/*',route)
            page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            
            if os.environ.get('REDA_INLINE_TEST'):
                page.evaluate('f=>window.__fixture=f',fixture or FIXTURE);page.set_content(inline_html())
            else:page.goto(ORIGIN+'/reda-2/patient.html')
            try:expect(page.locator('#app')).to_be_visible()
            except Exception:
                print('Browser errors:',errors);print('Auth error:',page.locator('#authError').inner_text());raise
            page.evaluate('(theme)=>document.documentElement.dataset.redaTheme=theme','dark' if dark else 'light')
            page.locator('#start').click();expect(page.locator('#player')).to_be_visible()
            return context,page,errors
        def mark(page):
            count=page.evaluate('window.__saves.length')
            page.locator('#rounds button:not(:disabled)').click()
            page.wait_for_function('(n)=>window.__saves.length>n',arg=count)
            expect(page.locator('#sync')).to_have_text('Synkad med kliniken')
        def overview(page):
            page.locator('#openSessionOverview').click();expect(page.locator('#sessionOverview')).to_be_visible()
        def assert_layout(page):
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            assert page.locator('#sessionOverview').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')

        # Overview is read-only; both-side counting, feedback and explicit pause.
        ctx,p,errors=page_for();before=p.evaluate('JSON.stringify(window.__fixture.plan)');overview(p)
        expect(p.locator('.session-overview-total')).to_contain_text('0 av 7');assert_layout(p)
        assert p.evaluate('window.__saves.length')==1
        p.locator('[data-overview-exercise="1"]').click();expect(p.locator('#exName')).to_have_text('Benspark från stol')
        mark(p);p.locator('#openPlayerOptions').click();p.locator('#skip').click();p.locator('[data-effort="heavy"]').click();expect(p.locator('#sync')).to_have_text('Synkad med kliniken')
        overview(p);expect(p.locator('.session-overview-sides')).to_have_text('Vänster 1 av 2 · Höger 0 av 2')
        expect(p.locator('.session-overview-feedback')).to_have_text('Ditt svar: För tungt')
        p.screenshot(path=str(RESULTS/'session-overview-mobile.png'))
        assert p.evaluate('JSON.stringify(window.__fixture.plan)')==before
        p.locator('[data-overview-pause]').click();expect(p.locator('#player')).to_be_hidden()
        assert p.evaluate('window.__fixture.sessions[0].completed_at') is None
        p.locator('#start').click();overview(p);expect(p.locator('.session-overview-total')).to_contain_text('1 av 7')
        # Finish last exercise while earlier exercises remain: must return to overview, not close session.
        p.locator('[data-overview-exercise="2"]').click();mark(p);p.locator('#next').click()
        expect(p.locator('#sessionOverview')).to_be_visible();assert p.evaluate('window.__fixture.sessions[0].completed_at') is None
        # Early finish is a distinct confirmed action, not silently marking untouched work as skipped.
        p.locator('[data-overview-end]').click();expect(p.locator('.session-overview-confirm')).to_contain_text('Återstående omgångar markeras inte som genomförda')
        p.evaluate('window.__saveDelay=150');p.locator('[data-overview-save]').click()
        expect(p.locator('#player')).to_be_hidden();expect(p.locator('#sessionReflection')).to_be_visible()
        row=p.evaluate('window.__fixture.sessions[0]');assert row['status']=='partial' and row['completed_at']
        assert [x['status'] for x in row['payload']['exercises']]==['pending','skipped','completed']
        assert [x['roundsDone'] for x in row['payload']['exercises']]==[0,1,1]
        assert len([s for s in p.evaluate('window.__saves') if s['completedAt']])==1
        p.locator('[data-barrier="energy"]').click();p.locator('[data-support="yes"]').click();p.locator('[data-reflection-save]').click()
        expect(p.locator('.loop-receipt')).to_be_visible();assert p.evaluate('window.__fixture.reflections[0].session_id')==row['id']
        assert not errors,errors;ctx.close();print('PASS: overview, side counts, pause, navigation, partial finish and exact-session feedback')

        # Full sequential flow stays one-click completion; completed work cannot become skipped.
        ctx,p,errors=page_for(1440,900)
        for rounds in [2,4,1]:
            for _ in range(rounds):mark(p)
            expect(p.locator('#skip')).to_be_disabled()
            p.locator('#next').click()
        expect(p.locator('#player')).to_be_hidden();assert p.evaluate('window.__fixture.sessions[0].status')=='completed'
        assert not errors,errors;ctx.close();print('PASS: existing full sequential completion')

        # Failed final write never displays feedback or a server success receipt; retry same session.
        ctx,p,errors=page_for(320,740,True);mark(p);overview(p);assert_layout(p)
        p.screenshot(path=str(RESULTS/'session-overview-dark-320.png'))
        p.locator('[data-overview-end]').click();p.evaluate('window.__failSaves=true');p.locator('[data-overview-save]').click()
        expect(p.locator('#retrySync')).to_be_visible();expect(p.locator('#sessionReflection')).to_be_hidden()
        assert p.evaluate('window.__fixture.sessions[0].completed_at') is None
        sid=p.evaluate('window.__fixture.sessions[0].client_session_id')
        p.locator('#start').click();expect(p.locator('#sync')).to_contain_text('Synka det avslutade passet')
        p.evaluate('window.__failSaves=false');p.locator('#retrySync').click();expect(p.locator('#retrySync')).to_be_hidden()
        row=p.evaluate('window.__fixture.sessions[0]');assert row['completed_at'] and row['client_session_id']==sid
        assert len(p.evaluate('window.__fixture.sessions'))==1
        assert not errors,errors;ctx.close();print('PASS: failed save, truthful status, blocked new session and same-ID retry')

        # Keyboard escape, all unregistered confirmation and safe literal text; no script injection.
        f=json.loads(json.dumps(FIXTURE));f['plan']['payload']['exercises'][0]['name']='<img src=x onerror="window.__injected=true">'
        ctx,p,errors=page_for(fixture=f);overview(p);assert p.locator('.session-overview-list img').count()==0
        p.keyboard.press('Escape');expect(p.locator('#sessionOverview')).to_be_hidden();expect(p.locator('#openSessionOverview')).to_be_focused()
        p.locator('#openPlayerOptions').click();p.locator('#endSessionEarly').click()
        expect(p.locator('.session-overview-confirm')).to_contain_text('Ingen omgång är registrerad')
        p.locator('[data-overview-save]').click();expect(p.locator('#player')).to_be_hidden()
        expect(p.locator('#history')).to_contain_text('Avslutat utan registrerade omgångar')
        assert all(x['roundsDone']==0 and x['status']=='pending' for x in p.evaluate('window.__fixture.sessions[0].payload.exercises'))
        assert not p.evaluate('Boolean(window.__injected)');assert not errors,errors;ctx.close();print('PASS: keyboard, options entry, empty-session truthfulness and literal content')
        browser.close()
try:
    run()
finally:
    server.shutdown()
