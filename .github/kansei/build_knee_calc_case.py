"""Build the clinician's knee mineral-deposition case with the shared reader.

Whole imagegen paintings are registered once globally; scan bytes and fixed
finding coordinates are preserved. Patient narrative is explicitly illustrative.
"""
from pathlib import Path
import argparse
import hashlib
import html
import json
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
PATH = '/ultraljud/kna/forkalkad-menisk/'
URL = 'https://www.kansei.se' + PATH
ASSETS = '/bilder/ultraljud/kna/kalk/'
VERSION = '20261022'
TITLE = 'Förkalkad menisk och kalk i brosket | Ultraljud knä | Kansei'
DESCRIPTION = 'Se förkalkad menisk och kalk i knäets ledbrosk på ultraljud. Verkliga bilder med naturtrogen anatomi, sidjämförelse och ett vardagsnära patientexempel från Kansei.'
HEADER = ' data-scan-header="68/960" style="--scan-header:7.0833333%"'
BOOK_US = 'https://www.bokadirekt.se/boka-tjanst/kansei-rehabcenter-48847/ultraljud-rorelseapparaten-1946824'
SOURCE_1177 = 'https://www.1177.se/sjukdomar--besvar/skelett-leder-och-muskler/leder/ledvark/'
ART = ROOT / '.github/kansei/artwork/knee-calc-20261022'

FAQ = [
    ('Vad betyder förkalkad menisk?', 'Undersökaren har identifierat kalkinlagringar i meniskens fiberbrosk. Det är ett annat fynd än en meniskspricka. Utseendet behöver bedömas i flera snitt och kopplas till symtom och funktion. Ett kalkfynd ensamt visar inte vad som gör ont.'),
    ('Vad är kondrokalcinos och CPPD?', 'Kondrokalcinos beskriver kalkinlagringar i brosk. CPPD handlar om deposition av kalciumpyrofosfatkristaller och kan ge olika kliniska bilder. En akut kristallutlöst ledinflammation kallas ibland pseudogikt. Bilderna här väcker frågan men fastställer inte i sig kristalltyp eller en aktiv CPPD-attack.'),
    ('Är kalk i brosket samma sak som fria kroppar i leden?', 'Nej. I det här bildfallet har undersökaren markerat två områden inne i ledbrosket. De återges därför i brosket även i anatomilagret. En fri kropp ligger löst i leden och är ett annat fynd.'),
    ('Betyder fyndet att jag har artros?', 'Kalkinlagringar och artros kan förekomma samtidigt, men är olika fynd. De här bilderna fastställer ingen artrosgrad. Knäbesvär bedöms med samtal och undersökning, ibland kompletterat med annan bilddiagnostik.'),
    ('Kan man ha kalk utan att ha ont?', 'Ja. Bildfynd av kristallinlagringar behöver inte motsvaras av symtom. Det är därför viktigt att bedöma när och hur knät gör ont och om det finns tecken på inflammation eller andra förändringar.'),
    ('Kan hyaluron ta bort kalken?', 'Hyaluron är inte en behandling för att lösa upp kalkinlagringar. Vid samtidig knäartros kan möjlig symtomlindring diskuteras efter individuell bedömning. På vår sida om hyaluron i knä finns forskningsläget, behandlingsalternativ och information inför bokning.'),
    ('Är jämförelsen en före- och efterbild?', 'Nej. Det är en sidjämförelse enligt undersökarens markeringar. Vänster sida är frisk och höger visar en förkalkad menisk. Olika sidor, snitt och probvinklar påverkar utseendet. Bilden visar ingen behandlingseffekt.'),
]

