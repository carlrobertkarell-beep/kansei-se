"""Register approved painted materials to the clinician's Achilles contours.

Only the anatomy layer is rendered. Original ultrasound pixels and finding
coordinates are retained separately. Requires Pillow, numpy, scipy and Inkscape.
"""
from pathlib import Path
from PIL import Image
from scipy.interpolate import RBFInterpolator
import numpy as np
import base64,io,json,argparse,subprocess
ROOT=Path(__file__).resolve().parents[2]
ASSETS=ROOT/'bilder/ultraljud/halsena'
MATERIALS=ROOT/'.github/kansei/artwork/halsena'
GEOMETRY=ROOT/'.github/kansei/artwork/achilles-contours.20261015.json'
def uri(path):
    if path.suffix=='.webp':
        stream=io.BytesIO();Image.open(path).save(stream,'PNG');data=stream.getvalue();mime='image/png'
    else:data=path.read_bytes();mime='image/jpeg'
    return 'data:'+mime+';base64,'+base64.b64encode(data).decode()
def render(key,data,out):
    pairs=[[[0,0],[0,0]],[[1280,0],[1280,0]],[[0,960],[0,960]],[[1280,960],[1280,960]]]+data['landmarks']
    targets=np.array([a for a,b in pairs],float);sources=np.array([b for a,b in pairs],float)
    # An inverse displacement field gives a continuous warp without triangle seams.
    fit=RBFInterpolator(targets,sources-targets,kernel='thin_plate_spline',smoothing=80)
    displacement=np.zeros((960,1280,2),float)
    for y0 in range(0,960,32):
        yy,xx=np.mgrid[y0:min(y0+32,960),0:1280]
        pts=np.column_stack([xx.ravel(),yy.ravel()]);displacement[y0:y0+len(yy)]=fit(pts).reshape(len(yy),1280,2)
    residual=float(np.abs(targets+fit(targets)-sources).max())
    dxdy,dxdx=np.gradient(displacement[:,:,0]);dydy,dydx=np.gradient(displacement[:,:,1]);jac=(1+dxdx)*(1+dydy)-dxdy*dydx
    minimum=float(jac[112:889,108:1172].min())
    if minimum<=0:raise ValueError(f'{key}: displacement field folds: {minimum}')
    material=f'<image id="material" href="{uri(MATERIALS/(key+"-material.20261015.webp"))}" width="1280" height="960"/>'
    cleanup=''
    defs=[f'<image id="original" href="{uri(ASSETS/(key+"-ultraljud.jpg"))}" width="1280" height="960"/>',material,'<g id="paint"><use href="#material"/></g>','<clipPath id="scan"><rect x="108" y="112" width="1064" height="777"/></clipPath>']
    # Keep the machine's original labels and readouts outside the illustration.
    fade_start,fade_end=(570,640) if key=='healthy' else (700,820) if key=='longitudinal' else (730,850)
    defs += [f'<linearGradient id="fade" x1="0" y1="0" x2="0" y2="960" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="black"/><stop offset=".135" stop-color="black"/><stop offset=".17" stop-color="white"/><stop offset="{fade_start/960}" stop-color="white"/><stop offset="{fade_end/960}" stop-color="black"/><stop offset="1" stop-color="black"/></linearGradient>','<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="18"/></filter><mask id="window" maskUnits="userSpaceOnUse" x="0" y="0" width="1280" height="960"><rect width="1280" height="960" fill="url(#fade)"/><rect x="0" y="600" width="232" height="180" fill="black" filter="url(#soft)"/><rect x="0" y="675" width="220" height="70" fill="black"/></mask>']
    # Native SVG affine patches approximate the continuous inverse field. Small
    # overlaps prevent antialiasing seams; the original field remains independent.
    mesh=[]
    xx=np.linspace(108,1172,15);yy=np.linspace(112,889,12)
    for j in range(len(yy)-1):
        for i in range(len(xx)-1):
            cell=np.array([[xx[i],yy[j]],[xx[i+1],yy[j]],[xx[i+1],yy[j+1]],[xx[i],yy[j+1]]])
            for ids in [[0,1,2],[0,2,3]]:
                target=cell[ids];source=target+fit(target)
                matrix=np.linalg.solve(np.column_stack([source,np.ones(3)]),target)
                center=target.mean(axis=0);expanded=target+(target-center)*.009
                idx=len(mesh);points=' '.join(f'{x:.4f},{y:.4f}' for x,y in expanded)
                defs.append(f'<clipPath id="patch{idx}"><polygon points="{points}"/></clipPath>')
                a,b=matrix[0];c,d=matrix[1];e,f=matrix[2]
                mesh.append(f'<g clip-path="url(#patch{idx})"><use href="#paint" transform="matrix({a} {b} {c} {d} {e} {f})"/></g>')
    doc='<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1280" height="960" viewBox="0 0 1280 960"><title>Hälsena – konturpassat anatomilager</title><defs>'+''.join(defs)+'</defs><use href="#original"/><g clip-path="url(#scan)" mask="url(#window)">'+''.join(mesh)+'</g></svg>'
    doc=doc.replace(' href=',' xlink:href=')
    svg=out/(key+'-registered.svg');svg.write_text(doc);png=out/(key+'-registered.png')
    subprocess.run(['inkscape','--batch-process',str(svg),'--export-overwrite','--export-width=1280','--export-type=png','--export-filename='+str(png)],check=True,capture_output=True)
    image=Image.open(png).convert('RGB');image.save(ASSETS/(key+'-anatomi.20261015.webp'),'WEBP',quality=93,method=6);image.save(out/(key+'-registered.jpg'),quality=93)
    return {'view':key,'landmarks':len(pairs),'maximum_landmark_error_px':residual,'minimum_jacobian':minimum}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    data=json.loads(GEOMETRY.read_text());results=[render(key,view,out) for key,view in data['views'].items()]
    (out/'registration-report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(results))
