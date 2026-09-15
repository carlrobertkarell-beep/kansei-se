"""Mobile-first booking guide. Only alter the isolated generated clinic preview.
The original medical safety/routing data and public-page content are retained.
"""
from pathlib import Path
from bs4 import BeautifulSoup as BS
import hashlib,json,re,sys


def refine(root: Path):
    root=root.resolve(); folder=Path(__file__).resolve().parent
    manifest=json.loads((root/'__clinic-build.json').read_text())
    assert not manifest.get('guide_mobile_pass'), 'Run on a fresh preview build.'
    page=BS((root/'index.html').read_text(),'html.parser')
    original_guide=page.select_one('script[data-guide-src]')['data-guide-src']
    original=(root/original_guide.lstrip('/')).read_text()
    runtime=original
    def change(old,new):
        nonlocal runtime
        assert runtime.count(old)==1, ('Unexpected guide source',old[:70])
        runtime=runtime.replace(old,new)
    change("heading('Börja med att förstå besvären.')", "heading('Ditt nästa steg')")
    change("?'Axelbedömning':'Naprapati: börja med en bedömning'", "?'Axelbedömning':'Naprapatisk bedömning'")
    change("'Ett undersökningsbesök är en ingång när du behöver förstå besvären och få en plan. Du behöver inte välja behandlingsmetod i förväg.'", "'Vi undersöker dina besvär och går igenom nästa steg. Du behöver inte välja behandlingsmetod i förväg.'")
    change("'När axeln är huvudproblemet kan du välja en riktad axelbedömning. Behandlaren avgör vad som behöver undersökas.'", "'Ett riktat besök för din axel. Behandlaren undersöker dina besvär och bedömer nästa steg.'")
    change('<span class="result-tag">${escapeHTML(area.label)}</span><p class="result-summary">${escapeHTML(pattern?.[1] || \'Jag vill börja med en bedömning.\')}</p>', '<div class="guide-selection"><span class="result-tag">${escapeHTML(area.label)}</span><p class="result-summary">${escapeHTML(pattern?.[1] || \'Jag vill börja med en bedömning.\')}</p></div>')
    change('<span class="eyebrow">EN INGÅNG TILL KLINIKEN</span>', '<span class="eyebrow">FÖRSTA BESÖKET</span>')
    change('<p>${escapeHTML(reason)}</p><a class="button button-dark"', '<p class="guide-visit-copy">${escapeHTML(reason)}</p><div class="guide-booking"><p class="guide-price"><span>Pris för besöket</span><strong>${escapeHTML(next.price)}</strong></p><a class="button button-dark"')
    change('<small>${escapeHTML(next.price)} · Du kommer till rätt tjänst. Du väljer tid och bekräftar själv på Bokadirekt.</small></div><div class="result-details">', '<small class="guide-booking-note">Välj tid och bekräfta på Bokadirekt.</small></div></div><div class="result-details">')
    # One visible back control near the top, instead of below all result content.
    start=runtime.index('    const step=');end=runtime.index('\n',start)
    runtime=runtime[:start]+'''    const step=(label,n)=>`<div class="guide-progress">${state.screen!=='areas'?'<button class="guide-back" type="button" data-guide-back aria-label="Tillbaka till föregående steg"><span aria-hidden="true">←</span> Tillbaka</button>':'<span class="guide-task-label">Hitta rätt besök</span>'}<span class="guide-step">${state.screen==='care'?'Vårdhänvisning':state.screen==='services'?'Välj tjänst':'Steg '+n+' av 3'}</span></div>`;'''+runtime[end:]
    start=runtime.index('    const back=');end=runtime.index('\n',start)
    runtime=runtime[:start]+'''    const back=()=>'<div class="guide-actions"><button class="guide-back" type="button" data-reset>Börja om</button></div>';'''+runtime[end:]
    # Set a stable state hook to test layout for every real screen, not just page width.
    change('      prepareLinks(content);', "      content.dataset.guideScreen=state.screen;\n      prepareLinks(content);")
    # Ensure safety copy and decisions are byte-identical to the old runtime.
    safety=lambda t:t[t.index("}else if(state.screen==='safety')"):t.index("}else if(state.screen==='result'")]
    assert safety(original)==safety(runtime), 'Medical safety flow changed'
    assert original.split('/* Loaded only')[0]==runtime.split('/* Loaded only')[0], 'Booking prices/URLs changed'
    js='/assets/guide.'+hashlib.sha256(runtime.encode()).hexdigest()[:12]+'.js'
    (root/js.lstrip('/')).write_text(runtime)
    stylesheet=(root/manifest['css'].lstrip('/')).read_text()+'\n'+(folder/'guide_mobile.css').read_text()
    css='/assets/clinic.'+hashlib.sha256(stylesheet.encode()).hexdigest()[:12]+'.css'
    (root/css.lstrip('/')).write_text(stylesheet)
    for row in manifest['pages']:
        f=root/row['file'];s=BS(f.read_text(),'html.parser')
        before_main=str(s.main);before_head=str(s.head)
        for link in s.select('link[rel=stylesheet]'):
            if link['href']==manifest['css']:link['href']=css
        for script in s.select('script[data-guide-src]'):
            assert script['data-guide-src']==original_guide
            script['data-guide-src']=js
        dialog=s.select_one('#guide-dialog');assert dialog,row['path']
        dialog['aria-modal']='true'
        header=dialog.select_one('.drawer-header');header['class']=['drawer-header','guide-header']
        label=header.select_one('.eyebrow');label.string='KANSEI / BOKNINGSHJÄLP'
        close=header.select_one('[data-close]');close['type']='button';close['aria-label']='Stäng bokningshjälpen'
        for icon in dialog.select('svg'):icon['aria-hidden']='true'
        footer=dialog.select('.drawer-header')[-1]
        if footer is not header:
            footer['class']=['guide-privacy']
            if footer.small:footer.small.string='Dina val sparas inte eller skickas till kliniken.'
        assert str(s.main)==before_main,(row['path'],'Public page content changed')
        assert str(s.head).replace(css,manifest['css'])==before_head,(row['path'],'SEO metadata changed')
        f.write_text(str(s));row['bytes']=f.stat().st_size
    manifest['css']=css
    manifest['guide_mobile_pass']={'version':'mobile-guide-v1','pages':len(manifest['pages']),'guide_script':js,'medical_safety_unchanged':True,'prices_and_destinations_unchanged':True,'public_content_and_metadata_unchanged':True}
    (root/'__clinic-build.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print(json.dumps(manifest['guide_mobile_pass']))

if __name__=='__main__':refine(Path(sys.argv[1]))
