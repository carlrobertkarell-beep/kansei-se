/* Reda movement studio 6: adult proportions, shaded clothing and continuous movement.
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
   // Weight transfer overlaps seat-off: never freeze the whole body between phases.
   const ease=x=>x*x*(3-2*x),rise=ease(clamp((t-.16)/.84)),lean=t<.30?ease(t/.30):1-ease((t-.30)/.70);
   q.hip=at([229,291],[289,221],rise);q.shoulder=polar(q.hip,80,-Math.PI/2+.48*lean);q.knee=joint(q.hip,q.ankle,72,72,-1);q.head=add(q.shoulder,[-1,-36]);q.back={hip:add(q.hip,[-12,0]),knee:add(q.knee,[-12,0]),ankle:add(q.ankle,[-12,0]),heel:add(q.heel,[-12,0]),toe:add(q.toe,[-12,0])};
   q.armLengths=[45,45];const release=clamp((t-.28)/.34),free=polar(q.shoulder,88,1.43);
   if(key==='sit-to-stand.support'){q.hand=at([247,270],free,release*release*(3-2*release));q.armrest=true;q.palmSupport=1-release*release*(3-2*release)}
   else{const rise=clamp((t-.23)/.77);q.hand=polar(q.shoulder,88,.55+.88*rise)}
   q.elbow=joint(q.shoulder,q.hand,...q.armLengths,key==='sit-to-stand.support'?1:-1);
  }
  if(key.startsWith('knee-extension.')||key.startsWith('calf-raise.')){q.elbow=joint(q.shoulder,q.hand,38,38,1);q.palmSupport=1;}
  if(key.startsWith('bridge.'))q.elbow=joint(q.shoulder,q.hand,38,38,1);
  return q;
 }
 let hip,shoulder,knee,ankle,heel,toe,hand,back;
 const press=key==='leg-press.bilateral';
 if(press){hip=[230,290];shoulder=polar(hip,80,-2.05);ankle=at([305,255],[337,220],t);knee=joint(hip,ankle,72,72,-1);heel=add(ankle,[-4,13]);toe=add(ankle,[21,-11]);hand=[252,258];back={hip:add(hip,[-8,-3]),knee:add(knee,[-8,-3]),ankle:add(ankle,[-8,-3]),heel:add(heel,[-8,-3]),toe:add(toe,[-8,-3])};}
 else{hip=at([300,231],[295,278],t);shoulder=polar(hip,80,-Math.PI/2+.13);ankle=[345,364];heel=[334,378];toe=[372,378];knee=joint(hip,ankle,72,72,-1);hand=add(shoulder,[4,73]);const rear=[208,306];back={hip,knee:joint(hip,rear,72,72,-1),ankle:rear,heel:[223,312],toe:[194,322]};}
 return {hip,shoulder,knee,ankle,heel,toe,hand,elbow:joint(shoulder,hand,38,38,-1),head:add(shoulder,[-1,-36]),back,press,bench:!press,weighted:key.endsWith('loaded')};
}
function camera(key){if(key.startsWith('bridge.'))return [125,260,320,145];if(key.startsWith('step-up.'))return [178,8,270,400];if(key.startsWith('knee-extension.'))return [175,135,255,273];if(key.startsWith('leg-press.'))return [155,130,258,278];return [175,58,255,344]}
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
 const pre1=off(at(a,b,.83),u,wb),post1=off(at(b,c,.17),v,wb),pre2=off(at(a,b,.83),u,-wb),post2=off(at(b,c,.17),v,-wb);
 return `<path d="M${a1}Q${off(at(a,b,.5),u,wa*.88)} ${pre1}Q${b1} ${post1}Q${off(at(b,c,.65),v,wb*.82)} ${c1}L${c2}Q${off(at(b,c,.65),v,-wb*.82)} ${post2}Q${b2} ${pre2}Q${off(at(a,b,.5),u,-wa*.88)} ${a2}Q${add(a,[-u[1]*wa,u[0]*wa])} ${a1}Z" fill="${color}" stroke="${stroke}" stroke-width=".65" stroke-linejoin="round"/>`;
}
function person(q,id){
 const portrait=at(q.head,q.shoulder,.14);
 const near=`url(#${id}-shirt)`,far='#3d5757',pants=`url(#${id}-pants)`,skin=`url(#${id}-skin)`,outline='#344d4c',b=q.back;
 const neck=at(portrait,q.shoulder,.54);
 const hand=(e,h,isFar=false)=>{const natural=Math.atan2(h[1]-e[1],h[0]-e[0])*180/Math.PI-90,angle=mix(natural,-90,q.palmSupport||0);return `<g transform="translate(${h}) rotate(${angle})" fill="${isFar?'#c39e85':skin}" stroke="#ae8972" stroke-width=".55" stroke-linejoin="round"><path d="M-3.1,-4Q-4.1,0 -3.7,3L-2.8,8Q-2.1,9.7 -1,8.4Q.2,10 1.3,8.1Q2.7,8.4 3.2,6.1L3.4,1.1Q5.8,-1 4,-2.3L2.7,-3.6Z"/><path d="M-1.6,4L-1,8M.4,4L1.2,7.8M3,-.8Q1.5,1 2,3" fill="none"/></g>`};
 const arm=(offset,isFar)=>{
  const s=add(q.shoulder,offset),e=add(q.elbow,offset),h=add(q.hand,offset),cuff=at(s,e,.49),tone=isFar?'#c39e85':skin;
  const d=dist(s,e),n=[-(e[1]-s[1])/d,(e[0]-s[0])/d];
  return `<g class="${isFar?'motion-far-arm':'motion-near-arm'}">${clothedChain(s,e,h,7.2,5.3,3.1,tone,'#b18d77')}${limb(s,cuff,9.2,7.6,isFar?far:near)}${line(add(cuff,[n[0]*7.8,n[1]*7.8]),add(cuff,[-n[0]*7.8,-n[1]*7.8]),.8,'#809b90')}${hand(e,h,isFar)}</g>`;
 };
 let s=arm([-5,1],true);
 s+=`<g class="motion-far-leg">${clothedChain(b.hip||q.hip,b.knee,b.ankle,14,9,6,'#3f4e58','#364650')}${foot(b.heel,b.toe,'#6e766d',b.ankle)}</g>`;
 s+=`<g class="motion-active-leg">${clothedChain(q.hip,q.knee,q.ankle,16,10,6.3,pants,'#303d47')}${line(at(q.hip,q.knee,.32),at(q.hip,q.knee,.77),.65,'#788993')}${foot(q.heel,q.toe,'#424d49',q.ankle)}</g>`;
 s+=line(neck,add(q.shoulder,[0,4]),10,skin);
 const u=[(q.hip[0]-q.shoulder[0])/80,(q.hip[1]-q.shoulder[1])/80],v=[-u[1],u[0]],pt=(a,n)=>add(a,[v[0]*n,v[1]*n]);
 s+=`<path d="M${pt(q.shoulder,12)}C${pt(at(q.shoulder,q.hip,.1),20)} ${pt(at(q.shoulder,q.hip,.36),18)} ${pt(at(q.shoulder,q.hip,.6),16)}Q${pt(at(q.shoulder,q.hip,.85),18)} ${pt(q.hip,16)}Q${add(q.hip,[u[0]*8,u[1]*8])} ${pt(q.hip,-18)}C${pt(at(q.shoulder,q.hip,.83),-21)} ${pt(at(q.shoulder,q.hip,.48),-18)} ${pt(at(q.shoulder,q.hip,.3),-19)}Q${pt(q.shoulder,-21)} ${pt(q.shoulder,-10)}Q${add(q.shoulder,[u[0]*6,u[1]*6])} ${pt(q.shoulder,12)}Z" fill="${near}" stroke="${outline}" stroke-width=".7"/>`;
 s+=`<path d="M${pt(at(q.shoulder,q.hip,.98),15)}Q${add(q.hip,[u[0]*4,u[1]*4])} ${pt(at(q.shoulder,q.hip,.98),-17)}M${pt(at(q.shoulder,q.hip,.62),12)}q-3,12 1,17" stroke="#729387" stroke-width="1" fill="none"/>`;
 // Smaller adult head, quiet facial detail and a relaxed, short hairstyle.
 const headAngle=q.mat?-85:Math.max(-6,Math.min(10,(q.shoulder[0]-q.hip[0])*.18));
 s+=`<g class="motion-human-profile" transform="translate(${portrait}) rotate(${headAngle}) scale(.82)">
 <path d="M-7,10L-6,28Q0,32 7,27L7,12Z" fill="${skin}"/>
 <path d="M-12,-9C-12,-22 0,-26 10,-20C16,-16 15,-7 14,-3L17.5,3Q18,5 13.8,5.6L13,12Q11,21 4,22C-5,20 -12,11 -12,1Z" fill="${skin}" stroke="#b18b74" stroke-width=".6"/>
 <path d="M-12,4C-18,-4 -16,-19 -8,-24C0,-29 12,-25 15,-18L14,-11Q11,-13 10,-18Q2,-13 -7,-12L-8,3Z" fill="#343d40"/>
 <path d="M-12,-14Q-6,-23 5,-22" stroke="#667173" stroke-width="1.5" opacity=".55" fill="none"/>
 <ellipse cx="-7" cy="2" rx="3.5" ry="5.5" fill="#cea187"/><path d="M-8,0Q-4,-2 -6,5" fill="none" stroke="#ad806c" stroke-width=".7"/>
 <path d="M7,-5Q10,-6 12,-4.5M9,12Q11,13 13,12" stroke="#846a5b" stroke-width=".8" fill="none" stroke-linecap="round"/>
 <path d="M8,-1.5h3" stroke="#3a4142" stroke-width="1.2" stroke-linecap="round"/>
 </g>`;
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
function defs(id){return `<defs>
 <linearGradient id="${id}-shirt" x1="0" y1="0" x2="1" y2=".25"><stop stop-color="#284746"/><stop offset=".35" stop-color="#547c76"/><stop offset=".65" stop-color="#638b82"/><stop offset="1" stop-color="#2d504e"/></linearGradient>
 <linearGradient id="${id}-pants" x1="0" y1="0" x2="1" y2=".15"><stop stop-color="#24323e"/><stop offset=".4" stop-color="#4d5e6d"/><stop offset=".7" stop-color="#3e5060"/><stop offset="1" stop-color="#263640"/></linearGradient>
 <linearGradient id="${id}-skin" x1="0" y1="0" x2="1" y2=".2"><stop stop-color="#b98669"/><stop offset=".4" stop-color="#dfb497"/><stop offset=".7" stop-color="#e7c3a8"/><stop offset="1" stop-color="#c69679"/></linearGradient></defs>`}
const sideText={left:'Vänster sida',right:'Höger sida',both:'En sida i taget',simultaneous:'Båda samtidigt'};
let seq=0;const oldSvg=F.svg,oldAnimate=F.animate,oldStills=F.stills,jobs=new WeakMap();
function svg(key,t=0,side='simultaneous',label,options={}){key=aliases[key]||key;if(!keys.has(key))return oldSvg(key,t,side,label);const id='reda-m6-'+(++seq),cam=camera(key),name=label||root.RedaMotionSpecs.get(key)?.label||key;
 // Fixed viewing direction. Side is an explicit prescription label, never inferred from a mirrored room.
 return `<svg class="exercise-svg reda-motion-v6" viewBox="${cam.join(' ')}" role="img" aria-label="${clean(name+(sideText[side]?' · '+sideText[side]:''))}" data-motion="${key}" data-renderer-version="6" data-side="${clean(side)}" data-focus="${clean(options.focus||'')}" data-paint="${id}" xmlns="http://www.w3.org/2000/svg"><title>${clean(name)}</title><desc>Sidovy av övningen. Sidangivelsen följer ordinationen. Individuellt rörelseomfång visas i instruktionen.</desc>${defs(id)}<g class="motion-scene">${scene(key,clamp(t),id,options.focus)}</g></svg>`;
}
F.drawFrame=(el,key,t,focus)=>{key=aliases[key]||key;const svgEl=el.querySelector('svg[data-renderer-version="6"]');if(!keys.has(key)||svgEl?.dataset.motion!==key)return false;const g=svgEl.querySelector('.motion-scene');if(!g)return false;g.innerHTML=scene(key,clamp(t),svgEl.dataset.paint,focus);svgEl.dataset.focus=focus||'';return true};
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
 const tick=now=>{if(stopped||!el.isConnected)return;const f=phaseState((now-start)/(1000*seconds),key),svgEl=el.querySelector('svg[data-renderer-version="6"]'),g=svgEl?.querySelector('.motion-scene');if(!g)return;g.innerHTML=scene(key,f.position,svgEl.dataset.paint,svgEl.dataset.focus);if(f.phase!==lastPhase){opt.onPhase?.(f.label,f.phase);lastPhase=f.phase}opt.onFrame?.(f.position,f.phase);raf=requestAnimationFrame(tick)};raf=requestAnimationFrame(tick);return stop;
};
root.RedaMotionStudio={VERSION:6,keys:[...keys],pose,camera,svg,phaseState};root.RedaMotionV4=root.RedaMotionStudio;
})(typeof window!=='undefined'?window:globalThis);
