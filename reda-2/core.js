/* Pure plan/session rules. No automatic clinical progression or dosage inference. */
(function(root){
'use strict';
const D=root.RedaData, clone=x=>JSON.parse(JSON.stringify(x));
function fail(msg){throw new Error(msg);}
function text(s,max=600){if(typeof s!=='string'||s.length>max||/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(s))fail('Ogiltig text i programmet.');return s;}
function integer(v,min,max){if(!Number.isInteger(v)||v<min||v>max)fail('Ett värde ligger utanför tillåtna gränser.');return v;}
function dateKey(date=new Date()){return [date.getFullYear(),String(date.getMonth()+1).padStart(2,'0'),String(date.getDate()).padStart(2,'0')].join('-');}
function validDate(s){if(!/^\d{4}-\d{2}-\d{2}$/.test(s))return false;const d=new Date(s+'T12:00:00');return Number.isFinite(d.getTime())&&dateKey(d)===s;}
function uid(){return 'r2-'+(root.crypto?.randomUUID?.() || Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,10));}
function lookup(id,variant){const e=D.exercises.find(e=>e.id===id); const v=e?.variants.find(v=>v.id===variant); if(!e||!v)fail('Övningsvarianten finns inte i denna prototyp.');return {e,v};}
function allowedSides(id,variant){return ['extension','rotation','balance','abduction'].includes(id)||(id==='calf'&&variant==='single')?['both','left','right']:['simultaneous'];}
function makeItem(id,variant,side){const {e,v}=lookup(id,variant);const sides=allowedSides(id,variant);return {key:uid(),exercise:e.id,variant:v.id,side:sides.includes(side)?side:sides[0],dose:clone(v.dose),note:''};}
function template(id='chair'){
 const t=D.templates.find(t=>t.id===id)||D.templates[0];
 return {schema:2,id:uid(),revision:1,title:t.id==='chair'?'Starkare i vardagen':t.name,goal:'Göra vardagens rörelser med mer trygghet.',author:'Carl-Robert Kårell',role:'Leg. naprapat · Kansei',message:'Här samlar vi övningarna och råden från ditt besök. I den här prototypen visas ett fiktivt program.',safety:'Följ de individuella råd du har fått av din behandlare. Avbryt övningen om du känner dig osäker och kontakta kliniken.',days:[1,3,5],reviewDate:'',startDate:dateKey(),items:t.items.map(a=>makeItem(...a)),adjustment:{enabled:false,sets:1,reason:'Anpassad start enligt behandlarens plan.'},demo:true};
}
function validatePlan(p){
 if(!p||p.schema!==2||p.demo!==true)fail('Det här är en prototyp. Endast Reda 2-testprogram kan öppnas.');
 const out={schema:2,id:text(p.id,100),revision:integer(p.revision,1,10000),title:text(p.title,80),goal:text(p.goal,300),author:text(p.author,80),role:text(p.role,80),message:text(p.message),safety:text(p.safety),days:[],startDate:'',reviewDate:'',demo:true,items:[],adjustment:{enabled:false,sets:1,reason:''}};
 if(!out.title.trim()||!out.id.trim())fail('Programmet saknar titel eller ID.');
 for(const name of ['startDate','reviewDate']){const v=p[name]||'';if(v&&!validDate(v))fail('Ogiltigt datum.');out[name]=v;}
 if(!Array.isArray(p.days)||p.days.length<1||p.days.length>7||new Set(p.days).size!==p.days.length)fail('Välj minst en träningsdag.');out.days=p.days.map(d=>integer(d,0,6)).sort();
 if(!Array.isArray(p.items)||p.items.length<1||p.items.length>12)fail('Välj mellan 1 och 12 övningar.');
 for(const item of p.items){
  lookup(item.exercise,item.variant);if(!allowedSides(item.exercise,item.variant).includes(item.side))fail('Sidan stämmer inte med den valda övningsvarianten.');
  const d=item.dose||{};
  out.items.push({key:text(item.key,100),exercise:item.exercise,variant:item.variant,side:item.side,note:text(item.note||'',300),dose:{sets:integer(d.sets,1,8),reps:integer(d.reps,1,40),hold:integer(d.hold,0,120),rest:integer(d.rest,0,180),tempo:integer(d.tempo,2,15)}});
 }
 if(new Set(out.items.map(i=>i.key)).size!==out.items.length)fail('Övningarna har dubbla ID.');
 const a=p.adjustment||{};out.adjustment={enabled:a.enabled===true,sets:integer(a.sets||1,1,8),reason:text(a.reason||'',200)};
 // Never permit an explicit start dose to increase the base prescription.
 if(out.adjustment.enabled&&out.items.some(i=>out.adjustment.sets>i.dose.sets))fail('Startdosen får inte öka den ordinarie dosen.');
 return out;
}
function doseFor(plan,item,first){const d=clone(item.dose);if(first&&plan.adjustment.enabled)d.sets=Math.min(d.sets,plan.adjustment.sets);return d;}
function sideLabel(side){return {left:'Vänster sida',right:'Höger sida',both:'Båda sidor, en i taget',simultaneous:'Båda samtidigt'}[side];}
function rounds(item){return item.dose.sets*(item.side==='both'?2:1);}
function roundInfo(item,completed){return {set:Math.floor(completed/(item.side==='both'?2:1))+1,side:item.side==='both'?(completed%2?'Höger':'Vänster'):({left:'Vänster',right:'Höger'}[item.side]||'')};}
function doseLabel(item){return `${item.dose.sets} ${item.dose.sets===1?'omgång':'omgångar'} × ${item.dose.hold?item.dose.hold+' sekunder':item.dose.reps+' repetitioner'}${item.side==='both'?' per sida':''}`;}
function minutes(plan,first=false){return Math.max(1,Math.round(plan.items.reduce((n,i)=>{const d=doseFor(plan,i,first);const k=i.side==='both'?2:1;return n+k*(d.sets*(d.hold||d.reps*d.tempo)+Math.max(0,d.sets-1)*d.rest)+20;},0)/60));}
function newSession(plan,first=false){const p=validatePlan(plan);return {schema:2,id:uid(),planId:p.id,revision:p.revision,date:dateKey(),startedAt:new Date().toISOString(),updatedAt:new Date().toISOString(),status:'active',feedback:null,issue:false,firstAdjusted:first&&p.adjustment.enabled,items:p.items.map(i=>({...clone(i),dose:doseFor(p,i,first),done:0,skipped:false,reason:''}))};}
function progress(s){const done=s.items.filter(i=>i.done>=rounds(i)&&!i.skipped).length;const skipped=s.items.filter(i=>i.skipped).length;const started=s.items.some(i=>i.done>0);return {done,skipped,total:s.items.length,started,settled:done+skipped===s.items.length};}
function markRound(s,index){const a=clone(s),i=a.items[index];if(!i||a.status!=='active')return a;i.skipped=false;i.reason='';i.done=Math.min(rounds(i),i.done+1);a.updatedAt=new Date().toISOString();return a;}
function skip(s,index,reason){const a=clone(s);if(a.status!=='active'||!a.items[index])return a;a.items[index].skipped=true;a.items[index].reason=text(reason,80);a.issue ||= reason==='Besvär under övningen';a.updatedAt=new Date().toISOString();return a;}
function finish(s){const a=clone(s),p=progress(a);a.status=p.done===p.total?'complete':(p.started?'partial':'not-done');a.updatedAt=new Date().toISOString();return a;}
function validateSession(s){
 if(!s||s.schema!==2||!Array.isArray(s.items)||s.items.length<1||s.items.length>12)fail('Ogiltig träningslogg.');
 text(s.id,100);text(s.planId,100);integer(s.revision,1,10000);
 if(!validDate(s.date)||!['active','complete','partial','not-done'].includes(s.status))fail('Ogiltig status eller datum i loggen.');
 if(!['Lätt','Lagom','Tung',null].includes(s.feedback))fail('Ogiltig återkoppling.');
 text(s.startedAt,40);text(s.updatedAt,40);
 const proxy=template();proxy.items=s.items;validatePlan(proxy);
 s.items.forEach(i=>{integer(i.done,0,rounds(i));if(typeof i.skipped!=='boolean')fail('Ogiltig övningsstatus.');text(i.reason||'',80);});
 const p=progress(s);if(s.status==='complete'&&p.done!==p.total)fail('Ett ofullständigt pass får inte räknas som genomfört.');
 return clone(s);
}
function weekSummary(sessions,plan,date=new Date()){
 const start=new Date(date);start.setHours(0,0,0,0);start.setDate(start.getDate()-((start.getDay()+6)%7));
 const days=Array.from({length:7},(_,n)=>{const d=new Date(start);d.setDate(d.getDate()+n);const key=dateKey(d);const list=sessions.filter(s=>s.planId===plan.id&&s.date===key);return {date:key,day:d.getDay(),scheduled:plan.days.includes(d.getDay()),today:key===dateKey(date),past:key<dateKey(date),status:list.some(s=>s.status==='complete')?'complete':list.some(s=>progress(s).started)?'partial':'empty'};});
 return {days,done:days.filter(d=>d.status==='complete').length,target:plan.days.length};
}
function encodePlan(plan){const str=JSON.stringify(validatePlan(plan));if(str.length>18000)fail('Programmet är för stort för en testlänk.');const bytes=new TextEncoder().encode(str);return btoa(Array.from(bytes,b=>String.fromCharCode(b)).join('')).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
function decodePlan(s){if(typeof s!=='string'||s.length>30000||!/^[\w-]+$/.test(s))fail('Testlänken är ogiltig.');try{return validatePlan(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(Uint8Array.from(atob(s.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0)))));}catch(e){fail('Testlänken är skadad eller hör inte till Reda 2.');}}
root.RedaCore={clone,uid,dateKey,lookup,allowedSides,makeItem,template,validatePlan,doseFor,sideLabel,rounds,roundInfo,doseLabel,minutes,newSession,progress,markRound,skip,finish,validateSession,weekSummary,encodePlan,decodePlan};
})(typeof window!=='undefined'?window:globalThis);
