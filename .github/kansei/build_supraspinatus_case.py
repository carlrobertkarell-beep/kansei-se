"""Build the clinician's supraspinatus case with the established case components."""
from pathlib import Path
import html
import json
import re

from unify_case_stories import chapter, facts
import build_case_context as context

ROOT = Path(__file__).resolve().parents[2]
DATA = json.loads((ROOT / '.github/kansei/content/supraspinatus-case.20261028.json').read_text())
PATH = '/ultraljud/axel/supraspinatusruptur/'
ASSETS = '/bilder/ultraljud/supraspinatusruptur/'
URL = 'https://www.kansei.se' + PATH
TITLE = 'Totalruptur i supraspinatus på ultraljud | Kansei patientfall'
DESCRIPTION = 'Kraftlös axel efter en tidigare skidolycka. Följ Kanseis patientfall med totalruptur i supraspinatus, ultraljud, anatomilager, behandling och egen insats.'
HEADER = ' data-scan-header="68/960" style="--scan-header:7.0833333%"'


def esc(value):
    return html.escape(value, quote=True)


def reader():
    tabs, panels = [], []
    for i, view in enumerate(DATA['views']):
        key = view['key']
        original = ASSETS + key + '.original.jpg'
        tabs.append(f'<button id="tab-{key}" class="patient-view-tab" type="button" role="tab" aria-controls="view-{key}" data-patient-panel="view-{key}" aria-selected="{str(i == 0).lower()}" tabindex="{0 if i == 0 else -1}"><img src="{original}" alt="" width="1280" height="960" decoding="async"{HEADER}><span><strong>{view["short"]}</strong><small>{"Rupturvyn" if "without" in key else "Jämförelsebild"}</small></span></button>')
        labels = ''.join(f'<text x="{x}" y="{y}">{esc(label)}</text>' for x, y, label in view['labels'])
        pointers = ''
        for finding in view['findings']:
            x, y = finding['end']; tx, ty = finding['text']
            pointers += f'<path class="finding-pointer-shadow" d="{finding["path"]}"/><path class="finding-pointer" d="{finding["path"]}" stroke="#ffda84"/><circle cx="{x}" cy="{y}" r="6" fill="#ffda84"/><text x="{tx}" y="{ty}" fill="#fff">{esc(finding["label"])}</text>'
        findings = ''.join(f'<div class="patient-finding" data-finding-mode="{mode}" aria-hidden="true"><svg viewBox="0 0 1280 960" aria-hidden="true">{pointers}</svg></div>' for mode in ('ultrasound', 'anatomy'))
        panels.append(f'<article class="reader-panel" id="view-{key}" role="tabpanel" aria-labelledby="tab-{key}" tabindex="0"{" hidden" if i else ""}><div class="panel-layout"><div class="panel-media"><figure class="scan-card"><div class="scan-surround"><div class="patient-picture" data-mode="ultrasound" data-findings="false"><img class="original patient-native-scan" src="{original}" alt="{esc(view["caption"])}" width="1280" height="960" decoding="async"{HEADER}><div class="anatomy-layer" aria-hidden="true"><div class="anatomy-layer-content"><img src="{ASSETS}{key}.anatomi.20261028.svg" alt="Anatomisk illustration av {esc(view["title"].lower())}" width="1280" height="960" decoding="async"><svg class="anatomy-labels" viewBox="0 0 1280 960" aria-hidden="true">{labels}</svg></div></div>{findings}</div></div><figcaption>{esc(view["caption"])}</figcaption></figure></div><div class="panel-copy"><p class="eyebrow">Bild {i + 1} · {view["plane"]}</p><h3>{esc(view["title"])}</h3><p>{esc(view["copy"])}</p></div></div></article>')
    switch = lambda attr, label: f'<button type="button" class="{"patient-toggle" if attr == "data-patient-toggle" else "patient-findings-toggle"}" {attr} role="switch" aria-checked="false"><span class="patient-switch-track" aria-hidden="true"><span class="patient-switch-thumb"></span></span><span>{label}</span></button>'
    return '<section class="section" id="bilder" data-reading-section data-reading-title="Bilder och fynd"><div class="wrap"><div class="case-copy"><span class="eyebrow">Vad vi såg</span><h2>Jämför senans plats i tvärsnitt och längdsnitt</h2><p>SAX betyder tvärsnitt och LAX betyder längdsnitt. Välj en vy och växla mellan originalultraljud och anatomisk illustration. Visa fynden pekar ut samma område i båda lägena.</p></div><div class="patient-viewer supraspinatus-viewer" data-patient-viewer data-anatomy="false" data-findings="false"><div class="patient-view-tabs" role="tablist" aria-label="Välj undersökningsvy" data-view-count="4">' + ''.join(tabs) + '</div><div class="patient-toggle-area"><div class="patient-toggle-row">' + switch('data-patient-toggle', 'Anatomi') + switch('data-patient-findings', 'Visa fynden') + '<span class="patient-image-state" data-patient-state aria-live="polite">Ultraljud</span></div></div>' + ''.join(panels) + '</div><p class="small">Originalbilderna är underlag för den kliniska bedömningen. Anatomilagren är pedagogiska illustrationer. Jämförelsebilderna visar en synlig sena och innebär inte att hela jämförelseaxeln har bedömts som frisk.</p></div></section>'