VIEWS = [
    dict(key='menisk-jamforelse', name='Jämför menisken', sub='Frisk och förkalkad sida',
         original='2_202601211019285900002.jpg', guide='2_202601211019285900002 (kopia).jpg',
         alt='Sidjämförelse med frisk menisk till vänster och förkalkad menisk till höger enligt undersökarens markeringar.',
         caption='Frisk menisk till vänster och förkalkad menisk till höger. Menisken och det mediala kollateralligamentet, MCL, kan följas var för sig. Jämförelsen visar inte en behandlingseffekt.',
         heading='Börja med att orientera dig mellan sidorna.',
         cue='Följ MCL som löper ytligt över ledspringan. Menisken ligger djupare mellan lårben och skenben. Jämför dess utseende i de två halvorna.',
         text='Undersökaren har angett vänster bildhalva som frisk och höger som påverkad med förkalkad menisk. Den friska menisken återges som jämnt grå fiberbrosk. Den påverkade innehåller ljusa kalkinlagringar. Bilderna har olika snitt och benkonturer. Skillnaden är inte i sig ett mått på skadans grad.',
         labels=[(343,231,'MCL'),(824,286,'MCL'),(174,336,'Menisk'),(1031,310,'Menisk'),(393,469,'Lårben'),(1176,458,'Skenben')],
         finding='<path class="finding-region" d="M1031 266 C1062 259 1107 272 1114 293 Q1122 314 1090 322 L1072 333 Q1033 331 1012 349 Q1000 362 1020 381 Q1046 407 1027 420 Q1015 429 1004 405 L977 360 Q953 345 957 318 Q964 294 993 281 Z"/><text x="970" y="611">Förkalkad menisk</text><text x="320" y="661">Frisk sida</text><text x="970" y="661">Förkalkad sida</text>'),
    dict(key='menisk-narbild', name='Menisken i närbild', sub='Insidan av knät',
         original='1_202601211019285900001.jpg', guide='Bild 1(1).jpg',
         alt='Ultraljud av mediala ledspringan med förkalkad menisk mellan femur till vänster och tibia till höger.',
         caption='Närbild av menisken på knäets insida. Femur ligger till vänster och tibia till höger i just detta snitt. MCL löper ovanför menisken.',
         heading='Kalkfyndet ligger i meniskens fiberbrosk.',
         cue='Se det utpekade meniskområdet mellan de två benytorna. Växla till anatomi för att skilja meniskens grå fiberbrosk från det ljusa ledbandet ovanför.',
         text='Meniskområdet återges efter undersökarens kontur. Kalkinlagringarna illustreras inom vävnaden. Det ska inte tolkas som att hela menisken har blivit ben, eller som en säker diagnos av en meniskruptur.',
         labels=[(362,218,'Underhud'),(373,312,'MCL'),(624,302,'Menisk'),(350,567,'Lårben'),(927,507,'Skenben')],
         finding='<path class="finding-region" d="M500 326 Q527 324 556 317 Q583 291 619 278 Q653 270 683 280 Q710 286 705 302 Q701 322 672 327 L622 329 Q595 325 598 350 Q606 378 625 403 Q639 423 620 428 Q606 425 592 407 L562 366 Q550 354 557 339 Q534 348 511 345 Q497 341 500 326 Z"/><text x="708" y="621">Förkalkad menisk</text>'),
    dict(key='brosk-kalk', name='Kalk i ledbrosket', sub='Två utpekade områden',
         original='6_202601211019285900006.jpg', guide='6_202601211019285900006 (kopia).jpg',
         alt='Tvärsnitt över femurs ledbrosk med två av undersökaren utpekade kalkområden inom broskbandet.',
         caption='Tvärsnitt framtill över lårbenets ledyta. Under quadricepssenan syns ledbrosket och den ljusa benkonturen. Två kalkområden är utpekade inne i brosket.',
         heading='Två små områden inne i brosket. De är inte fria kroppar.',
         cue='Följ det mörkare broskbandet ovanför den ljusa benlinjen. De två små markeringarna ligger inne i detta band, under quadricepssenan.',
         text='Anatomilagret skiljer fast, grått ledbrosk från ben och sena. De utpekade kalkområdena återges som små inlagringar på samma platser. Stillbilden ger ingen säker kemisk analys av kristallerna och visar inte att en akut inflammation pågår.',
         labels=[(625,186,'Underhud'),(228,301,'Vastus medialis'),(959,272,'Vastus lateralis'),(583,340,'Quadricepssena'),(545,526,'Ledbrosk'),(643,706,'Lårben')],
         finding='<path class="finding-region" d="M677 518 Q693 508 709 517 L721 536 Q728 552 714 560 L695 559 Q682 555 676 541 Q670 530 677 518 Z"/><path class="finding-region" d="M766 502 Q776 495 782 506 L784 523 Q781 537 773 537 Q760 535 762 522 L763 511 Z"/><text x="707" y="662">Kalk i ledbrosket</text>'),
]

