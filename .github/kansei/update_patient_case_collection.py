"""Use the existing /ultraljud/bilder/ collection as Patientfall.

Keep established addresses, add the approved knee case and derive catalogue
counts and ItemList from the actual cards. This does not migrate existing URLs.
"""
from pathlib import Path
import html
import json
import re
import xml.etree.ElementTree as ET
from build_knee_hyaluron_case import PATH, ASSETS, URL, HEADER, build

ROOT = Path(__file__).resolve().parents[2]
TITLE = 'Patientfall med ultraljud – anatomi och fynd | Kansei'
DESCRIPTION = 'Följ Kanseis patientfall med ultraljud: besvären, vad vi såg och vad vi gjorde. Se originalbilder, anatomilager, filmer och nästa steg i bedömningen.'


def rename_collection_links():
    for path in ROOT.rglob('*.html'):
        source = path.read_text()
        def label(match):
            link = match[0]
            replacements = {
                'Ultraljud i bild':'Patientfall',
                'Alla bildfall':'Alla patientfall',
                'Alla bildexempel:':'Alla patientfall:',
                'Till bildöversikten':'Till patientfallen',
                'Utforska bildexemplen':'Utforska patientfallen',
                'Utforska alla undersökningsfall':'Utforska alla patientfall',
                'Utforska alla bildexempel':'Utforska alla patientfall',
                'Alla knäbilder i biblioteket':'Alla patientfall om knä',
            }
            for before,after in replacements.items():
                link = link.replace(before,after)
            return link
        source = re.sub(r'<a\b[^>]*href="(?:https://www\.kansei\.se)?/ultraljud/bilder/[^\"]*"[^>]*>.*?</a>',label,source,flags=re.S)
        if source != path.read_text():
            path.write_text(source)


def collection():
    path = ROOT/'ultraljud/bilder/index.html'
    source = path.read_text()
    if PATH not in source:
        card = f'''<article class="atlas-entry" data-atlas-entry data-region="kna" data-symptoms="gang traning" data-search="knä knäsmärta artros långvarig kortison kortisoninjektioner hjälper inte ledband inre ledbandet uttänjt bristningar brosk hyaluron hyaluronsyra sinovial synovial promenad trappor stol"><div class="atlas-thumb" aria-hidden="true"><img src="{ASSETS}medial.original.jpg" alt="" width="1280" height="960" loading="lazy" decoding="async"{HEADER}/></div><div class="atlas-entry-copy"><small>Knä · Artros, ledband och hyaluron</small><h4><a href="{PATH}" data-atlas-case>Knäsmärta som kvarstår trots kortison?</a></h4><span class="atlas-case-type">Patientfall från Kansei</span><p>Följ kvinnans undersökning med artrosförändringar och skada i det inre ledbandet. Se anatomilagren och en ultraljudsvägledd hyaluroninjektion.</p><a class="atlas-image-shortcut" href="{PATH}#bilder">Direkt till bilder och fynd →</a></div></article>'''
        start = source.index('id="omrade-kna"')
        end = source.index('</div></section>',start)
        source = source[:end]+card+source[end:]
    source = source.replace('knä knäsmärta artros långvarig','knä knäsmärta smärta ont värk artros långvarig')
    source = re.sub(r'<title>.*?</title>','<title>'+TITLE+'</title>',source,count=1,flags=re.S)
    source = source.replace('<span>Bildexempel</span>','<span>Patientfall</span>')
    source = source.replace('KANSEIS EGNA ULTRALJUDSBILDER','FRÅN UNDERSÖKNING TILL FORTSATT PLAN')
    source = source.replace('Se och förstå<br><span>ultraljud.</span>','Patientfall med<br> <span>ultraljud.</span>')
    source = source.replace('Följ våra egna undersökningsfall från vardagsrörelse till bilder, klinisk bedömning och nästa steg.','Följ våra patientfall: besvären, vad vi såg och vad vi gjorde – från undersökning till fortsatt plan.')
    source = source.replace('Inget bildexempel matchar ditt val ännu.','Inget patientfall matchar ditt val ännu.')
    source = source.replace('Visa alla bildexempel','Visa alla patientfall').replace('Hitta bildfall efter besvär','Hitta patientfall efter besvär')
    def meta(match):
        tag=match[0]
        if any(k in tag for k in ['name="description"','property="og:description"','name="twitter:description"']):
            tag=re.sub(r'content="[^"]*"','content="'+html.escape(DESCRIPTION,quote=True)+'"',tag)
        if any(k in tag for k in ['property="og:title"','name="twitter:title"']):
            tag=re.sub(r'content="[^"]*"','content="'+TITLE+'"',tag)
        return tag
    source=re.sub(r'<meta\b[^>]*>',meta,source)
    cards=re.findall(r'<article class="atlas-entry".*?</article>',source,re.S)
    def schema(match):
        data=json.loads(match[2])
        for node in data.get('@graph',[]):
            kind=node.get('@type')
            if kind=='CollectionPage':
                node.update(name=TITLE,description=DESCRIPTION,dateModified='2026-10-27')
            if kind=='ItemList':
                entries=[]
                for i,card in enumerate(cards,1):
                    m=re.search(r'<h4><a href="([^"]+)"[^>]*>(.*?)</a>',card,re.S)
                    entries.append({'@type':'ListItem','position':i,'name':html.unescape(re.sub('<[^>]+>','',m[2])),'url':'https://www.kansei.se'+m[1]})
                node.update(name='Kanseis patientfall med ultraljud',numberOfItems=len(entries),itemListElement=entries)
            if kind=='BreadcrumbList':
                for item in node['itemListElement']:
                    if item.get('item')=='https://www.kansei.se/ultraljud/bilder/':item['name']='Patientfall'
        return match[1]+json.dumps(data,ensure_ascii=False,separators=(',',':'))+match[3]
    source=re.sub(r'(<script\b[^>]*type="application/ld\+json"[^>]*>)(.*?)(</script>)',schema,source,flags=re.S)
    source=re.sub(r'\d+ (?:bildfall|patientfall) · Alla områden',str(len(cards))+' patientfall · Alla områden',source)
    for region,label in [('alla','Alla områden'),('kna','Knä')]:
        count=len(cards) if region=='alla' else sum('data-region="kna"' in c for c in cards)
        source=re.sub(r'(<span>'+label+r'</span><small>)\d+(</small>)',lambda m:m[1]+str(count)+m[2],source)
    source=source.replace('/assets/ultrasound-explore.20261016.js','/assets/ultrasound-explore.20261027.js')
    path.write_text(source)


