"""Build the clinician supplied hip-joint case and register whole paintings.

Source clinical JPEGs stay byte-identical. One global placement per painting;
no local warp, texture tiles, or diagnostic alteration. The shared reader clips
the acquisition header in originals, thumbnails and enlarged views.
"""
from pathlib import Path
import base64
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
VERSION = '20261021c'
PATH = '/ultraljud/hoftled/bilder/'
URL = 'https://www.kansei.se' + PATH
ASSETS = '/bilder/ultraljud/hoftled/'
TITLE = 'Ultraljud av höftleden inför Sinogel | Kansei Stockholm'
DESCRIPTION = 'Följ ett patientfall med ultraljud av höftleden före en Sinogel-injektion. Utforska originalbilder, muskler, fascia, ledkapsel och benkontur hos Kansei i Stockholm.'
HEADER = ' data-scan-header="68/960" style="--scan-header:7.0833333%"'
BOOK_US = 'https://www.bokadirekt.se/boka-tjanst/kansei-rehabcenter-48847/ultraljud-rorelseapparaten-1946824'
BOOK_HA = 'https://www.bokadirekt.se/boka-tjanst/kansei-naprapati-rehabcenter-48847/hyaluronsyra-sinogel-3478216'
IBSA = 'https://www.ibsa-sinovial.de/wp-content/uploads/2024/03/IFU_SINOGEL_3ml_1ago_5000004509_Rev01_DE_280923_VISIONE.pdf'
ESSR = 'https://www.essr.org/content-essr/uploads/2016/10/hip.pdf'
SOC = 'https://www.socialstyrelsen.se/contentassets/f1aea0d977d64b18a57ea369fe17032e/2024-12-9337-bilaga-2-socialstyrelsens-icke-gora.pdf'
AAOS = 'https://www.aaos.org/aaos-home/newsroom/press-releases/aaos-updates-management-of-hip-osteoarthritis-guideline/'