def esc(value):
    return html.escape(str(value), quote=True)

def original(v):
    return ASSETS + v['key'] + '.original.jpg'

def anatomy(v):
    return ASSETS + v['key'] + '.anatomi.' + VERSION + '.webp'

def panel(v, index):
    labels = ''.join(f'<text x="{x}" y="{y}">{esc(t)}</text>' for x,y,t in v['labels'])
    return f'''<article class="knee-panel" data-key="{v['key']}" id="view-{v['key']}" role="tabpanel" aria-labelledby="tab-{v['key']}" tabindex="0"{' hidden' if index else ''}><figure><div class="knee-picture" data-anatomy="false" data-findings="false"><img class="knee-original" src="{original(v)}" width="1280" height="960" alt="{esc(v['alt'])}" decoding="async"{HEADER}/><div class="knee-anatomy" aria-hidden="true"><div class="knee-anatomy-content"><img src="{anatomy(v)}" width="1280" height="960" alt="Pedagogisk illustration av {esc(v['name'].lower())} i samma bildsnitt." decoding="async" loading="eager"/><svg class="knee-labels" viewBox="0 0 1280 960" aria-hidden="true">{labels}</svg></div></div><svg class="knee-findings" viewBox="0 0 1280 960" aria-hidden="true">{v['finding']}</svg></div><figcaption>{esc(v['caption'])}</figcaption></figure><div class="knee-panel-copy"><h3>{esc(v['heading'])}</h3><p class="knee-cue">{esc(v['cue'])}</p><p>{esc(v['text'])}</p></div></article>'''

