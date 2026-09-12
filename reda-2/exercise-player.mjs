// Presentation only. Session state and saving remain owned by patient-live.
export function mountExercisePlayer(root,{lesson}={}){
 const $=id=>root.querySelector('#'+id);let until=0,timer=null;
 function open(id){lesson.pause();if(id==='playerHelp'){const d=$('exerciseCoach').querySelector('details');if(d)d.open=true}$(id).showModal()}
 function closePanels(){for(const d of root.querySelectorAll('dialog[open]'))d.close()}
 $('openExerciseHelp').onclick=()=>open('playerHelp');$('openPlayerOptions').onclick=()=>open('playerOptions');
 root.querySelectorAll('[data-close-sheet]').forEach(b=>b.onclick=()=>$(b.dataset.closeSheet).close());
 const rest=document.createElement('div');rest.className='player-rest';rest.hidden=true;rest.innerHTML='<span>Vila enligt din plan</span><b id="restTime" aria-hidden="true"></b><p id="restStatus" role="status">Nästa omgång väntar på dig.</p>';
 $('motionStudio').append(rest);
 function tick(){const seconds=Math.max(0,Math.ceil((until-Date.now())/1000));$('restTime').textContent=Math.floor(seconds/60)+':'+String(seconds%60).padStart(2,'0');if(!seconds){clearInterval(timer);timer=null;$('restStatus').textContent='Vilotiden är slut. Fortsätt när du är redo.'}}
 function endRest(){clearInterval(timer);timer=null;until=0;rest.hidden=true;root.dataset.resting='false'}
 $('resumeExercise').onclick=()=>{endRest();$('rounds').querySelector('button:not(:disabled)')?.focus()};
 const source=document.getElementById('sync'),observer=source?new MutationObserver(()=>{$('playerSaveStatus').textContent=source.textContent}):null;
 if(source){$('playerSaveStatus').textContent=source.textContent;observer.observe(source,{childList:true,subtree:true,characterData:true})}
 return {closePanels,endRest,startRest(seconds){if(!Number.isFinite(seconds)||seconds<=0)return;lesson.pause();endRest();until=Date.now()+seconds*1000;rest.hidden=false;root.dataset.resting='true';$('restStatus').textContent='Nästa omgång väntar på dig.';tick();timer=setInterval(tick,250)},destroy(){endRest();closePanels();observer?.disconnect()}};
}
