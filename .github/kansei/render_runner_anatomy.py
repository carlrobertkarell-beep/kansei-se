"""Build native SVG tissue layers from source contours and imagegen textures.

Ultrasound and generated bitmap inputs are read without changing their pixels.
Geometry belongs to the ultrasound contour paths; the paintings supply material
texture only. This prevents a later image generation from changing tissue sizes.
"""
from pathlib import Path
import numpy as np
from scipy.spatial import Delaunay
import base64,json

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT
OUT=ROOT/'bilder/ultraljud/kna/loparkna'
VERSION='20261014-contours'

def uri(path):
    mime='image/jpeg' if path.suffix in ('.jpg','.jpeg') else 'image/'+path.suffix.lstrip('.')
    return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()

# These paths are traced in the original 1280 x 960 capture coordinates.
# They do not come from the generated image or the coloured guide image.
REGIONS={
'lateral-fluid':[
 ('superficial-fat','fat','M108 116 L1171 116 L1171 181 C1114 175 1066 163 1020 154 C952 141 869 145 807 152 C744 157 697 167 652 177 C534 186 391 182 285 186 C214 188 159 184 108 181 Z'),
 ('quadriceps','collagen','M108 181 C154 179 170 186 220 186 C362 184 476 185 600 183 C653 182 682 168 735 158 C802 147 856 146 921 147 C997 145 1047 155 1109 169 L1171 179 L1171 285 C1115 278 1095 280 1065 273 C1027 267 1014 263 976 267 C935 271 908 269 874 270 C830 273 802 280 752 279 C667 280 611 282 550 278 C489 275 432 269 381 264 C285 255 199 251 108 251 Z'),
 ('fat-pad','fat','M108 265 C254 266 401 275 575 273 C646 274 704 279 756 291 C783 299 802 315 814 338 C824 351 834 367 834 385 C834 400 827 408 809 413 C816 428 810 444 797 455 C782 463 762 454 746 447 C702 441 673 431 645 415 C625 402 625 380 611 373 C590 367 571 374 548 376 C401 393 231 389 111 380 Z'),
 ('left-bone','bone','M108 392 C295 393 461 397 575 385 C611 376 625 391 640 416 C666 446 706 454 744 470 C769 480 780 500 779 533 C779 582 783 622 801 655 L742 724 L108 724 Z'),
 ('right-bone','bone','M957 281 C1007 258 1052 276 1100 281 L1171 290 L1171 724 L1100 651 C1051 627 1010 598 981 544 C943 487 932 448 932 411 C928 355 932 307 957 281 Z'),
],
'itb-bursa':[
 ('superficial-fat','fat','M108 114 L1171 114 L1171 190 C1100 180 1060 183 1010 181 C932 173 880 178 810 176 C743 178 684 172 618 169 C479 164 415 168 320 167 C254 170 198 178 108 182 Z'),
 ('it-band','collagen','M108 182 C198 178 254 170 320 167 C415 168 479 164 618 169 C684 172 743 178 810 176 C880 178 932 173 1010 181 C1060 183 1100 180 1171 190 L1171 208 C1105 198 1054 196 1009 196 C934 190 879 184 800 187 C717 185 652 192 589 198 C482 203 414 213 309 220 C225 225 166 228 110 239 Z'),
 ('retinaculum','collagen','M695 194 C786 187 873 190 963 195 C1033 198 1082 197 1102 199 L1105 209 Q1135 215 1121 222 C1090 229 1046 230 993 232 C954 235 921 238 907 243 Q922 269 892 272 C869 272 835 262 816 256 Q791 251 794 240 C775 227 738 228 696 224 Q681 216 695 194 Z'),
 ('popliteus','collagen','M535 241 C573 238 601 245 628 260 C672 282 710 286 753 279 C778 278 789 270 801 261 L818 285 C796 282 780 298 764 320 C737 346 710 348 680 349 C645 352 610 342 589 319 C568 299 550 274 535 241 Z'),
 ('lateral-meniscus','meniscus','M957 243 C984 228 1010 229 1033 242 C1050 253 1070 255 1080 271 C1080 291 1064 294 1054 309 C1038 340 1038 379 1039 423 L1037 476 C1023 475 1026 442 1017 409 C1006 373 1007 350 990 320 C978 299 957 288 948 272 Q941 254 957 243 Z'),
 ('femur','bone','M129 308 C205 287 268 270 328 253 C376 240 414 236 451 241 C493 242 514 256 541 283 C568 309 597 340 629 360 C660 380 699 366 736 349 C771 332 784 303 811 288 C830 277 849 290 870 300 C912 323 952 357 972 396 L994 446 L1003 674 L109 674 L109 328 Z'),
 ('tibia','bone','M1081 285 C1108 274 1138 269 1171 265 L1171 674 L1044 674 L1042 470 C1044 412 1044 346 1068 309 Z'),
],
'posterior-meniscus':[
 ('superficial-fat','fat','M174 113 L1105 113 L1105 165 C984 165 872 166 745 166 C662 167 598 166 572 174 C549 180 552 198 569 211 C610 221 657 226 687 235 C789 260 862 280 950 300 C1008 314 1058 326 1105 333 L1105 348 C961 314 850 290 737 263 C588 231 519 215 413 207 C328 199 258 191 174 194 Z'),
 ('gastrocnemius','muscle','M572 174 C598 166 662 167 745 166 C872 166 984 165 1105 165 L1105 326 C1016 312 931 289 845 272 C785 261 752 262 724 251 C660 230 612 224 569 211 C552 198 549 180 572 174 Z'),
 ('semimembranosus','collagen','M174 194 C258 191 328 199 413 207 C519 215 588 231 737 263 C850 290 961 314 1105 348 L1105 386 C1027 379 954 348 873 332 C837 326 814 344 797 366 C754 365 706 348 663 333 C608 314 557 311 520 294 C470 272 408 253 356 244 C285 230 232 238 174 238 Z'),
 ('medial-meniscus','meniscus','M510 375 C535 358 568 357 599 358 C632 351 665 351 686 351 C708 355 732 363 751 373 C764 381 742 393 725 400 C711 414 713 442 710 472 L704 527 L696 555 C682 539 684 521 676 503 C669 484 658 466 660 449 C665 435 669 429 664 417 L643 390 Q634 384 638 397 L649 422 Q655 432 650 448 Q641 466 640 478 C640 495 651 511 659 528 C669 546 666 569 660 584 C645 566 639 547 628 526 C612 498 601 476 591 457 C570 425 536 400 513 385 Z'),
 ('femur','bone','M174 326 C202 321 230 322 257 322 C304 326 338 342 379 359 C427 378 467 405 507 434 C548 466 575 495 593 530 C607 557 618 592 628 634 L631 730 L174 730 Z'),
 ('tibia','bone','M784 375 C811 366 845 375 878 376 C917 377 950 391 982 403 C1023 417 1062 412 1105 399 L1105 730 L692 730 L701 618 C709 561 719 495 733 447 C743 414 761 391 784 375 Z'),
],
}

