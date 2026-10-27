"""Apply patient-facing catalogue text and contextual service entrances."""
from pathlib import Path
import json
import re
from build_case_context import CASES, BY_KEY, ROOT, attach_css, esc, linked


def update_catalogue():
    path = ROOT/'ultraljud/bilder/index.html'
    source = path.read_text()
    if 'data-atlas-symptom' in source:
        return
    old_to_case = {c['path']:c for c in CASES}
    def entry(match):
        old = match[0]
        url = re.search(r'href="([^"]+)"', old)[1].split('#')[0]
        c = old_to_case[url]
        thumb = re.search(r'<div class="atlas-thumb".*?</div>',old,re.S)[0]
        label = re.search(r'<small>(.*?)</small>',old,re.S)[1]
        words = c['search']+' '+' '.join(c['recognition'])
        card = c['summary'].split('. ')[0].rstrip('.')+'.'
        return f'''<article class="atlas-entry" data-atlas-entry data-region="{c['region']}" data-symptoms="{' '.join(c['symptoms'])}" data-search="{esc(words)}">{thumb}<div class="atlas-entry-copy"><small>{label}</small><h4><a href="{c['path']}" data-atlas-case>{esc(c['headline'])}</a></h4><span class="atlas-case-type">{esc(c['kind'])}</span><p>{esc(card)}</p><a class="atlas-image-shortcut" href="{c['path']}#bilder">Direkt till bilder och fynd</a></div></article>'''
    source, count = re.subn(r'<a class="atlas-entry".*?</a>',entry,source,flags=re.S)
    assert count == 10
    source = source.replace('/assets/ultrasound-explore.20261015.css','/assets/ultrasound-explore.20261016.css').replace('/assets/ultrasound-explore.20261015.js','/assets/ultrasound-explore.20261016.js')
    source = source.replace('Från svartvit bild till begriplig anatomi. Hitta ditt område och utforska vad ultraljudet visar – med målade anatomilager och utpekade fynd.', 'Känner du igen besvären? Följ våra egna undersökningsfall från vardagsrörelse till bilder, klinisk bedömning och nästa steg. Utforska originalultraljud, anatomi och utpekade fynd.')
    source = source.replace('Vad vill du titta närmare på?', 'Hitta ett fall som liknar ditt besvär.').replace('Välj område. Öppna ett exempel. Se vad bilderna visar.', 'Välj besvär eller område. Öppna rubriken för hela fallet, eller gå direkt till bilderna. Liknande besvär kan ha olika förklaringar.')
    source = source.replace('Sök område eller besvär','Sök med dina egna ord')
    source = re.sub(r'(<input[^>]*data-atlas-search[^>]*)(>)',lambda m:re.sub(r' placeholder="[^"]*"','',m[1])+' placeholder="Prova att söka på handen somnar på natten" maxlength="140"'+m[2],source)
    filters=[('alla','Alla besvär'),('lyft','Lyft'),('grepp','Grepp'),('domningar','Domningar'),('svullnad','Svullnad'),('lopning','Löpning'),('natt','Sömn')]
    links=''.join(f'<a href="?besvar={key}#exempel" data-atlas-symptom="{key}"'+(' aria-current="true"' if key=='alla' else '')+f'>{label}</a>' for key,label in filters)
    panel=f'<div class="atlas-patient-filters"><p>Vad begränsar dig i vardagen?</p><nav class="atlas-patient-options" aria-label="Hitta bildfall efter besvär">{links}</nav></div>'
    source=source.replace('<div class="atlas-layout">',panel+'<div class="atlas-layout">',1)
    source=source.replace('10 bildexempel · Alla områden','10 bildfall · Alla områden')
    # Visible whole-case links are also the primary structured catalogue entries.
    def schema(match):
        data=json.loads(match[2])
        def walk(item):
            if isinstance(item,dict):
                if item.get('@type')=='ListItem' and 'url' in item:
                    url=item['url']; case=old_to_case.get(url.replace('https://www.kansei.se','').split('#')[0])
                    if case:item['url']='https://www.kansei.se'+case['path'];item['name']=case['headline']
                for value in item.values():walk(value)
            elif isinstance(item,list):
                for value in item:walk(value)
        walk(data)
        return match[1]+json.dumps(data,ensure_ascii=False,separators=(',',':'))+match[3]
    source=re.sub(r'(<script\b[^>]*type="application/ld\+json"[^>]*>)(.*?)(</script>)',schema,source,flags=re.S)
    path.write_text(source)


def service_section(title, introduction, cases, links, section_id='fall-fran-kansei'):
    cards=''.join(f'<article>{linked(BY_KEY[key]["headline"],BY_KEY[key]["path"])}<p>{esc(description)}</p></article>' for key,description in cases)
    actions=''.join(linked(label,url) for label,url in links)
    return f'''<section class="us-case-guide case-context-service" id="{section_id}" aria-labelledby="{section_id}-title" data-case-service><div class="wrap"><span class="eyebrow">Från våra undersökningar vid Odenplan</span><h2 id="{section_id}-title">{esc(title)}</h2><p>{esc(introduction)}</p><div class="case-context-related" data-related-count="{len(cases)}">{cards}</div><div class="case-context-links">{actions}</div></div></section>'''


