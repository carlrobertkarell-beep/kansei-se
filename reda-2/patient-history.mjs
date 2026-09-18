import {hasNoRecordedRounds} from './session-overview-model.mjs?v=20260918-1';
// Read-only patient presentation. Never merge by date or guess which pass a reply belongs to.
import {barriers} from './patient-loop.mjs?v=2';
export function patientHistory(events,{sessions=[],reflections=[],responses=[]}={}){
 const known=new Map(sessions.map(s=>[s.id,s])),links=new Map();
 for(const [prefix,items] of [['reflection',reflections],['response',responses]])for(const r of items){const s=known.get(r.session_id);if(s&&s.plan_id===r.plan_id&&s.plan_version===r.plan_version)links.set(prefix+':'+r.id,r.session_id)}
 const groups=new Map(),result=[];
 for(const e of new Map(events.map(e=>[e.id,e])).values()){
  const match=/^(start|end):(.+)$/.exec(e.id),linked=known.get(links.get(e.id));
  const sid=match?.[2]||(linked&&linked.plan_id===e.plan_id&&linked.plan_version===e.plan_version?linked.id:null);
  if(!sid){result.push({...e});continue}
  // Include plan identity in the key even if a malformed feed reuses a session ID.
  const key=[sid,e.plan_id||'',e.plan_version||''].join('|');
  if(!groups.has(key))groups.set(key,{sid,events:[]});groups.get(key).events.push(e);
 }
 for(const {sid,events:xs} of groups.values()){
  const end=xs.find(e=>e.id==='end:'+sid),start=xs.find(e=>e.id==='start:'+sid),base=end||start||xs[0],s=known.get(sid);
  // Only show details fetched for this exact plan version and session.
  const exact=s&&s.plan_id===base.plan_id&&s.plan_version===base.plan_version?s:null;
  const completed=!!end||!!exact?.completed_at;
  const progress=exact?.payload?.exercises,parts=[];
  if(Array.isArray(progress)&&progress.length)parts.push(`${progress.filter(p=>p.status==='completed').length} av ${progress.length} övningar genomförda`);
  else if((end||start)?.detail)parts.push((end||start).detail);
  const answers=exact&&reflections.filter(r=>r.session_id===sid&&links.has('reflection:'+r.id)).sort((a,b)=>Date.parse(b.created_at)-Date.parse(a.created_at))[0]?.answers;
  if(answers){if(barriers[answers.barrier])parts.push(answers.barrier==='none'?'Inget särskilt gjorde passet svårt':barriers[answers.barrier]);if(answers.support==='yes')parts.push('Du har bett om hjälp')}
  const later=exact&&responses.some(r=>r.session_id===sid&&links.has('response:'+r.id));
  if(later)parts.push('Uppföljning efter passet besvarad');
  result.push({...base,id:'session:'+sid,category:'training',title:completed&&hasNoRecordedRounds(progress)?'Avslutat utan registrerade omgångar':completed?(end?.title||(exact?.status==='completed'?'Pass genomfört':'Pass delvis genomfört')):'Påbörjat pass',detail:parts.join(' · '),occurred_at:end?.occurred_at||exact?.completed_at||start?.occurred_at||base.occurred_at});
 }
 return result.sort((a,b)=>Date.parse(b.occurred_at)-Date.parse(a.occurred_at)||String(b.id).localeCompare(String(a.id)));
}