def schema():
    person = {'@id':'https://www.kansei.se/team/carl-robert-karell/#person'}
    graph = [
        {'@type':'MedicalWebPage','@id':URL+'#webpage','url':URL,'name':TITLE,'description':DESCRIPTION,'inLanguage':'sv-SE','datePublished':'2026-10-22','dateModified':'2026-10-22','author':person,'publisher':{'@id':'https://www.kansei.se/#clinic'},'isPartOf':{'@id':'https://www.kansei.se/#website'},'breadcrumb':{'@id':URL+'#breadcrumb'},'mainEntity':{'@id':URL+'#case'},'primaryImageOfPage':{'@id':URL+'#brosk-kalk'}},
        {'@type':'Article','@id':URL+'#case','headline':'Förkalkad menisk och kalk i knäets ledbrosk','description':DESCRIPTION,'inLanguage':'sv-SE','datePublished':'2026-10-22','dateModified':'2026-10-22','author':person,'mainEntityOfPage':{'@id':URL+'#webpage'},'image':[{'@id':URL+'#'+v['key']} for v in VIEWS],'citation':['https://pmc.ncbi.nlm.nih.gov/articles/PMC11103298/','https://rheumatology.org/patients/calcium-pyrophosphate-deposition-cppd',SOURCE_1177]},
        {'@type':'BreadcrumbList','@id':URL+'#breadcrumb','itemListElement':[{'@type':'ListItem','position':i,'name':name,'item':url} for i,(name,url) in enumerate([('Kansei','https://www.kansei.se/'),('Ultraljud','https://www.kansei.se/ultraljud/'),('Knä','https://www.kansei.se/ultraljud/kna/'),('Kalk i menisk och brosk',URL)],1)]},
        {'@type':'Person',**person,'name':'Carl-Robert Kårell','jobTitle':'Legitimerad naprapat','url':'https://www.kansei.se/team/carl-robert-karell/'},
        {'@type':'FAQPage','@id':URL+'#faq','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in FAQ]},
    ]
    graph += [{'@type':'ImageObject','@id':URL+'#'+v['key'],'contentUrl':'https://www.kansei.se'+original(v),'caption':v['caption'],'creator':person,'width':1280,'height':960,'inLanguage':'sv-SE','creditText':'Carl-Robert Kårell / Kansei'} for v in VIEWS]
    return '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False,separators=(',',':'))+'</script>'

def build_page():
    source = (ROOT/'ultraljud/hoftled/bilder/index.html').read_text()
    source = re.sub(r'<title>.*?</title>', '<title>'+esc(TITLE)+'</title>', source, count=1, flags=re.S)
    source = source.replace('https://www.kansei.se/ultraljud/hoftled/bilder/',URL)
    def meta(m):
        tag=m[0]
        if 'name="description"' in tag or 'property="og:description"' in tag:
            tag=re.sub(r'content="[^"]*"','content="'+esc(DESCRIPTION)+'"',tag)
        elif 'property="og:title"' in tag:
            tag=re.sub(r'content="[^"]*"','content="'+esc(TITLE)+'"',tag)
        elif 'property="og:image"' in tag:
            tag=re.sub(r'content="[^"]*"','content="https://www.kansei.se'+anatomy(VIEWS[2])+'"',tag)
        return tag
    source=re.sub(r'<meta\b[^>]*>',meta,source)
    source=re.sub(r'<script\b[^>]*type="application/ld\+json"[^>]*>.*?</script>',schema(),source,flags=re.S)
    source=source.replace(' hip-joint-case',' knee-calc-case')
    # Keep shared design, reader, controls and zoom dialog. Only the main
    # editorial content and metadata are new.
    tabs=''.join(f'<button class="knee-tab" role="tab" id="tab-{v["key"]}" aria-controls="view-{v["key"]}" aria-selected="{str(i==0).lower()}" tabindex="{0 if i==0 else -1}" type="button"><img src="{original(v)}" alt="" width="96" height="72"{HEADER}/><span><strong>{v["name"]}</strong><small>{v["sub"]}</small></span></button>' for i,v in enumerate(VIEWS))
    content=(ROOT/'.github/kansei/content/knee-calc-case.20261022.html.in').read_text()
    for key,value in {'TABS':tabs,'PANELS':''.join(panel(v,i) for i,v in enumerate(VIEWS)),'BOOK_US':BOOK_US,'HEADER':HEADER,'ASSETS':ASSETS,'1177':SOURCE_1177,'FAQ':''.join('<details><summary>'+esc(q)+'</summary><p>'+esc(a)+'</p></details>' for q,a in FAQ)}.items():
        content=content.replace('{{'+key+'}}',value)
    assert '{{' not in content
    source=re.sub(r'<main\b[^>]*>.*?</main>',lambda _:content,source,count=1,flags=re.S)
    # The history stylesheet also owns the shared full-canvas reader geometry.
    # Retain that dependency; remove only the hip-joint editorial supplement.
    source=re.sub(r'<link[^>]*href="/assets/hip-joint-case\.[^"]*"[^>]*>','',source)
    source=source.replace('</head>','<link rel="stylesheet" href="/assets/knee-calc-case.20261022.css"/></head>')
    target=ROOT/PATH.strip('/')/'index.html';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(source)
    return target

def add_catalogue():
    path=ROOT/'ultraljud/bilder/index.html';s=path.read_text()
    if PATH in s:return
    card=f'''<article class="atlas-entry" data-atlas-entry data-region="kna" data-symptoms="svullnad gang traning" data-search="förkalkad menisk menisken förkalkning förkalkningar kalk brosk brosket ledbrosk ledbrosket kondrokalcinos CPPD pseudogikt insida knä stelhet svullnad promenad trappor"><div class="atlas-thumb" aria-hidden="true"><img src="{original(VIEWS[2])}" alt="" width="1280" height="960" loading="lazy" decoding="async"{HEADER}/></div><div class="atlas-entry-copy"><small>Knä · Kalk i menisk och ledbrosk</small><h4><a href="{PATH}" data-atlas-case>Stelt knä och frågor om kalk i menisk eller brosk?</a></h4><span class="atlas-case-type">Verkliga bilder och illustrativ patientberättelse</span><p>Jämför meniskbilder och se två kalkområden inne i ledbrosket, med naturtrogna anatomilager.</p><a class="atlas-image-shortcut" href="{PATH}#bilder">Direkt till bilder och fynd</a></div></article>'''
    start=s.index('id="omrade-kna"');end=s.index('</div></section>',start)
    s=s[:end]+card+s[end:]
    # Compute all counts from actual cards, including the existing hip-joint
    # card that was not yet included in the catalogue's structured ItemList.
    cards=re.findall(r'<article class="atlas-entry".*?</article>',s,re.S)
    def update_ld(m):
        data=json.loads(m[2])
        for node in data.get('@graph',[]):
            if node.get('@type')=='ItemList':
                entries=[]
                for i,card in enumerate(cards,1):
                    match=re.search(r'<h4><a href="([^"]+)"[^>]*>(.*?)</a>',card,re.S)
                    assert match
                    entries.append({'@type':'ListItem','position':i,'name':html.unescape(re.sub('<[^>]+>','',match[2])),'url':'https://www.kansei.se'+match[1]})
                node['numberOfItems']=len(entries);node['itemListElement']=entries
        return m[1]+json.dumps(data,ensure_ascii=False,separators=(',',':'))+m[3]
    s=re.sub(r'(<script\b[^>]*type="application/ld\+json"[^>]*>)(.*?)(</script>)',update_ld,s,flags=re.S)
    s=re.sub(r'\d+ bildfall · Alla områden',str(len(cards))+' bildfall · Alla områden',s)
    s=re.sub(r'(<span>Alla områden</span><small>)\d+(</small>)',lambda m:m[1]+str(len(cards))+m[2],s)
    knee_count=sum('data-region="kna"' in c for c in cards)
    s=re.sub(r'(<span>Knä</span><small>)\d+(</small>)',lambda m:m[1]+str(knee_count)+m[2],s)
    path.write_text(s)

def add_internal_links():
    # Link from the established knee page, next to its existing sources; keep
    # the artrosis story and treatment statements unmodified.
    p=ROOT/'ultraljud/kna/index.html';s=p.read_text()
    if PATH not in s:
        link=f'<p><a href="{PATH}">Nytt bildfall med förkalkad menisk och kalk i ledbrosket</a> Se tre vyer med sidjämförelse, naturtrogen anatomi och förklaring av fynden.</p>'
        marker='<section class="section" id="kallor"'
        i=s.index(marker);j=s.index('</h2>',i) if '</h2>' in s[i:s.index('</section>',i)] else -1
        if j>=0:s=s[:j+5]+link+s[j+5:]
        else:
            i=s.index('<ul',i);s=s[:i]+link+s[i:]
        p.write_text(s)
    p=ROOT/'sitemap.xml';s=p.read_text()
    if URL not in s:
        images=''.join('<image:image><image:loc>https://www.kansei.se'+original(v)+'</image:loc><image:caption>'+esc(v['caption'])+'</image:caption></image:image>' for v in VIEWS)
        s=s.replace('</urlset>','<url><loc>'+URL+'</loc><lastmod>2026-10-22</lastmod>'+images+'</url>\n</urlset>');p.write_text(s)

def package_images(workspace, generation):
    from PIL import Image
    from paint_registration import register
    public=ROOT/ASSETS.strip('/');public.mkdir(parents=True,exist_ok=True)
    ART.mkdir(parents=True,exist_ok=True)
    qa=workspace/'knee-calc-qa';qa.mkdir(exist_ok=True)
    records=[]
    for v in VIEWS:
        source=workspace/'upload'/v['original'];guide=workspace/'upload'/v['guide']
        shutil.copy2(source,public/(v['key']+'.original.jpg'))
        spec=generation[v['key']];painting=Path(spec['path'])
        rec=register(painting,ROOT/anatomy(v).lstrip('/'),ART/(v['key']+'.painting.webp'),[1280,960],spec['source_bounds'],spec['target_bounds'],qa,False)
        rec.update({'key':v['key'],'original_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'guide_sha256':hashlib.sha256(guide.read_bytes()).hexdigest(),'clinician_guide':v['guide']})
        for key in ('archive','asset'):rec[key]=str(Path(rec[key]).relative_to(ROOT))
        records.append(rec)
    (ART/'manifest.json').write_text(json.dumps({'canvas':[1280,960],'method':'One global painting placement; no local warp. Clinical originals byte-identical. Acquisition header clipped by shared reader.','clinical_scope':'Clinician supplied mineral deposition in meniscus and articular cartilage in one individual. No demographics, symptom history, confirmed crystal type, arthrosis grade, treatment or outcome supplied. Narrative explicitly illustrative.','views':records},ensure_ascii=False,indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path);p.add_argument('--generation',type=Path);args=p.parse_args()
    if args.generation:package_images(args.workspace,json.loads(args.generation.read_text()))
    build_page();add_catalogue();add_internal_links()
    print(json.dumps({'page':PATH,'views':len(VIEWS)},ensure_ascii=False))

if __name__=='__main__':main()