def story():
    parts = DATA['sections']
    treatment = parts['behandling'] + '<h3>Sinogel i glenohumeralleden</h3>' + parts['sinogel']
    education = '<div class="case-story-education" data-case-education><h3>Vad betyder fynden och vad kan patienten göra själv?</h3><p>En viktig del av besöket var att patienten fick en begriplig förklaring av fynden, hur senskadan kan påverka axeln och vad det innebar för det fortsatta arbetet. Patienten fick också vägledning om rörelser och belastning utifrån armens funktion.</p><p>Målet var en aktiv roll i rehabiliteringen. Den egna träningen behöver anpassas till förmågan och utvecklas utifrån hur axeln reagerar. Att förstå vad som är skadat och hur armen kan användas gör planen lättare att följa i vardagen.</p></div>'
    chapters = '\n'.join(chapter('<h3>' + title + '</h3>' + body, i) for i, (title, body) in enumerate([
        ('Besvär och funktion', parts['bakgrund']),
        ('Bildfynd och bedömning', parts['undersokningen']),
        ('Behandling och fortsatt plan', treatment),
    ], 1))
    summary = facts([('Undersökning', 'Supraspinatussenan i två bildriktningar'), ('Bildfynd', 'Totalruptur vid fästet på överarmsbenet'), ('Genomförd behandling', 'Arbete med axelns funktion och intraartikulärt Sinogel'), ('Fortsatt plan', 'Anpassad rehabilitering och uppföljning av kraft och vardagsfunktion'), ('Falltyp', 'Patientfall från Kansei')])
    return '<section class="section case-story" id="patientfall" aria-labelledby="patientfall-title" data-reading-section data-reading-title="Patientfallet"><div class="wrap"><header class="case-story-heading"><p class="eyebrow">Patientfall från Kansei</p><h2 id="patientfall-title">En kraftlös axel och en sena som saknas vid sitt fäste</h2><p class="case-story-lead">Patienten sökte för stelhet och ömhet i nacken på samma sida, ny axelsmärta och kraftlöshet i armen. En skidolycka fem år tidigare var en viktig del av bakgrunden.</p><p class="case-story-note">Anonymiserat patientfall från Kansei. Här beskrivs undersökning och behandling. Något senare behandlingsresultat redovisas inte.</p></header><div class="case-story-layout"><div class="case-story-chapters">' + chapters + education + '<div class="case-story-follow"><h3>Vad följs upp?</h3>' + parts['fortsatt-plan'] + '</div><div class="case-story-actions"><a href="#bilder" data-case-view data-case-tab="tab-sax-without" data-case-findings="true">Se rupturfyndet i bildvisaren</a><a href="/ultraljud/axel/">Om axelundersökning och bokning</a></div></div><aside class="case-story-aside" aria-label="Patientfallet i korthet"><figure><a href="#bilder" data-case-view data-case-tab="tab-sax-without" data-case-findings="true"><img src="' + ASSETS + 'sax-without.original.jpg" alt="Originalultraljud i tvärsnitt utan synlig supraspinatussena över ledhuvudet." width="1280" height="960" loading="lazy" decoding="async"' + HEADER + '></a><figcaption>Öppna bilden för original, anatomi och fyndmarkeringar.</figcaption></figure>' + summary + '</aside></div></div></section>'