def contextual_links():
    for relative,anchor in [('ultraljud/kna/index.html','kallor'),('hyaluronsyra/kna/index.html','ultraljudsexempel')]:
        path=ROOT/relative;source=path.read_text()
        if PATH in source:continue
        paragraph=f'<p><a href="{PATH}">Patientfall: knäsmärta trots kortison →</a> Följ en kvinnas undersökning med artrosförändringar och skada i det inre ledbandet. Se anatomilagren och den ultraljudsvägledda hyaluroninjektionen.</p>'
        start=source.index('id="'+anchor+'"');end=source.index('</section>',start)
        index=source.index('<ul',start) if anchor=='kallor' else end
        source=source[:index]+paragraph+source[index:]
        path.write_text(source)


def sitemap():
    path=ROOT/'sitemap.xml';ns='http://www.sitemaps.org/schemas/sitemap/0.9'
    tree=ET.parse(path);root=tree.getroot()
    current={entry.findtext('{'+ns+'}loc'):entry for entry in root}
    if URL not in current:
        entry=ET.SubElement(root,'{'+ns+'}url');ET.SubElement(entry,'{'+ns+'}loc').text=URL
        current[URL]=entry
    for url in [URL,'https://www.kansei.se/ultraljud/bilder/','https://www.kansei.se/ultraljud/kna/','https://www.kansei.se/hyaluronsyra/kna/']:
        entry=current[url];last=entry.find('{'+ns+'}lastmod')
        if last is None:last=ET.SubElement(entry,'{'+ns+'}lastmod')
        last.text='2026-10-27'
    for prefix,uri in [('',ns),('image','http://www.google.com/schemas/sitemap-image/1.1'),('video','http://www.google.com/schemas/sitemap-video/1.1')]:ET.register_namespace(prefix,uri)
    ET.indent(tree,space='  ')
    path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='unicode')+'\n')


if __name__=='__main__':
    build()
    rename_collection_links()
    collection()
    contextual_links()
    sitemap()
    print('Updated the existing Patientfall collection and linked the approved knee case.')
