// Read-only preparation of a clinician shortcut. It never creates or activates a plan.
const text=v=>String(v||'').trim();
export function quickStartRecommendation(profile,blueprints,startProfiles){
 const focus=text(profile?.focus),goal=text(profile?.goal),saved=profile?.clinical_context||{};
 if(!focus&&!goal&&!Object.keys(saved).length)return null;
 const groups=[[/knä|kna|patell|menisk/i,/knä|knee/i],[/axel|skuld|cuff|shoulder/i,/axel|shoulder/i],[/höft|hoft|ljumsk|gtps/i,/höft|hip/i],[/hälsena|achill|vad|fotled/i,/fotled|achill/i],[/armbåge|armbage|epicond/i,/armbåge|elbow/i],[/nack|cervik/i,/nack|neck/i],[/länd|landrygg|rygg|lumb/i,/länd|lumbar/i]];
 const match=groups.find(([re])=>re.test(focus));
 const candidates=match?(blueprints||[]).filter(b=>match[1].test(text(b.name)+' '+text(b.id))):[];
 const blueprintId=saved.blueprintId||(candidates.length===1?candidates[0].id:'');
 const base={...(startProfiles?.home?.values||{}),...saved};
 const context={...base,blueprintId,goal,patientName:text(profile?.display_name)};
 const direction=(blueprints||[]).find(b=>b.id===blueprintId);
 return {context,title:direction?'Förbered '+direction.name:'Förbered plan från bedömningen',detail:[focus&&'Fokus: '+focus,goal&&'Mål: '+goal].filter(Boolean).join(' · ')||'Utgår från sparade kliniska förutsättningar.',direction:direction?.name||'',source:{focus:!!focus,goal:!!goal,savedContext:Object.keys(saved).length>0}};
}
export function quickStartSummary(rec){
 if(!rec)return[];const c=rec.context||{},stage={protected:'Skonsam belastning',build:'Uppbyggnad',higher:'Högre belastning'}[c.stage],capacity={supported:'Med stöd',standard:'Grundutförande',high:'Hög kapacitet'}[c.capacity],place={home:'Hemma',gym:'Gym',both:'Hemma + gym'}[c.equipment];
 return [rec.direction,stage,capacity,place].filter(Boolean);
}
