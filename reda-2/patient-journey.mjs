import {createMovementLesson} from './movement-lesson.mjs?v=4';
import {focusCamera} from './movement-lesson-model.mjs?v=3';
import {exerciseSide,sideLabels} from './exercise-help-model.mjs?v=20260912-coach1';

const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const motionKey=x=>x.motionKey||x.motion?.key||x.figure||x.variantId||x.id;
export function doseText(x){return x.dose?.label||[x.dose?.sets&&`${x.dose.sets} ${Number(x.dose.sets)===1?'omgång':'omgångar'}`,x.dose?.reps&&`${x.dose.reps} repetitioner`].filter(Boolean).join(' · ')||'Följ din ordination'}
export function thumb(x){
 const key=motionKey(x),html=window.RedaFigures?.svg(key,0,x.side,x.name)||'';
 const pose=window.RedaMotionStudio?.pose(key,0),camera=pose&&focusCamera(pose);
 return camera?html.replace(/viewBox="[^"]*"/,`viewBox="${camera.join(' ')}"`):html;
}
export function renderExerciseOverview(host,{exercises,progress=[],onPreview}){
 host.replaceChildren();
 exercises.forEach((x,i)=>{
  const p=progress[i],status=p?.status==='completed'?'Klar':p?.status==='skipped'?'Överhoppad':p?.roundsDone?`${p.roundsDone} omgångar klara`:'';
  const row=document.createElement('li');
  row.innerHTML=`<button type="button" class="journey-exercise" data-preview-exercise="${esc(x.id)}" aria-label="Titta på ${esc(x.name)}"><span class="journey-thumb" aria-hidden="true">${thumb(x)}</span><span class="journey-exercise-copy"><b>${esc(x.name)}</b><small>${esc(doseText(x))}${x.side==='left'?' · vänster':x.side==='right'?' · höger':x.side==='both'?' · per sida':''}</small><span class="journey-row-status">${esc(status||'Visa övningen')}</span></span><span class="journey-row-arrow" aria-hidden="true">${status==='Klar'?'✓':'↗'}</span></button>`;
  row.querySelector('button').onclick=()=>onPreview(x,i);host.append(row);
 });
}

// A read-only window into the current prescription. It cannot create or mark a session.
export function createExercisePreview(){
 const dialog=document.createElement('dialog');dialog.className='journey-preview';dialog.setAttribute('aria-labelledby','previewExerciseName');
 dialog.innerHTML='<header class="journey-preview-head"><div><span class="journey-overline">Titta på övningen</span><h2 id="previewExerciseName"></h2><p id="previewExerciseDose"></p></div><button type="button" class="journey-close" aria-label="Stäng övningen">✕</button></header><div class="journey-preview-body"><div id="previewLesson"></div><p class="journey-preview-why" hidden></p><details class="journey-prescription"><summary>Din ordination</summary><dl></dl></details></div><footer><button type="button" class="journey-return">Tillbaka till min plan</button><p>Att titta registrerar ingen träning.</p></footer>';
 document.body.append(dialog);const q=s=>dialog.querySelector(s),lesson=createMovementLesson(q('#previewLesson'),{idPrefix:'preview-'});let opener=null;
 const close=()=>dialog.close();q('.journey-close').onclick=close;q('.journey-return').onclick=close;
 dialog.addEventListener('close',()=>{lesson.pause();for(const d of dialog.querySelectorAll('dialog[open]'))d.close();opener?.isConnected&&opener.focus({preventScroll:true})});
 return {open(x,{contextId='',returnLabel='Tillbaka till min plan'}={}){
  opener=document.activeElement;q('#previewExerciseName').textContent=x.name;q('#previewExerciseDose').textContent=doseText(x);q('.journey-return').textContent=returnLabel;
  q('.journey-preview-why').hidden=!x.why;q('.journey-preview-why').textContent=x.why||'';
  q('.journey-prescription').open=false;
  q('dl').innerHTML=[['Sida',sideLabels[exerciseSide(x)]],['Utrustning och stöd',x.support||x.equipment],['Belastning',x.prescribedLoad||x.prescription?.load],['Rörelseomfång',x.prescribedRange||x.prescription?.rom],['Tempo',x.prescription?.tempo],['Vila',Number(x.dose?.rest)>0?x.dose.rest+' sekunder mellan omgångarna':null]].filter(([,v])=>v).map(([k,v])=>`<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('');
  lesson.setExercise(x,{motionKey:motionKey(x),exerciseSide:exerciseSide(x),contextId});dialog.showModal();
 },close,destroy(){close();lesson.destroy();dialog.remove()}};
}

export function renderPreparation(host,exercises){
 const equipment=[...new Set(exercises.map(x=>x.support||x.equipment).filter(x=>typeof x==='string'&&x.trim()))];
 host.hidden=!equipment.length;host.innerHTML=equipment.length?'<span aria-hidden="true">↳</span><p><b>Ta fram innan du börjar</b><span>'+equipment.map(esc).join(' · ')+'</span></p>':'';
}
