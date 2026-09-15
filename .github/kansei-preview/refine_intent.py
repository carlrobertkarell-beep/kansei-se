"""Separate booking from reading and rebuild the two unindexed topic hubs.
Runs on the isolated static export only; original services/articles/Reda are unchanged.
"""
from pathlib import Path
from bs4 import BeautifulSoup as BS
import hashlib, html, json

CSS = r'''
/* Task-specific components, not a second body-part selector. */
#hitta-ratt .finder-intro{align-items:start}
#hitta-ratt .finder-intro>div{max-width:420px}
#hitta-ratt .finder-intro h2{font-size:clamp(36px,5vw,70px);line-height:1.08;letter-spacing:-.035em;max-width:11ch;margin:16px 0 0}
#hitta-ratt .finder-intro .eyebrow{font-size:11px;color:var(--teal);margin:0}
#hitta-ratt .finder-intro p{margin:0;line-height:1.8}
#hitta-ratt .finder-intro .finder-purpose{font-size:13px;color:var(--muted);margin-top:16px}
#hitta-ratt .finder-help-link{display:inline-flex;margin-top:20px;font-size:14px;line-height:1.6}
#hitta-ratt .finder-visual-label{max-width:calc(100% - 48px);line-height:1.7}
#hitta-ratt .area-item{color:var(--ink);transition:background .18s,color .18s,padding .18s}
#hitta-ratt .area-item:hover,#hitta-ratt .area-item:focus-visible{color:#fff}
.home-reading{padding-block:clamp(56px,7vw,90px);background:#edf2f5}
.reading-inner,.hub-container{width:100%;max-width:1440px;margin-inline:auto;padding-inline:clamp(22px,4.2vw,66px);box-sizing:border-box}
.reading-intro{display:grid;grid-template-columns:1fr 1fr;gap:40px;align-items:end;margin-bottom:34px}
.reading-intro .eyebrow{color:var(--teal)}
.reading-intro h2{font-size:clamp(34px,4.3vw,62px);line-height:1.14;letter-spacing:-.03em;margin:16px 0 0;max-width:15ch}
.reading-intro>div+div>p{font-size:16px;line-height:1.8;color:var(--muted);max-width:50ch;margin:0}
.reading-intro .text-link{margin-top:16px}
.reading-stories{display:grid;grid-template-columns:1.04fr 1fr;gap:clamp(24px,4vw,56px);align-items:stretch}
.reading-feature{display:flex;flex-direction:column;min-width:0;background:#fff;border-radius:6px;overflow:hidden;border:1px solid var(--line);transition:box-shadow .2s}
.reading-feature:hover{box-shadow:0 10px 26px #13273812}
.reading-feature img{width:100%;height:auto;aspect-ratio:16/9;object-fit:cover}
.reading-feature-copy{padding:24px 28px;display:grid;gap:16px;justify-items:start}
.reading-feature-copy .eyebrow,.reading-story .eyebrow{font-size:10px;color:var(--teal)}
.reading-feature-copy h3,.reading-story h3{font-size:clamp(23px,2.6vw,34px);line-height:1.2;letter-spacing:-.025em;margin:0;overflow-wrap:anywhere}
.reading-feature-copy p,.reading-story p{font-size:14px;line-height:1.8;color:var(--muted);margin:0}
.reading-list{display:flex;flex-direction:column;border-top:1px solid var(--line);min-width:0}
.reading-story{display:flex;flex-direction:column;align-items:flex-start;gap:16px;flex:1;padding:28px 0;border-bottom:1px solid var(--line);transition:color .18s}
.reading-story:hover h3{color:var(--teal)}
.reading-cta{font-size:14px;line-height:1.6;display:inline-flex;align-items:center;gap:12px;min-height:32px;margin-top:auto;text-decoration:underline;text-underline-offset:5px}
/* Independent containers prevent the old .cluster-hero padding:30px 0 reset. */
.knowledge-hub .hub-container{padding-inline:clamp(22px,4.2vw,66px)}
.hub-head{padding-block:40px 38px;border-bottom:1px solid var(--line)}
.hub-crumbs{display:flex;gap:10px;flex-wrap:wrap;font-size:12px;line-height:1.7;color:var(--muted);margin:0 0 32px;padding:0}
.hub-crumbs a{text-decoration:underline;text-underline-offset:4px;min-height:24px;display:inline-flex;align-items:center}
.hub-head .eyebrow{font-size:11px;color:var(--teal)}
.hub-title{font-size:clamp(38px,5.1vw,72px);font-weight:500;line-height:1.08;letter-spacing:-.04em;margin:18px 0 24px;max-width:20ch;hyphens:manual;overflow-wrap:break-word}
.hub-title span{display:block;color:var(--teal)}
.knowledge-hub .hub-lead{max-width:66ch;font-size:17px;line-height:1.8;margin:0;color:var(--muted)}
.hub-shortcuts{display:flex;align-items:center;flex-wrap:wrap;gap:16px 30px;margin-top:24px}
.hub-shortcuts>span{font:12px/1.7 var(--mono);color:var(--muted)}
.hub-shortcuts .text-link{font-size:14px;min-height:44px}
.hub-library{padding-block:38px 56px}
.hub-library-intro{display:flex;align-items:baseline;justify-content:space-between;gap:20px;flex-wrap:wrap;margin-bottom:24px}
.hub-library-intro h2{font-size:26px;line-height:1.3;letter-spacing:-.025em;margin:0}
.hub-library-intro p{font-size:14px;line-height:1.7;color:var(--muted);margin:0}
.hub-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.hub-guide{min-width:0;display:flex;flex-direction:column;align-items:flex-start;gap:16px;background:#fff;border:1px solid var(--line);border-radius:6px;padding:28px;transition:background .18s,border-color .18s}
.hub-guide:hover{background:#f3f7f8;border-color:#92a6b2}
.hub-guide .eyebrow{font-size:10px;color:var(--muted)}
.hub-guide h3{font-size:26px;line-height:1.25;letter-spacing:-.025em;margin:0;overflow-wrap:anywhere}
.hub-guide p{font-size:15px;line-height:1.8;color:var(--muted);margin:0;max-width:64ch;overflow-wrap:anywhere}
.hub-next{display:grid;grid-template-columns:1fr auto;gap:26px;align-items:center;border-top:1px solid var(--line);margin-top:36px;padding-top:30px}
.hub-next h2{font-size:26px;line-height:1.25;margin:0 0 12px;letter-spacing:-.025em}
.hub-next p{font-size:15px;line-height:1.8;color:var(--muted);max-width:58ch;margin:0}
.hub-next .button{min-height:50px;white-space:normal;max-width:100%}
/* The four linked topic articles get the same reliable outer gutter. */
.knowledge-topic-article .article-wrap{width:100%;max-width:1440px;margin-inline:auto;padding-inline:clamp(22px,4.2vw,66px);padding-top:36px;gap:clamp(38px,6vw,88px);grid-template-columns:minmax(0,1fr) minmax(220px,260px)}
.knowledge-topic-article .article-main{min-width:0;max-width:800px}
.knowledge-topic-article .article-main .crumbs{font-size:12px;line-height:1.8;margin-bottom:28px}
.knowledge-topic-article .article-main h1{font-size:clamp(36px,4.8vw,66px);line-height:1.12;letter-spacing:-.035em;overflow-wrap:break-word;hyphens:manual}
.knowledge-topic-article .article-main>.lead{font-size:17px;line-height:1.8;margin-top:24px}
@media(max-width:960px){.knowledge-topic-article .article-wrap{display:block}.knowledge-topic-article .article-main{max-width:none}.knowledge-topic-article .article-aside{position:static}.hub-next{grid-template-columns:1fr}.hub-next .button{justify-self:start}}
@media(max-width:700px){
 #hitta-ratt .finder-intro{display:block}
 #hitta-ratt .finder-intro>div{margin:0}
 #hitta-ratt .finder-intro>div+div{margin-top:22px}
 #hitta-ratt .finder-intro h2{font-size:40px;max-width:11ch;margin-top:14px;line-height:1.12}
 #hitta-ratt .finder-intro .finder-purpose{font-size:13px;margin-top:14px}
 #hitta-ratt .area-item{min-height:66px}
 #hitta-ratt .area-item>span:nth-child(2){font-size:22px}
 .reading-inner,.hub-container,.knowledge-hub .hub-container{padding-inline:22px}
 .reading-intro{display:block;margin-bottom:28px}
 .reading-intro h2{font-size:36px;line-height:1.14;max-width:15ch}
 .reading-intro>div+div{margin-top:22px}
 .reading-stories{grid-template-columns:1fr;gap:26px}
 .reading-feature-copy{padding:22px;gap:14px}
 .reading-feature-copy h3,.reading-story h3{font-size:25px;line-height:1.25}
 .reading-story{padding-block:24px;gap:14px}
 .hub-head{padding-top:24px;padding-bottom:28px}
 .hub-crumbs{margin-bottom:24px;gap:8px;font-size:12px}
 .hub-title{font-size:38px;line-height:1.1;letter-spacing:-.035em;margin:16px 0 22px;max-width:16ch}
 .knowledge-hub .hub-lead{font-size:16px;line-height:1.8}
 .hub-shortcuts{gap:6px 18px;margin-top:18px}
 .hub-library{padding-top:28px;padding-bottom:48px}
 .hub-library-intro{display:block;margin-bottom:20px}
 .hub-library-intro h2{font-size:24px}
 .hub-library-intro p{margin-top:10px}
 .hub-grid{grid-template-columns:1fr;gap:14px}
 .hub-guide{padding:22px;gap:14px}
 .hub-guide h3{font-size:25px;line-height:1.25}
 .hub-guide p{font-size:15px;line-height:1.75}
 .hub-next{margin-top:28px;padding-top:26px;gap:22px}
 .hub-next h2{font-size:25px}
 .hub-next .button{width:100%}
 .knowledge-topic-article .article-wrap{padding:24px 22px 56px}
 .knowledge-topic-article .article-main h1{font-size:36px;line-height:1.15}
 .knowledge-topic-article .article-main>.lead{font-size:16px}
}
@media(prefers-reduced-motion:reduce){.reading-feature,.reading-story,.hub-guide,#hitta-ratt .area-item{transition:none}}
'''