FLUID={
'lateral-fluid':'M758 297 C778 289 811 298 830 315 C846 327 848 345 868 354 C900 371 923 384 924 403 C925 420 907 416 891 421 C879 433 882 463 873 490 L847 630 Q833 653 806 663 L791 644 L773 620 L768 558 L761 525 Q753 501 772 482 L801 468 L812 447 L816 425 Q842 413 836 390 C832 371 813 349 803 329 C790 313 773 308 758 306 Z',
'itb-bursa':'M215 235 C264 226 310 221 356 217 L449 204 C489 199 509 201 551 201 L605 201 L666 199 Q680 212 674 226 Q670 234 650 231 L584 224 L530 214 L467 215 L391 224 L318 231 L267 247 Q235 256 215 248 Q202 243 215 235 Z',
}


PAINT={
'lateral-fluid':OUT/'lateral-fluid-material-v3.webp',
'itb-bursa':OUT/'itb-bursa-anatomi-v2.webp',
'posterior-meniscus':OUT/'posterior-meniscus-anatomi.webp',
}

# Pairs are (original coordinate, painting coordinate). They register complete
# painted tissue against source landmarks without repeating or substituting its
# material texture. Source contour clipping is an additional geometry guard.
LANDMARKS={
 'lateral-fluid':[
 ((108,112),(102,104)),((1171,112),(1166,104)),
 ((150,182),(150,169)),((300,185),(300,168)),((500,184),(500,172)),
 ((650,180),(650,168)),((800,153),(800,151)),((950,147),(950,142)),
 ((1100,167),(1100,169)),((1171,179),(1166,188)),
 ((150,251),(150,241)),((300,258),(300,256)),((500,275),(500,271)),
 ((650,281),(650,277)),((800,278),(800,285)),((950,269),(950,267)),
 ((108,380),(108,372)),((300,386),(300,378)),((550,376),(550,369)),
 ((611,373),(611,377)),((645,415),(645,410)),((797,455),(797,452)),
 ((834,385),(830,382)),((758,297),(747,292)),((803,329),(800,327)),
 ((924,403),(915,399)),((891,421),(892,420)),((806,663),(815,667)),
 ((957,281),(945,279)),((1100,281),(1100,282)),
 ],
 'itb-bursa':[
 ((108,112),(111,115)),((1171,112),(1213,115)),
 ((108,182),(111,184)),((320,167),(332,175)),((618,169),(640,179)),
 ((810,176),(830,181)),((1010,181),(1034,189)),((1171,190),(1213,207)),
 ((110,239),(115,256)),((309,220),(321,225)),((589,198),(614,203)),
 ((215,242),(223,253)),((449,209),(466,224)),((666,214),(687,224)),
 ((535,241),(560,253)),((628,260),(641,273)),((680,349),(687,366)),
 ((801,261),(823,274)),
 ((129,308),(137,321)),((328,253),(350,275)),((451,241),(478,250)),
 ((541,283),(554,289)),((629,360),(651,361)),((736,349),(751,360)),
 ((811,288),(845,298)),((870,300),(899,315)),((972,396),(1001,416)),
 ((994,446),(1024,463)),((1081,285),(1110,304)),
 ((957,243),(984,255)),((1037,476),(1049,464)),
 ],
 'posterior-meniscus':[
 ((174,112),(174,111)),((1105,112),(1105,111)),
 ((174,194),(174,194)),((413,207),(413,203)),((572,174),(557,172)),
 ((745,166),(745,165)),((1105,165),(1105,165)),
 ((569,211),(569,210)),((724,251),(724,252)),((1105,326),(1105,342)),
 ((174,238),(174,242)),((356,244),(356,254)),((520,294),(519,290)),
 ((663,333),(663,337)),((797,366),(797,365)),
 ((510,375),(482,377)),((599,358),(600,358)),((686,351),(686,369)),
 ((751,373),(758,380)),((725,400),(729,401)),((710,472),(706,473)),
 ((696,555),(695,549)),((660,584),(665,584)),((628,526),(638,526)),
 ((591,457),(583,447)),((643,390),(640,391)),((646,481),(651,481)),
 ((174,326),(174,325)),((257,322),(257,322)),((379,359),(379,362)),
 ((507,434),(507,438)),((593,530),(588,529)),
 ((784,375),(786,374)),((878,376),(878,377)),((982,403),(982,403)),
 ],
}

