// Explanations are a projection of the saved exercise, never a new prescription.
export const HELP_VERSION=1;
export const helpTopics={setup:'Startposition',execution:'Själva rörelsen',side:'Vilken sida?',range:'Hur långt?',dose:'Dos och tempo'};
export const sideLabels={left:'Vänster sida',right:'Höger sida',both:'Båda sidor, en i taget',simultaneous:'Båda samtidigt'};
const text=v=>typeof v==='string'?v.trim():'';
export function exerciseKey(x){return x?.motionKey||x?.motion?.key||x?.figure||x?.variantId||x?.id}
export function exerciseSide(x,round){return x?.side==='both'&&['left','right'].includes(round?.side)?round.side:x?.side||null}
export function helpAnswer(x,topic){
 if(!x||!Object.hasOwn(helpTopics,topic))return null;
 const steps=(Array.isArray(x.instructions)?x.instructions:[]).map(text).filter(Boolean);
 const instruction=steps.length?steps:[text(x.instruction)||text(x.cue)].filter(Boolean);
 const setup=[text(x.support),text(x.equipment)].filter((v,i,a)=>v&&a.indexOf(v)===i);
 let paragraphs=[],frame=null,focus=null,missing=false;
 if(topic==='setup'){
  paragraphs=setup;frame=0;focus='support';
  if(!paragraphs.length){paragraphs=['Ingen separat startposition är angiven i planen.'];missing=true}
  if(instruction[0])paragraphs=[...paragraphs,instruction[0]];
 }
 if(topic==='execution'){
  paragraphs=instruction;frame=.5;focus='movement';
  if(!paragraphs.length){paragraphs=['Utförandeinstruktion saknas i den sparade planen. Be din behandlare förtydliga.'];missing=true}
 }
 if(topic==='side'){
  paragraphs=[sideLabels[x.side]||'Sida är inte angiven i planen. Be din behandlare förtydliga.'];focus='side';missing=!sideLabels[x.side];
  if(x.side==='both')paragraphs.push('Omgångarnas knappar visar vilken sida som står på tur.');
 }
 if(topic==='range'){
  const range=text(x.prescribedRange)||text(x.prescription?.rom);
  paragraphs=[range||'Rörelseomfång är inte preciserat i planen. Be din behandlare förtydliga.'];missing=!range;
  paragraphs.push('Illustrationen visar bibliotekets rörelse. Den återger inte en individuellt angiven vinkel.');
  focus='movement'; // Do not suggest the generic endpoint is the prescribed limit.
 }
 if(topic==='dose'){
  const d=x.dose||{};paragraphs=[text(d.label)].filter(Boolean);
  if(!paragraphs.length&&Number.isFinite(d.sets)&&Number.isFinite(d.reps))paragraphs.push(`${d.sets} omgångar × ${d.reps} repetitioner${x.side==='both'?' per sida':''}.`);
  if(Number.isFinite(d.hold)&&d.hold>0)paragraphs.push(`Ordinerad hålltid: ${d.hold} sekunder.`);
  if(Number.isFinite(d.rest))paragraphs.push(`Ordinerad vila: ${d.rest} sekunder mellan omgångarna.`);
  const tempo=text(x.prescription?.tempo);if(tempo)paragraphs.push(`Tempo: ${tempo}`);else if(Number.isFinite(d.tempo))paragraphs.push(`Tempo i planen: ${d.tempo} sekunder per repetition.`);
  if(text(x.prescribedLoad))paragraphs.push(`Belastning: ${text(x.prescribedLoad)}`);
  if(!paragraphs.length){paragraphs=['Dos saknas i den sparade planen. Be din behandlare förtydliga.'];missing=true}
  paragraphs.push('Rörelsedemon räknar inga repetitioner. Registrera omgången när du har gjort din ordinerade dos.');
 }
 return {topic,title:helpTopics[topic],paragraphs,frame,focus,missing};
}
export function helpSummary(h){
 if(!h)return [];
 return [
  [h.exercise_name,sideLabels[h.exercise?.side],h.option_label,Number.isFinite(h.plan_version)?`plan v${h.plan_version}`:null].filter(Boolean).join(' · '),
  'Hjälp som öppnats: '+(h.topics||[]).map(t=>helpTopics[t]||t).join(', '),
  h.outcome==='clear'?'Patienten uppger att instruktionen blev tydlig.':'Patienten behöver fortfarande hjälp av behandlaren.',
  h.note?'Patientens kommentar: '+h.note:null
 ].filter(Boolean);
}
