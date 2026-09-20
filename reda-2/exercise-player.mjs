// Presentation only. Session state and saving remain owned by patient-live.
export function mountExercisePlayer(root,{lesson}={}){
 const $=id=>root.querySelector('#'+id);let until=0,timer=null;
 function open(id){lesson.pause();if(id==='playerHelp'){const d=$('exerciseCoach').querySelector('details');if(d)d.open=true}$(id).showModal()}
 if($('playerStep')){const slow=$('motionSlow'),stills=$('movementLesson').querySelector('.lesson-stills');stills.before(slow);const note=document.createElement('p');note.className='player-demo-note';note.textContent='Demonstration · räknar inga repetitioner';$('movementLesson').querySelector('.lesson-transport').after(note)}
 $('playerShowClearly')?.addEventListener('click',()=>{closePanels();lesson.openDetails()});
 root.querySelectorAll('[data-player-concern]').forEach(b=>b.onclick=()=>{const panel=$('playerConcern');panel.hidden=false;$('playerConcernTitle').textContent=b.dataset.playerConcern==='pain'?'Det gör ont':'Övningen känns för svår';$('playerConcernTitle').focus()});
 $('playerPauseForHelp')?.addEventListener('click',()=>{$('closePlayer').click()});
 function closePanels(){for(const d of root.querySelectorAll('dialog[open]'))d.close()}
 $('openExerciseHelp').onclick=()=>open('playerHelp');$('openPlayerOptions').onclick=()=>open('playerOptions');
 root.querySelectorAll('[data-close-sheet]').forEach(b=>b.onclick=()=>$(b.dataset.closeSheet).close());
 const rest=document.createElement('div');rest.className='player-rest';rest.hidden=true;rest.innerHTML='<span>Vila enligt din plan</span><span id="restNext"></span><b id="restTime" aria-hidden="true"></b><p id="restStatus" role="status">Nästa omgång väntar på dig.</p>';
 $('motionStudio').append(rest);
 function tick(){const seconds=Math.max(0,Math.ceil((until-Date.now())/1000));$('restTime').textContent=Math.floor(seconds/60)+':'+String(seconds%60).padStart(2,'0');if(!seconds){clearInterval(timer);timer=null;$('restStatus').textContent='Vilotiden är slut. Fortsätt när du är redo.'}}
 function endRest(){clearInterval(timer);timer=null;until=0;rest.hidden=true;root.dataset.resting='false'}
 $('resumeExercise').onclick=()=>{endRest();$('rounds').querySelector('button:not(:disabled)')?.focus()};
 const source=document.getElementById('sync'),observer=source?new MutationObserver(()=>{$('playerSaveStatus').textContent=source.textContent}):null;
 if(source){$('playerSaveStatus').textContent=source.textContent;observer.observe(source,{childList:true,subtree:true,characterData:true})}
 return {closePanels,endRest,startRest(seconds){if(!Number.isFinite(seconds)||seconds<=0)return;lesson.pause();endRest();until=Date.now()+seconds*1000;rest.hidden=false;root.dataset.resting='true';const side=root.querySelector('#motionSide')?.textContent;$('restNext').textContent=side?'Nästa omgång: '+side.toLowerCase():'';$('resumeExercise').textContent=side?'Fortsätt · '+side.toLowerCase():'Fortsätt träna';$('restStatus').textContent='Nästa omgång väntar på dig.';tick();$('resumeExercise').focus({preventScroll:true});timer=setInterval(tick,250)},destroy(){endRest();closePanels();observer?.disconnect()}};
}