def refine(root: Path) -> None:
    root = root.resolve()
    manifest_path = root / '__clinic-build.json'
    manifest = json.loads(manifest_path.read_text())
    assert manifest.get('version') == 'coherent-clinic-preview-v3-spacing', 'Run after spacing pass.'
    assert not manifest.get('intent_pass'), 'This pass must run once per clean export.'
    parse = lambda text: BS(text, 'html.parser')
    esc = lambda text: html.escape(str(text), quote=True)
    icon = '<svg class="icon" aria-hidden="true"><use href="#i-arrow"/></svg>'
    home_path = root / 'index.html'
    home = parse(home_path.read_text())
    finder = home.select_one('#hitta-ratt')
    assert finder and len(finder.select('[data-area]')) == 7
    finder.select_one('.finder-intro').replace_with(parse('<div class="finder-intro"><div><span class="eyebrow">BOKNINGSHJÄLP</span><h2>Hitta rätt besök.</h2></div><div><p>Välj området som besvärar dig. Vi hjälper dig att hitta ett första besök, utan att du behöver välja behandlingsmetod.</p><p class="finder-purpose">Ditt val öppnar bokningsguiden. Det är inte en diagnos eller en bokning.</p></div></div>').div)
    for control in finder.select('.area-item[data-area]'):
        label = control.select('span')[1].get_text(' ', strip=True)
        control.name = 'a'
        control['href'] = '/hjalp-mig-boka/'
        control['aria-label'] = label + ': öppna bokningsguiden'
        control['aria-haspopup'] = 'dialog'
        control['aria-controls'] = 'guide-dialog'
        control.attrs.pop('type', None)
    finder.append(parse('<a class="text-link finder-help-link" href="/tjanster/">Vet du redan? Se besök och priser →</a>').a)
    old = home.select_one('.cluster-entry')
    assert old, 'Homepage duplicate entry was not found.'
    section = old.find_parent('section')
    picks = [('/blogg/ultraljud-eller-magnetkamera/', 'UNDERSÖKNING'),('/blogg/ont-i-axeln-nar-du-lyfter-armen/', 'AXELBESVÄR'),('/blogg/knaartros-vad-du-kan-gora/', 'KNÄARTROS')]
    entries = []
    for url, label in picks:
        article = parse((root / url.lstrip('/') / 'index.html').read_text())
        entries.append((url, label, article.h1.get_text(' ', strip=True), article.select_one('meta[name=description]')['content']))
    url, label, title, description = entries[0]
    feature = f'<a class="reading-feature" href="{url}"><img src="/bilder/k2eea6033d6.webp" width="1200" height="1500" loading="lazy" decoding="async" alt="Ultraljudsundersökning på Kansei"><div class="reading-feature-copy"><span class="eyebrow">{label}</span><h3>{esc(title)}</h3><p>{esc(description)}</p><span class="reading-cta">Läs artikeln {icon}</span></div></a>'
    stories = ''.join(f'<a class="reading-story" href="{url}"><span class="eyebrow">{label}</span><h3>{esc(title)}</h3><p>{esc(description)}</p><span class="reading-cta">Läs artikeln {icon}</span></a>' for url, label, title, description in entries[1:])
    section.replace_with(parse(f'<section class="home-reading" aria-labelledby="reading-title"><div class="reading-inner"><div class="reading-intro"><div><span class="eyebrow">LÄS &amp; FÖRSTÅ</span><h2 id="reading-title">Kunskap inför ditt nästa steg.</h2></div><div><p>Läs om vanliga besvär, undersökningar och behandlingsalternativ.</p><a class="text-link" href="/kunskapsbank/">Till hela kunskapsbanken {icon}</a></div></div><div class="reading-stories">{feature}<div class="reading-list">{stories}</div></div></div></section>').section)
    home_path.write_text(str(home))
    hub_records = []
    for slug, bodypart, area, service in [('axel','Axel','shoulder','/skuldra/'), ('kna','Knä','knee','/naprapati/')]:
        file = root / 'kunskapsbank' / slug / 'index.html'
        page = parse(file.read_text())
        before_head = str(page.head)
        cards = page.select('.cluster-card')
        assert len(cards) == 6, (slug, 'Unexpected original card set.')
        data = [(c.h2.get_text(' ', strip=True), c.p.get_text(' ', strip=True), c.a['href']) for c in cards]
        lead = page.select_one('.cluster-lead').get_text(' ', strip=True)
        title = 'Ont i axeln?' if slug == 'axel' else 'Ont i knät?'
        card_html = ''.join(f'<a class="hub-guide" href="{esc(url)}"><span class="eyebrow">GUIDE / {bodypart.upper()}</span><h3>{esc(t)}</h3><p>{esc(d)}</p><span class="reading-cta">Läs guiden {icon}</span></a>' for t,d,url in data)
        service_label = 'Så går axelbedömningen till' if slug == 'axel' else 'Så går en klinisk bedömning till'
        fragment = parse(f'<main id="main" tabindex="-1" class="knowledge-hub"><header class="hub-head"><div class="hub-container"><nav class="hub-crumbs" aria-label="Brödsmulor"><a href="/">Hem</a><span aria-hidden="true">/</span><a href="/kunskapsbank/">Kunskapsbanken</a><span aria-hidden="true">/</span><span aria-current="page">{bodypart}</span></nav><span class="eyebrow">KUNSKAPSBANKEN / {bodypart.upper()}</span><h1 class="hub-title">{title}<span>Börja med att förstå.</span></h1><p class="hub-lead">{esc(lead)}</p><div class="hub-shortcuts"><span>{len(data)} guider</span><a class="text-link" href="{service}">{service_label} {icon}</a></div></div></header><section class="hub-library hub-container" aria-labelledby="hub-library-title"><div class="hub-library-intro"><h2 id="hub-library-title">Välj en guide att läsa</h2><p>Fördjupning om besvär och bedömning.</p></div><div class="hub-grid">{card_html}</div><aside class="hub-next" aria-label="Bokningshjälp"><div><h2>Vill du hellre få hjälp att välja besök?</h2><p>Du behöver inte läsa alla guider eller ställa diagnos själv. Bokningshjälpen leder dig vidare till ett första besök.</p></div><a class="button button-dark" data-area="{area}" href="/hjalp-mig-boka/" aria-haspopup="dialog" aria-controls="guide-dialog">Hjälp mig välja besök {icon}</a></aside></section></main>')
        page.main.replace_with(fragment.main)
        assert str(page.head) == before_head, (slug, 'metadata drift')
        assert [(c.h3.get_text(' ',strip=True),c.p.get_text(' ',strip=True),c['href']) for c in page.select('.hub-guide')] == data
        assert len(page.select('h1')) == 1
        file.write_text(str(page))
        hub_records.append({'path':f'/kunskapsbank/{slug}/','cards':len(data),'old_links_and_descriptions_preserved':True})
    for slug in ('axel','kna'):
        for file in (root/'kunskapsbank'/slug).glob('*/index.html'):
            page = parse(file.read_text())
            page.main['class'] = list(dict.fromkeys(page.main.get('class',[]) + ['knowledge-topic-article']))
            file.write_text(str(page))
    old_css = manifest['css']
    combined = (root/old_css.lstrip('/')).read_text() + '\n' + CSS
    new_css = '/assets/clinic.' + hashlib.sha256(combined.encode()).hexdigest()[:12] + '.css'
    (root/new_css.lstrip('/')).write_text(combined)
    for row in manifest['pages']:
        file = root/row['file']
        text = file.read_text()
        assert old_css in text, row['path']
        file.write_text(text.replace(old_css,new_css))
        row['bytes'] = file.stat().st_size
    manifest['css'] = new_css
    manifest['intent_pass'] = {'version':'booking-vs-reading-v1','homepage':'One seven-area booking entry; editorial article teasers instead of a second partial area selector.','hubs':hub_records,'new_js_bytes':0,'original_service_and_article_copy_changed':False,'existing_titles_and_canonicals_changed':False,'new_hub_h1_updated':True}
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print(json.dumps({'intent_refinement':'PASS','hubs':hub_records,'css':new_css}))

if __name__ == '__main__':
    import sys
    refine(Path(sys.argv[1]))
