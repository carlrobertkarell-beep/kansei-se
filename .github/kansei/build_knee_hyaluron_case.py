"""Build the approved knee case inside the existing patient-case collection.

The case itself is the video's watch page; no extra case index or film page is
created. Clinical text and tissue illustrations were approved by the clinician.
"""
from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parents[2]
PATH = '/ultraljud/kna/artros-ledband-hyaluron/'
ORIGIN = 'https://www.kansei.se'
URL = ORIGIN + PATH
ASSETS = '/bilder/ultraljud/kna/artros-ledband/'
TITLE = 'Knäsmärta trots kortison – artros och ledbandsskada | Kansei'
DESCRIPTION = 'Följ ett patientfall med långvarig knäsmärta trots kortison. Se ultraljud, anatomilager, skada i inre ledbandet och en ultraljudsvägledd hyaluroninjektion.'
HEADER = ' data-scan-header="68/960" style="--scan-header:7.0833333%"'
AUTHOR = {'@id': ORIGIN + '/team/carl-robert-karell/#person'}

INTRO = 'En kvinna med långvarig knäsmärta sökte Kansei för en ny bedömning. Hon hade tidigare fått kortisoninjektioner, men smärtan kvarstod.'
RECOGNITION = 'När knät gör ont under lång tid kan vanliga saker som att promenera, gå i trappor eller resa sig från en stol börja kännas besvärliga. Det kan också bli svårt att veta hur mycket man vågar belasta knät och vad nästa steg ska vara när tidigare behandling inte har hjälpt. Vid besöket undersöktes därför både leden och vävnaderna runt omkring med ultraljud, för att bedöma vilka förändringar som kunde bidra till besvären och vad den fortsatta behandlingen behövde ta hänsyn till.'
FINDINGS = 'Ultraljudsundersökningen visade artrosrelaterade förändringar i brosket och benets ledyta. Bilderna visade också en skada i ledbandet på knäts insida. På den påverkade sidan var ledbandet uttänjt, med bristningar i delar av vävnaden. Skillnaden mot den friska sidan framgår i jämförelsebilderna.'
MEANING = 'Fynden behövde därför vägas samman: både förändringarna i leden och ledbandsskadan var relevanta för den fortsatta planeringen. Anatomibilderna hjälper till att förklara var strukturerna ligger och vilka områden som är påverkade.'
TREATMENT = 'Efter samlad bedömning genomfördes en ultraljudsvägledd hyaluroninjektion med Sinovial i knäleden. Nålen fördes in från knäts utsida. Ultraljudet användes för att följa nålens läge och skilja utrymmet inne i leden från omgivande vävnader.'
PLAN = 'Syftet med injektionen var att lindra de ledrelaterade besvären. Ledbandsskadan behöver samtidigt tas med i en anpassad plan för belastning och rehabilitering. Träning och uppföljning är fortsatt viktiga, och injektionens effekt behöver utvärderas över tid.'

