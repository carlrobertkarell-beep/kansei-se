const validDate=v=>v&&Number.isFinite(Date.parse(v));const day=ts=>validDate(ts)?new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Stockholm',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(ts)):'';
const labelFeedback={heavy:'för tung',easy:'lätt',okay:'lagom'};
export function followupDigest({plan,sessions=[],responses=[],reflections=[],now=new Date().toISOString(),days=14}={}){
 if(!plan?.id)return {valid:false};
 const cutoff=Date.parse(now)-days*86400000,match=x=>x?.plan_id===plan.id&&(x.plan_version===undefined||x.plan_version===plan.version);
 const ss=sessions.filter(s=>match(s)&&validDate(s.started_at)&&Date.parse(s.started_at)>=cutoff),completed=ss.filter(s=>s.status==='completed'),partial=ss.filter(s=>['partial','started'].includes(s.status));
 const exerciseMap=new Map((plan.payload?.exercises||[]).map(x=>[x.id,{id:x.id,name:x.name,heavy:0,skipped:0,completed:0,total:0}]));
 for(const s of ss)for(const x of s.payload?.exercises||[]){const r=exerciseMap.get(x.exerciseId);if(!r)continue;r.total++;if(x.status==='completed')r.completed++;if(x.status==='skipped')r.skipped++;if(x.feedback==='heavy')r.heavy++}
 const exerciseSignals=[...exerciseMap.values()].filter(x=>x.heavy||x.skipped).sort((a,b)=>(b.heavy+b.skipped)-(a.heavy+a.skipped)||a.name.localeCompare(b.name,'sv-SE'));
 const rr=responses.filter(r=>match(r)&&validDate(r.created_at)&&Date.parse(r.created_at)>=cutoff),rf=reflections.filter(r=>match(r)&&validDate(r.created_at)&&Date.parse(r.created_at)>=cutoff);
 const worse=rr.filter(r=>r.answers?.nextDay==='worse'||r.answers?.function==='worse'),contact=rr.filter(r=>r.answers?.contact==='yes').length+rf.filter(r=>r.answers?.support==='yes').length,execution=rr.filter(r=>r.answers?.quality==='difficult').length+rf.filter(r=>r.answers?.barrier==='execution').length,symptoms=rf.filter(r=>r.answers?.barrier==='symptoms').length;
 const flags=[];if(worse.length||symptoms)flags.push({kind:'symptoms',label:'Förändrade besvär/funktion',count:worse.length+symptoms});if(contact)flags.push({kind:'contact',label:'Patienten har bett om hjälp',count:contact});if(execution)flags.push({kind:'execution',label:'Utförandet behöver stämmas av',count:execution});for(const x of exerciseSignals.slice(0,3))flags.push({kind:'exercise',exerciseId:x.id,label:x.name,detail:[x.heavy&&x.heavy+' × för tung',x.skipped&&x.skipped+' × överhoppad'].filter(Boolean).join(' · ')});
 const headline=completed.length+' genomförda pass'+(partial.length?' · '+partial.length+' delvis/påbörjade':'')+' · senaste '+days+' dagarna';
 const action=flags.length?'Granska underlaget':'Ingen ny avvikande signal i registrerat underlag';
 return {valid:true,headline,action,flags,completed:completed.length,partial:partial.length,sessionCount:ss.length,responseCount:rr.length,reflectionCount:rf.length,exerciseSignals,lastSession:ss.sort((a,b)=>Date.parse(b.started_at)-Date.parse(a.started_at))[0]?.started_at||null,asOf:day(now)};
}
