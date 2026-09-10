/* Reference renderer 3: fixed segment lengths, explicit contact points.
   These five families remain pending clinical review; other variants keep their renderer. */
(function(root){'use strict';
const F=root.RedaFigures,M=root.RedaMotionSpecs;if(!F||!M)return;
const keys=new Set(['sit-to-stand.support','sit-to-stand.free','sit-to-stand.tempo','knee-extension.seated','knee-extension.pause','calf-raise.bilateral','calf-raise.eccentric-bilateral','bridge.bilateral','bridge.pause','step-up.supported','step-up.standard']);
const clamp=t=>Math.max(0,Math.min(1,t)),lerp=(a,b,t)=>a+(b-a)*t,smooth=t=>t*t*(3-2*t),at=(a,b,t)=>[lerp(a[0],b[0],t),lerp(a[1],b[1],t)],add=(a,b)=>[a[0]+b[0],a[1]+b[1]],polar=(o,l,a)=>[o[0]+l*Math.cos(a),o[1]+l*Math.sin(a)],dist=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
function joint(a,b,l1,l2,sign=1){const d=dist(a,b);if(d>l1+l2+.001||d<Math.abs(l1-l2)-.001)throw Error('Unreachable reference pose');const along=(l1*l1-l2*l2+d*d)/(2*d),h=Math.sqrt(Math.max(0,l1*l1-along*along)),ux=(b[0]-a[0])/d,uy=(b[1]-a[1])/d;return[a[0]+ux*along-sign*uy*h,a[1]+uy*along+sign*ux*h]}
const thigh=72,shin=72,torso=80,upperArm=38,forearm=38;
function pose(key,t){t=clamp(t);const spec=M.get(key);if(!keys.has(key))return null;let hip,shoulder,knee,ankle,heel,toe,hand,elbow,head,back=null,chair=false,step=false,rail=false,mat=false;
 if(spec.kind==='sitStand'){
  // Feet do not slide. Forward trunk inclination precedes seat-off.
  const rise=smooth(clamp((t-.23)/.77)),lean=t<.23?smooth(t/.23):1-smooth((t-.23)/.77);
  ankle=[298,364];heel=[287,378];toe=[323,378];hip=at([229,291],[289,221],rise);knee=joint(hip,ankle,thigh,shin,-1);
  shoulder=polar(hip,torso,-Math.PI/2+.48*lean);chair=true;
  hand=spec.equipment.includes('armrest')&&t<.30?[247,270]:polar(shoulder,65,.38+1.08*rise);
 }
 else if(spec.kind==='kneeExtension'){
  hip=[232,288];shoulder=[232,208];knee=[304,288];ankle=polar(knee,shin,(1-t)*Math.PI/2);heel=add(ankle,[-8,12]);toe=add(ankle,[26,12]);hand=[270,267];chair=true;
  back={hip:[220,288],knee:[292,288],ankle:[292,360],heel:[282,378],toe:[315,378]};
 }
 else if(spec.kind==='calfRaise'){
  toe=[321,378];const ang=Math.PI+t*.48;heel=polar(toe,36,ang);ankle=add(heel,[11,-14]);hip=add(ankle,[-8,-143]);knee=joint(hip,ankle,thigh,shin,-1);shoulder=add(hip,[0,-torso]);hand=[340,180];rail=true;
 }
 else if(spec.kind==='bridge'){
  // Shoulder remains on the mat; pelvis rotates around it at fixed trunk length.
  shoulder=[193,356];hip=polar(shoulder,torso,lerp(.05,-.62,t));ankle=[375,361];heel=[365,377];toe=[402,377];knee=joint(hip,ankle,thigh,shin,-1);hand=[267,366];mat=true;
 }
 else if(spec.kind==='stepUp'){
  step=true;rail=spec.equipment.includes('support');ankle=[345,314];heel=[333,328];toe=[370,328];hip=at([276,221],[337,171],smooth(t));knee=joint(hip,ankle,thigh,shin,-1);shoulder=polar(hip,torso,-Math.PI/2+.15*(1-t));hand=rail?add(hip,[62,-45]):polar(shoulder,65,1.15);
  const trailing=at([264,364],[325,314],smooth(t));trailing[1]-=18*Math.sin(Math.PI*t);
  const k=joint(hip,trailing,thigh,shin,-1);back={knee:k,ankle:trailing,heel:add(trailing,[-9,14]),toe:add(trailing,[25,14])};
 }
 elbow=joint(shoulder,hand,upperArm,forearm,-1);
 head=mat?add(shoulder,[-29,1]):add(shoulder,[-1,-36]);
 if(!back)back={knee:add(knee,[-12,0]),ankle:add(ankle,[-12,0]),heel:add(heel,[-12,0]),toe:add(toe,[-12,0]),hip:add(hip,[-12,0])};
 return {hip,shoulder,knee,ankle,heel,toe,hand,elbow,head,back,chair,step,rail,mat};
}
const clean=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function limb(a,b,w1,w2,color){const l=dist(a,b),nx=-(b[1]-a[1])/l,ny=(b[0]-a[0])/l,p=(v,w,s)=>`${v[0]+nx*w*s},${v[1]+ny*w*s}`;return `<path d="M${p(a,w1,1)} Q${p(at(a,b,.52),(w1+w2)/2,1)} ${p(b,w2,1)} Q${b[0]+(b[0]-a[0])/l*w2},${b[1]+(b[1]-a[1])/l*w2} ${p(b,w2,-1)} L${p(a,w1,-1)} Q${a[0]-(b[0]-a[0])/l*w1},${a[1]-(b[1]-a[1])/l*w1} ${p(a,w1,1)}Z" fill="${color}"/>`}
function foot(heel,toe,color){return `<path d="M${heel[0]-5},${heel[1]-10} Q${heel[0]+8},${heel[1]-13} ${toe[0]},${toe[1]-9} Q${toe[0]+9},${toe[1]-7} ${toe[0]+7},${toe[1]} L${heel[0]-5},${heel[1]}Z" fill="${color}"/><path d="M${heel[0]-5},${heel[1]}L${toe[0]+7},${toe[1]}" stroke="#e4e9e8" stroke-width="3"/>`}
function line(a,b,w,c){return `<path d="M${a}L${b}" fill="none" stroke="${c}" stroke-width="${w}" stroke-linecap="round"/>`}
function body(q){const b=q.back;let s=`<g opacity=".60">${limb(b.hip||q.hip,b.knee,19,13,'#445b65')}${limb(b.knee,b.ankle,13,8,'#445b65')}${foot(b.heel,b.toe,'#5c7079')}</g>`;
 s+=limb(q.hip,q.knee,22,14,'#263e4c')+limb(q.knee,q.ankle,14,8,'#263e4c')+foot(q.heel,q.toe,'#344b59');
 s+=limb(q.shoulder,q.hip,23,20,'#668c91')+line(add(q.shoulder,[-11,15]),add(q.hip,[-10,-9]),3,'#91adb0');
 s+=line(q.head,q.shoulder,15,'#bb8c72');
 s+=`<g transform="translate(${q.head}) rotate(${q.mat?-85:0})"><path d="M-16,-13 Q-12,-27 4,-25 Q21,-22 19,-3 L24,4 L17,8 Q16,24 5,24 Q-10,22 -14,8Z" fill="#c99b7e"/><path d="M-16,0Q-22,-22 -5,-29Q17,-34 23,-16L15,-9Q4,-20 -11,-9L-10,5Z" fill="#48545a"/><path d="M15,-1h2" stroke="#48545a" stroke-width="2"/><path d="M13,15h5" stroke="#9d6f59" stroke-width="1.5"/></g>`;
 s+=limb(q.shoulder,q.elbow,11,9,'#668c91')+limb(q.elbow,q.hand,8,5,'#c99b7e')+`<ellipse cx="${q.hand[0]}" cy="${q.hand[1]}" rx="7" ry="6" fill="#c99b7e"/>`;
 return s;
}
function scene(key,t){const q=pose(key,t);if(!q)return'';let eq='';
 if(q.mat)eq='<rect x="134" y="379" width="321" height="7" rx="3" fill="#a6b9ba"/>';
 if(q.chair)eq='<g stroke="#9f9687" stroke-width="7" stroke-linecap="round" fill="none"><path d="M205 219V303H271M212 305L207 380M263 305L270 380"/><path d="M210 303H272" stroke-width="13"/></g>'+(M.get(key).equipment.includes('armrest')?'<path d="M208 270H253M246 270V298" stroke="#9f9687" stroke-width="6" stroke-linecap="round"/>':'');
 if(q.step)eq='<path d="M302 330H422V380H302Z" fill="#d8d8cf"/><path d="M302 330H422" stroke="#a2a79f" stroke-width="4"/>';
 if(q.rail&&q.step)eq+='<path d="M338 176L399 126V380" stroke="#9f9687" stroke-width="7" stroke-linecap="round" fill="none"/>';
 if(q.rail&&!q.step){const y=180,x=340;eq+=`<path d="M${x-5} ${y}H${x+34}M${x+19} ${y}V380" stroke="#9f9687" stroke-width="7" stroke-linecap="round" fill="none"/>`;}
 return `<rect width="640" height="440" rx="20" fill="#f2f5f5"/><ellipse cx="320" cy="386" rx="185" ry="9" fill="#d8e1e1" opacity=".55"/><path d="M100 380H534" stroke="#bdcccc" stroke-width="1.5"/>${eq}${body(q)}`;
}
const aliases={'chair-support':'sit-to-stand.support','chair-free':'sit-to-stand.free',extension:'knee-extension.seated','extension-pause':'knee-extension.pause','calf-both':'calf-raise.bilateral',bridge:'bridge.bilateral','bridge-pause':'bridge.pause'};
function svg(key,t=0,side='simultaneous',label){key=aliases[key]||key;if(!keys.has(key))return null;const spec=M.get(key);return `<svg class="exercise-svg reference-motion" viewBox="${spec.kind==='bridge'?'110 250 350 150':'0 0 640 440'}" role="img" aria-label="${clean(label||spec.label)}" data-motion="${key}" data-motion-version="${spec.version}" data-renderer-version="3" xmlns="http://www.w3.org/2000/svg"><title>${clean(label||spec.label)}</title><g${side==='right'?' transform="translate(640 0) scale(-1 1)"':''}>${scene(key,t)}</g></svg>`}
function phase(x){x=((x%1)+1)%1;if(x<.12)return 0;if(x<.44)return smooth((x-.12)/.32);if(x<.58)return 1;if(x<.96)return 1-smooth((x-.58)/.38);return 0;}
const prevSvg=F.svg,prevAnimate=F.animate,prevStills=F.stills,jobs=new WeakMap();
F.svg=(key,t,side,label)=>svg(key,t,side,label)||prevSvg(key,t,side,label);
F.animate=(el,key,opt={})=>{key=aliases[key]||key;if(!keys.has(key))return prevAnimate(el,key,opt);jobs.get(el)?.();let raf=0,stopped=false,start=performance.now();const stop=()=>{stopped=true;cancelAnimationFrame(raf)};jobs.set(el,stop);if(root.matchMedia?.('(prefers-reduced-motion: reduce)').matches)return stop;function tick(now){if(stopped||!el.isConnected)return;const g=el.querySelector('svg g');if(g)g.innerHTML=scene(key,phase((now-start)/(1000*Math.max(4,opt.seconds||6))));raf=requestAnimationFrame(tick)}raf=requestAnimationFrame(tick);return stop};
F.stills=(key,side)=>keys.has(key)?[0,.5,1].map((t,i)=>({label:['Startläge','På väg','Slutläge'][i],svg:svg(key,t,side)})):prevStills(key,side);
root.RedaReferenceMotion={keys:[...keys],pose,phase,svg,segmentLengths:{thigh,shin,torso,upperArm,forearm},version:3};
})(typeof window!=='undefined'?window:globalThis);