def build():
    # Header, footer, navigation, typography and reader scripts are the same as existing cases.
    page = (ROOT / 'ultraljud/axel/pectoralisruptur/index.html').read_text()
    page = page.replace('https://www.kansei.se/ultraljud/axel/pectoralisruptur/', URL)
    page = re.sub(r'<title>.*?</title>', '<title>' + TITLE + '</title>', page, count=1, flags=re.S)
    page = re.sub(r'<script\b[^>]*type="application/ld\+json"[^>]*>.*?</script>', '', page, flags=re.S)
    def meta(m):
        tag = m[0]
        for key, value in [('name="description"', DESCRIPTION), ('property="og:title"', TITLE), ('name="twitter:title"', TITLE), ('property="og:description"', DESCRIPTION), ('name="twitter:description"', DESCRIPTION), ('property="og:image"', 'https://www.kansei.se' + ASSETS + 'sax-without.original.jpg')]:
            if key in tag:
                return re.sub(r'content="[^"]*"', 'content="' + esc(value) + '"', tag)
        return tag
    page = re.sub(r'<meta\b[^>]*>', meta, page)
    page = page.replace('upper-limb-alignment-case clinic-site condition-page biceps-case simple-case ultrasound-case', 'clinic-site condition-page biceps-case simple-case ultrasound-case supraspinatus-case')
    page = re.sub(r'<link\b[^>]*href="/assets/pectoralis-case[^>]*>', '', page)
    page = page.replace('</head>', '<link rel="stylesheet" href="/assets/ultrasound-presentation.20261016.css"><link rel="stylesheet" href="/assets/supraspinatus-case.20261028.css"></head>', 1)
    c = {'key':'supraspinatus', 'path':PATH, 'region':'axel', 'story':'patientfall', 'kind':'Patientfall från Kansei',
         'headline':'Svårt att tvätta håret eller lyfta armen åt sidan?', 'summary':'I det här patientfallet ledde ny axelsmärta och kraftlöshet till en undersökning. Ultraljudet visade en totalruptur av supraspinatussenan. Skadans exakta ålder kunde inte fastställas.',
         'recognition':['Tvätta håret', 'Lyfta något ut från kroppen', 'Använda armen med bättre kraft och kontroll'],
         'question':'Hur stämmer senfyndet med armens svaghet och vad behöver den fortsatta planen ta hänsyn till?',
         'key_title':'Skadan och armens funktion behöver förklaras tillsammans.',
         'key_text':'Supraspinatussenan saknas på sin förväntade plats i de valda tvär- och längdsnitten. Jämförelsebilderna visar var senan normalt ligger. Fascia ovanför ledhuvudet ska skiljas från den sena som saknas.',
         'implication':'Behandlingen riktades mot axelns, armens och skulderpartiets funktion. Sinogel gavs som ett individuellt symtomlindrande tillägg i glenohumeralleden. Det återfäster inte senan och ska inte beskrivas som en etablerad behandling av totalrupturen.',
         'follow':'Kraft, smärta och förmågan att tvätta håret och lyfta armen behöver följas över tid. Något senare behandlingsresultat redovisas inte.',
         'naprapati':'Få armens styrka, rörelse och vardagsbelastning bedömda och en individuellt anpassad plan för behandling och rehabilitering.',
         'related':[['bursit','Se hur slemsäck och samtidiga senskador bedöms i flera vyer.'],['kalkaxel','Jämför med kalkinlagring och senskada i samma sena.']], 'media':['tab-sax-without','Se området där supraspinatussenan saknas'],
         'faq':[['Vad betyder bald head på ultraljud?', 'Uttrycket beskriver att rotatorkuffsenan inte syns över ledhuvudet i den undersökta vyn. I det här fallet avser det en totalruptur av supraspinatussenan.'],['Kan skadan dateras till skidolyckan?', 'Nej. Olyckan är relevant som bakgrund, men bilderna fastställer inte när rupturen uppstod. Det går inte heller att säkert säga att den är äldre än sex till tolv månader.']], 'description':DESCRIPTION}
    context.US_BOOK = 'https://www.bokadirekt.se/boka-tjanst/kansei-naprapati-rehabcenter-48847/muskuloskeletalt-ultraljud-1946824'
    decision = context.decision(c).replace('Bildgenomgång och förklaringar uppdaterade 16 oktober 2026.', 'Publicerat 28 oktober 2026.').replace('id="nasta-steg"', 'id="nasta-steg" data-reading-section data-reading-title="Bedömning och nästa steg"')
    hero = '<section class="condition-hero wrap"><nav class="crumbs" aria-label="Brödsmulor"><a href="/ultraljud/">Ultraljud</a> / <a href="/ultraljud/axel/">Axel</a> / <span>Supraspinatusruptur</span></nav><span class="eyebrow">Patientfall från Kansei · Rotatorkuffen</span><h1>Kraftlöshet i axeln vid totalruptur av supraspinatussenan</h1><p class="lead">En tidigare skidolycka, ny axelsmärta och en arm som kändes kraftlös. Se vad ultraljudet visade och hur fynden kopplades till behandling, egen insats och fortsatt plan.</p><aside class="case-brief"><span class="eyebrow">I det här fallet</span><p><strong>Totalruptur av supraspinatussenan</strong></p><p>Fyra ultraljudsvyer med originalbilder, anatomilager och fyndmarkeringar.</p></aside><a class="case-library-back" href="/ultraljud/bilder/">Alla patientfall</a><nav class="case-page-nav" aria-label="På den här sidan"><a href="#patientfall">Patientfallet</a><a href="#bilder">Bilder och fynd</a><a href="#nasta-steg">Bedömning och nästa steg</a><a href="#kallor">Om patientfallet</a></nav></section>'
    sources = '<section class="section" id="kallor" data-reading-section data-reading-title="Om patientfallet"><div class="wrap sources"><h2>Om patientfallet och källorna</h2>' + DATA['sections']['kallor'] + '<p>Undersökning och behandling beskrivs av <a href="/team/carl-robert-karell/">Carl-Robert Kårell, legitimerad naprapat</a>. Kansei erbjuder behandlingen och har ett kommersiellt intresse. Publicerat <time datetime="2026-10-28">28 oktober 2026</time>.</p></div></section>'
    main = '<main id="main" tabindex="-1">' + hero + story() + reader() + decision + sources + '<nav class="atlas-case-bottom wrap" aria-label="Fler patientfall"><a href="/ultraljud/bilder/?omrade=axel#exempel">Fler patientfall om axeln</a><a href="/ultraljud/bilder/">Alla patientfall</a></nav></main>'
    page = re.sub(r'<main\b[^>]*>.*?</main>', lambda _:main, page, count=1, flags=re.S)
    graph = [ {'@type':'MedicalWebPage','@id':URL+'#webpage','url':URL,'name':TITLE,'description':DESCRIPTION,'inLanguage':'sv-SE','datePublished':'2026-10-28','dateModified':'2026-10-28','author':{'@id':'https://www.kansei.se/team/carl-robert-karell/#person'},'mainEntity':{'@id':URL+'#case'},'about':{'@type':'MedicalCondition','name':'Supraspinatusruptur'}}, {'@type':'Article','@id':URL+'#case','headline':'Kraftlöshet i axeln vid totalruptur av supraspinatussenan','mainEntityOfPage':{'@id':URL+'#webpage'},'datePublished':'2026-10-28','dateModified':'2026-10-28','author':{'@type':'Person','name':'Carl-Robert Kårell','url':'https://www.kansei.se/team/carl-robert-karell/'}} ]
    graph += [{'@type':'ImageObject','@id':URL+'#bild-'+v['key'],'contentUrl':'https://www.kansei.se'+ASSETS+v['key']+'.original.jpg','caption':v['caption'],'width':1280,'height':960,'creditText':'Carl-Robert Kårell / Kansei'} for v in DATA['views']]
    page = page.replace('</head>', '<script type="application/ld+json">' + json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False,separators=(',',':')) + '</script></head>', 1)
    target = ROOT / PATH.strip('/') / 'index.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page)
    return target


if __name__ == '__main__':
    print(build())
