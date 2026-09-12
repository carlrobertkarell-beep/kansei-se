/* Reda movement studio 5: fixed contact geometry and a continuous garment silhouettes and profile illustration.
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
  if(key.startsWith('sit-to-stand.')){
   q.armLengths=[45,45];const release=clamp((t-.28)/.34),free=polar(q.shoulder,88,1.43);
   if(key==='sit-to-stand.support'){q.hand=at([247,270],free,release*release*(3-2*release));q.armrest=true}
   else{const rise=clamp((t-.23)/.77);q.hand=polar(q.shoulder,88,.55+.88*rise)}
   q.elbow=joint(q.shoulder,q.hand,...q.armLengths,key==='sit-to-stand.support'?1:-1);
  }
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
// Continuous garment silhouettes hide the construction joints. Hands have a palm,
// thumb and fingers; their orientation follows the forearm and the support contact.
function clothedChain(a,b,c,wa,wb,wc,color,stroke){
 const norm=(p,q)=>{const d=dist(p,q);return [-(q[1]-p[1])/d,(q[0]-p[0])/d]},u=norm(a,b),v=norm(b,c),n=add(u,v),d=Math.hypot(...n)||1,k=[n[0]/d,n[1]/d];
 const off=(p,n,w)=>add(p,[n[0]*w,n[1]*w]),a1=off(a,u,wa),a2=off(a,u,-wa),b1=off(b,k,wb),b2=off(b,k,-wb),c1=off(c,v,wc),c2=off(c,v,-wc);
 return `<path d="M${a1}Q${off(at(a,b,.6),u,wa*.86)} ${b1}Q${off(at(b,c,.6),v,wb*.83)} ${c1}L${c2}Q${off(at(b,c,.5),v,-wb*.78)} ${b2}Q${off(at(a,b,.5),u,-wa*.85)} ${a2}Q${add(a,[-u[1]*wa,u[0]*wa])} ${a1}Z" fill="${color}" stroke="${stroke}" stroke-width=".65" stroke-linejoin="round"/>`;
}
function person(q,id){
 const near='#41675e',far='#526b61',pants='#344653',skin='#d9b399',outline='#526158',b=q.back;
 const neck=at(q.head,q.shoulder,.54);
 const hand=(e,h,isFar=false)=>{const angle=Math.atan2(h[1]-e[1],h[0]-e[0])*180/Math.PI-90;return `<g transform="translate(${h}) rotate(${angle})" fill="${isFar?'#c39e85':skin}" stroke="#aa8773" stroke-width=".55" stroke-linejoin="round"><path d="M-3.7,-6C-4.2,-3 -5,0 -4.7,3L-3.8,8.2Q-3,10 -1.8,8.8L-1.1,9.5Q.3,10 1,8.3Q2.6,9 3.2,6.6L4.3,1.7Q6.2,-.4 4.7,-2L2.8,-4.1L2.8,-6Z"/><path d="M-2.1,3.7L-1.8,8.5M.1,3.9L.5,8M2,2.8L2.8,6.3M3.2,-1.7Q1.7,.7 1.7,3" fill="none"/></g>`};
 const arm=(offset,isFar)=>{const s=add(q.shoulder,offset),e=add(q.elbow,offset),h=add(q.hand,offset),w=at(e,h,.83);return `<g class="${isFar?'motion-far-arm':'motion-near-arm'}">${clothedChain(s,e,w,9.5,6.7,4.1,isFar?far:near,outline)}${line(add(w,[-2,0]),add(w,[3,0]),1.2,'#8faaa0')}${hand(e,h,isFar)}</g>`};
 let s=arm([-12,-2],true);
 s+=`<g class="motion-far-leg">${clothedChain(b.hip||q.hip,b.knee,b.ankle,15,10,6.5,'#637078','#536267')}${foot(b.heel,b.toe,'#6e766d',b.ankle)}</g>`;
 s+=`<g class="motion-active-leg">${clothedChain(q.hip,q.knee,q.ankle,18,11,7,pants,'#2c3a44')}${line(at(q.hip,q.knee,.32),at(q.hip,q.knee,.77),.65,'#788993')}${foot(q.heel,q.toe,'#424d49',q.ankle)}</g>`;
 s+=line(neck,add(q.shoulder,[0,5]),12,skin);
 const u=[(q.hip[0]-q.shoulder[0])/80,(q.hip[1]-q.shoulder[1])/80],v=[-u[1],u[0]],pt=(a,n)=>add(a,[v[0]*n,v[1]*n]);
 s+=`<path d="M${pt(q.shoulder,12)}C${pt(at(q.shoulder,q.hip,.1),23)} ${pt(at(q.shoulder,q.hip,.36),21)} ${pt(at(q.shoulder,q.hip,.6),19)}Q${pt(at(q.shoulder,q.hip,.85),21)} ${pt(q.hip,16)}Q${add(q.hip,[u[0]*8,u[1]*8])} ${pt(q.hip,-18)}C${pt(at(q.shoulder,q.hip,.83),-21)} ${pt(at(q.shoulder,q.hip,.48),-22)} ${pt(at(q.shoulder,q.hip,.3),-20)}Q${pt(q.shoulder,-21)} ${pt(q.shoulder,-10)}Q${add(q.shoulder,[u[0]*6,u[1]*6])} ${pt(q.shoulder,12)}Z" fill="${near}" stroke="${outline}" stroke-width=".7"/>`;
 s+=`<path d="M${pt(at(q.shoulder,q.hip,.98),15)}Q${add(q.hip,[u[0]*4,u[1]*4])} ${pt(at(q.shoulder,q.hip,.98),-17)}M${pt(at(q.shoulder,q.hip,.62),12)}q-3,12 1,17" stroke="#729387" stroke-width="1" fill="none"/>`;
 // A natural profile, silver hair and a visible neckline, without spherical shoulders.
 s+=`<g class="motion-human-profile" transform="translate(${q.head}) rotate(${q.mat?-85:0})">
 <path d="M-9,9L-8,24Q-2,29 5,26L7,13Z" fill="${skin}" stroke="#b2917d" stroke-width=".5"/>
 <path d="M-12,-7C-12,-22 1,-25 10,-18Q16,-14 15,-7L14,-3Q14,0 18,3Q19,5 14.2,5.4L14,9Q15.5,11 13.2,12L12.2,17Q8,23 .5,21C-7,19 -11,12 -12,4Z" fill="${skin}" stroke="#ad8c77" stroke-width=".65"/>
 <path d="M-13,7C-18,1 -18,-13 -12,-21C-8,-29 4,-29 13,-24Q21,-20 17,-11Q13,-13 11,-18C8,-14 3,-17 -3,-11L-6,-1L-9,9Z" fill="#d5d6cf" stroke="#8e9893" stroke-width=".7"/>
 <path d="M-13,-14Q-6,-24 5,-23M-12,-6Q-8,-17 2,-19M-13,3Q-11,-5 -8,-9M5,-21Q10,-25 15,-18" fill="none" stroke="#a8b1aa" stroke-width=".8" stroke-linecap="round"/>
 <path d="M-8,3C-10,-3 -3,-5 -2,1Q-1,7 -6,9Q-8,8 -8,3Z" fill="#d4aa90" stroke="#b28e78" stroke-width=".6"/><path d="M-5,0q3,-1 1,4" fill="none" stroke="#b18a73" stroke-width=".6"/>
 <path d="M8,-3Q11,-4.5 13,-2.5M8,-7Q11,-8 13,-6.5M9,13Q11,12 13,12M6,18Q8,19 10,18M8,3l2,.5" stroke="#806d60" stroke-width=".7" fill="none" stroke-linecap="round"/><circle cx="11.5" cy="-2.6" r=".85" fill="#424b44"/>
 <path d="M8,-10l4,-.3M2,9q1,3 4,4" stroke="#bc947d" stroke-width=".55" fill="none"/></g>`;
 if(q.armrest)s+='<path d="M208,270H253M246,270V298" stroke="#a7ada1" stroke-width="4.5" stroke-linecap="round" fill="none"/>';
 s+=arm([0,0],false);
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
F.drawFrame=(el,key,t,focus)=>{key=aliases[key]||key;const svgEl=el.querySelector('svg[data-renderer-version="5"]');if(!keys.has(key)||svgEl?.dataset.motion!==key)return false;const g=svgEl.querySelector('.motion-scene');if(!g)return false;g.innerHTML=scene(key,clamp(t),svgEl.dataset.paint,focus);svgEl.dataset.focus=focus||'';return true};
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
