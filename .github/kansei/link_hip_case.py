"""Add the published hip case to the current clinic entrances, idempotently."""
from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parents[2]
CASE='/ultraljud/glutealsenor/bilder/'
IMAGE='/bilder/ultraljud/hoft/gmed.original.jpg'
HEADING='Ont på höftens utsida i flera år?'

def schema_update(source, kind):
    def update(match):
        data=json.loads(match[2])
        graph=data.get('@graph',[]) if isinstance(data,dict) else []
        for item in graph:
            if item.get('@type')=='CollectionPage':
                item['description']='Utforska Kanseis egna ultraljudsfall av axel, armbåge, hand, höft, knä och hälsena. Se originalbilder, anatomi och fynd.'
                item['dateModified']='2026-10-21'
            if item.get('@type')=='ItemList' and kind=='catalogue':
                entries=item.setdefault('itemListElement',[])
                if not any(x.get('url')=='https://www.kansei.se'+CASE for x in entries):
                    entries.append({'@type':'ListItem','position':len(entries)+1,'name':HEADING,'url':'https://www.kansei.se'+CASE})
                item['numberOfItems']=len(entries)
        return match[1]+json.dumps(data,ensure_ascii=False,separators=(',',':'))+match[3]
    return re.sub(r'(<script\b[^>]*type="application/ld\+json"[^>]*>)(.*?)(</script>)',update,source,flags=re.S)

def catalogue():
    path=ROOT/'ultraljud/bilder/index.html';s=path.read_text()
    if 'data-region="hoft"' in s:return
    link='<a href="/ultraljud/bilder/?omrade=hoft#exempel" data-atlas-region="hoft" data-label="Höft &amp; ljumske"><span>Höft &amp; ljumske</span><small>1</small></a>'
    marker='<a href="/ultraljud/bilder/?omrade=kna#exempel"'
    assert marker in s;s=s.replace(marker,link+marker,1)
    article=f'''<section class="atlas-group" data-atlas-group id="omrade-hoft" aria-labelledby="heading-hoft"><h3 id="heading-hoft">Höft &amp; ljumske</h3><div class="atlas-entries"><article class="atlas-entry" data-atlas-entry data-region="hoft" data-symptoms="" data-search="höft höften hoft hoften utsida utsidan lateral trokanter trokanterit gluteal tendinopati glutealsenor gluteus medius minimus tendinos labrum paralabral cysta röntgen artros injektionskonsultation långvarig smärta"><div class="atlas-thumb" aria-hidden="true"><img src="{IMAGE}" alt="" loading="lazy" decoding="async" width="1280" height="960" data-scan-header="68/960" style="--scan-header:7.0833333%"/></div><div class="atlas-entry-copy"><small>Höft · Glutealsenor och främre labrum</small><h4><a href="{CASE}" data-atlas-case>{HEADING}</a></h4><span class="atlas-case-type">Patientfall från Kansei</span><p>Röntgen hade enligt patienten inte visat artros. Se senförändringarna, ett separat cystfynd och varför funktion blev första steget.</p><a class="atlas-image-shortcut" href="{CASE}#bilder">Direkt till bilder och fynd</a></div></article></div></section>'''
    marker='<section class="atlas-group" data-atlas-group id="omrade-kna"'
    assert marker in s;s=s.replace(marker,article+marker,1)
    s=s.replace('<span>Alla områden</span><small>10</small>','<span>Alla områden</span><small>11</small>').replace('10 bildfall · Alla områden','11 bildfall · Alla områden')
    s=s.replace('axel, armbåge, hand, knä och hälsena','axel, armbåge, hand, höft, knä och hälsena')
    s=schema_update(s,'catalogue');path.write_text(s)

def services():
    for slug in ['ultraljud/glutealsenor','ultraljud/hoft-ljumske']:
        path=ROOT/slug/'index.html';s=path.read_text()
        if 'id="hoft-patientfall"' in s:continue
        block=f'''<section class="section us-case-entry" id="hoft-patientfall" data-reading-section data-reading-title="Patientfall från Kansei"><div class="wrap"><span class="eyebrow">Långvarig smärta på höftens utsida</span><h2>Röntgen visade enligt patienten ingen artros. Vad kunde ultraljud tillföra?</h2><p>Följ en kvinna som sökte för injektionskonsultation efter många år med smärta. Bilderna visar glutealsenorna och ett separat cystfynd framtill vid leden. Efter den samlade bedömningen valdes naprapatisk vård som första steg.</p><ul class="us-case-entry-list"><li><a class="text-link" href="{CASE}">Läs patientfallet: {HEADING.lower()}</a></li><li><a class="text-link" href="{CASE}#bilder">Se originalbilder, anatomi och fynd</a></li></ul></div></section>'''
        assert '</main>' in s;s=s.replace('</main>',block+'</main>',1)
        if '/assets/ultrasound-case-path.20261015.css' not in s:s=s.replace('</head>','<link rel="stylesheet" href="/assets/ultrasound-case-path.20261015.css"/></head>',1)
        path.write_text(s)
    p=ROOT/'ultraljud/index.html';s=p.read_text()
    new='<a href="/ultraljud/bilder/?omrade=hoft#exempel">Höft &amp; ljumske</a>'
    if new not in s:
        m=re.search(r'<nav class="atlas-area-links"[^>]*>.*?</nav>',s,re.S)
        assert m, 'Ultrasound body-area navigation missing'
        s=s[:m.start()]+m[0].replace('</nav>',new+'</nav>')+s[m.end():]
        p.write_text(s)

def discovery():
    p=ROOT/'sitemap.xml';s=p.read_text();url='https://www.kansei.se'+CASE
    if '<loc>'+url+'</loc>' not in s:
        node=f'<url><loc>{url}</loc><lastmod>2026-10-21</lastmod></url>\n'
        s=s.replace('</urlset>',node+'</urlset>');p.write_text(s)
    p=ROOT/'llms.txt';s=p.read_text()
    if CASE not in s:
        s+='\n- [Patientfall: långvarig smärta på höftens utsida](https://www.kansei.se'+CASE+'): gluteal tendinos, främre paralabral cysta och varför naprapatisk vård valdes först.\n'
        p.write_text(s)
    p=ROOT/'.github/kansei/ultrasound_design_check.py';s=p.read_text()
    s=s.replace("'/ultraljud/bursit-axel/'}","'/ultraljud/bursit-axel/','/ultraljud/glutealsenor/bilder/'}")
    s=s.replace(".count()!=5:raise AssertionError('Body-region shortcuts missing')",".count()!=6:raise AssertionError('Body-region shortcuts missing')")
    s=s.replace("!=10 or search.input_value()","!=11 or search.input_value()")
    p.write_text(s)

if __name__=='__main__':
    catalogue();services();discovery();print('Hip case linked from catalogue, regional pages, ultrasound hub, sitemap and llms.txt.')