def build(key,painting):
    original=OUT/(key+'-ultraljud.jpg')
    pairs=[((0,0),(0,0)),((1280,0),(1280,0)),((0,960),(0,960)),((1280,960),(1280,960)),
           ((108,760),(108,760)),((1171,760),(1171,760))]+LANDMARKS[key]
    target=np.array([a for a,b in pairs],dtype=float)
    source=np.array([b for a,b in pairs],dtype=float)
    mesh=Delaunay(source)
    defs=[f'<image id="paint" xlink:href="{uri(painting)}" width="1280" height="960" preserveAspectRatio="none"/>',
          f'<image id="original" xlink:href="{uri(original)}" width="1280" height="960"/>']
    defs.append('<clipPath id="tissue-contours">'+''.join(f'<path d="{d}"/>' for n,m,d in REGIONS[key])+'</clipPath>')
    triangles=[];max_error=0
    for i,ids in enumerate(mesh.simplices):
        src=source[ids];dst=target[ids]
        mat=np.linalg.solve(np.column_stack([src,np.ones(3)]),dst)
        a,b=mat[0];c,d=mat[1];e,f=mat[2]
        det=a*d-b*c
        if det<=0: raise ValueError(f'{key}: flipped tissue triangle {i}')
        max_error=max(max_error,float(np.max(np.abs(np.column_stack([src,np.ones(3)])@mat-dst))))
        # A tiny overlap eliminates antialias seams between neighbouring clips.
        center=dst.mean(axis=0);padded=dst+(dst-center)*.003
        points=' '.join(f'{x:.5f},{y:.5f}' for x,y in padded)
        defs.append(f'<clipPath id="triangle-{i}"><polygon points="{points}"/></clipPath>')
        triangles.append(f'<g clip-path="url(#triangle-{i})"><use xlink:href="#paint" transform="matrix({a:.9f} {b:.9f} {c:.9f} {d:.9f} {e:.9f} {f:.9f})"/></g>')
    x0,x1=(174,1105) if key=='posterior-meniscus' else (108,1171)
    defs.append(f'<clipPath id="scan"><rect x="{x0}" y="112" width="{x1-x0}" height="648"/></clipPath>')
    findings=[]
    if key in FLUID:
        defs.append(f'<clipPath id="source-fluid"><path d="{FLUID[key]}"/></clipPath>')
        findings.append('<g clip-path="url(#source-fluid)"><use xlink:href="#original"/></g>')
    if key=='posterior-meniscus':
        cleft='M637 391 Q659 417 653 440 Q644 462 646 481 Q648 499 658 520 Q671 547 662 579'
        defs.append(f'<clipPath id="source-cleft"><path d="{cleft}" fill="none" stroke="white" stroke-width="14"/></clipPath>')
        findings.append('<g clip-path="url(#source-cleft)"><use xlink:href="#original"/></g>')
    doc='<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1280" height="960" viewBox="0 0 1280 960"><title>Konturpassat anatomilager</title><defs>'+''.join(defs)+'</defs><use xlink:href="#original"/><g clip-path="url(#scan)"><g clip-path="url(#tissue-contours)">'+''.join(triangles)+'</g>'+''.join(findings)+'</g></svg>'
    out=OUT/(key+'-anatomi-'+VERSION+'.svg');out.write_text(doc)
    print(key,'landmarks',len(pairs),'triangles',len(mesh.simplices),'landmark residual',f'{max_error:.8f}px')
    return out

if __name__=='__main__':
    for key,painting in PAINT.items():
        f=build(key,painting);print(key, f.name, f.stat().st_size)
    (OUT/'source-contours.20261014.json').write_text(json.dumps({'coordinate_system':[1280,960],'version':VERSION,'regions':REGIONS,'fluid':FLUID},ensure_ascii=False,indent=2))