VIEWS = [
    dict(key='left', name='Vänster knä', sub='Brosk och sena',
         caption='I vänster knä framträder ett mer sammanhängande broskband i det avbildade området. Anatomibilden skiljer på hud, underhudsfett, sena, brosk och ben.',
         labels='<path d="M580 145 L500 125"/><text x="590" y="159">Hud</text><path d="M410 214 L570 214"/><text x="190" y="225">Underhudsfett</text><path d="M690 345 L600 410"/><text x="705" y="342">Sena</text><path d="M300 650 L565 585"/><text x="175" y="665">Brosk</text>',
         finding='<path class="pointer-shadow" d="M285 650 L555 575"/><path class="pointer" d="M285 650 L555 575"/><circle cx="555" cy="575" r="7"/><text x="285" y="696">Broskband</text>'),
    dict(key='right', name='Höger knä', sub='Förändrad ledyta',
         caption='Höger knä visar en mer oregelbunden brosk- och benkontur i det visade området. Markeringen visar den lokala förändringen.',
         labels='<path d="M410 175 L600 115"/><text x="250" y="175">Hud</text><path d="M490 220 L660 220"/><text x="250" y="240">Underhudsfett</text><path d="M760 360 L900 365"/><text x="660" y="370">Sena</text><path d="M390 625 L704 483"/><text x="190" y="647">Påverkat brosk</text>',
         finding='<path class="pointer-shadow" d="M390 625 L704 483"/><path class="pointer" d="M390 625 L704 483"/><circle cx="704" cy="483" r="7"/><text x="290" y="680">Ojämn ledyta</text>'),
    dict(key='medial', name='Inre ledbandet', sub='Frisk och påverkad sida',
         caption='Till vänster visas den friska sidan. Till höger är det inre ledbandet uttänjt, med bristningar i delar av vävnaden. Menisken ligger under ledbandet mellan ledkanterna.',
         labels='<path d="M360 217 L430 186"/><text x="135" y="230">Underhudsfett</text><path d="M755 190 L830 120"/><text x="660" y="190">Hud</text><path d="M420 565 L405 415"/><text x="330" y="610">Menisk</text><path d="M855 545 L900 300"/><text x="700" y="600">Inre ledbandet</text><text x="350" y="745">Frisk sida</text><text x="925" y="745">Påverkad sida</text>',
         finding='<path class="pointer-shadow" d="M880 565 L900 300 M1070 510 L1105 306"/><path class="pointer" d="M880 565 L900 300 M1070 510 L1105 306"/><circle cx="900" cy="300" r="7"/><circle cx="1105" cy="306" r="7"/><text x="825" y="620">Uttänjt ledband</text><text x="1090" y="555">Bristningar</text><text x="350" y="745">Frisk sida</text><text x="925" y="745">Påverkad sida</text>'),
]


def esc(value):
    return html.escape(value, quote=True)


def panel(view, index):
    key = view['key']
    return f'''<article class="knee-panel" data-key="{key}" id="view-{key}" role="tabpanel" aria-labelledby="tab-{key}" tabindex="0"{' hidden' if index else ''}><figure><div class="knee-picture" data-anatomy="false" data-findings="false"><img class="knee-original" src="{ASSETS}{key}.original.jpg" width="1280" height="960" alt="{esc(view['caption'])}" decoding="async"{HEADER}/><div class="knee-anatomy" aria-hidden="true"><div class="knee-anatomy-content"><img src="{ASSETS}{key}.anatomi.20261027.webp" width="1280" height="960" alt="Anatomisk illustration av {esc(view['name'].lower())}, i samma bildsnitt." decoding="async" loading="eager"{HEADER}/><svg class="knee-labels" viewBox="0 0 1280 960" aria-hidden="true">{view['labels']}</svg></div></div><svg class="knee-findings" viewBox="0 0 1280 960" aria-hidden="true">{view['finding']}</svg></div><figcaption>{esc(view['caption'])}</figcaption></figure></article>'''


def schema():
    graph = [
        {'@type':'MedicalWebPage','@id':URL+'#webpage','url':URL,'name':TITLE,'description':DESCRIPTION,'inLanguage':'sv-SE','datePublished':'2026-10-27','dateModified':'2026-10-27','author':AUTHOR,'publisher':{'@id':ORIGIN+'/#clinic'},'isPartOf':{'@id':ORIGIN+'/ultraljud/bilder/#webpage'},'breadcrumb':{'@id':URL+'#breadcrumb'},'mainEntity':{'@id':URL+'#video'},'about':[{'@type':'MedicalCondition','name':'Knäartros'},{'@type':'MedicalCondition','name':'Skada i knäts inre ledband'}]},
        {'@type':'Person',**AUTHOR,'name':'Carl-Robert Kårell','jobTitle':'Legitimerad naprapat','url':ORIGIN+'/team/carl-robert-karell/'},
        {'@type':'BreadcrumbList','@id':URL+'#breadcrumb','itemListElement':[{'@type':'ListItem','position':i,'name':name,'item':url} for i,(name,url) in enumerate([('Kansei',ORIGIN+'/'),('Patientfall',ORIGIN+'/ultraljud/bilder/'),('Knäartros och ledbandsskada',URL)],1)]},
        {'@type':'VideoObject','@id':URL+'#video','url':URL,'mainEntityOfPage':{'@id':URL+'#webpage'},'name':'Långvarig knäsmärta – ultraljud, anatomibilder och hyaluroninjektion','description':'Patientfall med broskförändringar och skada i det inre ledbandet. Originalultraljud och anatomiska illustrationer följs av en ultraljudsvägledd hyaluroninjektion med Sinovial.','thumbnailUrl':ORIGIN+ASSETS+'film-poster.jpg','contentUrl':ORIGIN+ASSETS+'knaartros-hyaluron.mp4','uploadDate':'2026-10-27','duration':'PT1M28S','inLanguage':'sv-SE','creator':AUTHOR},
    ]
    graph += [{'@type':'ImageObject','@id':URL+'#bild-'+v['key'],'contentUrl':ORIGIN+ASSETS+v['key']+'.original.jpg','caption':v['caption'],'creator':AUTHOR,'width':1280,'height':960,'creditText':'Carl-Robert Kårell / Kansei'} for v in VIEWS]
    return '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False,separators=(',',':'))+'</script>'