def update_services():
    content={
      'naprapati':service_section('Från det som gör ont till en plan för vardagen.', 'Vid naprapatbesöket undersöker Carl-Robert hur muskler, leder och nerver fungerar och vad du vill kunna göra lättare. Behandling, rådgivning och rehabilitering anpassas efter bedömningen. När en särskild bildfråga behöver besvaras kan muskuloskeletalt ultraljud komplettera undersökningen.', [('biceps','Följ hur fynden i senan och gradvis träning kopplas till att kunna lyfta armen och ta på sig jackan.'),('tennis','Se hur en rehabplan utgår från det armen ska klara, från att lyfta kaffekoppen och matkassen till att spela padel.'),('halsena','Följ hur senans tillstånd påverkar belastning och rehab för promenader och frånskjut.')], [('Så går ett naprapatbesök till','/blogg/forsta-besoket-hos-naprapat/'),('Utforska alla undersökningsfall','/ultraljud/bilder/')]),
      'hyaluronsyra':service_section('Se hur knäartros bedöms före ett behandlingsval.', 'Målet med hyaluron är att lindra ledsmärta och underlätta rörelse. En del med knäartros får hjälp av behandlingen. Resultatet behöver utvärderas utifrån vardag och aktivitet. I knäfallet visar vi hur tidigare röntgen, undersökning och ultraljudsfynd kan kopplas till rehabilitering och möjlig hyaluronbehandling.', [('kna','Följ patientfallet med svullnad och artrosfynd. Se ledvätska och benpålagringar och läs hur behandlingsalternativen vägs samman.')], [('Följ knäfallet från bedömning till plan','/ultraljud/kna/#artros'),('Läs om hyaluron i knä och boka besök','/hyaluronsyra/kna/'),('Rehabilitering och vardagsfunktion','/rehabilitering/')]),
      'hyaluronsyra/kna':service_section('Bilderna blir begripliga när de kopplas till ditt knä.', 'Vad visar svullnaden och hur påverkar den promenader och träning? Knäfallet från Kansei kopplar ledvätska, artrosfynd och tidigare röntgen till en plan. Där ser du även var hyaluron kan komma in som ett komplement vid kvarstående artrosrelaterad smärta.', [('kna','Se originalultraljud, illustrerad anatomi och fyndmarkeringar och följ resonemanget om rehabilitering och möjlig hyaluronbehandling.')], [('Läs hela patientfallet','/ultraljud/kna/#artros'),('Se knäts bildexempel','/ultraljud/kna/#bilder')])
    }
    for slug,block in content.items():
        path=ROOT/slug/'index.html';source=attach_css(path.read_text())
        if 'data-case-service' in source:
            continue
        if slug=='hyaluronsyra/kna':
            source=source.replace('id="ultraljudsexempel"','id="ultraljudsexempel" data-case-service',1)
            source=source.replace('Från bild till plan vid knäartros med svullnad.','Vad betyder fynden vid svullet knä och artros för dig?',1)
            source=source.replace('Öppna bilderna för att växla mellan original, illustrerad anatomi och fyndmarkeringar.', 'Promenader, trappor och träningsförmåga ger konkreta mål att följa upp. Öppna bilderna för att växla mellan original, illustrerad anatomi och fyndmarkeringar.',1)
            path.write_text(source)
            continue
        if slug=='naprapati':
            # Place within the full-width flow, before the existing two-column article.
            hero=re.search(r'<section\b[^>]*class="[^"]*np-visit[^\"]*"[^>]*>.*?</section>',source,re.S)
            assert hero
            source=source[:hero.end()]+block+source[hero.end():]
        else:
            marker=re.search(r'<section\b[^>]*\bid="in-7"[^>]*>',source)
            if marker is None:marker=re.search(r'<section\b[^>]*\bid="boka-cta"[^>]*>',source)
            if marker is None:marker=re.search(r'<section\b[^>]*\bid="faq"[^>]*>',source)
            assert marker
            source=source[:marker.start()]+block+source[marker.start():]
        path.write_text(source)
    path=ROOT/'ultraljud/index.html';source=path.read_text()
    source=source.replace('/assets/ultrasound-explore.20261015.js','/assets/ultrasound-explore.20261016.js')
    source=source.replace('Vad är en sena – och var syns förändringen? Utforska våra egna bildexempel med målade anatomilager och tydliga fyndmarkeringar.', 'Från ont vid lyft eller domningar i handen till en begriplig undersökning. Följ våra egna fall med vardagsbesvär, ultraljudsbilder, anatomilager och kliniska förklaringar.')
    source=source.replace('Välj ditt område och öppna ett exempel. Du behöver inga förkunskaper.', 'Hitta ett fall som liknar ditt besvär och se hur fynden kopplas till en fortsatt plan. Du behöver inga förkunskaper.')
    path.write_text(source)


if __name__=='__main__':
    update_catalogue()
    update_services()
    print('Updated the ten-case catalogue and ultrasound, naprapathy and hyaluron service entrances.')
