"""Author native SVG anatomy from clinician contours and approved clinic materials.

Raster inputs are embedded unchanged. All region boundaries, clipping, and
affine mesh geometry remain editable SVG; no patient pixels are retouched.
"""
from pathlib import Path
import argparse
import base64
import json
import subprocess
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'bilder/ultraljud/bursit-axel'
ART = ROOT / '.github/kansei/artwork/bursa'
VERSION = '20261016d'
CROPS = {
    'fat': [0, 0, 640, 1280/3],
    'muscle': [640, 0, 640, 1280/3],
    'tendon': [0, 1280/3, 640, 1280/3],
    'bone': [646, 432, 628, 414],
    'residual': [0, 950, 640, 300],
    'fluid': [640, 2560/3, 640, 1280/3],
}

def region(name, material, path, box, top=None, bottom=None, opacity=1):
    return dict(name=name, material=material, path=path, box=box,
                top=top, bottom=bottom, opacity=opacity)

BONE3 = 'M404 921 Q382 713 502 594 Q571 554 639 551 Q646 523 662 529 Q695 539 717 524 Q769 532 769 508 Q748 468 782 480 Q825 484 833 519 Q851 547 890 509 Q892 496 939 499 Q935 477 956 484 Q992 488 1018 524 Q1030 511 1054 512 Q1134 531 1167 555'
DEFECT4 = 'M290 442 Q339 436 379 427 L381 416 Q350 411 361 389 Q371 370 433 379 Q570 386 735 416 L733 443 Q789 492 793 544 Q805 579 832 621 Q866 673 862 737 Q870 782 860 833 Q824 843 701 834 Q668 827 662 767 L654 635 Q644 595 608 556 Q592 514 548 501 Q491 475 428 471 Q383 472 354 456 Q332 451 316 471 L297 469 Z'
STUMP4 = 'M397 374 Q314 370 250 402 Q222 420 228 459 L261 489 Q284 497 297 482 L297 470 Q275 459 289 440 Q330 434 379 427 L381 416 Q350 411 361 389 Q371 377 397 374 Z'

