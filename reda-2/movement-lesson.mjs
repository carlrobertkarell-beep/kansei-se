import {lessonInstructions,lessonSegments,wholeLessonSequence,focusCamera,createLessonPlayback,localSwedishVoice} from './movement-lesson-model.mjs?v=3';
import {sideLabels} from './exercise-help-model.mjs?v=20260912-coach1';
const icon=(name)=>({play:'<path d="m9 5 11 7-11 7Z"/>',pause:'<path d="M8 5v14M16 5v14"/>',expand:'<path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5"/>',close:'<path d="m6 6 12 12M18 6 6 18"/>',sound:'<path d="m11 4-6 5H2v6h3l6 5ZM16 8a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14"/>'}[name]||'');
const glyph=name=>`<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${icon(name)}</svg>`;
export function createMovementLesson(host){
 const F=window.RedaFigures,media=matchMedia('(prefers-reduced-motion: reduce)'),speech=window.speechSynthesis;
 let exercise=null,key='',side='',identity='',instructions=[],segments=[],readIndex=0,part=0,view='whole',focus=null,voice=null,utterance=null,customStill=false;
 const remembered=new Map();host.classList.add('movement-lesson');
 host.innerHTML=`<div class="lesson-media"><div id="motionStudio" class="motion-studio" tabindex="-1" aria-label="Övningens demonstration"><div class="motion-caption"><span id="motionSide" class="motion-side"></span><button type="button" id="lessonExpand" class="lesson-icon" aria-label="Förstora rörelsen">${glyph('expand')}</button></div><div id="motion" class="motion"></div><span id="motionPhase" class="motion-phase">Startläge</span></div><div class="lesson-transport"><button type="button" id="motionPlay">${glyph('play')}<span>Visa rörelsen</span></button><button type="button" id="motionSlow" aria-pressed="false" aria-label="Visa extra långsamt">Långsamt</button><button type="button" id="lessonGuided" aria-haspopup="dialog">Instruktion</button></div><p id="lessonStatus" class="lesson-status" role="status"></p></div>

 <dialog id="lessonDetails" class="exercise-sheet" aria-labelledby="lessonDetailsTitle"><div class="sheet-heading"><h2 id="lessonDetailsTitle">Så gör du</h2><button type="button" id="lessonCloseDetails" class="lesson-icon" aria-label="Stäng instruktionen">${glyph('close')}</button></div><div class="sheet-content"><div class="lesson-tabs" role="group" aria-label="Välj förklaring"><button type="button" data-lesson-mode="read" aria-pressed="true">Instruktion</button><button type="button" data-lesson-mode="watch" aria-pressed="false">Rörelsens delar</button></div><div class="lesson-reading"><p class="lesson-counter" id="lessonCounter"></p><p class="lesson-instruction" id="lessonInstruction" tabindex="-1"></p><div class="lesson-read-actions"><button type="button" id="lessonPrevious" aria-label="Föregående instruktion">←</button><button type="button" id="lessonListen" hidden>${glyph('sound')} Lyssna</button><button type="button" id="lessonNext">Nästa</button></div></div><div class="lesson-parts" hidden><p>Välj en del att se i stor bild. Den stannar när delen är klar.</p><div id="lessonParts"></div></div><details class="lesson-stills"><summary>Visa en stillbild</summary><div class="lesson-frame-buttons"><button type="button" data-motion-frame="0" data-frame="0">Startläge</button><button type="button" data-motion-frame="0.5" data-frame="0.5">På väg</button><button type="button" data-motion-frame="1" data-frame="1">Slutläge</button></div></details><p class="lesson-note">Visningen förklarar rörelsen. Följ dos, tempo och rörelseomfång i din plan.</p></div></dialog>
 <dialog id="lessonFocus" class="lesson-focus" aria-label="Förstorad rörelse"><div class="focus-heading"><span id="focusTitle"></span><button type="button" id="lessonCloseFocus" class="lesson-icon" aria-label="Stäng förstorad rörelse">${glyph('close')}</button></div><div class="focus-body"></div></dialog>`;
 let originalCamera=null;
 const $=s=>host.querySelector(s),play=$('#motionPlay'),status=$('#lessonStatus'),details=$('#lessonDetails'),zoom=$('#lessonFocus'),visual=$('.lesson-media'),anchor=document.createComment('exercise media');visual.before(anchor);
 function draw(t){if(!exercise)return;const el=$('#motion');if(!F.drawFrame?.(el,key,t,focus))el.innerHTML=F.svg(key,t,side,exercise.name,{focus});el.dataset.position=String(t)}
 const playback=createLessonPlayback({draw,change:renderPlayback});
 function renderPlayback(s){
  host.dataset.playing=String(s.playing);host.dataset.view=view;
  play.disabled=media.matches;
  const label=media.matches?'Stillbild':s.playing?'Pausa':s.complete?'Visa igen':s.progress>0?'Fortsätt':view==='whole'?'Visa':'Visa delen';
  play.innerHTML=glyph(s.playing?'pause':'play')+`<span>${label}</span>`;
  play.setAttribute('aria-label',s.playing?'Pausa rörelsen':label==='Visa'?'Visa hela rörelsen':label);
  status.textContent=media.matches?'Välj en stillbild under Så gör du.':s.playing?'En visning. Sedan stannar rörelsen.':s.complete?'Visningen är klar. Träna i din takt.':s.progress>0?'Pausad. Fortsätt när du vill.':'Tryck på play om du vill se rörelsen.';
 }
 function silence(){if(utterance){utterance.onend=null;utterance.onerror=null;speech?.cancel();utterance=null}$('#lessonListen').innerHTML=glyph('sound')+' Lyssna'}
 function voices(){voice=localSwedishVoice(speech?.getVoices());$('#lessonListen').hidden=!voice}
 function pause(){playback.pause();silence()}
 function resetCamera(){if(originalCamera){$('#motion svg')?.setAttribute('viewBox',originalCamera);originalCamera=null}}
 function remember(){if(identity)remembered.set(identity,{readIndex,slow:playback.state().slow})}
 function renderRead(){
  $('#lessonCounter').textContent=instructions.length?`${readIndex+1} av ${instructions.length}`:'Instruktion saknas';
  $('#lessonInstruction').textContent=instructions[readIndex]||'Be din behandlare förtydliga hur du ska göra. Använd hjälpen i övningen.';
  $('#lessonPrevious').disabled=readIndex===0;$('#lessonNext').textContent=readIndex<instructions.length-1?'Nästa →':'Klart';
 }
 function choosePart(i){pause();view='parts';part=i;customStill=false;focus=null;const s=segments[part];$('#motionPhase').textContent=s.label;playback.select(s);details.close();if(!media.matches)playback.play();play.focus({preventScroll:true})}
 function showFrame(t,newFocus=null){pause();focus=newFocus;view='whole';playback.still(t);customStill=true;$('#motionPhase').textContent=t===0?'Startläge':t===1?'Slutläge':'På väg';host.querySelectorAll('[data-motion-frame]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.motionFrame)===t)))}
 function openDetails(){pause();renderRead();details.showModal()}
 $('#lessonGuided').onclick=openDetails;$('#lessonCloseDetails').onclick=()=>details.close();details.addEventListener('close',silence);
 host.querySelectorAll('[data-lesson-mode]').forEach(b=>b.onclick=()=>{silence();const read=b.dataset.lessonMode==='read';$('.lesson-reading').hidden=!read;$('.lesson-parts').hidden=read;host.querySelectorAll('[data-lesson-mode]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)))});
 $('#lessonPrevious').onclick=()=>{silence();readIndex=Math.max(0,readIndex-1);renderRead();remember();$('#lessonInstruction').focus()};
 $('#lessonNext').onclick=()=>{silence();if(readIndex<instructions.length-1){readIndex++;renderRead();remember();$('#lessonInstruction').focus()}else details.close()};
 play.onclick=()=>{silence();if(media.matches)return;if(playback.state().playing)playback.pause();else{resetCamera();if(customStill){view='whole';customStill=false;playback.select(wholeLessonSequence(key));$('#motionPhase').textContent='Hela rörelsen'}playback.play()}};
 $('#motionSlow').onclick=()=>{const slow=!playback.state().slow;playback.speed(slow);$('#motionSlow').setAttribute('aria-pressed',String(slow));remember()};
 host.querySelectorAll('[data-motion-frame]').forEach(b=>b.onclick=()=>{showFrame(Number(b.dataset.motionFrame));details.close();play.focus({preventScroll:true})});
 $('#lessonListen').onclick=()=>{if(utterance){silence();return}voices();if(!voice||!instructions[readIndex])return;playback.pause();const u=new SpeechSynthesisUtterance(instructions[readIndex]);u.voice=voice;u.lang=voice.lang;u.rate=.9;utterance=u;$('#lessonListen').textContent='Stoppa uppläsning';u.onend=()=>{if(utterance===u)silence()};u.onerror=()=>{if(utterance===u){silence();$('#lessonCounter').textContent='Uppläsningen kunde inte starta. Texten finns kvar.'}};speech.speak(u)};
 $('#lessonExpand').onclick=()=>{pause();$('#focusTitle').textContent=exercise.name;const svg=$('#motion svg'),q=window.RedaMotionStudio?.pose(key,playback.state().position),camera=q?focusCamera(q):null;if(camera){originalCamera=svg.getAttribute('viewBox');svg.setAttribute('viewBox',camera.join(' '))}$('.focus-body').append(visual);$('#lessonExpand').hidden=true;$('#lessonGuided').hidden=true;zoom.showModal()};
 $('#lessonCloseFocus').onclick=()=>zoom.close();zoom.addEventListener('close',()=>{pause();resetCamera();anchor.after(visual);$('#lessonExpand').hidden=false;$('#lessonGuided').hidden=false;$('#lessonExpand').focus({preventScroll:true})});
 function visibility(){if(document.hidden)pause()}
 function reduce(){pause();renderPlayback(playback.state())}
 document.addEventListener('visibilitychange',visibility);media.addEventListener('change',reduce);speech?.addEventListener('voiceschanged',voices);voices();
 return {pause,showFrame,openDetails,position:()=>playback.state().position,
  setExercise(x,{motionKey,exerciseSide,contextId}={}){
   const nextKey=motionKey||x.motionKey||x.figure||x.id,nextSide=exerciseSide||x.side,next=String(contextId||'')+':'+x.id+':'+nextKey;
   if(identity===next&&side===nextSide){exercise=x;return}
   const changed=identity!==next;pause();remember();if(details.open)details.close();if(zoom.open)zoom.close();identity=next;exercise=x;key=nextKey;side=nextSide;instructions=lessonInstructions(x);segments=lessonSegments(key);focus=null;view='whole';customStill=false;if(changed){$('.lesson-stills').open=false;$('.lesson-reading').hidden=false;$('.lesson-parts').hidden=true;host.querySelectorAll('[data-lesson-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.lessonMode==='read')))}host.querySelectorAll('[data-motion-frame]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.motionFrame)===0)));
   const previous=remembered.get(identity);readIndex=Math.min(previous?.readIndex||0,Math.max(0,instructions.length-1));
   $('#motion').innerHTML=F.svg(key,0,side,x.name);$('#motionSide').textContent=sideLabels[side]||'Sida behöver förtydligas';$('#motionPhase').textContent='Startläge';

   $('#lessonParts').replaceChildren();segments.forEach((s,i)=>{const b=document.createElement('button');b.type='button';b.textContent=`${i+1}. ${s.label}`;b.dataset.lessonPart=String(i);b.onclick=()=>choosePart(i);$('#lessonParts').append(b)});
   playback.select(wholeLessonSequence(key));playback.speed(previous?.slow||false);$('#motionSlow').setAttribute('aria-pressed',String(playback.state().slow));renderRead();host.dataset.mode='exercise';
  },
  destroy(){pause();if(details.open)details.close();if(zoom.open)zoom.close();document.removeEventListener('visibilitychange',visibility);media.removeEventListener('change',reduce);speech?.removeEventListener('voiceschanged',voices)}
 };
}
