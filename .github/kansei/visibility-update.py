"""One-off, source-preserving public-site update. Run only on the review branch."""
from pathlib import Path
from bs4 import BeautifulSoup
import json,re,hashlib,subprocess
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[2]
DATE='2026-10-16'
ORIGIN='https://www.kansei.se'
OLD_ANALYTICS='/assets/analytics.20261009b.js'
NEW_ANALYTICS='/assets/analytics.20261016.js'
CLINIC='/assets/clinic.20261008.js'
MEANINGFUL=set()
changed=[]

def soup(text): return BeautifulSoup(text,'html.parser')
def span(text,node):
    assert node.sourceline is not None and node.sourcepos is not None
    start=sum(len(x) for x in text.splitlines(keepends=True)[:node.sourceline-1])+node.sourcepos
    assert text[start:start+len(node.name)+1].lower()=='<'+node.name.lower(), (node.name,text[start:start+80])
    if node.name in ['meta','link','img','input','source','br','hr']:
        return start,text.index('>',start)+1
    depth=0
    for m in re.finditer(r'</?'+re.escape(node.name)+r'\b[^>]*>',text[start:],re.I):
        tag=m.group()
        if tag.startswith('</'): depth-=1
        elif not tag.endswith('/>'): depth+=1
        if depth==0:return start,start+m.end()
    raise AssertionError('Unclosed '+node.name)
def substitute(text,node,replacement):
    a,b=span(text,node)
    return text[:a]+replacement+text[b:]
def replace_match(text,selector,needle,replacement,required=True):
    matches=[n for n in soup(text).select(selector) if needle in n.get_text(' ',strip=True)]
    if required:assert len(matches)==1,(selector,needle,len(matches))
    if not matches:return text
    return substitute(text,matches[0],replacement)
def append_to(text,node,fragment):
    a,b=span(text,node)
    end=text.rfind('</'+node.name,a,b)
    assert end>=a
    return text[:end]+fragment+text[end:]