VIEWS = {
    'bursit-vy-1': {
        'tab': 'bursa-1',
        'guide': 'Bild 1 annoteirngar(2).jpg',
        'scan': 'M91 142 L1190 142 L1279 700 L1230 835 L0 835 L0 563 Z',
        'regions': [
            region('humerus', 'bone', 'M20 580 L82 524 Q150 490 175 496 Q210 501 215 480 Q240 445 282 449 L309 404 Q377 375 432 390 Q475 420 521 433 Q631 458 765 523 Q830 550 879 593 L891 601 Q1000 650 1038 700 Q1090 739 1117 767 L1140 890 L20 890 Z', [20,385,1120,505]),
            region('superficial-fat', 'fat', 'M0 149 L1280 149 L1240 435 Q1050 390 800 332 Q570 300 296 287 Q190 302 51 314 L0 325 Z', [0,149,1280,286],
                   [[0,149],[200,149],[400,149],[600,149],[800,149],[1000,149],[1280,149]],
                   [[0,325],[200,297],[400,293],[600,309],[800,332],[1000,378],[1280,446]]),
            region('deltoid', 'muscle', 'M51 314 Q190 302 296 287 Q570 300 800 332 Q1050 390 1240 435 L1180 730 Q1090 695 1080 632 Q1050 509 880 450 Q626 398 350 345 Q190 365 30 417 Z', [25,285,1220,450],
                   [[51,314],[200,297],[350,290],[500,301],[700,320],[900,355],[1100,404],[1240,435]],
                   [[30,417],[180,366],[350,345],[520,383],[700,419],[880,450],[1080,632],[1180,730]]),
            region('supraspinatus', 'tendon', 'M20 440 Q130 376 267 376 Q283 375 256 390 Q247 405 309 404 L282 449 Q230 449 215 490 Q200 510 153 495 Q92 505 35 551 L10 490 Z', [10,375,300,180]),
            region('bursa', 'fluid', 'M258 400 Q320 375 430 382 Q475 390 520 410 Q700 431 836 454 Q1012 509 1129 738 Q1146 763 1117 767 Q1038 741 951 658 Q866 573 765 523 Q631 458 521 433 Q465 422 432 390 Q358 387 304 402 Z', [250,378,900,395], opacity=.88),
        ],
        'cortex': 'M82 524 Q150 490 175 496 Q210 501 215 480 Q240 445 282 449 L309 404 Q377 375 432 390 Q475 420 521 433 Q631 458 765 523 Q830 550 879 593 L891 601 Q1000 650 1038 700 Q1090 739 1117 767',
    },
    'bursit-vy-2': {
        'tab': 'bursa-2',
        'guide': 'Bild 2 annoteringar(2).jpg',
        'scan': 'M91 142 L1190 142 L1279 560 L1279 835 L0 835 L0 540 Z',
        'regions': [
            region('humerus', 'bone', 'M122 855 Q130 775 198 755 Q230 792 280 780 Q350 755 430 690 Q570 580 658 531 Q750 511 759 540 Q872 579 978 637 Q1010 692 1065 691 Q1180 693 1274 722 L1279 900 L122 900 Z', [122,520,1157,380]),
            region('superficial-fat', 'fat', 'M0 149 L1280 149 L1280 325 Q1190 285 1100 267 Q900 245 700 244 Q500 245 300 263 Q150 280 44 305 L0 316 Z', [0,149,1280,176],
                   [[0,149],[200,149],[400,149],[600,149],[800,149],[1000,149],[1280,149]],
                   [[0,316],[200,272],[400,253],[600,245],[800,245],[1000,255],[1280,325]]),
            region('deltoid', 'muscle', 'M0 316 Q150 280 300 263 Q500 245 700 244 Q900 245 1100 267 Q1190 285 1240 311 L1279 325 L1279 503 Q1226 470 1180 432 Q1145 397 1115 388 Q1030 356 970 350 Q880 337 800 342 Q720 338 650 349 Q530 354 416 402 Q340 436 288 473 Q230 529 196 582 Q152 643 135 700 Q117 773 121 830 L0 855 Z', [0,244,1280,611],
                   [[0,840],[0,680],[0,510],[0,360],[100,293],[300,263],[500,249],[700,244],[900,250],[1100,267],[1240,311]],
                   [[121,840],[135,700],[196,582],[288,473],[416,402],[540,364],[650,349],[800,342],[970,350],[1115,388],[1279,503]]),
            region('supraspinatus', 'tendon', 'M658 531 Q779 469 937 468 Q1090 480 1276 611 L1274 722 Q1180 693 1065 691 Q1010 692 978 637 Q872 579 759 540 Q753 511 658 531 Z', [650,465,630,260],
                   [[658,520],[780,487],[937,468],[1100,505],[1276,611]],
                   [[658,542],[780,555],[978,637],[1100,697],[1274,722]]),
            region('bursa', 'fluid', 'M180 738 Q130 660 203 568 Q293 434 466 379 Q665 329 865 355 Q1118 366 1223 496 L1272 527 L1273 610 Q1092 493 940 468 Q807 467 659 504 Q535 611 381 725 Q273 813 233 773 Z', [155,340,1125,445], opacity=.87),
        ],
        'cortex': 'M198 755 Q230 792 280 780 Q350 755 430 690 Q570 580 658 531 Q750 511 759 540 Q872 579 978 637 Q1010 692 1065 691 Q1180 693 1274 722',
    },
    'supraspinatus': {
        'tab': 'supraspinatus',
        'guide': 'Bild 3 annoteringar(2).jpg',
        'scan': 'M169 142 L1110 142 L1240 835 L0 835 Z',
        'regions': [
            region('humerus', 'bone', BONE3+' L1220 920 Z', [400,475,820,445]),
            region('acromion', 'bone', 'M129 456 Q136 383 227 338 Q311 300 367 311 Q442 315 472 353 Q507 417 491 479 Q491 527 474 549 L475 900 L80 900 L85 462 Z', [85,305,420,595]),
            region('superficial-fat', 'fat', 'M110 149 L1140 149 L1126 362 Q991 322 901 290 Q762 266 517 285 Q438 299 378 283 Q249 264 122 265 Z', [110,149,1030,215],
                   [[122,149],[300,149],[500,149],[700,149],[900,149],[1126,149]],
                   [[122,265],[300,275],[500,287],[700,278],[900,290],[1126,362]]),
            region('deltoid', 'muscle', 'M122 265 Q249 264 378 283 Q438 299 517 285 Q762 266 901 290 Q991 322 1126 362 L1170 546 Q1120 527 1093 510 Q1037 461 977 400 Q950 380 923 376 Q883 363 847 366 Q750 354 690 367 Q640 371 570 389 L499 408 Q489 360 460 329 Q410 314 363 309 Q310 301 279 310 Q200 320 152 381 Q130 410 119 458 L85 462 Z', [85,264,1085,282]),
            region('supraspinatus', 'tendon', 'M500 455 Q606 420 649 408 Q802 387 898 415 Q967 442 1018 525 L1034 520 L1018 524 Q992 488 956 484 Q935 477 939 499 Q892 496 890 509 Q851 547 833 519 Q825 484 782 480 Q748 468 769 508 Q769 532 717 524 Q695 539 662 529 Q646 523 639 551 Q571 554 502 594 Z', [498,393,546,205]),
            region('bursa-location', 'tendon', 'M492 418 Q548 410 594 387 Q704 372 839 380 Q950 397 1005 450 L1077 506 L1073 526 L969 450 Q893 393 720 395 Q625 399 504 453 Z', [492,375,585,152], opacity=.67),
            region('rupture-upper', 'residual', 'M661 461 Q695 453 714 456 Q731 443 748 450 Q800 449 828 472 Q796 471 788 481 Q751 468 718 476 Q681 474 662 469 Z', [655,446,180,38]),
            region('rupture-lower', 'residual', 'M628 510 Q627 497 654 500 Q655 476 674 482 Q715 488 738 483 Q754 490 750 513 Q733 519 707 512 Q687 503 664 512 Q640 516 623 516 Z', [620,476,140,43]),
        ],
        'cortex': BONE3,
        'acromion_cortex': 'M129 456 Q136 383 227 338 Q311 300 367 311 Q442 315 472 353 Q507 417 491 479 Q491 527 474 549 L475 588',
    },
    'subscapularis': {
        'tab': 'subscapularis',
        'guide': 'Bild 4 annoteringar(1).jpg',
        'scan': 'M169 142 L1110 142 L1241 835 L0 835 Z',
        'regions': [
            region('humerus', 'bone', 'M0 540 Q95 510 218 489 L297 470 Q332 451 354 456 Q383 472 428 471 Q491 475 548 501 Q592 514 608 556 Q644 595 654 635 L662 767 Q668 827 701 834 L701 910 L0 910 Z', [0,450,705,460]),
            region('superficial-fat', 'fat', 'M130 149 L1130 149 L1140 264 Q1000 239 850 245 Q650 241 500 250 Q300 253 130 278 Z', [130,149,1010,130],
                   [[130,149],[350,149],[570,149],[800,149],[1140,149]],
                   [[130,278],[350,256],[570,246],[800,245],[1140,264]]),
            region('deltoid', 'muscle', 'M130 278 Q300 253 500 250 Q650 241 850 245 Q1000 239 1140 264 L1180 430 Q1010 415 850 414 Q760 422 650 395 Q500 387 397 374 Q314 370 250 402 Q185 387 110 370 Z', [110,240,1070,192],
                   [[130,278],[350,256],[570,246],[800,245],[1140,264]],
                   [[110,370],[350,375],[570,390],[800,416],[1180,430]]),
            region('subscapularis-defect', 'residual', DEFECT4, [287,375,582,465],
                   [[360,380],[500,388],[650,402],[735,418],[790,543],[850,667],[862,833]],
                   [[288,442],[350,458],[490,482],[548,501],[608,556],[654,635],[701,834]]),
            region('subscapularis-stump', 'tendon', STUMP4, [222,372,179,122]),
            region('separate-fluid', 'fluid', 'M830 431 Q899 423 958 433 L1067 441 Q1094 463 1093 485 L1094 516 Q1086 541 1046 547 Q1034 580 1007 571 Q971 581 953 565 Q912 559 898 540 Q884 504 866 487 Q830 461 820 450 Q816 435 830 431 Z', [815,424,285,155], opacity=.88),
        ],
        'cortex': 'M0 540 Q95 510 218 489 L297 470 Q332 451 354 456 Q383 472 428 471 Q491 475 548 501 Q592 514 608 556 Q644 595 654 635 L662 767 Q668 827 701 834',
    },
}

