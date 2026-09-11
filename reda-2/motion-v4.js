/* Reda movement studio 4. Pose geometry and illustration are separate.
 * Reviewed contact constraints, pending clinical approval of each complete motion.
 */
(function(root){'use strict';
const F=root.RedaFigures,R=root.RedaReferenceMotion;if(!F||!R)return;
const additional=['leg-press.bilateral','split-squat.rfess','split-squat.rfess-loaded'],keys=new Set([...R.keys,...additional]);
const aliases={'chair-support':'sit-to-stand.support','chair-free':'sit-to-stand.free',extension:'knee-extension.seated','extension-pause':'knee-extension.pause','calf-both':'calf-raise.bilateral',bridge:'bridge.bilateral','bridge-pause':'bridge.pause'};
const clamp=t=>Math.max(0,Math.min(1,t)),mix=(a,b,t)=>a+(b-a)*t,at=(a,b,t)=>[mix(a[0],b[0],t),mix(a[1],b[1],t)],add=(a,b)=>[a[0]+b[0],a[1]+b[1]],polar=(a,l,t)=>add(a,[l*Math.cos(t),l*Math.sin(t)]),dist=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
function joint(a,b,l1,l2,sign=-1){const d=dist(a,b);if(d>l1+l2+.001||d<Math.abs(l1-l2)-.001||d<.001)throw Error('Unsupported joint position');const z=(l1*l1-l2*l2+d*d)/(2*d),h=Math.sqrt(Math.max(0,l1*l1-z*z)),ux=(b[0]-a[0])/d,uy=(b[1]-a[1])/d;return [a[0]+ux*z-sign*uy*h,a[1]+uy*z+sign*ux*h]}
function pose(key,t){key=aliases[key]||key;t=clamp(t);if(!keys.has(key))return null;
 if(!additional.includes(key)){
  const q=R.pose(key,t);
  if(key==='sit-to-stand.support'){const rise=clamp((t-.23)/.77),free=polar(q.shoulder,65,.38+1.08*rise);q.hand=at([247,270],free,clamp((t-.24)/.3));q.elbow=joint(q.shoulder,q.hand,38,38)}
  return q;
 }
 let hip,shoulder,knee,ankle,heel,toe,hand,back;
 const press=key==='leg-press.bilateral';
 if(press){hip=[230,290];shoulder=polar(hip,80,-2.05);ankle=at([305,255],[337,220],t);knee=joint(hip,ankle,72,72,-1);heel=add(ankle,[-4,13]);toe=add(ankle,[21,-11]);hand=[266,260];back={hip:add(hip,[-8,-3]),knee:add(knee,[-8,-3]),ankle:add(ankle,[-8,-3]),heel:add(heel,[-8,-3]),toe:add(toe,[-8,-3])};}
 else{hip=at([288,244],[287,278],t);shoulder=polar(hip,80,-Math.PI/2+.13);ankle=[345,364];heel=[334,378];toe=[372,378];knee=joint(hip,ankle,72,72,-1);hand=add(shoulder,[4,73]);const rear=[208,306];back={hip,knee:joint(hip,rear,72,72,1),ankle:rear,heel:[195,320],toe:[228,320]};}
 return {hip,shoulder,knee,ankle,heel,toe,hand,elbow:joint(shoulder,hand,38,38,-1),head:add(shoulder,[-1,-36]),back,press,bench:!press,weighted:key.endsWith('loaded')};
}
function camera(key){if(key.startsWith('bridge.'))return [128,257,315,143];if(key.startsWith('step-up.'))return [180,12,270,392];if(key.startsWith('knee-extension.'))return [168,130,267,270];if(key.startsWith('leg-press.'))return [155,137,258,268];return [165,65,280,340]}
const clean=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function stroke(a,b,w,c){return `<path d="M${a}L${b}" fill="none" stroke="${c}" stroke-width="${w}" stroke-linecap="round"/>`}
function limb(a,b,w1,w2,color){const d=dist(a,b),nx=-(b[1]-a[1])/d,ny=(b[0]-a[0])/d;const p=(v,w,s)=>add(v,[nx*w*s,ny*w*s]);return `<path d="M${p(a,w1,1)}Q${p(at(a,b,.65),w2*1.14,1)} ${p(b,w2,1)}Q${add(b,[(b[0]-a[0])/d*w2,(b[1]-a[1])/d*w2])} ${p(b,w2,-1)}L${p(a,w1,-1)}Q${add(a,[-(b[0]-a[0])/d*w1,-(b[1]-a[1])/d*w1])} ${p(a,w1,1)}Z" fill="${color}"/>`}
function foot(h,t,color){const angle=Math.atan2(t[1]-h[1],t[0]-h[0])*180/Math.PI,length=dist(h,t);return `<g transform="translate(${h}) rotate(${angle})"><path d="M-6,-10Q1,-14 9,-9L${length-3},-7Q${length+9},-6 ${length+7},0H-6Z" fill="${color}"/><path d="M-6,0H${length+7}" stroke="#dae3e6" stroke-width="3"/><path d="M9,-8l11,3" stroke="#81929d" stroke-width="2"/></g>`}
function person(q,id){const b=q.back,shirt=`url(#${id}-shirt)`,pants=`url(#${id}-pants)`,skin=`url(#${id}-skin)`;let s=`<g opacity=".75">${limb(b.hip||q.hip,b.knee,16,11,'#496071')}${limb(b.knee,b.ankle,11,7,'#496071')}${foot(b.heel,b.toe,'#71828b')}</g>`;
 s+=limb(q.hip,q.knee,19,12,pants)+limb(q.knee,q.ankle,12,7,pants)+foot(q.heel,q.toe,'#263d50');
 s+=stroke(at(q.hip,q.knee,.18),at(q.hip,q.knee,.82),1.2,'#647988');
 const u=[(q.hip[0]-q.shoulder[0])/80,(q.hip[1]-q.shoulder[1])/80],v=[-u[1],u[0]],pt=(a,n)=>add(a,[v[0]*n,v[1]*n]);
 s+=`<path d="M${pt(q.shoulder,19)}Q${pt(at(q.shoulder,q.hip,.52),23)} ${pt(q.hip,18)}Q${add(q.hip,[u[0]*7,u[1]*7])} ${pt(q.hip,-18)}Q${pt(at(q.shoulder,q.hip,.5),-18)} ${pt(q.shoulder,-19)}Q${add(q.shoulder,[-u[0]*10,-u[1]*10])} ${pt(q.shoulder,19)}Z" fill="${shirt}"/>`;
 s+=stroke(pt(at(q.shoulder,q.hip,.3),13),pt(at(q.shoulder,q.hip,.83),12),1.6,'#bdcdd2');
 s+=stroke(q.head,q.shoulder,12,skin);
 s+=`<g transform="translate(${q.head}) rotate(${q.mat?-85:0})"><path d="M-13,-10Q-16,-24 -1,-25Q16,-25 16,-8L21,0L16,4Q15,18 7,21Q-6,23 -12,9Z" fill="${skin}"/><path d="M-13,3Q-20,-20 -6,-28Q9,-32 18,-17L14,-10Q3,-19 -8,-11L-8,5Z" fill="#4b555c"/><path d="M-12,-10Q-5,-22 8,-20" stroke="#6d777c" stroke-width="2" fill="none"/><ellipse cx="-8" cy="3" rx="3" ry="4" fill="#ba8d75"/><path d="M11,-1h2M12,12h4" stroke="#785747" stroke-width="1.1"/></g>`;
 s+=limb(q.shoulder,at(q.shoulder,q.elbow,.52),11,9,shirt)+limb(at(q.shoulder,q.elbow,.47),q.elbow,8,7,skin)+limb(q.elbow,q.hand,7,4.5,skin);
 s+=`<g transform="translate(${q.hand})"><path d="M-5,-4Q3,-9 7,-3L7,5Q1,9 -4,5Z" fill="${skin}"/><path d="M-2,1l5,2" stroke="#aa7d66" stroke-width="1"/></g>`;
 if(q.weighted)s+=`<g transform="translate(${q.hand[0]},${q.hand[1]+8})"><path d="M-15,0H15" stroke="#6c7e88" stroke-width="4"/><rect x="-20" y="-9" width="8" height="18" rx="2" fill="#263d50"/><rect x="12" y="-9" width="8" height="18" rx="2" fill="#263d50"/></g>`;return s;
}
function equipment(q,key){let s='';const metal='#9aaab2',dark='#627983';
 if(q.chair)s=`<g stroke="${metal}" stroke-width="5" stroke-linecap="round" fill="none"><path d="M205,220V303H276M211,306L204,380M267,306L274,380"/><path d="M208,300H275" stroke="${dark}" stroke-width="10"/><path d="M205,220V281" stroke="${dark}" stroke-width="12"/></g>`+(key==='sit-to-stand.support'?`<path d="M208,270H253M246,270V298" stroke="${metal}" stroke-width="5" stroke-linecap="round" fill="none"/>`:'');
 if(q.mat)s+='<rect x="138" y="379" width="304" height="5" rx="2" fill="#b6c5ce"/><path d="M139,379H439" stroke="#d6e0e5" stroke-width="1.5"/>';
 if(q.step)s+='<path d="M302,330H420V380H302Z" fill="#d8e0e2"/><path d="M303,330H420" stroke="#8b9fa9" stroke-width="5"/><path d="M403,334V378" stroke="#b3c2c8" stroke-width="2"/>';
 if(q.rail)s+=q.step?`<path d="M338,176L399,126V380" stroke="${metal}" stroke-width="5" stroke-linecap="round" fill="none"/>`:`<path d="M336,180H377M359,180V380" stroke="${metal}" stroke-width="5" stroke-linecap="round" fill="none"/>`;
 if(q.bench)s+='<path d="M173,323H237M179,328V379M229,328V379" stroke="#9aadb7" stroke-width="5"/><path d="M170,321H240" stroke="#627983" stroke-width="9" stroke-linecap="round"/>';
 if(q.press)s+=`<path d="M169,380H386M190,374L215,299M280,374L245,299M290,319L374,201" stroke="${metal}" stroke-width="7" fill="none"/><path d="M188,217L221,292H254" stroke="${dark}" stroke-width="14" stroke-linecap="round" fill="none"/><path d="M${add(q.ankle,[-9,24])}L${add(q.ankle,[34,-30])}" stroke="${dark}" stroke-width="8"/>`;
 return s;
}
function contacts(q,key,t){const pts=q.mat?[q.shoulder,q.heel]:q.press?[q.hip]:key.startsWith('knee-extension')?[q.hip]:key.startsWith('calf-raise')?[q.toe]:q.step?[q.heel]:q.bench?[q.heel,q.back.heel]:[q.heel];return `<g opacity=".38">${pts.map(p=>`<ellipse cx="${p[0]}" cy="${p[1]+3}" rx="11" ry="3" fill="#588094"/>`).join('')}</g>`}
function scene(key,t,id){const q=pose(key,t);return `<ellipse cx="305" cy="388" rx="134" ry="6" fill="#d6e1e5" opacity=".6"/><path d="M120,382H452" stroke="#c8d7de" stroke-width="1"/>${equipment(q,key)}${contacts(q,key,t)}${person(q,id)}`}
function defs(id){return `<defs><linearGradient id="${id}-shirt" x1="0" x2="1"><stop stop-color="#91abb8"/><stop offset=".52" stop-color="#d0dde2"/><stop offset="1" stop-color="#7895a5"/></linearGradient><linearGradient id="${id}-pants" x1="0" x2="1"><stop stop-color="#20374a"/><stop offset=".52" stop-color="#425d72"/><stop offset="1" stop-color="#21394c"/></linearGradient><linearGradient id="${id}-skin" x1="0" x2="1"><stop stop-color="#b3866d"/><stop offset=".6" stop-color="#d4ac91"/><stop offset="1" stop-color="#bc9178"/></linearGradient></defs>`}
let seq=0;const oldSvg=F.svg,oldAnimate=F.animate,oldStills=F.stills;
function svg(key,t=0,side='simultaneous',label){key=aliases[key]||key;if(!keys.has(key))return oldSvg(key,t,side,label);const id='reda-m4-'+(++seq),cam=camera(key),flip=cam[0]*2+cam[2];return `<svg class="exercise-svg reda-motion-v4" viewBox="${cam.join(' ')}" role="img" aria-label="${clean(label||root.RedaMotionSpecs.get(key)?.label||key)}" data-motion="${key}" data-renderer-version="4" data-side="${side}" data-paint="${id}" xmlns="http://www.w3.org/2000/svg"><title>${clean(label||key)}</title>${defs(id)}<g class="motion-scene"${side==='right'?` transform="translate(${flip} 0) scale(-1 1)"`:''}>${scene(key,clamp(t),id)}</g></svg>`}
F.svg=svg;F.stills=(key,side)=>keys.has(aliases[key]||key)?[0,.5,1].map((t,i)=>({label:['Startläge','På väg','Slutläge'][i],svg:svg(key,t,side)})):oldStills(key,side);
F.animate=(el,key,opt={})=>{key=aliases[key]||key;if(!keys.has(key))return oldAnimate(el,key,opt);let stop=false,raf=0,last=0,start=performance.now();if(root.matchMedia?.('(prefers-reduced-motion: reduce)').matches)return()=>{};const tick=now=>{if(stop||!el.isConnected)return;raf=requestAnimationFrame(tick);if(now-last<32)return;last=now;const x=((now-start)/(1000*Math.max(4,opt.seconds||7)))%1,t=R.phase(x),svgEl=el.querySelector('svg[data-renderer-version="4"]'),g=svgEl?.querySelector('.motion-scene');if(g)g.innerHTML=scene(key,t,svgEl.dataset.paint);opt.onPhase?.(x<.12?'Förbered':x<.44?'Rörelse':x<.58?'Stanna till':x<.96?'Återgå':'Förbered')};raf=requestAnimationFrame(tick);return()=>{stop=true;cancelAnimationFrame(raf)}};
root.RedaMotionV4={VERSION:4,keys:[...keys],pose,camera,svg};
})(typeof window!=='undefined'?window:globalThis);