def build():
    source = (ROOT/'ultraljud/kna/forkalkad-menisk/index.html').read_text()
    old_url = ORIGIN+'/ultraljud/kna/forkalkad-menisk/'
    source = source.replace(old_url, URL)
    source = re.sub(r'<title>.*?</title>','<title>'+TITLE+'</title>',source,flags=re.S,count=1)
    def metadata(match):
        tag = match[0]
        for needle,value in [('name="description"',DESCRIPTION),('property="og:description"',DESCRIPTION),('property="og:title"',TITLE),('property="og:image"',ORIGIN+ASSETS+'film-poster.jpg')]:
            if needle in tag:
                return re.sub(r'content="[^"]*"','content="'+esc(value)+'"',tag)
        return tag
    source = re.sub(r'<meta\b[^>]*>',metadata,source)
    source = re.sub(r'<script\b[^>]*type="application/ld\+json"[^>]*>.*?</script>',lambda _:schema(),source,flags=re.S)
    source = source.replace(' knee-calc-case',' knee-hyaluron-case')
    source = re.sub(r'<link[^>]*href="/assets/knee-calc-case\.[^"]*"[^>]*>','',source)
    source = source.replace('</head>','<link rel="stylesheet" href="/assets/video-watch.20261027.css"><link rel="stylesheet" href="/assets/knee-hyaluron-case.20261027.css"></head>')
    tabs = ''.join(f'<button class="knee-tab" role="tab" id="tab-{v["key"]}" aria-controls="view-{v["key"]}" aria-selected="{str(i==0).lower()}" tabindex="{0 if i==0 else -1}" type="button"><img src="{ASSETS}{v["key"]}.original.jpg" alt="" width="96" height="72"{HEADER}/><span><strong>{v["name"]}</strong><small>{v["sub"]}</small></span></button>' for i,v in enumerate(VIEWS))
    # Reuse the established keyboard-accessible reader and its zoom dialog.
    zoom = re.search(r'<dialog\b[^>]*id="knee-zoom".*?</dialog>',source,re.S)[0]
    main = f'''<main id="main" tabindex="-1" class="video-watch-page">
<div class="wrap watch-intro"><nav class="crumbs" aria-label="Brödsmulor"><a href="/">Kansei</a> / <a href="/ultraljud/bilder/">Patientfall</a> / Knäartros och ledbandsskada</nav><p class="eyebrow">Patientfall från Kansei · Knä</p><h1>Långvarig knäsmärta – artros och skada i det inre ledbandet</h1><figure class="watch-figure" id="filmen"><video class="watch-player" controls playsinline preload="metadata" poster="{ASSETS}film-poster.jpg" aria-label="Knäsmärta, anatomibilder och ultraljudsvägledd hyaluroninjektion"><source src="{ASSETS}knaartros-hyaluron.mp4" type="video/mp4"><a href="{ASSETS}knaartros-hyaluron.mp4">Öppna filmen</a></video><figcaption>1 minut 28 sekunder. Se originalultraljud, anatomiska illustrationer och en hyaluroninjektion som ges från knäts utsida. Förklarande text i filmen.</figcaption></figure><p class="knee-case-byline">Undersökning och behandling: <a href="/team/carl-robert-karell/">Carl-Robert Kårell</a>, legitimerad naprapat · Kansei, Odenplan.</p><nav class="case-page-nav" aria-label="Sidans innehåll"><a href="#patientfall">Kvinnans besvär</a><a href="#bilder">Bilder och anatomi</a><a href="#behandlingen">Vad vi gjorde</a><a href="#nasta-steg">Fortsatt plan</a></nav></div>
<section class="section" id="patientfall"><div class="wrap case-context-summary"><p class="eyebrow">Besvären och undersökningen</p><h2>När knäsmärtan blir kvar</h2><p>{INTRO}</p><p>{RECOGNITION}</p></div></section>
<section class="section" id="bilder"><div class="wrap"><div class="viewer-head"><p class="eyebrow">Vad vi såg</p><h2>Brosket, ledytan och det inre ledbandet</h2><p>{FINDINGS}</p><p>{MEANING}</p><p>Välj en bild. Slå på <strong>Anatomi</strong> för att följa vävnaderna och <strong>Visa fynden</strong> för att se de utpekade områdena. Hud, underhudsfett och sena visas som skilda vävnader.</p></div><div class="knee-viewer" data-knee-viewer><div class="knee-tabs" role="tablist" aria-label="Välj bild av knät">{tabs}</div><div class="knee-controls"><button class="knee-toggle" type="button" role="switch" aria-checked="false" data-knee-anatomy><span class="knee-switch" aria-hidden="true"></span>Anatomi</button><button class="knee-toggle" type="button" role="switch" aria-checked="false" data-knee-findings><span class="knee-switch" aria-hidden="true"></span><span data-knee-findings-label>Visa fynden</span></button><button class="knee-enlarge" type="button" aria-haspopup="dialog" data-knee-enlarge>Förstora bilden</button><span class="knee-state" role="status" aria-live="polite">Vänster knä · ultraljudsbild</span></div>{''.join(panel(v,i) for i,v in enumerate(VIEWS))}<p class="knee-small">Originalultraljud från Kansei. Anatomibilderna är pedagogiska illustrationer av undersökarens bildmaterial. Sidjämförelsen visar ingen behandlingseffekt.</p></div></div></section>
<section class="section" id="behandlingen"><div class="wrap case-context-summary"><p class="eyebrow">Vad vi gjorde</p><h2>Hyaluron i knäleden – in från utsidan</h2><p>{TREATMENT}</p><p>På sidan om <a href="/hyaluronsyra/kna/">hyaluroninjektion i knäleden</a> finns information om möjliga effekter, risker, forskningsläget och alternativ.</p></div></section>
<section class="section" id="nasta-steg"><div class="wrap case-context-summary"><p class="eyebrow">Belastning, träning och uppföljning</p><h2>En plan för hela knät</h2><p>{PLAN}</p><div class="case-context-links"><a href="/ultraljud/kna/">Om ultraljud av knä →</a><a href="/hyaluronsyra/kna/">Hyaluron i knä: information och bokning →</a><a href="/rehabilitering/">Om rehabilitering →</a></div></div></section>
<section class="section" id="kallor"><div class="wrap case-context-summary"><h2>Om patientfallet</h2><p>Undersökning och behandling: Carl-Robert Kårell, legitimerad naprapat, Kansei Naprapati &amp; Rehabcenter. Inget behandlingsresultat tillskrivs patienten; effekten behöver följas upp.</p><p>Publicerat <time datetime="2026-10-27">27 oktober 2026</time>. <a href="/bildinformation/">Bildkälla och återanvändning →</a></p></div></section>
<nav class="atlas-case-bottom wrap" aria-label="Fler patientfall"><a href="/ultraljud/bilder/?omrade=kna#exempel">← Fler patientfall om knä</a><a href="/ultraljud/bilder/">Alla patientfall →</a></nav>
</main>'''
    source = re.sub(r'<main\b[^>]*>.*?</main>',lambda _:main,source,count=1,flags=re.S)
    # The template keeps its zoom dialog outside main; do not duplicate it.
    assert source.count('id="knee-zoom"') == 1
    target = ROOT/PATH.strip('/')/'index.html'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(source)
    return target


if __name__ == '__main__':
    print(build())