VIEWS = [
    dict(key='kapsel', name='Främre ledkapsel', sub='Muskler och fascia',
         original='1_202610211457092110001.jpg', guide='Höftled 2 bild1 .jpg',
         painting='exec-092f001f-41cc-4421-97a1-065234e62136.png', scan=[226,111,1053,891], source_scan=[244,88,1203,987],
         alt='Ultraljud framtill över höftleden med överliggande muskler, fascieplan och ett utpekat kapselområde.',
         caption='Främre höftleden i ett obliqt snitt. Sartorius, rectus femoris och iliopsoas ligger ytligare än kapselområdet och benytan.',
         heading='Följ vävnaderna från musklerna ned till leden.',
         cue='De ljusa stråken delar upp muskelbukarna. Följ sedan det djupare kapselområdet mot den ljusa benkonturen.',
         text='I längdsnittet skiljs den tunna kapselytan från innehållet i den främre ledrecessen. Innehållet återges grått och heterogent med interna ekon, som i originalet. I anatomilagret återges området därför inte som ett enda fibröst vävnadsblock. Hela utrymmets bredd ska inte tolkas som kapselväggens tjocklek.',
         labels=[(825,187,'Sartorius',''),(748,243,'Rectus femoris',''),(620,370,'Iliopsoas',''),(404,339,'Fascia','dark-label'),(638,660,'Ledrecess',''),(586,857,'Lårben','')],
         finding='<path class="finding-region" d="M228 462 C348 474 435 485 513 517 S675 572 761 592 S911 679 925 738 L936 800"/><path class="pointer-shadow" d="M817 719 L735 652"/><path class="pointer" d="M817 719 L735 652"/><circle cx="735" cy="652" r="5"/><text x="802" y="758">Kapselområdet</text>'),
    dict(key='caput', name='Caput femoris', sub='Ojämn benkontur',
         original='17_202610201326063720003.jpg', guide='Höftled 2 anno bild 1.jpg',
         painting='exec-b1fb92d6-59b6-4f80-a12e-f06e879c4355.png', scan=[226,111,1053,891], source_scan=[254,136,1194,1003],
         alt='Ultraljud i obliqt snitt över caput femoris med oregelbunden benkontur och överliggande kapselområde.',
         caption='Obliqt snitt över lårbenshuvudet, caput femoris. Undersökaren har pekat ut en oregelbunden benkontur under kapselområdet.',
         heading='Den ojämna benytan behöver läsas i sitt sammanhang.',
         cue='Följ den ljusa benlinjen och dess ojämnheter. Slå på anatomin för att skilja benkonturen från kapseln och musklerna ovanför.',
         text='Visa fynden pekar ut benkonturen som undersökaren bedömde som förändrad. En stillbild visar en begränsad del av leden och graderar inte ensam höftartros. Varken hela ledbrosket eller all ledens anatomi kan bedömas i detta snitt.',
         labels=[(834,187,'Sartorius',''),(833,253,'Rectus femoris',''),(616,332,'Iliopsoas',''),(838,383,'Fascia','dark-label'),(772,487,'Ledrecess',''),(472,701,'Caput femoris','')],
         finding='<path class="cyst-region" d="M231 539 C280 508 335 483 383 473 L440 461 C426 474 438 482 414 488 C377 492 376 500 420 505 L446 494 L462 476 L521 462 C560 459 592 461 611 473 C624 492 610 519 580 535 C554 547 558 555 587 558 L630 548 C686 527 737 550 790 581"/><path class="pointer-shadow" d="M801 438 L606 511"/><path class="pointer" d="M801 438 L606 511"/><circle cx="606" cy="511" r="5"/><text x="818" y="409">Ojämn benkontur</text>'),
    dict(key='jamforelse', name='Jämför sidorna', sub='Referens och påverkan',
         original='2_202610201338526910001 (kopia).jpg', guide='Höftled 2 anno bild 3.jpg',
         painting='exec-a8d967ee-90cd-4c61-be41-ccb2c385e012.png', scan=[75,111,1203,891], source_scan=[57,107,1392,993],
         alt='Två ultraljudsvyer av höftens främre kapselområde, med referenssidan till vänster och den påverkade sidan till höger enligt undersökarens annotering.',
         caption='Referenssida till vänster och påverkad sida till höger, enligt undersökarens annotering. Bilderna visar olika sidor och snitt, inte före och efter injektionen.',
         heading='Jämförelsen hjälper ögat att hitta kapselområdet.',
         cue='Jämför området mellan iliopsoas och benkonturen. Se också hur fascian delar upp musklerna ovanför leden på båda sidor.',
         text='Kapselområdet framträder olika i de två vyerna. Probens vinkel och det valda snittet påverkar utseendet. Jämförelsen visar undersökarens orientering i vävnaderna och är inte en standardiserad mätning eller ett behandlingsresultat.',
         labels=[(366,188,'Sartorius',''),(920,188,'Sartorius',''),(354,241,'Rectus femoris',''),(918,218,'Rectus femoris',''),(370,451,'Iliopsoas',''),(936,377,'Iliopsoas',''),(468,374,'Fascia','dark-label'),(354,649,'Ledrecess',''),(959,643,'Ledrecess',''),(353,842,'Referenssida',''),(937,842,'Påverkad sida','')],
         finding='<path class="finding-region" d="M648 449 C748 483 837 514 939 531 S1117 550 1201 571"/><path class="pointer-shadow" d="M1022 629 L955 578"/><path class="pointer" d="M1022 629 L955 578"/><circle cx="955" cy="578" r="5"/><text x="933" y="686">Utpekat kapselområde</text><text x="350" y="842">Referenssida</text><text x="935" y="842">Påverkad sida</text>'),
]

def esc(value):
    return html.escape(str(value), quote=True)

def image(key):
    return ASSETS + key + '.original.jpg'

def anatomy(key):
    return ASSETS + key + '.anatomi.' + VERSION + '.webp'

def link(key, text):
    return f'<a href="#bilder" data-case-view data-case-tab="tab-{key}" data-case-findings="true">{esc(text)} →</a>'

def panel(v, index):
    key = v['key']
    labels = ''.join(f'<text x="{x}" y="{y}" class="{css}">{esc(text)}</text>' for x,y,text,css in v['labels'])
    return f'''<article class="knee-panel" data-key="{key}" id="view-{key}" role="tabpanel" aria-labelledby="tab-{key}" tabindex="0"{' hidden' if index else ''}><figure><div class="knee-picture" data-anatomy="false" data-findings="false"><img class="knee-original" src="{image(key)}" width="1280" height="960" alt="{esc(v['alt'])}" decoding="async"{HEADER}/><div class="knee-anatomy" aria-hidden="true"><div class="knee-anatomy-content"><img src="{anatomy(key)}" width="1280" height="960" alt="Pedagogisk illustration av {esc(v['name'].lower())}, muskler och fascia i samma snitt." decoding="async" loading="eager"/><svg class="knee-labels" viewBox="0 0 1280 960" aria-hidden="true">{labels}</svg></div></div><svg class="knee-findings" viewBox="0 0 1280 960" aria-hidden="true">{v['finding']}</svg></div><figcaption>{esc(v['caption'])}</figcaption></figure><div class="knee-panel-copy"><h3>{esc(v['heading'])}</h3><p class="knee-cue"><strong>Titta efter:</strong> {esc(v['cue'])}</p><p>{esc(v['text'])}</p></div></article>'''

