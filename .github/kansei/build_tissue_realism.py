"""Build the approved tissue-realism images with one global placement per view.

Run from the repository root. Generation, registration and visual review records
are kept together; this script never generates material or changes source scans.
"""
from pathlib import Path
import argparse, base64, hashlib, html, importlib.util, json, subprocess
import numpy as np
from PIL import Image
from paint_registration import register
from ultrasound_layer_check import Document, ANATOMY, local_source

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / '.github/kansei/artwork/tissue-realism-20261022'
QA = ROOT.parent / 'realism-qa'
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def bounds(path, threshold=15):
    im = Image.open(path).convert('RGBA')
    a = np.asarray(im)
    keep = (a[:,:,:3].max(2) > threshold) & (a[:,:,3] > 32)
    y,x = np.where(keep)
    return [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]

def xml(node):
    if node.tag in ('script','style'):
        return ''
    if node.tag == 'text' or node.tag == 'tspan':
        return ''
    attrs = dict(node.attrs)
    attrs.pop('aria-hidden',None)
    attrs.pop('id',None)
    attrs = {'viewBox' if k=='viewbox' else k:v for k,v in attrs.items()}
    inner = ''.join(xml(c) for c in node.children)
    return '<'+node.tag+' '+ ' '.join(k+'="'+html.escape(str(v),quote=True)+'"' for k,v in attrs.items() if v is not None)+'>'+inner+'</'+node.tag+'>'

def source_findings(spec):
    doc=Document((ROOT/spec['case']/'index.html').read_text())
    for p in doc.root.walk():
        if not p.classes.intersection({'patient-picture','knee-picture'}):continue
        if not any(n.tag in ('img','image') and n.attrs.get('src') in ('/'+spec['anatomy'],'/'+spec['output']) for n in p.walk()):continue
        layers=[n for n in p.walk() if 'knee-findings' in n.classes or ('patient-finding' in n.classes and n.attrs.get('data-finding-mode')=='ultrasound')]
        if len(layers)!=1: raise ValueError('Finding layer missing '+spec['key'])
        return xml(layers[0])
    raise ValueError('Picture missing '+spec['key'])

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--keys',nargs='*')
    args=parser.parse_args()
    specs=json.loads((ART/'prompts.json').read_text())
    files=json.loads((ART/'generation-files.json').read_text())
    config_path=ART/'placements.json'
    config=json.loads(config_path.read_text()) if config_path.exists() else {}
    manifest_path=ART/'manifest.json'
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for s in specs:
        key=s['key']
        if key not in files or (args.keys and key not in args.keys):continue
        painting=Path(files[key])
        with Image.open(painting) as im: pw,ph=im.size
        target=bounds(ROOT/s['anatomy'])
        source=bounds(painting)
        # Fit scan width and top edge. Depth falloff changes with the material;
        # its brightness threshold is deliberately not a vertical size anchor.
        left,top,right,bottom=target;sl,st,sr,sb=source
        scale=(right-left)/(sr-sl)
        source=[sl,st,sr,st+(bottom-top)/scale]
        chosen=config.get(key,{'source_bounds':source,'target_bounds':target})
        rec=register(painting,ROOT/s['output'],ART/(key+'.painting.webp'),s['size'],
                     chosen['source_bounds'],chosen['target_bounds'],QA,s.get('has_alpha',False))
        rec.update({'key':key,'original':s['original'],'original_sha256':s['original_sha256'],
                    'previous_anatomy':s['anatomy'],'previous_anatomy_sha256':s['previous_anatomy_sha256'],
                    'approved_reference_sha256':s['approved_reference_sha256'],
                    'source_png_sha256':SHA(painting),'preserves_alpha':s.get('has_alpha',False)})
        for name in ('archive','asset'):
            rec[name]=str(Path(rec[name]).relative_to(ROOT))
        rec['qa_png']=str(Path(rec['qa_png']).relative_to(ROOT.parent))
        manifest[key]=rec
        config[key]={'source_bounds':chosen['source_bounds'],'target_bounds':chosen['target_bounds']}
        png=QA/(Path(s['output']).stem+'.png')
        data=base64.b64encode(png.read_bytes()).decode()
        w,h=s['size']
        outlines=source_findings(s)
        # Strip non-SVG wrapper: the inner SVG retains its original viewBox.
        svg_start=outlines.find('<svg')
        if svg_start>=0:
            outlines=outlines[svg_start:outlines.rfind('</svg>')+6]
            # The website may crop a source scan through its SVG viewport.
            # QA instead draws its fixed source coordinates on the full bitmap.
            import re
            start=outlines[:outlines.index('>')+1]
            rest=outlines[len(start):]
            start=re.sub(r'viewBox="[^"]*"',f'viewBox="0 0 {w} {h}"',start)
            start=start[:-1]+f' width="{w}" height="{h}">'
            outlines=start+rest
        qa_svg=(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
                '<style>svg{overflow:visible}path,polygon,polyline,line,ellipse{fill:none!important;stroke:#ffdc76!important;stroke-width:2!important}circle{fill:#ffdc76!important;stroke:#193237!important;stroke-width:1!important}.affected-cartilage{fill:#ffdc7611!important}</style>'
                f'<rect width="{w}" height="{h}" fill="black"/><image xlink:href="data:image/png;base64,{data}" width="{w}" height="{h}"/>{outlines}</svg>')
        q=QA/(key+'.findings.svg');q.write_text(qa_svg)
        qa_png=QA/(key+'.findings.png')
        for attempt in range(2):
            destination=qa_png if not attempt else QA/(key+'.findings.retry.png')
            subprocess.run(['inkscape','--batch-process',str(q),'--export-type=png','--export-filename='+str(destination)],check=True,capture_output=True)
            try:
                Image.open(destination).load()
                if destination!=qa_png:destination.replace(qa_png)
                break
            except OSError:
                if attempt:raise
        print(key,flush=True)
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    config_path.write_text(json.dumps(config,indent=2)+'\n')

if __name__=='__main__': main()
