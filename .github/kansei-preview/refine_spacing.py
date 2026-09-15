"""Correct generated preview semantics/spacing; leave original sources untouched."""
from pathlib import Path
from bs4 import BeautifulSoup as BS
import hashlib,json,sys
root=Path(sys.argv[1]).resolve()
manifest=json.loads((root/'__clinic-build.json').read_text())
folder=Path(__file__).resolve().parent
css=folder.joinpath('readability.css').read_text()
base=root/manifest['css'].lstrip('/')
combined=base.read_text()+'\n'+css
new_css='/assets/clinic.'+hashlib.sha256(combined.encode()).hexdigest()[:12]+'.css'
(root/new_css.lstrip('/')).write_text(combined)
changed=[]
for row in manifest['pages']:
 path=root/row['file'];s=BS(path.read_text(),'html.parser')
 before_head=str(s.head);before_h=[h.get_text(' ',strip=True) for h in s.select('main h1,main h2,main h3')]
 # Restrict transformations to the known preview template. Do not process app/product pages.
 assert len(s.select('.site-header'))==1,row['path']
 for group in s.select('main div'):
  actions=group.find_all(['a','button'],recursive=False)
  if len([a for a in actions if {'button','btn'} & set(a.get('class',[]))])>=2:
   group['class']=list(dict.fromkeys(group.get('class',[])+['action-group']))
 for a in s.select('main a[href="/#guide"]'):
  a['href']='/hjalp-mig-boka/'
 for panel in s.select('main #boka-cta, main .art-cta'):
  panel['class']=list(dict.fromkeys(panel.get('class',[])+['booking-panel']))
 for trust in s.select('main .cta-trust'):
  stars=trust.select_one('.ct-s');quote=trust.select_one('.ct-q');old_help=trust.select_one('.ct-o')
  proof=s.new_tag('div',attrs={'class':'cta-proof'})
  if stars:stars['aria-hidden']='true';proof.append(stars.extract())
  if quote:quote.name='p';proof.append(quote.extract())
  trust.clear()
  if old_help:
   helper=s.new_tag('div',attrs={'class':'cta-help'})
   start=old_help.select_one('a[href*="bokadirekt"]')
   p=s.new_tag('p');p.append('Osäker på rätt behandling? ')
   if start:p.append(start.extract())
   else:p.append('Börja med en undersökning.')
   helper.append(p)
   p=s.new_tag('p');p.append('Frågor inför besöket? ')
   a=s.new_tag('a',href='/fragor-och-svar/');a.string='Läs vanliga frågor';p.append(a);p.append(' eller ')
   a=s.new_tag('a',href='mailto:info@kansei.se');a.string='mejla oss';p.append(a);p.append('.')
   helper.append(p);trust.append(helper)
  if proof.get_text(strip=True):trust.append(proof)
 if row['path']=='/kontakt/':
  s.main['class']=list(dict.fromkeys(s.main.get('class',[])+['contact-page']))
  note=s.select_one('.contact-no-call');note.clear()
  h=s.new_tag('strong');h.string='Vi hjälper dig via mejl';note.append(h)
  p=s.new_tag('p');p.string='Vi läser och besvarar meddelanden under arbetstid, mellan patientbesöken. Telefonsamtal besvaras normalt inte under behandling eller efter arbetstid.';note.append(p)
  p=s.new_tag('p');p.string='För en kort praktisk fråga går det också bra att skicka SMS.';note.append(p)
  lead=s.select_one('.page-lead');lead.string='Boka ditt besök online. Svar om priser, behandlingar och praktiska frågor finns i våra vanliga frågor. Behöver du ett personligt svar, mejla oss.'
  actions=note.find_next_sibling('div');actions['class']=list(dict.fromkeys(actions.get('class',[])+['contact-actions','action-group']))
  first=actions.select_one('a');arrow=first.select_one('svg');arrow=arrow.extract() if arrow else None;first.clear();first.append('Boka besök ')
  if arrow:first.append(arrow)
  # Put practical actions before the explanatory contact policy.
  note.insert_before(actions.extract())
  layout=s.select_one('.contact-page .services-layout');layout.parent['class']=layout.parent.get('class',[])+['contact-info']
  address=layout.find('div',recursive=False);address['class']=address.get('class',[])+['contact-address']
  tasks=layout.select_one('.service-list');tasks['class']=['contact-tasks']
  for t in tasks.select('.service'):
   t['class']=['contact-task']
   child=t.find('div',recursive=False)
   if child:child.unwrap()
 # Identical SEO head apart from the new single cache-busted CSS file.
 for link in s.select('link[rel=stylesheet]'):
  if link.get('href')==manifest['css']:link['href']=new_css
 assert before_h==[h.get_text(' ',strip=True) for h in s.select('main h1,main h2,main h3')],(row['path'],'heading drift')
 after_head=str(s.head).replace(new_css,manifest['css']);assert before_head==after_head,(row['path'],'SEO head drift')
 path.write_text(str(s));row['bytes']=path.stat().st_size;changed.append(row['path'])
manifest['css']=new_css;manifest['version']='coherent-clinic-preview-v3-spacing';manifest['spacing_pass']={'pages':len(changed),'headings_preserved':True,'metadata_preserved':True,'changes':'Named action groups; semantic booking help/review blocks; reading rhythm. Contact operating copy clarified and extra-hours promise removed from CTA help, not medical content. Stale /#guide links now target booking-help page.'}
(root/'__clinic-build.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps({'spacing_refined':len(changed),'css':new_css,'headings_and_metadata':'preserved'}))
