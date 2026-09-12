import {lessonInstructions,lessonSegments,createLessonPlayback,localSwedishVoice} from './movement-lesson-model.mjs?v=1';
import {sideLabels} from './exercise-help-model.mjs?v=20260912-coach1';

export function createMovementLesson(host,{onReady=()=>{}}={}){
 const F=window.RedaFigures,media=matchMedia('(prefers-reduced-motion: reduce)'),speech=window.speechSynthesis;
 let exercise=null,key='',side='',identity='',instructions=[],segments=[],readIndex=0,part=0,mode='read',focus=null,voice=null,utterance=null,customStill=false;
 host.classList.add('movement-lesson');
 host.innerHTML=`<div class="lesson-tabs" role="group" aria-label="Välj hur du vill gå igenom övningen"><button type="button" data-lesson-mode="read" aria-pressed="true">1. Läs eller lyssna</button><button type="button" data-lesson-mode="watch" aria-pressed="false">2. Se rörelsen</button></div>
 <div id="motionStudio" class="motion-studio" tabindex="-1" aria-label="Övningens demonstration"><div class="motion-caption"><span>REDA · ÖVNINGSGUIDE</span><span id="motionSide" class="motion-side"></span></div><div id="motion" class="motion"></div>
 <div class="lesson-reading"><p class="lesson-counter" id="lessonCounter"></p><p class="lesson-instruction" id="lessonInstruction" tabindex="-1"></p><div class="lesson-read-actions"><button type="button" id="lessonPrevious">Föregående</button><button type="button" id="lessonListen" hidden>Lyssna</button><button type="button" id="lessonNext">Nästa instruktion</button></div></div>
 <div class="lesson-watching" hidden><div class="motion-guide"><div><b id="motionPhase">Startläge</b><span id="lessonStatus" role="status">Starta när du vill. Visningen stannar efter varje del.</span></div><span id="lessonPart" class="lesson-counter"></span></div><div class="ei-motion-controls" role="group" aria-label="Styr rörelsevisningen"><button id="motionPlay" type="button">Visa den här delen</button><button id="lessonNextPart" type="button">Visa nästa del</button></div><div class="lesson-secondary"><button id="motionSlow" type="button" aria-pressed="false">Extra långsamt</button><button id="lessonPreviousPart" type="button">Föregående del</button></div>
 <details class="lesson-stills"><summary>Välj en stillbild</summary><div class="lesson-frame-buttons"><button type="button" data-motion-frame="0" data-frame="0">Startläge</button><button type="button" data-motion-frame="0.5" data-frame="0.5">På väg</button><button type="button" data-motion-frame="1" data-frame="1">Slutläge</button></div></details></div></div>
 <p class="lesson-note">Visningens hastighet är till för att lära. Träna i tempot i din plan.</p><button type="button" id="lessonReady" class="lesson-ready">Jag är redo att träna <span aria-hidden="true">→</span></button>`;
 const $=s=>host.querySelector(s),play=$('#motionPlay'),status=$('#lessonStatus');
 function draw(t){if(!exercise)return;const el=$('#motion');if(!F.drawFrame?.(el,key,t,focus))el.innerHTML=F.svg(key,t,side,exercise.name,{focus});el.dataset.position=String(t)}
 const playback=createLessonPlayback({draw,change:s=>{
  host.dataset.playing=String(s.playing);play.disabled=media.matches;play.textContent=media.matches?'Använd stillbilderna':s.playing?'Pausa rörelsen':s.complete?'Visa delen igen':s.progress>0?'Fortsätt visningen':'Visa den här delen';
  status.textContent=media.matches?'Stilla visning är på. Välj en bild nedan.':s.playing?'Titta i lugn och ro. Du kan pausa när som helst.':s.complete?'Den här delen är klar. Nästa del väntar på dig.':s.progress>0?'Pausad. Fortsätt när du vill.':'Starta när du vill. Visningen stannar efter varje del.';
 }});
 function silence(){if(utterance){utterance.onend=null;utterance.onerror=null;speech?.cancel();utterance=null}$('#lessonListen').textContent='Lyssna'}
 function voices(){voice=localSwedishVoice(speech?.getVoices());$('#lessonListen').hidden=!voice}
 function pause(){playback.pause();silence()}
 function renderRead(){
  $('#lessonCounter').textContent=instructions.length?`Instruktion ${readIndex+1} av ${instructions.length}`:'Instruktion saknas';
  $('#lessonInstruction').textContent=instructions[readIndex]||'Be din behandlare förtydliga hur du ska göra. Använd hjälpen nedan.';
  $('#lessonPrevious').disabled=readIndex===0;$('#lessonNext').textContent=readIndex<instructions.length-1?'Nästa instruktion':'Se rörelsen';
 }
 function renderPart(){customStill=false;const s=segments[part];$('#motionPhase').textContent=s.label;$('#lessonPart').textContent=`Del ${part+1} av ${segments.length}`;$('#lessonNextPart').disabled=part===segments.length-1;$('#lessonPreviousPart').disabled=part===0;playback.select(s);$('[data-motion-frame="0"]').closest('details').open=media.matches;host.querySelectorAll('[data-motion-frame]').forEach(b=>b.setAttribute('aria-pressed','false'))}
 function setMode(next){pause();mode=next;host.dataset.mode=mode;host.querySelectorAll('[data-lesson-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.lessonMode===mode)));$('.lesson-reading').hidden=mode!=='read';$('.lesson-watching').hidden=mode!=='watch';if(mode==='read'){draw(0);renderRead()}else{draw(playback.state().position)}}
 function showFrame(t,newFocus=null){pause();focus=newFocus;setMode('watch');playback.still(t);customStill=true;$('#motionPhase').textContent=t===0?'Startläge':t===1?'Slutläge':'På väg';$('.lesson-stills').open=true;host.querySelectorAll('[data-motion-frame]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.motionFrame)===t)))}
 host.querySelectorAll('[data-lesson-mode]').forEach(b=>b.onclick=()=>setMode(b.dataset.lessonMode));
 $('#lessonPrevious').onclick=()=>{silence();readIndex=Math.max(0,readIndex-1);renderRead();$('#lessonInstruction').focus({preventScroll:true})};
 $('#lessonNext').onclick=()=>{silence();if(readIndex<instructions.length-1){readIndex++;renderRead();$('#lessonInstruction').focus({preventScroll:true})}else{setMode('watch');play.focus({preventScroll:true})}};
 play.onclick=()=>{silence();if(media.matches)return;if(playback.state().playing)playback.pause();else{if(customStill)renderPart();playback.play()}};
 $('#motionSlow').onclick=()=>{const slow=!playback.state().slow;playback.speed(slow);$('#motionSlow').setAttribute('aria-pressed',String(slow))};
 $('#lessonNextPart').onclick=()=>{if(part>=segments.length-1)return;silence();part++;renderPart();if(!media.matches)playback.play()};
 $('#lessonPreviousPart').onclick=()=>{if(part===0)return;pause();part--;renderPart()};
 host.querySelectorAll('[data-motion-frame]').forEach(b=>b.onclick=()=>showFrame(Number(b.dataset.motionFrame),focus));
 $('#lessonListen').onclick=()=>{if(utterance){silence();return}voices();if(!voice||!instructions[readIndex])return;playback.pause();const u=new SpeechSynthesisUtterance(instructions[readIndex]);u.voice=voice;u.lang=voice.lang;u.rate=.85;utterance=u;$('#lessonListen').textContent='Stoppa uppläsning';u.onend=()=>{if(utterance===u){utterance=null;$('#lessonListen').textContent='Lyssna'}};u.onerror=()=>{if(utterance===u){silence();$('#lessonCounter').textContent='Uppläsningen kunde inte starta. Texten finns kvar.'}};speech.speak(u)};
 $('#lessonReady').onclick=()=>{pause();onReady()};
 function visibility(){if(document.hidden)pause()}
 function reduce(){pause();renderPart()}
 document.addEventListener('visibilitychange',visibility);media.addEventListener('change',reduce);speech?.addEventListener('voiceschanged',voices);voices();
 return {pause,showFrame,position:()=>playback.state().position,
  setExercise(x,{motionKey,exerciseSide,contextId}={}){
   const next=String(contextId||'')+':'+x.id+':'+exerciseSide;
   if(identity===next){exercise=x;return}
   pause();identity=next;exercise=x;key=motionKey||x.motionKey||x.figure||x.id;side=exerciseSide||x.side;instructions=lessonInstructions(x);segments=lessonSegments(key);readIndex=0;part=0;focus=null;
   $('#motion').innerHTML=F.svg(key,0,side,x.name);$('#motionSide').textContent=sideLabels[side]||'Sida behöver förtydligas';renderPart();setMode('read');
  },
  destroy(){pause();document.removeEventListener('visibilitychange',visibility);media.removeEventListener('change',reduce);speech?.removeEventListener('voiceschanged',voices)}
 };
}
