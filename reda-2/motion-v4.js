/* Reda movement studio 5: fixed contact geometry and a shared human illustration.
 * Reference motions await clinical review. No patient range is inferred from free text. */
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
 if(press){hip=[230,290];shoulder=polar(hip,80,-2.05);ankle=at([305,255],[337,220],t);knee=joint(hip,ankle,72,72,-1);heel=add(ankle,[-4,13]);toe=add(ankle,[21,-11]);hand=[252,258];back={hip:add(hip,[-8,-3]),knee:add(knee,[-8,-3]),ankle:add(ankle,[-8,-3]),heel:add(heel,[-8,-3]),toe:add(toe,[-8,-3])};}
 else{hip=at([300,231],[295,278],t);shoulder=polar(hip,80,-Math.PI/2+.13);ankle=[345,364];heel=[334,378];toe=[372,378];knee=joint(hip,ankle,72,72,-1);hand=add(shoulder,[4,73]);const rear=[208,306];back={hip,knee:joint(hip,rear,72,72,-1),ankle:rear,heel:[223,312],toe:[194,322]};}
 return {hip,shoulder,knee,ankle,heel,toe,hand,elbow:joint(shoulder,hand,38,38,-1),head:add(shoulder,[-1,-36]),back,press,bench:!press,weighted:key.endsWith('loaded')};
}
function camera(key){if(key.startsWith('bridge.'))return [125,260,320,145];if(key.startsWith('step-up.'))return [178,8,270,400];if(key.startsWith('knee-extension.'))return [175,135,255,273];if(key.startsWith('leg-press.'))return [155,130,258,278];return [170,42,265,366]}
const clean=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function line(a,b,w,c,extra=''){return `<path d="M${a}L${b}" fill="none" stroke="${c}" stroke-width="${w}" stroke-linecap="round" ${extra}/>`}
function limb(a,b,w1,w2,color){const d=dist(a,b),nx=-(b[1]-a[1])/d,ny=(b[0]-a[0])/d,p=(v,w,s)=>add(v,[nx*w*s,ny*w*s]);return `<path d="M${p(a,w1,1)}Q${p(at(a,b,.55),(w1+w2)*.57,1)} ${p(b,w2,1)}Q${add(b,[(b[0]-a[0])/d*w2,(b[1]-a[1])/d*w2])} ${p(b,w2,-1)}Q${p(at(a,b,.55),(w1+w2)*.48,-1)} ${p(a,w1,-1)}Q${add(a,[-(b[0]-a[0])/d*w1,-(b[1]-a[1])/d*w1])} ${p(a,w1,1)}Z" fill="${color}"/>`}
// The sole ends at the contact point. A lifted heel never pushes the toe through the floor.
function foot(h,t,color,ankle){const a=Math.atan2(t[1]-h[1],t[0]-h[0])*180/Math.PI,l=dist(h,t),rad=a*Math.PI/180,sock=ankle?line(ankle,add(at(h,t,.25),[Math.sin(rad)*6,-Math.cos(rad)*6]),8,color):'';return `${sock}<g transform="translate(${h}) rotate(${a})"><path d="M0,0L0,-9Q4,-14 11,-9L${l-8},-7Q${l},-6 ${l},0Z" fill="${color}"/><path d="M1,-1H${l-1}" stroke="#f6f6f1" stroke-width="2"/><path d="M12,-8l9,2" stroke="#a9b7bc" stroke-width="1.5"/></g>`}
function person(q,id){const b=q.back,shirt=`url(#${id}-shirt)`,pants=`url(#${id}-pants)`,skin=`url(#${id}-skin)`;
 const arm=(s,e,h,far=false)=>`<g${far?' opacity=".78"':''}>${limb(s,e,9,6,far?'#bd957f':skin)}${limb(s,at(s,e,.36),11,9,far?'#657a82':shirt)}${limb(e,h,6,4,far?'#bd957f':skin)}<ellipse cx="${h[0]}" cy="${h[1]}" rx="5.5" ry="4" fill="${far?'#bd957f':skin}"/></g>`;
 let s=arm(add(q.shoulder,[-9,-1]),add(q.elbow,[-9,-1]),add(q.hand,[-9,-1]),true);
 s+=`<g class="motion-far-leg">${limb(b.hip||q.hip,b.knee,16,10,'#75828d')}${limb(b.knee,b.ankle,10,6,'#75828d')}${foot(b.heel,b.toe,'#6d8088',b.ankle)}</g>`;
 s+=`<g class="motion-active-leg">${limb(q.hip,q.knee,18,11,pants)}${limb(q.knee,q.ankle,11,6,pants)}${line(at(q.hip,q.knee,.25),at(q.hip,q.knee,.8),1,'#718190')}${foot(q.heel,q.toe,'#294553',q.ankle)}</g>`;
 const u=[(q.hip[0]-q.shoulder[0])/80,(q.hip[1]-q.shoulder[1])/80],v=[-u[1],u[0]],pt=(a,n)=>add(a,[v[0]*n,v[1]*n]);
 s+=`<path d="M${pt(q.shoulder,18)}Q${pt(at(q.shoulder,q.hip,.35),20)} ${pt(at(q.shoulder,q.hip,.8),16)}L${pt(q.hip,18)}Q${add(q.hip,[u[0]*6,u[1]*6])} ${pt(q.hip,-18)}Q${pt(at(q.shoulder,q.hip,.58),-14)} ${pt(q.shoulder,-18)}Q${add(q.shoulder,[-u[0]*11,-u[1]*11])} ${pt(q.shoulder,18)}Z" fill="${shirt}"/>`;
 s+=line(pt(at(q.shoulder,q.hip,.27),12),pt(at(q.shoulder,q.hip,.81),11),1.2,'#b1c8c5');
 const neck=at(q.head,q.shoulder,.52);s+=line(neck,q.shoulder,11,skin);
 s+=`<g transform="translate(${q.head}) rotate(${q.mat?-85:0})"><path d="M-11,-9Q-13,-22 0,-23Q14,-22 14,-8L18,-1L14,3Q14,17 6,19Q-5,20 -10,6Z" fill="${skin}"/><path d="M-11,3Q-17,-14 -8,-24Q4,-32 16,-18L13,-10Q5,-17 -4,-13L-7,4Z" fill="#455357"/><path d="M-8,-14Q-3,-24 9,-19" stroke="#778280" stroke-width="2" fill="none"/><ellipse cx="-7" cy="3" rx="3" ry="4" fill="#c79e87"/><path d="M10,-1h2M9,12h4" stroke="#79594b" stroke-width="1"/></g>`;
 s+=arm(q.shoulder,q.elbow,q.hand);
 if(q.weighted)s+=`<g transform="translate(${q.hand[0]},${q.hand[1]+7})"><path d="M-15,0H15" stroke="#82949a" stroke-width="4"/><rect x="-20" y="-9" width="8" height="18" rx="2" fill="#263d50"/><rect x="12" y="-9" width="8" height="18" rx="2" fill="#263d50"/></g>`;
 return s;
}
function equipment(q,key){let s='',metal='#b6bab2',dark='#8b9284';
 if(q.chair)s=`<g stroke="${metal}" stroke-width="5" stroke-linecap="round" fill="none"><path d="M205,222V303H276M211,306L204,378M267,306L274,378"/><path d="M208,301H275" stroke="${dark}" stroke-width="8"/><path d="M205,222V279" stroke="${dark}" stroke-width="11"/></g>`+(key==='sit-to-stand.support'?`<path d="M208,270H253M246,270V298" stroke="${metal}" stroke-width="5" stroke-linecap="round" fill="none"/>`:'');
 if(q.mat)s+='<rect x="138" y="377" width="298" height="5" rx="2" fill="#b1c5bd"/><path d="M139,377H435" stroke="#dce8e0" stroke-width="1.5"/>';
 if(q.step)s+='<path d="M302,330H420V380H302Z" fill="#d4d9cc"/><path d="M302,330H420" stroke="#9da98e" stroke-width="4"/><path d="M403,332V378" stroke="#b5c2a8" stroke-width="2"/>';
 if(q.rail)s+=q.step?`<path d="M338,176L399,126V380" stroke="${metal}" stroke-width="5" stroke-linecap="round" fill="none"/>`:`<path d="M336,180H377M359,180V378" stroke="${metal}" stroke-width="5" stroke-linecap="round" fill="none"/>`;
 if(q.bench)s+='<path d="M173,323H237M179,328V378M229,328V378" stroke="#b6bab2" stroke-width="5"/><path d="M170,321H240" stroke="#8b9284" stroke-width="9" stroke-linecap="round"/>';
 if(q.press)s+=`<path d="M169,380H386M190,374L215,299M280,374L245,299M290,319L374,201" stroke="${metal}" stroke-width="7" fill="none"/><path d="M188,217L221,292H254" stroke="${dark}" stroke-width="14" stroke-linecap="round" fill="none"/><path d="M${add(q.ankle,[-9,24])}L${add(q.ankle,[34,-30])}" stroke="${dark}" stroke-width="8"/>`;
 return s;
}
function emphasis(q,key,focus){if(!focus)return '';let p=focus==='support'?(q.mat?[q.shoulder,q.heel]:q.chair?[q.hip,q.heel]:q.rail?[q.hand,q.toe]:[q.heel]):focus==='side'?[q.knee,q.ankle]:key.startsWith('bridge')?[q.hip]:key.startsWith('calf-raise')?[q.ankle]:[q.knee];
 return `<g class="motion-emphasis" fill="none" stroke="#0e8277" stroke-width="1.7">${p.map(v=>`<circle cx="${v[0]}" cy="${v[1]}" r="13" fill="#d3eee5" fill-opacity=".3"/><circle cx="${v[0]}" cy="${v[1]}" r="3" fill="#0e8277" stroke="none"/>`).join('')}</g>`;
}
function scene(key,t,id,focus){const q=pose(key,t);return `<ellipse cx="305" cy="384" rx="117" ry="4" fill="#cdd9d1" opacity=".46"/><path d="M142,381H436" stroke="#d3ddd3" stroke-width="1"/>${equipment(q,key)}${person(q,id)}${emphasis(q,key,focus)}`}
function defs(id){return `<defs><linearGradient id="${id}-shirt" x1="0" x2="1"><stop stop-color="#628980"/><stop offset=".55" stop-color="#8aafa0"/><stop offset="1" stop-color="#587f77"/></linearGradient><linearGradient id="${id}-pants" x1="0" x2="1"><stop stop-color="#263e4b"/><stop offset=".55" stop-color="#4c6370"/><stop offset="1" stop-color="#304957"/></linearGradient><linearGradient id="${id}-skin" x1="0" x2="1"><stop stop-color="#bf977f"/><stop offset=".6" stop-color="#dfbda2"/><stop offset="1" stop-color="#c89e85"/></linearGradient></defs>`}
const sideText={left:'Vänster sida',right:'Höger sida',both:'En sida i taget',simultaneous:'Båda samtidigt'};
let seq=0;const oldSvg=F.svg,oldAnimate=F.animate,oldStills=F.stills,jobs=new WeakMap();
function svg(key,t=0,side='simultaneous',label,options={}){key=aliases[key]||key;if(!keys.has(key))return oldSvg(key,t,side,label);const id='reda-m5-'+(++seq),cam=camera(key),name=label||root.RedaMotionSpecs.get(key)?.label||key;
 // Fixed viewing direction. Side is an explicit prescription label, never inferred from a mirrored room.
 return `<svg class="exercise-svg reda-motion-v5" viewBox="${cam.join(' ')}" role="img" aria-label="${clean(name+(sideText[side]?' · '+sideText[side]:''))}" data-motion="${key}" data-renderer-version="5" data-side="${clean(side)}" data-focus="${clean(options.focus||'')}" data-paint="${id}" xmlns="http://www.w3.org/2000/svg"><title>${clean(name)}</title><desc>Sidovy av övningen. Sidangivelsen följer ordinationen. Individuellt rörelseomfång visas i instruktionen.</desc>${defs(id)}<g class="motion-scene">${scene(key,clamp(t),id,options.focus)}</g></svg>`;
}
F.svg=svg;F.stills=(key,side)=>keys.has(aliases[key]||key)?[0,.5,1].map((t,i)=>({label:['Startläge','På väg','Slutläge'][i],svg:svg(key,t,side)})):oldStills(key,side);
function phaseState(x,key){
 x=((x%1)+1)%1;const spec=root.RedaMotionSpecs.get(aliases[key]||key),slow=spec?.tempo==='slow-return',pause=Number(spec?.pause)>0;
 const outEnd=slow?.34:.46,endEnd=pause?.68:slow?.42:.52,smooth=t=>t*t*(3-2*t);
 if(x<.12||x>=.96)return {position:0,phase:'start',label:'Startläge'};
 if(x<outEnd)return {position:smooth((x-.12)/(outEnd-.12)),phase:'out',label:'Utförande'};
 if(x<endEnd)return {position:1,phase:'end',label:pause?'Paus i visningen':'Slutläge'};
 return {position:1-smooth((x-endEnd)/(.96-endEnd)),phase:'back',label:slow?'Långsam återgång':'Tillbaka'};
}
F.animate=(el,key,opt={})=>{key=aliases[key]||key;if(!keys.has(key))return oldAnimate(el,key,opt);jobs.get(el)?.();let stopped=false,raf=0,start=performance.now(),lastPhase=null;const stop=()=>{stopped=true;cancelAnimationFrame(raf)};jobs.set(el,stop);if(root.matchMedia?.('(prefers-reduced-motion: reduce)').matches)return stop;
 const seconds=Number.isFinite(opt.seconds)&&opt.seconds>0?opt.seconds:7;
 const tick=now=>{if(stopped||!el.isConnected)return;const f=phaseState((now-start)/(1000*seconds),key),svgEl=el.querySelector('svg[data-renderer-version="5"]'),g=svgEl?.querySelector('.motion-scene');if(!g)return;g.innerHTML=scene(key,f.position,svgEl.dataset.paint,svgEl.dataset.focus);if(f.phase!==lastPhase){opt.onPhase?.(f.label,f.phase);lastPhase=f.phase}opt.onFrame?.(f.position,f.phase);raf=requestAnimationFrame(tick)};raf=requestAnimationFrame(tick);return stop;
};
root.RedaMotionStudio={VERSION:5,keys:[...keys],pose,camera,svg,phaseState};root.RedaMotionV4=root.RedaMotionStudio;
})(typeof window!=='undefined'?window:globalThis);