def data_uri(path):
    mime = 'image/webp' if path.suffix == '.webp' else 'image/jpeg'
    return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()

def mesh_region(item, defs):
    top = np.array(item['top'],float)
    bottom = np.array(item['bottom'],float)
    assert len(top)==len(bottom)
    # Extend the texture underneath the exact clip so curved edges never leave seams.
    span = bottom-top
    top = top-span*.12
    bottom = bottom+span*.12
    crop = CROPS[item['material']]
    source_x = np.linspace(crop[0],crop[0]+crop[2],len(top))
    rows = np.linspace(0,1,5)
    triangles=[]
    min_det = float('inf')
    for col in range(len(top)-1):
        for row in range(len(rows)-1):
            src=[];dst=[]
            for station,t in [(col,rows[row]),(col+1,rows[row]),(col+1,rows[row+1]),(col,rows[row+1])]:
                src.append([source_x[station],crop[1]+crop[3]*t])
                dst.append(top[station]*(1-t)+bottom[station]*t)
            for indices in [(0,1,2),(0,2,3)]:
                source=np.array(src)[list(indices)]
                target=np.array(dst)[list(indices)]
                mat=np.linalg.solve(np.column_stack([source,np.ones(3)]),target)
                a,b=mat[0];c,d=mat[1];e,f=mat[2]
                det=a*d-b*c
                if det<=0: raise ValueError(item['name']+' folded material mesh')
                min_det=min(min_det,float(det))
                center=target.mean(axis=0)
                padded=target+(target-center)*.012
                points=' '.join(f'{x:.5f},{y:.5f}' for x,y in padded)
                ident=item['name']+'-tri-'+str(len(triangles))
                defs.append(f'<clipPath id="{ident}"><polygon points="{points}"/></clipPath>')
                triangles.append(f'<g clip-path="url(#{ident})"><use xlink:href="#material" transform="matrix({a:.9f} {b:.9f} {c:.9f} {d:.9f} {e:.9f} {f:.9f})"/></g>')
    return ''.join(triangles),min_det

