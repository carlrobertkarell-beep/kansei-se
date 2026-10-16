"""Final source-preserving copy/layout polish and a factual delivery manifest."""
from pathlib import Path
import json,re,shutil,subprocess
ROOT=Path(__file__).resolve().parents[2]
OUT=Path('/tmp/kansei-visibility-artifacts');OUT.mkdir(exist_ok=True)
p=ROOT/'cookie/index.html';t=p.read_text()
t=t.replace('<section class="page wrap" id="statistik-kallgrupp">','<section class="ref-section wrap" id="statistik-kallgrupp">')
t=t.replace('Hur vi skiljer hänvisningar och bokningsklick åt','Hänvisningar och bokningsklick.')
t=t.replace('Information uppdaterad 9 oktober 2026.','Information uppdaterad 16 oktober 2026.')
t=t.replace('href="/kontakt/" aria-current="page"','href="/kontakt/"')
m=re.search(r'<section class="ref-section wrap" id="statistik-kallgrupp">.*?</section>',t,re.S)
assert m
section=m.group();t=t[:m.start()]+t[m.end():]
marker='<section class="ref-section wrap"><h2>Cookies och sparat val.'
assert t.count(marker)==1
t=t.replace(marker,section+marker);p.write_text(t)
p=ROOT/'naprapati/index.html';t=p.read_text()
t=t.replace('Specialistmedverkan sker efter förfrågan</a>, inte som en fast bemannad fysioterapeut- eller ortopedmottagning.','Specialistmedverkan sker efter förfrågan</a> och planeras separat när det är aktuellt.')
p.write_text(t)
p=ROOT/'blogg/naprapat-fysioterapeut-kiropraktor-eller-ortoped/index.html';t=p.read_text()
t=t.replace('Specialistmedverkan kan undersökas efter förfrågan; kliniken har inte en fast bemannad fysioterapeut- eller ortopedmottagning.','Vid behov kan vi också undersöka möjligheten till specialistmedverkan efter förfrågan.')
old='Hos Kansei kan du boka naprapati och ultraljud utan remiss. För annan vård behöver du kontrollera vad som gäller hos den mottagning du väljer. Specialistmedverkan på Kansei sker efter förfrågan och är inte ett ordinarie besök hos en fast bemannad ortoped- eller fysioterapeutmottagning.'
new='Hos Kansei kan du boka naprapati och ultraljud utan remiss. Specialistmedverkan planeras separat efter förfrågan. För besök hos andra mottagningar behöver du kontrollera deras remisskrav.'
assert t.count(old)==2, 'Visible FAQ and schema must both be present'
t=t.replace(old,new);p.write_text(t)
p=ROOT/'.github/scripts/check-visibility.py';t=p.read_text()
t=t.replace("assert 'fast bemannad fysioterapeut- eller ortopedmottagning' in article", "assert 'Specialistmedverkan planeras separat efter förfrågan' in article\n    assert 'under samma tak' not in article")
p.write_text(t)
# These output files contain only public site/code and an entirely unfilled benchmark.
subprocess.run(['python3','.github/kansei/visibility.py','--template',str(OUT/'ai-benchmark-template.json')],cwd=ROOT,check=True)
shutil.copy(ROOT/'.github/kansei/visibility.py',OUT/'visibility.py')
shutil.copy(ROOT/'docs/visibility-measurement-2026-10-16.md',OUT/'matning-och-avgransningar.md')
files=subprocess.check_output(['git','diff','--name-only','origin/main'],cwd=ROOT,text=True).splitlines()
media=[f for f in files if Path(f).suffix.lower() in ['.png','.jpg','.jpeg','.webp','.svg','.mp4','.webm','.gif','.woff','.woff2','.ttf']]
assert not media,media
new_pages=[];booking=0;ignored=0
for p in ROOT.rglob('*.html'):
    t=p.read_text()
    if '/assets/analytics.20261016.js' in t:
        new_pages.append(p.relative_to(ROOT).as_posix())
        booking+=t.count('data-measure="booking_click"');ignored+=t.count('data-measure="ignore"')
manifest={'date':'2026-10-16','public_pages_with_updated_bridge':len(new_pages),'html_files_changed':sum(f.endswith('.html') for f in files),'booking_links_classified':booking,'non_booking_links_excluded':ignored,'media_or_font_files_changed':media,'benchmark_questions':30,'benchmark_planned_runs':360,'benchmark_runs_performed':0,'ga4_collection_verified':False,'deployment_verified':False,'scope':'Prepared and browser-tested changes; release and actual account data are verified separately.'}
(OUT/'delivery-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('DELIVERY MANIFEST',json.dumps(manifest,ensure_ascii=False))
