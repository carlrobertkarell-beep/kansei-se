"""Register clean AC paintings to the unchanged native clinical scan canvases."""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paint_registration import register

VERSION = '20261021f'
ART = ROOT / '.github/kansei/artwork/layer-audit-20261021/ac'
ASSETS = ROOT / 'bilder/ultraljud/ac-led'
SPECS = [
    dict(key='jamforelse-skadad', painting='exec-1d3e2779-76f0-47b0-a52e-ced33bdeeed1.png', canvas=[1280,830], source=[182,56,1376,920], target=[169,41,1110,732],
         labels=[(217,250,'Clavicula'),(354,286,'Subclavius'),(760,270,'Pectoralis major'),(850,84,'Subkutant fett'),(1030,545,'Korakoiden'),(440,610,'Revben')],
         finding='<path d="M295 354 L960 480" class="ac-distance"/><circle cx="295" cy="354" r="8"/><circle cx="960" cy="480" r="8"/><text x="665" y="555">Avstånd mellan benen</text>'),
    dict(key='jamforelse-motsatt', painting='exec-dc7fbda5-8b30-4724-b34f-a6a945e282e2.png', canvas=[1280,830], source=[207,53,1350,903], target=[169,41,1110,732],
         labels=[(315,170,'Clavicula'),(565,335,'Subclavius'),(830,200,'Pectoralis major'),(900,78,'Subkutant fett'),(1020,510,'Korakoiden')],
         finding='<path d="M437 223 L946 423" class="ac-distance"/><circle cx="437" cy="223" r="8"/><circle cx="946" cy="423" r="8"/><text x="710" y="515">Avstånd mellan benen</text>'),
    dict(key='ac-led', painting='exec-be168a14-7268-488f-8b5b-18d72186e9d1.png', canvas=[942,690], source=[0,0,1465,1073], target=[0,0,942,690],
         labels=[(330,280,'Clavicula'),(790,375,'Akromion'),(650,170,'AC-ledens kapsel'),(550,390,'AC-leden')],
         finding='<path class="finding-pointer-shadow" d="M365 345 L735 250"/><path class="finding-pointer" d="M365 345 L735 250"/><circle cx="735" cy="250" r="6"/><text x="365" y="325">AC-ledens kapselområde</text>'),
    dict(key='mjukdelsplan', painting='exec-c468604e-cf33-4cd0-a7ad-1cb23d34b251.png', canvas=[942,690], source=[0,0,1465,1073], target=[0,0,942,690],
         labels=[(320,60,'Subkutant fett'),(450,210,'Clavicula')],
         finding='<path class="finding-pointer-shadow" d="M405 370 L660 116"/><path class="finding-pointer" d="M405 370 L660 116"/><circle cx="660" cy="116" r="6"/><text x="365" y="400">Spalt vid benytan</text>'),
]


def svg_labels(spec):
    w,h=spec['canvas']
    text=''.join(f'<text x="{x}" y="{y}">{label}</text>' for x,y,label in spec['labels'])
    return f'<svg class="ac-anatomy-labels" viewBox="0 0 {w} {h}" aria-hidden="true">{text}</svg>'


def finding(spec):
    w,h=spec['canvas']
    return f'<svg class="ac-registered-findings" viewBox="0 0 {w} {h}" aria-hidden="true">{spec["finding"]}</svg>'


def update_page():
    page=ROOT/'ultraljud/axel/ac-ledsskada/index.html'
    s=page.read_text()
    s=s.replace('simple-case ultrasound-case"','simple-case ultrasound-case ac-alignment-case"')
    if '/assets/ac-alignment.20261021f.css' not in s:
        s=s.replace('</head>','<link href="/assets/ac-alignment.20261021f.css" rel="stylesheet"></head>',1)
    # The four panels are separate pictures. Replace their anatomy sources and
    # make both modes use the very same source-derived finding coordinates.
    for spec in SPECS:
        key=spec['key']
        old=re.compile(r'(<div class="patient-picture"[^>]*>)(.*?)(?=</div></div><figcaption>)',re.S)
        match=next((m for m in old.finditer(s) if f'/ac-led/{key}.jpg' in m[2]),None)
        if not match:
            raise ValueError('Missing picture '+key)
        block=match[2]
        block=re.sub(r'(<img\b[^>]*class="patient-anatomy-image"[^>]*src=")[^"]+("[^>]*>)', lambda m:m[1]+f'/bilder/ultraljud/ac-led/{key}-anatomi.{VERSION}.webp'+m[2],block,count=1)
        # Idempotent re-build: labels have no embedded raster annotation.
        block=re.sub(r'<svg class="ac-anatomy-labels".*?</svg>','',block,flags=re.S)
        block=re.sub(r'(<img\b[^>]*class="patient-anatomy-image"[^>]*>)',lambda m:m[1]+svg_labels(spec),block,count=1)
        for mode in ['ultrasound','anatomy']:
            pattern=re.compile(r'(<div class="patient-finding" data-finding-mode="'+mode+r'" aria-hidden="true">).*?(</div>)',re.S)
            block,n=pattern.subn(lambda m:m[1]+finding(spec)+m[2],block,count=1)
            if n!=1:raise ValueError('Missing findings '+key+' '+mode)
        s=s[:match.start(2)]+block+s[match.end(2):]
    s=re.sub(r'("dateModified"\s*:\s*")[^"]+(" )',r'\g<1>2026-10-21\2',s)
    # JSON-LD formatting in this document has no space after the date value.
    s=re.sub(r'("dateModified"\s*:\s*")[^"]+(")',r'\g<1>2026-10-21\2',s)
    page.write_text(s)


def build(workspace):
    workspace=Path(workspace)
    ART.mkdir(parents=True,exist_ok=True)
    records=[]
    for spec in SPECS:
        source=workspace/'generated_images'/spec['painting']
        archive=ART/(spec['key']+'.painting.'+VERSION+'.webp')
        if not source.exists():source=archive
        original=ASSETS/(spec['key']+'.jpg')
        record=register(source,ASSETS/(spec['key']+'-anatomi.'+VERSION+'.webp'),archive,spec['canvas'],spec['source'],spec['target'],workspace/'audit-qa/ac-new')
        record['key']=spec['key']
        record['original_sha256']=hashlib.sha256(original.read_bytes()).hexdigest()
        record['labels']=spec['labels']
        record['finding_geometry']=spec['finding']
        records.append(record)
    (ART/'registration.json').write_text(json.dumps({'version':VERSION,'views':records,'findings_policy':'Identical finding geometry in original and anatomy modes. Caliper endpoints use native clinical scan positions; no new measurement. AC and soft-plane pointer, shadow and dot now agree. Soft-plane anchor follows the visible upper separation rather than the previous inconsistent lower-bone endpoint.','previous_authored_endpoints':{'ac-led':{'shadow_dot':[735,250],'colored_pointer':[750,285]},'mjukdelsplan':{'shadow_dot':[760,225],'colored_pointer':[770,180]},'damaged_anatomy_distance':[[320,414],[1070,580]]}},ensure_ascii=False,indent=2)+'\n')
    update_page()
    print(json.dumps({'registered':len(records),'page':'/ultraljud/axel/ac-ledsskada/'}))

if __name__=='__main__':build(sys.argv[1])