def rewrite_schema(text,relative,description=None):
    nodes=soup(text).select('script[type="application/ld+json"]')
    for n in reversed(nodes):
        old=json.loads(n.get_text())
        data=json.loads(n.get_text())
        def walk(v):
            if isinstance(v,dict):
                if v.get('name')=='Kansei Rehabcenter':v['name']='Kansei Naprapati & Rehabcenter'
                if v.get('@type')=='Person' and v.get('name')=='Carl-Robert Kårell':
                    v.setdefault('@id',ORIGIN+'/team/carl-robert-karell/#person')
                    v.setdefault('url',ORIGIN+'/team/carl-robert-karell/')
                if relative in MEANINGFUL and v.get('@type') in ['WebPage','MedicalWebPage','ContactPage','ProfilePage','BlogPosting','Article']:
                    v['dateModified']=DATE
                if description and v.get('@type')=='BlogPosting':v['description']=description
                if relative=='naprapati/index.html' and v.get('@type')=='MedicalWebPage' and isinstance(v.get('mainEntity'),dict) and v['mainEntity'].get('@type')=='MedicalTherapy':
                    v['mainEntity']={'@type':'Service','@id':ORIGIN+'/naprapati/#service','name':'Naprapati vid Odenplan','serviceType':'Naprapati','url':ORIGIN+'/naprapati/','provider':{'@id':ORIGIN+'/#clinic'},'areaServed':{'@type':'City','name':'Stockholm'},'offers':{'@type':'Offer','price':'890','priceCurrency':'SEK','url':ORIGIN+'/naprapati/'}}
                if relative=='blogg/naprapat-fysioterapeut-kiropraktor-eller-ortoped/index.html' and v.get('@type')=='Question' and v.get('name')=='Behöver jag remiss till någon av yrkesgrupperna?':
                    v['acceptedAnswer']['text']='Hos Kansei kan du boka naprapati och ultraljud utan remiss. För annan vård behöver du kontrollera vad som gäller hos den mottagning du väljer. Specialistmedverkan på Kansei sker efter förfrågan och är inte ett ordinarie besök hos en fast bemannad ortoped- eller fysioterapeutmottagning.'
                for value in list(v.values()):walk(value)
            elif isinstance(v,list):
                for value in v:walk(value)
        walk(data)
        if data!=old:text=substitute(text,n,'<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False,separators=(',',':'))+'</script>')
    return text

files=[]
for p in sorted(ROOT.rglob('*.html')):
    rel=p.relative_to(ROOT).as_posix()
    if rel.startswith(('.github/','reda/','reda2/')):continue
    text=p.read_text()
    s=soup(text)
    if not s.body or 'clinic-site' not in s.body.get('class',[]):continue
    robots=s.select_one('meta[name="robots"]')
    if robots and 'noindex' in robots.get('content','').lower():continue
    files.append((p,rel,text))
assert len(files)>=120,len(files)
case_hashes={rel:hashlib.sha256(text[span(text,soup(text).find('main'))[0]:span(text,soup(text).find('main'))[1]].encode()).hexdigest() for _,rel,text in files if rel.startswith('ultraljud/') and rel!='ultraljud/index.html' and soup(text).find('main')}

for p,rel,original in files:
    text=original
    description=None
    if rel=='naprapati/index.html':
        text=replace_match(text,'p','Hos oss är frågan sällan antingen eller','<p>Hos Kansei träffar du <a href="/team/carl-robert-karell/">Carl-Robert Kårell, legitimerad naprapat</a>. Vi kombinerar undersökning och anpassad behandling med <a href="/rehabilitering/">rehabilitering</a>. <a href="/ultraljud/">Muskuloskeletalt ultraljud</a> kan komplettera bedömningen när det finns en relevant frågeställning. Behöver du annan kompetens rekommenderar vi vidare vård. <a href="/om-oss/">Specialistmedverkan sker efter förfrågan</a>, inte som en fast bemannad fysioterapeut- eller ortopedmottagning.</p>')
        MEANINGFUL.add(rel)
    if rel=='team/carl-robert-karell/index.html':
        s=soup(text)
        a=s.select_one('main a[href="/team/thomas-eriksson/"]')
        if a:
            parent=a.find_parent('p')
            assert parent and len(parent.get_text())<1500
            text=substitute(text,parent,'<p><a href="/om-oss/">Läs om kliniken och specialistmedverkan efter förfrågan</a> · <a href="/naprapati/">Så går naprapatbesöket till</a></p>')
            MEANINGFUL.add(rel)
    if rel=='ultraljud/index.html':
        block=soup(text).select_one('#vardgivare')
        assert block
        matches=[n for n in block.select('p') if 'Du behöver inte veta vilken sena' in n.get_text(' ',strip=True)]
        assert len(matches)>=1
        if len(matches)>1:text=substitute(text,matches[0],'')
        block=soup(text).select_one('#vardgivare')
        if not block.select_one('a[href="/for-vardgivare/"]'):
            text=append_to(text,block,'<p class="muted">Har du redan kontakt med en behandlare? <a href="/for-vardgivare/">Läs om frågeställning, undersökning och återkoppling till vårdgivare.</a></p>')
        MEANINGFUL.add(rel)
    if rel=='kontakt/index.html':
        needle='Naprapati och muskuloskeletalt ultraljud på Upplandsgatan 26'
        if needle in text:text=text.replace(needle,'Naprapati, muskuloskeletalt ultraljud och injektionsbehandling på Upplandsgatan 26')
        MEANINGFUL.add(rel)
    if rel=='blogg/naprapat-fysioterapeut-kiropraktor-eller-ortoped/index.html':
        description='Naprapat, fysioterapeut, kiropraktor eller ortoped? Läs om yrkena, hur du väljer mottagning och hur undersökning och vidare hänvisning fungerar hos Kansei.'
        text=text.replace('Naprapat, fysioterapeut, kiropraktor eller ortoped? Så skiljer sig yrkena, så väljer du rätt för ditt besvär, och därför behöver du inte välja rätt dörr hos oss.',description)
        text=replace_match(text,'p','Fysioterapeutens kärna','<p>Fysioterapeuter arbetar med funktion, träning och rehabilitering och kan ha olika specialistinriktningar. Kiropraktorer arbetar bland annat med manuell behandling av leder och muskler. Vilken kompetens som passar beror på besvären och behandlarens utbildning och erfarenhet. Hos Kansei sker eventuell specialistmedverkan <a href="/om-oss/">efter förfrågan</a>.</p>')
        text=replace_match(text,'p','under samma tak','<p>Den löpande verksamheten på Kansei drivs av <a href="/team/carl-robert-karell/">Carl-Robert Kårell, legitimerad naprapat</a>. Du kan boka undersökning, behandling och <a href="/ultraljud/">muskuloskeletalt ultraljud</a> utan remiss. Utifrån bedömningen planerar vi nästa steg eller rekommenderar vidare vård. Specialistmedverkan kan undersökas efter förfrågan; kliniken har inte en fast bemannad fysioterapeut- eller ortopedmottagning.</p>')
        text=text.replace('Därför behöver du inte välja rätt dörr hos oss','Så hjälper vi dig att välja nästa steg')
        text=text.replace('Hos oss bokar du alla besökstyper utan remiss.','Hos Kansei kan du boka naprapati och ultraljud utan remiss. Specialistmedverkan sker efter förfrågan.')
        # Keep the visible FAQ and JSON-LD answer identical.
        s=soup(text)
        for detail in s.select('details'):
            sm=detail.find('summary')
            if sm and sm.get_text(' ',strip=True)=='Behöver jag remiss till någon av yrkesgrupperna?':
                ptag=detail.find('p')
                assert ptag
                text=substitute(text,ptag,'<p>Hos Kansei kan du boka naprapati och ultraljud utan remiss. För annan vård behöver du kontrollera vad som gäller hos den mottagning du väljer. Specialistmedverkan på Kansei sker efter förfrågan och är inte ett ordinarie besök hos en fast bemannad ortoped- eller fysioterapeutmottagning.</p>')
                break
        byline=soup(text).select_one('main .byline')
        if byline:
            text=append_to(text,byline,' · Verksamhetsuppgifter uppdaterade 16 oktober 2026')
        MEANINGFUL.add(rel)
    if rel in ['blogg/index.html','kunskapsbank/index.html']:
        new='Så skiljer sig yrkena och så fungerar undersökning och vidare hänvisning hos Kansei.'
        text=text.replace('Så skiljer sig yrkena, så väljer du rätt för ditt besvär, och därför behöver du inte välja rätt dörr hos oss.',new)
        text=text.replace('därför behöver du inte välja rätt dörr hos oss','så fungerar undersökning och vidare hänvisning hos Kansei')
        if text!=original:MEANINGFUL.add(rel)
    if rel=='cookie/index.html':
        main=soup(text).find('main')
        section='<section class="page wrap" id="statistik-kallgrupp"><h2>Hur vi skiljer hänvisningar och bokningsklick åt</h2><p>Efter ditt godkännande kan statistiken ange en övergripande källgrupp, till exempel ChatGPT, Perplexity, Copilot, Gemini, Google, Bing, annan webbplats eller okänd. Gruppen bestäms från den hänvisande webbplatsens domän. Vi läser inte din fråga eller konversation hos tjänsten, och okända besök antas inte komma från AI.</p><p>En tillfällig källgrupp kan sparas i flikens sessionStorage i upp till 30 minuter efter senaste mätta aktivitet. Den innehåller bara gruppen och en tidsstämpel, inte namn, kontaktuppgifter, diagnoser eller ett nytt besökar-ID. Den tas bort när du avstår från statistik. Det befintliga statistikvalet sparas fortfarande i upp till 180 dagar.</p><p>Ett bokningsklick betyder att du klickat vidare för att boka. Det bekräftar inte att en bokning genomförts. Länkar för att läsa omdömen räknas inte som bokningsklick. Uppdatering av mätbeskrivningen: 16 oktober 2026.</p></section>'
        assert main and not soup(text).select_one('#statistik-kallgrupp')
        text=append_to(text,main,section)
        MEANINGFUL.add(rel)
    # Shared navigation must exist in HTML, not depend on a JavaScript-injected link.
    menu=soup(text).select_one('#site-menu .menu-secondary')
    if menu and not menu.select_one('a[href="/ultraljud/bilder/"]'):
        current=' aria-current="page"' if rel=='ultraljud/bilder/index.html' else ''
        text=append_to(text,menu,'<a href="/ultraljud/bilder/"'+current+'>Ultraljud i bild</a>')
    # Large previews are an explicit permission, never a promised search feature.
    r=soup(text).select_one('meta[name="robots"]')
    if r and 'max-image-preview:' not in r.get('content',''):
        content=r.get('content','index,follow').rstrip(',')+',max-image-preview:large'
        text=substitute(text,r,'<meta name="robots" content="'+content+'"/>')
    # Replace only source references, preserving the approved image/SVG markup byte for byte.
    text=text.replace(OLD_ANALYTICS,NEW_ANALYTICS)
    text=re.sub(r'(?P<q>[\"\'])'+re.escape(CLINIC)+r'(?:\?[^\"\']*)?(?P=q)',lambda m:m.group('q')+CLINIC+'?v=20261016'+m.group('q'),text)
    # Label outbound clinic links locally. Labels and destinations are never transmitted.
    for a in reversed(soup(text).select('a[href]')):
        try:u=urlsplit(a['href'])
        except ValueError:continue
        if u.hostname not in ['www.bokadirekt.se','bokadirekt.se'] or '48847' not in u.path:continue
        label=(a.get('aria-label','')+' '+a.get_text(' ',strip=True)).lower()
        review=bool(re.search(r'omdöme|recension|betyg|reviews|ratings',label))
        booking=not review and (u.path.startswith('/boka-tjanst/') or bool(re.search(r'\bboka\b|lediga tider|välj tid|öppna bokadirekt|boka­',label)))
        flag='booking_click' if booking else 'ignore'
        start,_=span(text,a)
        stop=text.index('>',start)
        opening=text[start:stop]
        opening=re.sub(r'\sdata-measure=(?:"[^"]*"|\'[^\']*\')','',opening)
        text=text[:start]+opening+' data-measure="'+flag+'"'+text[stop:]
    # Current brand name in metadata; don't rewrite historical text or external URLs.
    for n in reversed(soup(text).select('meta[property="og:site_name"],.brand,.brand img')):
        a,b=span(text,n)
        frag=text[a:b]
        if 'Kansei Rehabcenter' in frag:
            text=text[:a]+frag.replace('Kansei Rehabcenter','Kansei Naprapati &amp; Rehabcenter')+text[b:]
    text=rewrite_schema(text,rel,description)
    if rel=='index.html':
        graph={'@context':'https://schema.org','@type':'WebSite','@id':ORIGIN+'/#website','url':ORIGIN+'/','name':'Kansei Naprapati & Rehabcenter','inLanguage':'sv-SE','publisher':{'@id':ORIGIN+'/#clinic'}}
        if not any('"@type":"WebSite"' in x.get_text().replace(' ','') for x in soup(text).select('script[type="application/ld+json"]')):
            text=text.replace('</head>','<script type="application/ld+json">'+json.dumps(graph,ensure_ascii=False,separators=(',',':'))+'</script></head>',1)
    if rel in case_hashes:
        m=soup(text).find('main');a,b=span(text,m)
        assert hashlib.sha256(re.sub(r' data-measure="[^"]*"', '', text[a:b]).encode()).hexdigest()==case_hashes[rel], 'Case content changed: '+rel
    if text!=original:p.write_text(text);changed.append(rel)

js_path=ROOT/'assets/clinic.20261008.js'
js=js_path.read_text()
old="if(destination?.hostname==='www.bokadirekt.se' && /48847/.test(destination.pathname)){"
new="if(destination?.hostname==='www.bokadirekt.se' && /48847/.test(destination.pathname) && a.dataset.measure!=='ignore' && (a.dataset.measure==='booking_click' || destination.pathname.startsWith('/boka-tjanst/') || /\\bboka\\b|lediga tider|välj tid|öppna bokadirekt/i.test(a.getAttribute('aria-label') || a.textContent || '')) && !/omdöme|recension|betyg|reviews|ratings/i.test(a.getAttribute('aria-label') || a.textContent || '')){"
assert js.count(old)==1,'Booking hook changed; review required'
js_path.write_text(js.replace(old,new))

# Preserve image/video sitemap entries and all untouched lastmod values.
p=ROOT/'sitemap.xml';xml=p.read_text()
for rel in MEANINGFUL:
    url=ORIGIN+'/'+(rel[:-10] if rel.endswith('index.html') else rel)
    pattern=r'(<url>\s*<loc>'+re.escape(url)+r'</loc>)(.*?)(</url>)'
    matches=list(re.finditer(pattern,xml,re.S))
    if not matches:continue
    assert len(matches)==1
    m=matches[0];middle=m.group(2)
    if re.search(r'<lastmod>.*?</lastmod>',middle,re.S):middle=re.sub(r'<lastmod>.*?</lastmod>','<lastmod>'+DATE+'</lastmod>',middle,count=1,flags=re.S)
    else:middle='<lastmod>'+DATE+'</lastmod>'+middle
    xml=xml[:m.start()]+m.group(1)+middle+m.group(3)+xml[m.end():]
p.write_text(xml)

# Add stdlib-only regression checks to the existing CI entry point. No workflow changes.
p=ROOT/'.github/scripts/check-seo.py';text=p.read_text()
needle='    check_static()\n    if args.live:'
assert needle in text
text=text.replace(needle,"    check_static()\n    import runpy\n    runpy.run_path(str(ROOT / '.github/scripts/check-visibility.py'), run_name='__main__')\n    if args.live:")
p.write_text(text)
print('UPDATED PUBLIC PAGES',len(changed))
print('SEMANTIC CONTENT UPDATES',sorted(MEANINGFUL))
print('CASE MAIN CONTENT PRESERVED BYTE-FOR-BYTE',len(case_hashes))
print('BOOKING TAG COUNTS',sum(p.read_text().count('data-measure="booking_click"') for p,_,_ in files),sum(p.read_text().count('data-measure="ignore"') for p,_,_ in files))