def main_content():
    tabs = ''.join(f'<button class="knee-tab" role="tab" id="tab-{v["key"]}" aria-controls="view-{v["key"]}" aria-selected="{str(i==0).lower()}" tabindex="{0 if i==0 else -1}" type="button"><img src="{image(v["key"])}" alt="" width="96" height="72"{HEADER}/><span><strong>{v["name"]}</strong><small>{v["sub"]}</small></span></button>' for i,v in enumerate(VIEWS))
    panels = ''.join(panel(v,i) for i,v in enumerate(VIEWS))
    content = (ROOT/'.github/kansei/content/hip-joint-case.20261021.html.in').read_text()
    replacements = {'{{TABS}}':tabs,'{{PANELS}}':panels,'{{BOOK_US}}':BOOK_US,'{{BOOK_HA}}':BOOK_HA,'{{IBSA}}':IBSA,'{{ESSR}}':ESSR,'{{SOC}}':SOC,'{{AAOS}}':AAOS,'{{HEADER}}':HEADER}
    for token, value in replacements.items():
        content = content.replace(token, value)
    assert '{{' not in content
    return content

def schema():
    person = {'@id':'https://www.kansei.se/team/carl-robert-karell/#person'}
    graph = [
        {'@type':'MedicalWebPage','@id':URL+'#webpage','url':URL,'name':TITLE,'description':DESCRIPTION,'inLanguage':'sv','datePublished':'2026-10-21','dateModified':'2026-10-21','author':person,'publisher':{'@id':'https://www.kansei.se/#clinic'},'isPartOf':{'@id':'https://www.kansei.se/#website'},'breadcrumb':{'@id':URL+'#breadcrumb'},'mainEntity':{'@id':URL+'#case'},'primaryImageOfPage':{'@id':URL+'#kapsel'}},
        {'@type':'Article','@id':URL+'#case','headline':'Höftleden på ultraljud – inför en Sinogel-injektion','description':DESCRIPTION,'inLanguage':'sv','datePublished':'2026-10-21','dateModified':'2026-10-21','author':person,'mainEntityOfPage':{'@id':URL+'#webpage'},'image':[{'@id':URL+'#'+v['key']} for v in VIEWS]},
        {'@type':'BreadcrumbList','@id':URL+'#breadcrumb','itemListElement':[{'@type':'ListItem','position':i,'name':name,'item':url} for i,(name,url) in enumerate([('Kansei','https://www.kansei.se/'),('Ultraljud','https://www.kansei.se/ultraljud/'),('Höft och ljumske','https://www.kansei.se/ultraljud/hoft-ljumske/'),('Patientfall',URL)],1)]},
        {'@type':'Person',**person,'name':'Carl-Robert Kårell','jobTitle':'Legitimerad naprapat','url':'https://www.kansei.se/team/carl-robert-karell/'}]
    graph += [{'@type':'ImageObject','@id':URL+'#'+v['key'],'contentUrl':'https://www.kansei.se'+image(v['key']),'caption':v['caption'],'creator':person,'width':1280,'height':960,'inLanguage':'sv','creditText':'Carl-Robert Kårell / Kansei'} for v in VIEWS]
    return '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False,separators=(',',':'))+'</script>'