def build(key, view, preview):
    defs=[f'<image id="material" xlink:href="{data_uri(ART/"tissue-material.20261016d.jpg")}" width="1280" height="1280" preserveAspectRatio="none"/>',
          f'<clipPath id="scan"><path d="{view["scan"]}"/></clipPath>',
          '<linearGradient id="edge-fade" x1="0" y1="0" x2="0" y2="960" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="white"/><stop offset=".79" stop-color="white"/><stop offset=".89" stop-color="black"/><stop offset="1" stop-color="black"/></linearGradient>',
          '<mask id="scan-window" maskUnits="userSpaceOnUse" x="0" y="0" width="1280" height="960"><rect width="1280" height="960" fill="url(#edge-fade)"/><rect x="1136" y="165" width="77" height="245" fill="black"/></mask>',
          '<linearGradient id="bone-depth" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#24160b" stop-opacity="0"/><stop offset=".5" stop-color="#24160b" stop-opacity=".12"/><stop offset="1" stop-color="#0d0906" stop-opacity=".83"/></linearGradient>']
    # Small trabecular texture is mirrored at tile edges rather than stretched
    # with the depth of the bone region. Bone shape still belongs to its clip.
    crop=CROPS['bone'];tw,th=crop[2]*.7,crop[3]*.7
    bx,by=tw/crop[2],th/crop[3]
    defs.append(f'<clipPath id="bone-tile-window"><rect width="{tw}" height="{th}"/></clipPath>')
    defs.append(f'<g id="bone-tile" clip-path="url(#bone-tile-window)"><use xlink:href="#material" transform="matrix({bx} 0 0 {by} {-crop[0]*bx} {-crop[1]*by})"/></g>')
    tile='<use xlink:href="#bone-tile"/>'
    defs.append(f'<pattern id="bone-material" patternUnits="userSpaceOnUse" width="{tw*2}" height="{th*2}">{tile}<g transform="translate({tw*2} 0) scale(-1 1)">{tile}</g><g transform="translate(0 {th*2}) scale(1 -1)">{tile}</g><g transform="translate({tw*2} {th*2}) scale(-1 -1)">{tile}</g></pattern>')
    shapes=[];checks=[]
    for item in view['regions']:
        ident='region-'+item['name']
        defs.append(f'<clipPath id="{ident}"><path d="{item["path"]}"/></clipPath>')
        x,y,w,h=item['box'];crop=CROPS[item['material']]
        # A fully textured backing also fills small cap areas outside the warp band.
        paint=f'<svg overflow="hidden" x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{" ".join(map(str,crop))}" preserveAspectRatio="none"><use xlink:href="#material"/></svg>'
        if item['material']=='bone':
            paint=f'<path d="{item["path"]}" fill="url(#bone-material)"/>'
        if item['top']:
            mesh,minimum=mesh_region(item,defs)
            paint+=mesh
            checks.append({'region':item['name'],'minimum_material_jacobian':minimum})
        shape=f'<g data-tissue="{item["name"]}" clip-path="url(#{ident})" opacity="{item["opacity"]}">{paint}'
        if item['material']=='bone':
            shape+=f'<path d="{item["path"]}" fill="url(#bone-depth)"/>'
        shape+='</g>'
        shapes.append(shape)
        if item['name']=='deltoid':
            shapes.append(f'<path d="{item["path"]}" fill="none" stroke="#d7c5b4" stroke-width="2.4" opacity=".45"/>')
        if item['material']=='fluid':
            shapes.append(f'<path d="{item["path"]}" fill="none" stroke="#c8c7b3" stroke-width="1.8" opacity=".35"/>')
    # Cortical shape follows the clinician's line; it is never filled as another tissue.
    cortex=f'<path data-cortex="humerus" d="{view["cortex"]}" fill="none" stroke="#f1dfc1" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"/>'
    # Keep the cortex behind subscapularis fibers at their shared interface.
    shapes.append(cortex)
    if view.get('acromion_cortex'):
        shapes.append(f'<path d="{view["acromion_cortex"]}" fill="none" stroke="#f1dfc1" stroke-width="3.2" stroke-linejoin="round"/>')
    doc='<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1280" height="960" viewBox="0 0 1280 960"><title>Axel – konturpassat anatomilager</title><desc>Pedagogisk illustration med vävnadsgränser från undersökarens annoteringar. Bildfynden bedöms i originalultraljudet.</desc><defs>'+''.join(defs)+'</defs><g clip-path="url(#scan)" mask="url(#scan-window)">'+''.join(shapes)+'</g></svg>'
    vector=preview/(key+'-anatomy-source.svg')
    vector.write_text(doc)
    png=preview/(key+'-anatomy-source.png')
    subprocess.run(['inkscape','--batch-process',str(vector),'--export-type=png','--export-filename='+str(png)],check=True,capture_output=True)
    path=OUT/(key+'.anatomi.'+VERSION+'.webp')
    # Rendering the exact vector, followed by format compression; originals are not edited.
    subprocess.run(['convert',str(png),'-quality','94',str(path)],check=True,capture_output=True)
    if preview:
        # Internal review renders the unchanged original beneath the transparent SVG.
        base=f'<image xlink:href="{data_uri(OUT/(key+".original.jpg"))}" width="1280" height="960"/>'
        composite=doc.replace('<g clip-path="url(#scan)"',base+'<g clip-path="url(#scan)"',1)
        (preview/(key+'-preview.svg')).write_text(composite)
    return {'view':key,'asset':str(path.relative_to(ROOT)),'region_count':len(view['regions']),'mesh_checks':checks}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preview',type=Path,required=True);args=parser.parse_args()
    if args.preview:args.preview.mkdir(parents=True,exist_ok=True)
    results=[build(k,v,args.preview) for k,v in VIEWS.items()]
    (ART/('contours.'+VERSION+'.json')).write_text(json.dumps({'coordinate_system':[1280,960],'views':VIEWS},ensure_ascii=False,indent=2)+'\n')
    (ART/('registration-report.'+VERSION+'.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(results,ensure_ascii=False))
