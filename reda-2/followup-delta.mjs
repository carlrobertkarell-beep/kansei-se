const msDay=86400000;const valid=v=>v&&Number.isFinite(Date.parse(v));const inRange=(v,start,end)=>valid(v)&&Date.parse(v)>=Date.parse(start)&&Date.parse(v)<Date.parse(end);
function summarize({plan,sessions=[],responses=[],reflections=[],start,end}){
 const match=x=>x?.plan_id===plan.id&&(x.plan_version===undefined||x.plan_version===plan.version),ss=sessions.filter(x=>match(x)&&inRange(x.started_at,start,end)),rr=responses.filter(x=>match(x)&&inRange(x.created_at,start,end)),rf=reflections.filter(x=>match(x)&&inRange(x.created_at,start,end));
 const exercises=new Map((plan.payload?.exercises||[]).map(x=>[x.id,{id:x.id,name:x.name,heavy:0,skipped:0,okay:0,easy:0}]));
 for(const s of ss)for(const x of s.payload?.exercises||[]){const r=exercises.get(x.exerciseId);if(!r)continue;if(x.status==='skipped')r.skipped++;if(['heavy','okay','easy'].includes(x.feedback))r[x.feedback]++}
 return {completed:ss.filter(x=>x.status==='completed').length,partial:ss.filter(x=>['partial','started'].includes(x.status)).length,worse:rr.filter(x=>x.answers?.nextDay==='worse'||x.answers?.function==='worse').length,contact:rr.filter(x=>x.answers?.contact==='yes').length+rf.filter(x=>x.answers?.support==='yes').length,execution:rr.filter(x=>x.answers?.quality==='difficult').length+rf.filter(x=>x.answers?.barrier==='execution').length,exercises:[...exercises.values()]};
}
export function followupDelta({plan,sessions=[],responses=[],reflections=[],boundary,now=new Date().toISOString()}={}){
 if(!plan?.id||!valid(boundary)||!valid(now)||Date.parse(boundary)>=Date.parse(now))return {valid:false};
 const span=Math.min(28,Math.max(1,Math.ceil((Date.parse(now)-Date.parse(boundary))/msDay))),previousStart=new Date(Date.parse(boundary)-span*msDay).toISOString();
 const current=summarize({plan,sessions,responses,reflections,start:boundary,end:now}),previous=summarize({plan,sessions,responses,reflections,start:previousStart,end:boundary});
 const changes=[];const diff=(a,b)=>a-b;
 if(diff(current.completed,previous.completed))changes.push({kind:'training',label:'Genomförda pass',before:previous.completed,after:current.completed});
 if(current.worse!==previous.worse)changes.push({kind:'symptoms',label:'Registreringar med försämring',before:previous.worse,after:current.worse});
 if(current.contact!==previous.contact)changes.push({kind:'contact',label:'Önskemål om hjälp',before:previous.contact,after:current.contact});
 if(current.execution!==previous.execution)changes.push({kind:'execution',label:'Svårt med utförandet',before:previous.execution,after:current.execution});
 for(const x of current.exercises){const old=previous.exercises.find(y=>y.id===x.id);if(!old)continue;if(x.heavy!==old.heavy||x.skipped!==old.skipped){changes.push({kind:'exercise',label:x.name,before:[old.heavy&&old.heavy+' × för tung',old.skipped&&old.skipped+' × överhoppad'].filter(Boolean).join(' · ')||'ingen sådan registrering',after:[x.heavy&&x.heavy+' × för tung',x.skipped&&x.skipped+' × överhoppad'].filter(Boolean).join(' · ')||'ingen sådan registrering'})}}
 return {valid:true,boundary,previousStart,current,previous,changes,headline:changes.length?changes.length+' förändringar sedan jämförelseperioden':'Ingen tydlig förändring i de jämförda registreringarna'};
}