def build_page():
    source = (ROOT/'ultraljud/glutealsenor/bilder/index.html').read_text()
    source = re.sub(r'<title>.*?</title>', '<title>'+TITLE+'</title>', source, count=1, flags=re.S)
    source = source.replace('https://www.kansei.se/ultraljud/glutealsenor/bilder/',URL)
    source = re.sub(r'<script\b[^>]*type="application/ld\+json"[^>]*>.*?</script>','',source,flags=re.S)
    source = source.replace('</head>',schema()+'<link href="/assets/hip-joint-case.20261021.css" rel="stylesheet"/></head>',1)
    def metadata(match):
        tag = match[0]
        key = re.search(r'(?:name|property)="([^"]+)"',tag)
        values = {'description':DESCRIPTION,'og:description':DESCRIPTION,'twitter:description':DESCRIPTION,'og:title':TITLE,'twitter:title':TITLE,'og:image':'https://www.kansei.se'+image('kapsel'),'twitter:image':'https://www.kansei.se'+image('kapsel')}
        if key and key[1] in values:
            tag = re.sub(r'content="[^"]*"',lambda _: 'content="'+esc(values[key[1]])+'"',tag)
        return tag
    source = re.sub(r'<meta\b[^>]*>',metadata,source)
    source = source.replace('knee-case hip-case','knee-case hip-case hip-joint-case')
    source = re.sub(r'<main\b.*?</main>',lambda _:main_content(),source,count=1,flags=re.S)
    out = ROOT/PATH.strip('/')/'index.html'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(source)

def package(workspace):
    out = ROOT/ASSETS.strip('/'); out.mkdir(parents=True,exist_ok=True)
    art = ROOT/'.github/kansei/artwork/hip-joint'; art.mkdir(parents=True,exist_ok=True)
    qa = workspace/'hip-joint-qa'; qa.mkdir(exist_ok=True)
    manifest = {'version':VERSION,'canvas':[1280,960],'method':'Full-frame imagegen contour correction using original scans and clinician guides as geometry anchors, retaining approved materials and gray heterogeneous recess contents. One recorded global rectangular registration per painting; no local warp. Findings retain their original scan coordinates. Original JPEGs byte-identical; acquisition header clipped by shared reader.','style_references':['bilder/ultraljud/bicepssena/langdsnitt-anatomi.webp'],'clinical_scope':'Ultrasound followed by hip-joint Sinogel injection, supplied by clinician. No demographics, symptom duration, radiographic grade or treatment outcome supplied; none invented. Comparison is between sides, not before/after. Unclassified small round feature in capsule view is not assigned a diagnosis.','views':[]}
    for v in VIEWS:
        original = workspace/'upload'/v['original']; guide = workspace/'upload'/v['guide']; painting = workspace/'generated_images'/v['painting']
        shutil.copy2(original,out/(v['key']+'.original.jpg'))
        # Asset export only: global rectangular registration, never a local warp.
        paint_target = art/(v['key']+'.painting.'+VERSION+'.webp')
        subprocess.run(['convert',str(painting),'-quality','96',str(paint_target)],check=True)
        left,top,right,bottom = v['scan']
        encoded = base64.b64encode(painting.read_bytes()).decode()
        paint_width,paint_height = map(int,subprocess.check_output(['identify','-format','%w %h',str(painting)]).split())
        sl,st,sr,sb = v['source_scan']
        placed = f'<svg x="{left}" y="{top}" width="{right-left}" height="{bottom-top}" viewBox="{sl} {st} {sr-sl} {sb-st}" preserveAspectRatio="none" overflow="hidden"><image xlink:href="data:image/png;base64,{encoded}" x="0" y="0" width="{paint_width}" height="{paint_height}"/></svg>'
        clip = f'<defs><clipPath id="scan"><rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}"/></clipPath></defs>'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1280" height="960" viewBox="0 0 1280 960">{clip}<g clip-path="url(#scan)">{placed}</g></svg>'
        svgfile = qa/(v['key']+'.svg'); svgfile.write_text(svg)
        png = qa/(v['key']+'.png')
        subprocess.run(['inkscape','--batch-process',str(svgfile),'--export-type=png','--export-filename='+str(png)],check=True,capture_output=True)
        target = out/(v['key']+'.anatomi.'+VERSION+'.webp')
        subprocess.run(['convert',str(png),'-quality','94',str(target)],check=True)
        sha = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        manifest['views'].append({'key':v['key'],'original':str((out/(v['key']+'.original.jpg')).relative_to(ROOT)),'original_sha256':sha(original),'clinician_guide_uploaded_name':v['guide'],'guide_sha256':sha(guide),'painting':str(paint_target.relative_to(ROOT)),'painting_sha256':sha(paint_target),'source_registration_bounds':v['source_scan'],'target_scan_bounds':v['scan'],'anatomy':str(target.relative_to(ROOT)),'anatomy_sha256':sha(target)})
    (art/('whole-paintings.'+VERSION+'.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    build_page()
    print(json.dumps({'page':PATH,'views':len(VIEWS),'originals_byte_identical':True,'qa':str(qa)},ensure_ascii=False))

if __name__=='__main__':
    package(Path(sys.argv[1]))
