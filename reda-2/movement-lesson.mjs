import {lessonInstructions,lessonSegments,wholeLessonSequence,createLessonPlayback,localSwedishVoice} from './movement-lesson-model.mjs?v=2';
import {sideLabels} from './exercise-help-model.mjs?v=20260912-coach1';

export function createMovementLesson(host,{onReady=()=>{}}={}){
 const F=window.RedaFigures,media=matchMedia('(prefers-reduced-motion: reduce)'),speech=window.speechSynthesis;
 let exercise=null,key='',side='',identity='',instructions=[],segments=[],readIndex=0,part=0,mode='overview',view='whole',focus=null,voice=null,utterance=null,customStill=false;
 const remembered=new Map();
 host.classList.add('movement-lesson');
 host.innerHTML=`<div class="lesson-entry"><span id="motionSide" class="lesson-side"></span><button type="button" id="lessonReady" class="lesson-ready">Börja träna <span aria-hidden="true">→</span></button><div class="lesson-choices"><button type="button" id="lessonWhole"><b>Visa hela rörelsen</b><small>Se en gång, sedan stopp</small></button><button type="button" id="lessonGuided"><b>Steg för steg</b><small>Läs eller lyssna i din takt</small></button></div><p id="lessonPractice" hidden>Visning och hjälp finns kvar om du behöver dem.</p></div><div class="lesson-tabs" role="group" aria-label="Välj hur du vill gå igenom övningen"><button type="button" data-lesson-mode="read" aria-pressed="true">Läs eller lyssna</button><button type="button" data-lesson-mode="watch" aria-pressed="false">Visa delar</button></div>
 <div id="motionStudio" class="motion-studio" tabindex="-1" aria-label="Övningens demonstration"><div class="motion-caption"><span>REDA · ÖVNINGSGUIDE</span></div><div id="motion" class="motion"></div>
 <div class="lesson-reading"><p class="lesson-counter" id="lessonCounter"></p><p class="lesson-instruction" id="lessonInstruction" tabindex="-1"></p><div class="lesson-read-actions"><button type="button" id="lessonPrevious">Föregående</button><button type="button" id="lessonListen" hidden>Lyssna</button><button type="button" id="lessonNext">Nästa instruktion</button></div></div>
 <div class="lesson-watching" hidden><div class="motion-guide"><div><b id="motionPhase">Startläge</b><span id="lessonStatus" role="status">Starta när du vill. Visningen stannar efter varje del.</span></div><span id="lessonPart" class="lesson-counter"></span></div><div class="ei-motion-controls" role="group" aria-label="Styr rörelsevisningen"><button id="motionPlay" type="button">Visa den här delen</button><button id="lessonNextPart" type="button">Visa nästa del</button></div><div class="lesson-secondary"><button id="motionSlow" type="button" aria-pressed="false">Extra långsamt</button><button id="lessonPreviousPart" type="button">Föregående del</button></div>
 <details class="lesson-stills"><summary>Välj en stillbild</summary><div class="lesson-frame-buttons"><button type="button" data-motion-frame="0" data-frame="0">Startläge</button><button type="button" data-motion-frame="0.5" data-frame="0.5">På väg</button><button type="button" data-motion-frame="1" data-frame="1">Slutläge</button></div></details></div></div>
 <p class="lesson-note">Visningens hastighet är till för att lära. Träna i tempot i din plan.</p><button type="button" id="lessonContinue" class="lesson-ready">Till träningen <span aria-hidden="true">→</span></button>`;
 const $=s=>host.querySelector(s),play=$('#motionPlay'),status=$('#lessonStatus');
 function draw(t){if(!exercise)return;const el=$('#motion');if(!F.drawFrame?.(el,key,t,focus))el.innerHTML=F.svg(key,t,side,exercise.name,{focus});el.dataset.position=String(t)}
 const playback=createLessonPlayback({draw,change:renderPlayback});
 function renderPlayback(s){
  const whole=view==='whole';host.dataset.playing=String(s.playing);play.disabled=media.matches;
  play.textContent=media.matches?'Använd stillbilderna':s.playing?'Pausa rörelsen':s.complete?(whole?'Visa hela igen':'Visa delen igen'):s.progress>0?'Fortsätt visningen':whole?'Visa hela rörelsen':'Visa den här delen';
  status.textContent=media.matches?'Stilla visning är på. Välj en bild nedan.':s.playing?'Du kan pausa eller gå till träningen när du vill.':s.complete?(whole||part===segments.length-1?'Visningen är klar. Se igen, få mer stöd eller börja träna.':'Den här delen är klar. Nästa del väntar på dig.'):s.progress>0?'Pausad. Fortsätt när du vill.':whole?'En hel visning. Sedan stannar bilden.':'Starta när du vill. Visningen stannar efter varje del.';
 }
 function silence(){if(utterance){utterance.onend=null;utterance.onerror=null;speech?.cancel();utterance=null}$('#lessonListen').textContent='Lyssna'}
 function voices(){voice=localSwedishVoice(speech?.getVoices());$('#lessonListen').hidden=!voice}
 function pause(){playback.pause();silence()}
 function renderRead(){
  $('#lessonCounter').textContent=instructions.length?`Instruktion ${readIndex+1} av ${instructions.length}`:'Instruktion saknas';
  $('#lessonInstruction').textContent=instructions[readIndex]||'Be din behandlare förtydliga hur du ska göra. Använd hjälpen nedan.';
  $('#lessonPrevious').disabled=readIndex===0;$('#lessonNext').textContent=readIndex<instructions.length-1?'Nästa instruktion':'Se rörelsen';
 }
 function renderPart(){customStill=false;const s=segments[part];$('#motionPhase').textContent=s.label;$('#lessonPart').textContent=`Del ${part+1} av ${segments.length}`;$('#lessonNextPart').disabled=part===segments.length-1;$('#lessonPreviousPart').disabled=part===0;playback.select(s);$('[data-motion-frame="0"]').closest('details').open=media.matches;host.querySelectorAll('[data-motion-frame]').forEach(b=>b.setAttribute('aria-pressed','false'))}
 function remember(){if(identity)remembered.set(identity,{mode,view,readIndex,part,slow:playback.state().slow})}
 function renderMode(){
  const expanded=mode==='read'||mode==='watch';host.dataset.mode=mode;host.dataset.view=view;
  $('#motionStudio').hidden=!expanded;$('.lesson-tabs').hidden=!expanded||view==='whole';$('.lesson-note').hidden=!expanded;$('#lessonContinue').hidden=!expanded;$('#lessonReady').hidden=mode==='practice';$('#lessonPractice').hidden=mode!=='practice';
  host.querySelectorAll('[data-lesson-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.lessonMode===mode)));
  $('#lessonWhole').setAttribute('aria-pressed',String(mode==='watch'&&view==='whole'));$('#lessonGuided').setAttribute('aria-pressed',String(expanded&&view==='parts'));
  $('.lesson-reading').hidden=mode!=='read';$('.lesson-watching').hidden=mode!=='watch';
  $('#lessonNextPart').hidden=view==='whole';$('#lessonPreviousPart').hidden=view==='whole';$('#lessonPart').hidden=view==='whole';
  if(mode==='read'){draw(0);renderRead()}else if(mode==='watch')draw(playback.state().position);
  renderPlayback(playback.state());
 }
 function setMode(next){pause();mode=next;if(next==='read')view='parts';renderMode();remember()}
 function selectView(next,{autoplay=false}={}){
  pause();focus=null;view=next;customStill=false;
  if(view==='whole'){mode='watch';$('#motionPhase').textContent='Hela rörelsen';playback.select(wholeLessonSequence(key));$('.lesson-stills').open=media.matches}
  else{mode='read';renderPart()}
  renderMode();remember();if(autoplay&&!media.matches)playback.play();
 }
 function showFrame(t,newFocus=null){pause();focus=newFocus;view='parts';renderPart();setMode('watch');playback.still(t);customStill=true;$('#motionPhase').textContent=t===0?'Startläge':t===1?'Slutläge':'På väg';$('.lesson-stills').open=true;host.querySelectorAll('[data-motion-frame]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.motionFrame)===t)))}
 host.querySelectorAll('[data-lesson-mode]').forEach(b=>b.onclick=()=>{view='parts';setMode(b.dataset.lessonMode)});
 $('#lessonWhole').onclick=()=>{selectView('whole',{autoplay:true});play.focus({preventScroll:true})};
 $('#lessonGuided').onclick=()=>{selectView('parts');$('#lessonInstruction').focus({preventScroll:true})};
 $('#lessonPrevious').onclick=()=>{silence();readIndex=Math.max(0,readIndex-1);renderRead();remember();$('#lessonInstruction').focus({preventScroll:true})};
 $('#lessonNext').onclick=()=>{silence();if(readIndex<instructions.length-1){readIndex++;renderRead();remember();$('#lessonInstruction').focus({preventScroll:true})}else{setMode('watch');play.focus({preventScroll:true})}};
 play.onclick=()=>{silence();if(media.matches)return;if(playback.state().playing)playback.pause();else{if(customStill){view='parts';renderPart()}playback.play()}};
 $('#motionSlow').onclick=()=>{const slow=!playback.state().slow;playback.speed(slow);$('#motionSlow').setAttribute('aria-pressed',String(slow));remember()};
 $('#lessonNextPart').onclick=()=>{if(part>=segments.length-1)return;silence();part++;renderPart();remember();if(!media.matches)playback.play()};
 $('#lessonPreviousPart').onclick=()=>{if(part===0)return;pause();part--;renderPart();remember()};
 host.querySelectorAll('[data-motion-frame]').forEach(b=>b.onclick=()=>showFrame(Number(b.dataset.motionFrame),focus));
 $('#lessonListen').onclick=()=>{if(utterance){silence();return}voices();if(!voice||!instructions[readIndex])return;playback.pause();const u=new SpeechSynthesisUtterance(instructions[readIndex]);u.voice=voice;u.lang=voice.lang;u.rate=.85;utterance=u;$('#lessonListen').textContent='Stoppa uppläsning';u.onend=()=>{if(utterance===u){utterance=null;$('#lessonListen').textContent='Lyssna'}};u.onerror=()=>{if(utterance===u){silence();$('#lessonCounter').textContent='Uppläsningen kunde inte starta. Texten finns kvar.'}};speech.speak(u)};
 function ready(){setMode('practice');onReady()}
 $('#lessonReady').onclick=ready;$('#lessonContinue').onclick=ready;
 function visibility(){if(document.hidden)pause()}
 function reduce(){pause();renderPlayback(playback.state());$('.lesson-stills').open=media.matches}
 document.addEventListener('visibilitychange',visibility);media.addEventListener('change',reduce);speech?.addEventListener('voiceschanged',voices);voices();
 return {pause,showFrame,position:()=>playback.state().position,
  setExercise(x,{motionKey,exerciseSide,contextId}={}){
   const nextKey=motionKey||x.motionKey||x.figure||x.id,nextSide=exerciseSide||x.side;
   const next=String(contextId||'')+':'+x.id+':'+nextKey;
   if(identity===next&&side===nextSide){exercise=x;return}
   pause();remember();identity=next;exercise=x;key=nextKey;side=nextSide;instructions=lessonInstructions(x);segments=lessonSegments(key);focus=null;
   const previous=remembered.get(identity);readIndex=Math.min(previous?.readIndex||0,Math.max(0,instructions.length-1));part=Math.min(previous?.part||0,segments.length-1);view=previous?.view||'whole';mode=previous?.mode||'overview';
   $('#motion').innerHTML=F.svg(key,0,side,x.name);$('#motionSide').textContent=sideLabels[side]||'Sida behöver förtydligas';
   if(view==='whole'){customStill=false;$('#motionPhase').textContent='Hela rörelsen';playback.select(wholeLessonSequence(key))}else renderPart();
   playback.speed(previous?.slow||false);$('#motionSlow').setAttribute('aria-pressed',String(playback.state().slow));$('.lesson-stills').open=media.matches;renderMode();
  },
  destroy(){pause();document.removeEventListener('visibilitychange',visibility);media.removeEventListener('change',reduce);speech?.removeEventListener('voiceschanged',voices)}
 };
}
