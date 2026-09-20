const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// Only report a duration when every exercise has an explicit timed dose.
export function durationHint(exercises=[]){
 let seconds=0;if(!exercises.length)return 'I din takt';
 for(const x of exercises){const d=x.dose||{},rounds=Number(d.sets)*(x.side==='both'?2:1),reps=Number(d.reps),tempo=Number(d.tempo),hold=Number(d.hold||0),rest=Number(d.rest||0);
  if(!Number.isFinite(rounds)||rounds<1||!Number.isFinite(reps)||reps<1||!Number.isFinite(tempo)||tempo<=0||!Number.isFinite(hold)||hold<0||!Number.isFinite(rest)||rest<0)return 'I din takt';
  seconds+=rounds*reps*(tempo+hold)+Math.max(0,rounds-1)*rest;
 }
 const minutes=Math.max(1,Math.ceil(seconds/60));return `Cirka ${minutes} min + egna pauser`;
}
const dose=x=>x?.dose?.label||`${x?.dose?.sets||'–'} omgångar × ${x?.dose?.reps||'–'} repetitioner`;
export function planChanges(previous,current){
 if(!previous||!current||previous.id===current.id)return [];
 const before=previous.payload?.exercises||[],after=current.payload?.exercises||[],changes=[];
 for(const x of after){const old=before.find(v=>v.id===x.id);if(!old){changes.push(`${x.name}: tillagd i planen.`);continue}
  if(JSON.stringify(old.dose)!==JSON.stringify(x.dose))changes.push(`${x.name}: ${dose(old)} → ${dose(x)}. Kontrollera dos, tempo och vila i övningen.`);
  if(old.side!==x.side)changes.push(`${x.name}: sida har ändrats.`);
  if(old.variantId!==x.variantId||old.prescribedLoad!==x.prescribedLoad||old.prescribedRange!==x.prescribedRange)changes.push(`${x.name}: utförande, belastning eller rörelseomfång har ändrats. Läs ordinationen.`);
 }
 for(const x of before)if(!after.some(v=>v.id===x.id))changes.push(`${x.name}: finns inte längre i planen.`);
 if(JSON.stringify(previous.payload?.schedule)!==JSON.stringify(current.payload?.schedule))changes.push('Träningsdagarna har ändrats.');
 return changes.length?changes:['En ny planversion har publicerats. Läs den aktuella ordinationen och informationen från din behandlare.'];
}
export function changesHTML(changes,version){return changes.length?`<section class="patient-change-note" aria-labelledby="patientChangeTitle"><h3 id="patientChangeTitle">Din plan har uppdaterats · version ${esc(version)}</h3><ul>${changes.map(s=>'<li>'+esc(s)+'</li>').join('')}</ul><p>Detta jämför med planen som visades nyss. Följ den nya ordinationen; behandlarens förklaring visas separat när den finns.</p></section>`:''}
export function contactHint(support,messages){
 if(messages?.status==='ready'&&messages.data?.reply_to)return {kind:'messages',title:'Din behandlare har en fråga',detail:'Öppna meddelandet och svara.'};
 if(support?.status==='ready'){
  const phase=support.data?.phase;
  if(['needs_review','needs_resolution','scheduled'].includes(phase))return {kind:'support',title:'Din återkoppling finns hos kliniken',detail:'Visa status för din hjälp och uppföljning.'};
  if(phase==='handled')return {kind:'support',title:'Din återkoppling är hanterad',detail:'Läs status. Fortsätt följa din aktuella plan.'};
 }
 if(messages?.status==='error'||support?.status==='error')return {kind:'support',title:'Kontaktstatus kunde inte hämtas',detail:'Öppna kontakt och försök uppdatera.'};
 if(messages?.status==='ready'&&messages.data?.messages?.some(x=>x.kind!=='patient'))return {kind:'messages',title:'Meddelanden från din behandlare',detail:'Öppna din dialog med kliniken.'};
 return null;
}
