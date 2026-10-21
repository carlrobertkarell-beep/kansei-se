"""Package continuous hip paintings and the clinician-supplied case.

Clinical originals stay byte-identical. Only the acquisition header is hidden
by the existing presentation CSS. Paintings receive one global placement each;
there is no internal deformation, repeated material tile, or diagnostic edit.
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
VERSION = '20261021'
PATH = '/ultraljud/glutealsenor/bilder/'
URL = 'https://www.kansei.se' + PATH
ASSETS = '/bilder/ultraljud/hoft/'
BOOK = 'https://www.bokadirekt.se/boka-tjanst/kansei-rehabcenter-48847/ultraljud-rorelseapparaten-1946824'
TITLE = 'Ont på höftens utsida – ultraljudscase | Kansei Stockholm'
DESCRIPTION = 'Långvarig smärta på höftens utsida trots röntgen utan påvisad artros? Följ ett patientfall med gluteal tendinos, paralabral cysta och individuellt behandlingsval.'
HEADER = ' data-scan-header="68/960" style="--scan-header:7.0833333%"'

VIEWS = [
    dict(key='gmed', name='Gluteus medius', sub='Mer uttalad tendinos', original='Gmed utan anno.jpg', guide='Gmed anno.jpg',
         painting='exec-d97b3e9f-3dbf-4981-a5de-6e08aca69dce.png', bounds=[174,80,1276,1009],
         alt='Längdsnitt av höger gluteus medius med mer uttalade tendinotiska förändringar enligt undersökarens bedömning.',
         caption='Höger höfts utsida, längdsnitt. Gluteus medius bedömdes vara mer tendinotisk än gluteus minimus i de utvalda vyerna.',
         heading='Gluteus medius – mer uttalad förändring i senstrukturen',
         cue='Följ gluteus medius-senan fram till infästningen på trochanter major. Visa fynden avgränsar senområdet som bedömdes som tendinotiskt.',
         text='Gluteus medius är en av musklerna som hjälper till att föra benet utåt och stabilisera bäckenet. I detta fall bedömde undersökaren senan som tendinotisk. Bildfyndet vägs samman med smärtans läge, belastningen och höftens funktion.',
         labels=[(610,225,'Fettvävnad','dark-label'),(625,354,'Iliotibialband','dark-label'),(620,470,'Muskulatur',''),(735,715,'Gluteus medius','dark-label'),(355,758,'Trochanter major','')],
         finding='<path class="finding-region" d="M304 557 C310 533 365 518 420 521 C620 529 845 577 1104 666 L1104 869 C909 882 759 862 652 808 C565 755 539 688 505 660 C457 624 401 615 351 625 C315 634 287 601 304 557 Z"/><path class="pointer-shadow" d="M785 804 L754 697"/><path class="pointer" d="M785 804 L754 697"/><circle cx="754" cy="697" r="5"/><text x="843" y="846">Tendinotiskt senområde</text>'),
    dict(key='gmin', name='Gluteus minimus', sub='Lätt tendinos', original='Gmin annoteirngar.jpg', guide='Gmin utan annoteringar.jpg',
         painting='exec-2e4f903f-5318-4042-adaf-9b03ae366fea.png', bounds=[143,91,1305,1019],
         alt='Längdsnitt av höger gluteus minimus med lätt tendinotisk senstruktur enligt undersökarens bedömning.',
         caption='Höger höfts utsida, längdsnitt. Gluteus minimus bedömdes ha lätt tendinotiska förändringar. Det är en annan sena än gluteus medius.',
         heading='Gluteus minimus – lättare tendinotiska förändringar',
         cue='Identifiera gluteus minimus-senan under muskellagret och följ den mot den ljusa benkonturen. Det markerade området visar senan som bedömdes ha lätt tendinos.',
         text='Gluteus minimus ligger djupare och fäster också på lårbenets stora trokanter. I den här vyn beskrivs mindre uttalade senförändringar än i gluteus medius-vyn. Vyerna visar olika senor och snitt; de är inte en före- och efterjämförelse eller en mätning av skadans storlek.',
         labels=[(610,250,'Fettvävnad','dark-label'),(660,417,'Iliotibialband','dark-label'),(435,492,'Muskulatur',''),(620,610,'Gluteus minimus','dark-label'),(835,755,'Trochanter major','')],
         finding='<path class="finding-region" d="M175 584 C316 584 435 555 532 545 C709 542 917 562 1103 574 L1103 616 C938 641 745 656 570 659 C523 663 506 683 486 719 C415 803 292 869 175 883 Z"/><path class="pointer-shadow" d="M321 773 L390 655"/><path class="pointer" d="M321 773 L390 655"/><circle cx="390" cy="655" r="5"/><text x="340" y="815">Lätt tendinos</text>'),
    dict(key='paralabral', name='Främre labrum', sub='Paralabral cysta', original='Labrumcysta ej anno.jpg', guide='Labrumcysta anno.jpg',
         painting='exec-d2140346-bd71-4306-b385-673c61388305.png', bounds=[157,103,1298,1019],
         alt='Längdsnitt framtill i höger höft med ett cystiskt område vid främre labrum, bedömt som paralabral cysta av undersökaren.',
         caption='Höger höftled framtill, längdsnitt. Det cystiska området vid labrum bedömdes som en paralabral cysta. Vyn visar ett annat område än glutealsenorna på höftens utsida.',
         heading='Ett separat fynd framtill vid höftledens labrum',
         cue='Det mörka, oregelbundet formade området ligger vid främre labrum, under ledkapseln. Växla till anatomi för att skilja vätskan från labrum och de närliggande benytorna.',
         text='Labrum är en ring av fiberbrosk vid höftledens ledskål. En paralabral cysta är en vätskefylld förändring intill labrum. Sådana cystor kan förekomma tillsammans med labrumskador, men bilden fastställer inte i sig en labrumruptur eller att cystan förklarar patientens laterala smärta.',
         labels=[(640,204,'Fettvävnad','dark-label'),(650,374,'Iliopsoas',''),(803,552,'Ledkapsel','dark-label'),(656,677,'Labrum','dark-label'),(969,683,'Cystiskt område',''),(363,823,'Acetabulum',''),(935,842,'Lårbenshuvud','')],
         finding='<path class="cyst-region" d="M385 685 C407 653 451 626 492 607 C559 574 644 561 707 561 C739 561 760 580 774 600 C799 598 833 592 850 602 C869 611 868 626 889 629 C958 624 1036 636 1105 658 M1105 700 C1021 707 956 723 890 737 C791 758 708 785 658 816"/><path class="pointer-shadow" d="M1001 544 L1007 668"/><path class="pointer" d="M1001 544 L1007 668"/><circle cx="1007" cy="668" r="5"/><text x="930" y="514">Paralabral cysta</text>')
]

def esc(s):
    return html.escape(str(s), quote=True)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def image(key):
    return ASSETS + key + '.original.jpg'

def anatomy(key):
    return ASSETS + key + '.anatomi.' + VERSION + '.webp'

def panel(v, index):
    key = v['key']
    labels = ''.join(f'<text x="{x}" y="{y}" class="{css}">{esc(text)}</text>' for x,y,text,css in v['labels'])
    return f'''<article class="knee-panel" data-key="{key}" id="view-{key}" role="tabpanel" aria-labelledby="tab-{key}" tabindex="0"{' hidden' if index else ''}><figure><div class="knee-picture" data-anatomy="false" data-findings="false"><img class="knee-original" src="{image(key)}" width="1280" height="960" alt="{esc(v['alt'])}" decoding="async"{HEADER}/><div class="knee-anatomy" aria-hidden="true"><div class="knee-anatomy-content"><img src="{anatomy(key)}" width="1280" height="960" alt="Pedagogisk anatomisk illustration av {esc(v['name'].lower())} och omgivande vävnader i samma längdsnitt." decoding="async" loading="eager"/><svg class="knee-labels" viewBox="0 0 1280 960" aria-hidden="true">{labels}</svg></div></div><svg class="knee-findings" viewBox="0 0 1280 960" aria-hidden="true">{v['finding']}</svg></div><figcaption>{esc(v['caption'])}</figcaption></figure><div class="knee-panel-copy"><h3>{esc(v['heading'])}</h3><p class="knee-cue"><strong>Titta efter:</strong> {esc(v['cue'])}</p><p>{esc(v['text'])}</p></div></article>'''

def view_link(key, text):
    return f'<a class="text-link" href="#bilder" data-case-view data-case-tab="tab-{key}" data-case-findings="true">{esc(text)} →</a>'

def main_content():
    tabs = ''.join(f'<button class="knee-tab" role="tab" id="tab-{v["key"]}" aria-controls="view-{v["key"]}" aria-selected="{str(i==0).lower()}" tabindex="{0 if i==0 else -1}" type="button"><img src="{image(v["key"])}" alt="" width="96" height="72"{HEADER}/><span><strong>{v["name"]}</strong><small>{v["sub"]}</small></span></button>' for i,v in enumerate(VIEWS))
    panels = ''.join(panel(v,i) for i,v in enumerate(VIEWS))
    return f'''<main id="main" tabindex="-1">
<section class="condition-hero"><div class="wrap"><p class="crumbs"><a href="/">Kansei</a> / <a href="/ultraljud/">Ultraljud</a> / <a href="/ultraljud/glutealsenor/">Höftens utsida</a> / Patientfall</p><span class="eyebrow">Patientfall från Kansei · höger höft</span><h1>Ont på höftens utsida i flera år?</h1><p class="lead">Röntgen hade enligt patienten inte visat någon artros. Vid injektionskonsultationen undersöktes höftens utsida och den främre delen av höftleden med ultraljud. Här följer du fynden och varför naprapatisk vård blev första steget.</p><p>Undersökning och klinisk bedömning: <a href="/team/carl-robert-karell/">Carl-Robert Kårell, legitimerad naprapat</a> · Kansei, Odenplan i Stockholm.</p></div></section>
<nav class="case-page-nav" aria-label="Sidans innehåll"><div class="wrap"><a href="#bilder">Bilder och anatomi</a><a href="#patientfall">Patientens berättelse</a><a href="#nasta-steg">Bedömning och plan</a><a href="#faq">Frågor och svar</a></div></nav>
<section class="us-case-guide case-context-summary" id="igenkanning" data-case-context="summary" aria-labelledby="igenkanning-title" data-reading-section data-reading-title="Känner du igen besvären?"><div class="wrap"><div class="case-context-columns"><div><span class="eyebrow">Känner du igen besvären?</span><h2 id="igenkanning-title">Smärta som har funnits länge, men inget artrosfynd på röntgen.</h2><p>Kvinnan i detta fall hade haft ont på höftens utsida i många år. Antiinflammatorisk medicinering hjälpte måttligt. Hon sökte för att diskutera injektionsbehandling, men undersökningen gav anledning att först arbeta med höftens funktion och belastning.</p><ul class="case-context-goals" aria-label="Det patienten sökte för"><li>Långvarig smärta på höftens utsida</li><li>Röntgen utan påvisad artros enligt patienten</li><li>Måttlig lindring av antiinflammatorisk medicin</li></ul></div><aside class="case-context-question"><p class="case-context-kind">Anonymiserat patientfall från Kansei</p><h3>Frågan vi ville besvara</h3><p>Hur såg glutealsenorna och de åtkomliga delarna av höften ut, och vilken behandling var rimlig att börja med?</p><div class="case-context-links"><a href="#patientfall">Följ patientfallet →</a><a href="#bilder">Se bilder och fynd →</a></div></aside></div></div></section>
<section class="section" id="bilder" data-reading-section data-reading-title="Bilder och anatomi"><div class="wrap"><div class="viewer-head"><p class="eyebrow">Tre utvalda längdsnitt</p><h2>Två glutealsenor och ett separat fynd framtill i höften.</h2><p>Välj bild. Slå på <strong>Anatomi</strong> för att känna igen vävnaderna och <strong>Visa fynden</strong> för att se det utpekade området. Du kan förstora varje bild.</p></div><div class="atlas-reading-guide" aria-label="Så utforskar du bilden"><span><b>1</b> Se originalbilden</span><span><b>2</b> Slå på <strong>Anatomi</strong></span><span><b>3</b> Välj <strong>Visa fynden</strong></span></div><div class="knee-viewer" data-knee-viewer><div class="knee-tabs" role="tablist" aria-label="Välj höftbild">{tabs}</div><div class="knee-controls"><button class="knee-toggle" type="button" role="switch" aria-checked="false" data-knee-anatomy><span class="knee-switch" aria-hidden="true"></span>Anatomi</button><button class="knee-toggle" type="button" role="switch" aria-checked="false" data-knee-findings><span class="knee-switch" aria-hidden="true"></span><span data-knee-findings-label>Visa fynden</span></button><button class="knee-enlarge" type="button" aria-haspopup="dialog" data-knee-enlarge>Förstora bilden</button><span class="knee-state" role="status" aria-live="polite">Gluteus medius · ultraljudsbild</span></div>{panels}<p class="knee-example-note knee-small">Tre längdsnitt från samma patients undersökning. Anatomilagren är pedagogiska illustrationer; färger, vävnadsteckning och benets inre är förklarande. Markeringarna visar undersökarens utpekade områden, inte exakta mått på senförändringarnas utbredning. Vyerna kartlägger inte hela senorna eller labrum.</p><noscript><style>.hip-case .knee-panel[hidden]{{display:block;margin-top:40px}}.hip-case .knee-controls,.hip-case .knee-tabs{{display:none}}</style><p>Alla tre originalbilder visas här. Aktivera JavaScript för anatomi och fyndmarkeringar.</p></noscript></div></div></section>
<section class="section" id="patientfall" data-reading-section data-reading-title="Patientens berättelse"><div class="wrap"><span class="eyebrow">Bakgrund och undersökning</span><h2>Hon sökte för en injektionskonsultation.</h2><div class="hip-case-story"><div><p>Patienten hade haft smärta på höger höfts utsida under många år. Hon uppgav att tidigare slätröntgen inte hade visat någon artros. Antiinflammatorisk medicinering gav endast måttlig lindring.</p><p>Vid konsultationen användes ultraljud som komplement till den kliniska bedömningen. Gluteus minimus bedömdes vara lätt tendinotisk och gluteus medius mer uttalat tendinotisk. Framtill vid höftledens labrum sågs dessutom en cystisk förändring som bedömdes vara en paralabral cysta.</p><div class="hip-next-links">{view_link('gmed','Se gluteus medius')}{view_link('gmin','Se gluteus minimus')}{view_link('paralabral','Se cystfyndet')}</div><div class="hip-case-note"><h3>Fynden behövde sättas i sitt sammanhang.</h3><p>Smärtan var framför allt lokaliserad till höftens utsida. Cystfyndet låg framtill vid leden. Det bedömdes därför separat och beskrevs inte som en säker förklaring till den laterala smärtan.</p></div></div><figure><img src="{image('gmed')}" alt="Patientens gluteus medius i längdsnitt på ultraljud." width="1280" height="960" loading="lazy" decoding="async"{HEADER}/><figcaption>Patientens egen undersökningsbild. I bildvisaren kan du lägga till anatomi och fyndmarkeringar.</figcaption></figure></div></div></section>
<section class="us-case-guide case-context-decision" id="nasta-steg" data-case-context="decision" aria-labelledby="case-key-title" data-reading-section data-reading-title="Bedömning och plan"><div class="wrap"><div class="case-context-key" id="klinisk-nyckel"><span class="eyebrow">Det viktiga i just det här fallet</span><h2 id="case-key-title">Första steget blev att arbeta med höftens funktion.</h2><p>Den samlade bedömningen talade för belastningsrelaterade besvär kring höftens utsida, med tendinotiska förändringar i glutealsenorna. Valet föll på att först inleda naprapatisk vård med fokus på patientens funktionella förutsättningar.</p><p>Att patienten sökte för en injektionskonsultation innebar alltså inte att en injektion blev första åtgärden. Den fortsatta vården behövde anpassas efter symtom, belastning och funktion tillsammans med bildfynden.</p><p class="case-context-follow"><strong>Fortsatt plan:</strong> Arbeta med höftens funktion och anpassa belastningen. Därefter kan behovet av ytterligare bedömning eller behandling omprövas. Något senare behandlingsresultat redovisas inte i detta fall.</p><div class="case-context-links">{view_link('gmed','Till senbilden och fynden')}</div></div><h3>Vilket besök passar ditt besvär?</h3><div class="case-context-care" data-care-count="2"><article><h3>Funktion, behandling och rehabilitering</h3><p>Vid ett naprapatbesök undersöks höftens rörelse, belastning och funktion. Planen kan omfatta behandling, råd och individuellt anpassad träning.</p><a href="/naprapati/">Läs om naprapati och boka besök →</a></article><article><h3>En riktad fråga om senor eller mjukdelar</h3><p>Vid långvariga besvär och en särskild frågeställning kan ultraljud bidra med information om åtkomliga senor och mjukdelar.</p><a href="{BOOK}" target="_blank" rel="noopener noreferrer" data-measure="booking_click" data-service="ultrasound" data-placement="hip-case">Boka ultraljud vid Odenplan →</a></article></div><div class="hip-case-note"><h3>Var kommer PRP och hyaluron in?</h3><p>Den här patienten fick i första hand en plan för naprapatisk vård. Tendinos eller ett cystfynd innebär inte i sig att PRP eller hyaluron behövs. Forskningsläget för PRP vid gluteal tendinopati är osäkert, och cystfyndet är inte i sig en indikation för hyaluron.</p><p><a href="/injektioner/">Läs om injektionskonsultation och behandlingsval →</a></p></div><h3>Jämför med andra undersökningsfall</h3><div class="case-context-related"><article><a href="/ultraljud/halsena/bilder/">Långvariga besvär från hälsenan →</a><p>Se ett annat senområde och hur strukturförändringar kopplas till belastning.</p></article><article><a href="/ultraljud/kna/#artros">Knäartros med svullnad →</a><p>Jämför med ett fall där tidigare röntgen hade visat artros.</p></article></div><div class="case-context-links"><a href="/ultraljud/bilder/">Alla bildfall →</a><a href="/ultraljud/glutealsenor/">Om undersökning av glutealsenorna →</a></div></div></section>
<section class="section" id="faq" data-reading-section data-reading-title="Frågor och svar"><div class="wrap"><span class="eyebrow">Om fynden och behandlingsvalet</span><h2>Frågor som patientfallet väcker.</h2><div class="knee-faq"><details><summary>Kan man ha ont i höften utan att röntgen visar artros?</summary><p>Ja. Smärta på höftens utsida kan bland annat beröra glutealsenor och närliggande mjukdelar. Slätröntgen och ultraljud besvarar olika frågor. Att röntgen inte visar artros utesluter inte alla orsaker till höftsmärta.</p></details><details><summary>Är tendinos samma sak som en senruptur?</summary><p>Nej. Tendinos beskriver en förändrad senstruktur. I detta fall beskrev undersökaren tendinotiska förändringar i gluteus minimus och medius; någon senruptur anges inte i fallunderlaget.</p></details><details><summary>Förklarar en paralabral cysta alltid smärtan?</summary><p>Nej. Cystor kan förekomma även utan symtom och kan vara förknippade med labrumförändringar. Fyndets betydelse bedöms tillsammans med smärtans läge och den kliniska undersökningen. De här längdsnitten visar inte hela labrum. Om en kvarstående fråga om labrum eller leden påverkar fortsatt handläggning kan annan bilddiagnostik, exempelvis MR, behövas.</p></details><details><summary>Varför blev det naprapatisk vård efter en injektionskonsultation?</summary><p>I just detta fall valdes först vård med fokus på höftens funktion och belastning. Behandlingsvalet grundades på den samlade bedömningen; ultraljudsfynden var en del av underlaget.</p></details></div></div></section>
<section class="section" id="kallor" data-reading-section data-reading-title="Bildkälla och medicinska källor"><div class="wrap sources"><h2>Bildkälla och vidare läsning.</h2><p>Falluppgifter, ultraljudsbilder, annoteringar och klinisk bedömning: <a href="/team/carl-robert-karell/">Carl-Robert Kårell, legitimerad naprapat</a>, Kansei Naprapati &amp; Rehabcenter, Upplandsgatan 26 i Stockholm. Fallbeskrivningen bygger på undersökarens uppgifter. Uppgiften om röntgensvaret kommer från patienten; själva röntgenutlåtandet ingår inte i underlaget.</p><p>Anatomilagren är illustrativa och ersätter inte originalbilderna. Läs om <a href="/bildinformation/">bildmaterial och återanvändning</a>.</p><ul class="knee-source-list"><li><a href="https://www.bmj.com/content/361/bmj.k1662" target="_blank" rel="noopener noreferrer">Mellor m.fl.: utbildning och träning vid gluteal tendinopati, randomiserad studie (BMJ, 2018)</a>.</li><li><a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC7869726/" target="_blank" rel="noopener noreferrer">Chang m.fl.: ultraljud av en främre paralabral cysta i höftleden (Journal of Medical Ultrasound, 2020)</a>.</li><li><a href="https://eprints.ncl.ac.uk/303811" target="_blank" rel="noopener noreferrer">Atchia m.fl.: PRP jämfört med placebo vid trokantersmärta, randomiserad studie (JBJS, 2025)</a>.</li></ul><p class="knee-small">Publicerad och uppdaterad 21 oktober 2026.</p></div></section>
</main>'''

def schema():
    person = {'@id':'https://www.kansei.se/team/carl-robert-karell/#person'}
    graph = [
        {'@type':'MedicalWebPage','@id':URL+'#webpage','url':URL,'name':TITLE,'description':DESCRIPTION,'inLanguage':'sv','datePublished':'2026-10-21','dateModified':'2026-10-21','author':person,'publisher':{'@id':'https://www.kansei.se/#clinic'},'isPartOf':{'@id':'https://www.kansei.se/#website'},'breadcrumb':{'@id':URL+'#breadcrumb'},'mainEntity':{'@id':URL+'#case'},'primaryImageOfPage':{'@id':URL+'#gmed'}},
        {'@type':'Article','@id':URL+'#case','headline':'Ont på höftens utsida i flera år?','description':DESCRIPTION,'inLanguage':'sv','datePublished':'2026-10-21','dateModified':'2026-10-21','author':person,'mainEntityOfPage':{'@id':URL+'#webpage'},'image':[{'@id':URL+'#'+v['key']} for v in VIEWS]},
        {'@type':'BreadcrumbList','@id':URL+'#breadcrumb','itemListElement':[{'@type':'ListItem','position':i+1,'name':n,'item':u} for i,(n,u) in enumerate([('Kansei','https://www.kansei.se/'),('Ultraljud','https://www.kansei.se/ultraljud/'),('Glutealsenor','https://www.kansei.se/ultraljud/glutealsenor/'),('Patientfall',URL)])]},
        {'@type':'Person','@id':person['@id'],'name':'Carl-Robert Kårell','jobTitle':'Legitimerad naprapat','url':'https://www.kansei.se/team/carl-robert-karell/'}
    ]
    graph.extend({'@type':'ImageObject','@id':URL+'#'+v['key'],'contentUrl':'https://www.kansei.se'+image(v['key']),'caption':v['caption'],'creator':person,'width':1280,'height':960,'inLanguage':'sv','creditText':'Carl-Robert Kårell / Kansei'} for v in VIEWS)
    return '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False,separators=(',',':'))+'</script>'

def build_page():
    source = (ROOT/'ultraljud/tennisarmbage/bilder/index.html').read_text()
    source = re.sub(r'<title>.*?</title>', '<title>'+TITLE+'</title>', source, count=1, flags=re.S)
    source = source.replace('https://www.kansei.se/ultraljud/tennisarmbage/bilder/', URL)
    source = re.sub(r'<script\b[^>]*type="application/ld\+json"[^>]*>.*?</script>', '', source, flags=re.S)
    source = source.replace('</head>', schema()+'</head>',1)
    def metadata(match):
        tag=match[0]
        key=re.search(r'(?:name|property)="([^"]+)"',tag)
        values={'description':DESCRIPTION,'og:description':DESCRIPTION,'twitter:description':DESCRIPTION,'og:title':TITLE,'twitter:title':TITLE,'og:image':'https://www.kansei.se'+image('gmed'),'twitter:image':'https://www.kansei.se'+image('gmed')}
        if key and key[1] in values:
            tag=re.sub(r'content="[^"]*"',lambda _: 'content="'+esc(values[key[1]])+'"',tag)
        return tag
    source = re.sub(r'<meta\b[^>]*>',metadata,source)
    source = source.replace('ultrasound-case knee-case elbow-case','ultrasound-case knee-case hip-case')
    source = source.replace('/assets/elbow-case.20261015.css','/assets/hip-case.20261021.css').replace('/assets/elbow-case.20261015.js','/assets/knee-case.20261014.js')
    source = re.sub(r'<main\b.*?</main>',main_content(),source,count=1,flags=re.S)
    source = source.replace('https://www.kansei.se/bilder/ultraljud/armbage/tennisarmbage/skadad-ultraljud.jpg','https://www.kansei.se'+image('gmed'))
    out=ROOT/PATH.strip('/')/'index.html'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(source)

def package(workspace):
    out=ROOT/ASSETS.strip('/');out.mkdir(parents=True,exist_ok=True)
    art=ROOT/'.github/kansei/artwork/hip';art.mkdir(parents=True,exist_ok=True)
    preview=workspace/'hip-qa';preview.mkdir(exist_ok=True)
    manifest={'version':VERSION,'canvas':[1280,960],'method':'Continuous imagegen painting, one global placement, clinician-defined original coordinates. No local warp, mesh or repeated tiles. Originals retained byte-identically; acquisition headers hidden by shared presentation CSS.','style_references':['Anatomiskt materialatlas med sex vävnadsskikt.png','Sex målade vävnadstexturer i rutnät.png','bilder/ultraljud/bicepssena/langdsnitt-anatomi.webp'],'views':[]}
    for v in VIEWS:
        key=v['key']; original=workspace/'upload'/v['original'];guide=workspace/'upload'/v['guide'];painting=workspace/'generated_images'/v['painting']
        shutil.copy2(original,out/(key+'.original.jpg'))
        source_paint=art/(key+'.painting.'+VERSION+'.webp')
        subprocess.run(['convert',str(painting),'-quality','96',str(source_paint)],check=True)
        left,top,right,bottom=v['bounds'];sx=931/(right-left);sy=780/(bottom-top);tx=174-left*sx;ty=111-top*sy
        encoded=base64.b64encode(painting.read_bytes()).decode()
        placed=f'<image xlink:href="data:image/png;base64,{encoded}" width="1448" height="1086" transform="matrix({sx} 0 0 {sy} {tx} {ty})"/>'
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1280" height="960" viewBox="0 0 1280 960"><defs><clipPath id="scan"><rect x="174" y="111" width="931" height="780"/></clipPath></defs><g clip-path="url(#scan)">{placed}</g></svg>'
        svgfile=preview/(key+'.svg');svgfile.write_text(svg)
        png=preview/(key+'.png')
        subprocess.run(['inkscape','--batch-process',str(svgfile),'--export-type=png','--export-filename='+str(png)],check=True,capture_output=True)
        target=out/(key+'.anatomi.'+VERSION+'.webp')
        subprocess.run(['convert',str(png),'-quality','94',str(target)],check=True)
        original_uri='data:image/jpeg;base64,'+base64.b64encode(original.read_bytes()).decode()
        review=svg.replace('<g clip-path=',f'<image xlink:href="{original_uri}" width="1280" height="960"/><g opacity="0.55" clip-path=',1)
        reviewfile=preview/(key+'.review.svg');reviewfile.write_text(review)
        subprocess.run(['inkscape','--batch-process',str(reviewfile),'--export-type=png','--export-filename='+str(preview/(key+'.review.png'))],check=True,capture_output=True)
        manifest['views'].append({'key':key,'original':str((out/(key+'.original.jpg')).relative_to(ROOT)),'original_sha256':sha(original),'clinician_guide_uploaded_name':v['guide'],'guide_sha256':sha(guide),'painting':str(source_paint.relative_to(ROOT)),'painting_sha256':sha(source_paint),'source_scan_bounds':v['bounds'],'global_placement':[sx,0,0,sy,tx,ty],'anatomy':str(target.relative_to(ROOT)),'anatomy_sha256':sha(target)})
    (art/('whole-paintings.'+VERSION+'.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    prompts=json.loads((workspace/'hip-prompts.json').read_text())
    for p in prompts:p['refs']=[Path(r).name for r in p['refs']]
    (art/('prompts.'+VERSION+'.json')).write_text(json.dumps(prompts,ensure_ascii=False,indent=2)+'\n')
    build_page()
    print(json.dumps({'page':PATH,'assets':len(VIEWS),'originals_byte_identical':True,'preview':str(preview)},ensure_ascii=False))

if __name__=='__main__':
    package(Path(sys.argv[1]))
