/* Schematic motion studies for the prototype; no image, analytics or media requests. */
(function(root){
'use strict';
const poses={
 'chair-support':[[[178,88],[185,123],[198,191],[255,194],[247,260],[194,154],[211,179]],[[234,49],[234,85],[235,160],[242,210],[247,260],[211,124],[213,179]]],
 'chair-free':[[[178,88],[185,123],[198,191],[255,194],[247,260],[232,126],[269,118]],[[234,49],[234,85],[235,160],[242,210],[247,260],[261,112],[281,119]]],
 'extension':[[[182,80],[181,118],[185,192],[252,194],[250,260],[204,157],[208,188]],[[182,80],[181,118],[185,192],[252,194],[313,192],[204,157],[208,188]]],
 'calf-both':[[[194,45],[194,83],[199,158],[202,207],[208,255],[227,114],[251,153]],[[194,35],[194,73],[199,148],[202,197],[212,244],[225,109],[251,153]]],
 'calf-single':[[[194,45],[194,83],[199,158],[202,207],[208,255],[227,114],[251,153]],[[194,35],[194,73],[199,148],[202,197],[212,244],[225,109],[251,153]]],
 'bridge':[[[71,233],[108,232],[200,233],[259,185],[295,258],[145,249],[193,253]],[[71,233],[108,232],[199,184],[259,185],[295,258],[145,249],[193,253]]],
 'row':[[[202,48],[204,87],[204,158],[205,209],[210,260],[264,116],[318,124]],[[202,48],[204,87],[204,158],[205,209],[210,260],[179,131],[234,132]]],
 'rotation':[[[210,47],[208,86],[209,159],[202,209],[201,258],[230,146],[265,144]],[[210,47],[208,86],[209,159],[202,209],[201,258],[230,146],[292,108]]],
 'balance':[[[193,47],[193,85],[198,159],[204,208],[206,258],[230,115],[251,153]],[[193,47],[193,85],[198,159],[204,208],[206,258],[230,115],[251,153]]],
 'abduction':[[[205,46],[205,85],[208,159],[204,209],[204,259],[234,115],[252,153]],[[205,46],[205,85],[208,159],[204,209],[204,259],[234,115],[252,153]]]
};
const line=(p,color,width)=>`<polyline points="${p.map(a=>a.join(',')).join(' ')}" stroke="${color}" stroke-width="${width}" stroke-linecap="round" stroke-linejoin="round" fill="none"/>`;
const mix=(a,b,t)=>a.map((p,i)=>p.map((n,j)=>n+(b[i][j]-n)*t));
function frame(pose,t=0,side='simultaneous'){
 const key=pose.replace('-pause','');const pair=poses[key]||poses['chair-support'];const p=mix(pair[0],pair[1],t);const [head,shoulder,hip,knee,foot,elbow,hand]=p;
 let equipment='';
 if(key.startsWith('chair')||key==='extension')equipment='<path d="M152 108V197H220M155 197L147 267M212 197L220 267" fill="none" stroke="#a59b86" stroke-width="8" stroke-linejoin="round" stroke-linecap="round"/><path d="M150 195H221" stroke="#c0b59f" stroke-width="14" stroke-linecap="round"/>'+(key==='chair-support'?'<path d="M151 171H216M212 171V195" fill="none" stroke="#a59b86" stroke-width="6" stroke-linecap="round"/>':'');
 if(['calf-both','calf-single','balance','abduction'].includes(key))equipment='<path d="M248 159H304M255 162V268M299 162V268" stroke="#afa38c" stroke-width="7" fill="none" stroke-linecap="round"/>';
 if(key==='bridge')equipment='<rect x="49" y="263" width="291" height="8" rx="4" fill="#bccbc4"/>';
 if(key==='row')equipment='<path d="M350 78V267" stroke="#b6ad9d" stroke-width="7"/>'+line([[350,121],hand],'#c49567',3);
 if(key==='rotation')equipment='<path d="M125 131V267" stroke="#b6ad9d" stroke-width="7"/>'+line([[125,144],hand],'#c49567',3);
 let backK=[knee[0]-14,knee[1]+1],backF=[foot[0]-16,foot[1]];
 if(['balance','calf-single'].includes(key)){backK=[hip[0]-27,hip[1]+47];backF=[hip[0]-47,hip[1]+65];}
 if(key==='abduction'){backK=[hip[0]-7-44*t,hip[1]+49-8*t];backF=[hip[0]-10-85*t,hip[1]+99-20*t];}
 let torso=line([shoulder,hip],'#557d72',31)+line([[shoulder[0]+5,shoulder[1]+10],[hip[0]+5,hip[1]-10]],'#678f83',7);
 const neck=key==='bridge'?line([head,shoulder],'#b78868',13):line([[head[0],head[1]+13],shoulder],'#b78868',13);
 const backArm=line([[shoulder[0]-6,shoulder[1]+4],[elbow[0]-11,elbow[1]+3],[hand[0]-9,hand[1]+2]],'#ae7c5e',11);
 const hair=`<path d="M${head[0]-11} ${head[1]-2}q-2 -21 15 -18q13 1 11 15q-12 -7 -20 3Z" fill="#514a40"/>`;
 const person=backArm+line([hip,backK,backF],'#47575a',19)+line([backF,[backF[0]+18,backF[1]+1]],'#d3cec3',10)+line([hip,knee,foot],'#253b40',22)+line([foot,[foot[0]+20,foot[1]+1]],'#eeeadf',11)+torso+neck+`<ellipse cx="${head[0]}" cy="${head[1]}" rx="14" ry="18" fill="#c39676"/>`+hair+line([shoulder,elbow],'#587f73',16)+line([elbow,hand],'#c39676',12)+`<circle cx="${hand[0]}" cy="${hand[1]}" r="7" fill="#c39676"/>`;
 return `<rect width="400" height="290" fill="#edf1e9"/><circle cx="210" cy="128" r="118" fill="#e4ebdf"/><path d="M34 269H366" stroke="#c3cfc0"/><ellipse cx="205" cy="270" rx="99" ry="8" fill="#cad5c4" opacity=".55"/><g${side==='right'?' transform="translate(400 0) scale(-1 1)"':''}>${equipment}${person}</g>`;
}
function svg(pose,t=0,side='simultaneous',label='Schematisk illustration av övningen'){
 return `<svg class="exercise-svg" viewBox="0 0 400 290" role="img" aria-label="${label.replace(/["<>]/g,'')}" xmlns="http://www.w3.org/2000/svg">${frame(pose,t,side)}</svg>`;
}
let job=0;
function animate(element,pose,options={}){
 const id=++job;let raf;const start=performance.now();const cycle=options.seconds||5;
 function tick(now){if(id!==job||!element.isConnected)return;const x=((now-start)/1000/cycle)%1;let t=(1-Math.cos(x*2*Math.PI))/2;if(pose.endsWith('-pause'))t=x<.32?(1-Math.cos(x/.32*Math.PI))/2:x<.67?1:(1+Math.cos((x-.67)/.33*Math.PI))/2;const svg=element.querySelector('svg');if(svg)svg.innerHTML=frame(pose,t,options.side);raf=requestAnimationFrame(tick);}
 raf=requestAnimationFrame(tick);return ()=>{if(id===job)job++;cancelAnimationFrame(raf);};
}
root.RedaFigures={svg,animate};
})(window);
