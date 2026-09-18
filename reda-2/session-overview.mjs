import {sessionOverview} from './session-overview-model.mjs?v=20260918-1';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// Presentation and explicit user intent only. Existing patient-live owns saving.
export function mountSessionOverview(root,{read,isBusy=()=>false,onOpen,onSelect,onPause,onFinish}){
 const dialog=document.createElement('dialog');dialog.className='exercise-sheet session-overview';dialog.id='sessionOverview';dialog.setAttribute('aria-labelledby','sessionOverviewTitle');root.append(dialog);
 const launch=document.createElement('button');launch.type='button';launch.id='openSessionOverview';launch.className='session-overview-launch';launch.textContent='Passöversikt ▾';launch.setAttribute('aria-haspopup','dialog');
 root.querySelector('.player-context b')?.replaceWith(launch);
 const finish=document.createElement('button');finish.type='button';finish.id='endSessionEarly';finish.className='btn ghost';finish.textContent='Avsluta passet här';root.querySelector('#playerOptions .sheet-content')?.append(finish);
 let context=null,busy=false,confirming=false,opener=null,restoreFocus=true;
 const q=s=>dialog.querySelector(s);
 function current(){const c=read();return c&&context&&c.session.id===context.session.id&&c.planId===context.planId&&c.version===context.version&&(c.session.optionId||null)===(context.session.optionId||null)?c:null}
 function close(restore=true){restoreFocus=restore;if(!busy&&dialog.open)dialog.close()}
 function render(){
  const c=current(),view=sessionOverview(c?.exercises,c?.session);
  dialog.innerHTML=`<div class="sheet-heading"><h2 id="sessionOverviewTitle" tabindex="-1">${confirming?'Avsluta passet här?':'Ditt pass, i din takt'}</h2><button type="button" class="lesson-icon" data-overview-close aria-label="Tillbaka till övningen">✕</button></div><div class="session-overview-body"></div>`;
  const body=q('.session-overview-body');
  if(!view.valid||!view.canFinish){body.innerHTML='<p role="alert">Passöversikten kunde inte visas för det här passet. Gå tillbaka till din plan.</p>';q('[data-overview-close]').onclick=()=>close();return}
  body.innerHTML=`<p class="session-overview-context">Plan v${esc(c.version)}${c.optionLabel?' · '+esc(c.optionLabel):''}</p><div class="session-overview-total"><strong>${view.done}<span> av ${view.total} omgångar registrerade</span></strong><progress max="${view.total}" value="${view.done}" aria-label="Registrerade omgångar"></progress><p>${view.completed} av ${view.items.length} övningar helt registrerade${view.skipped?' · '+view.skipped+' överhoppade':''}</p></div>`;
  if(confirming){
   body.insertAdjacentHTML('beforeend',`<div class="session-overview-confirm"><p>${view.allCompleted?'Alla omgångar är registrerade. Dina markeringar sparas med passet.':view.done===0?'Ingen omgång är registrerad. Passet avslutas utan att någon träning markeras som genomförd.':'Dina '+view.done+' registrerade omgångar sparas. Återstående omgångar markeras inte som genomförda.'}</p><p>Din ordination ändras inte. När passet har sparats kan du berätta hur det fungerade.</p><p>Vill du fortsätta med samma pass senare? Välj att pausa i stället.</p></div><div class="session-overview-actions"><button type="button" class="btn primary" data-overview-save>Spara och avsluta</button><button type="button" class="btn ghost" data-overview-pause>Pausa och fortsätt senare</button><button type="button" class="btn ghost" data-overview-back>Tillbaka till passöversikten</button></div><p role="status" data-overview-status></p>`);
   q('[data-overview-back]').onclick=()=>{confirming=false;render();q('#sessionOverviewTitle').focus()};
   q('[data-overview-save]').onclick=async()=>{
    if(busy||isBusy())return;const latest=current();if(!sessionOverview(latest?.exercises,latest?.session).canFinish){render();return}
    busy=true;dialog.setAttribute('aria-busy','true');dialog.querySelectorAll('button').forEach(b=>b.disabled=true);q('[data-overview-status]').textContent='Sparar passet…';
    let failed=false;
    try{await onFinish()}catch{failed=true;if(dialog.open){busy=false;render();q('[data-overview-status]').textContent='Passet kunde inte avslutas. Gå tillbaka och kontrollera synkstatus.'}}
    finally{busy=false;dialog.removeAttribute('aria-busy');if(!failed&&dialog.open)dialog.close()}
   };
  }else{
   body.insertAdjacentHTML('beforeend',`<p>Öppna en övning för att se instruktionen eller fortsätta där du är. Översikten ändrar inga markeringar.</p><ol class="session-overview-list">${view.items.map(x=>`<li data-state="${x.status}"><button type="button" data-overview-exercise="${x.index}"${x.index===c.index?' aria-current="step"':''}><span class="session-overview-number" aria-hidden="true">${x.status==='completed'?'✓':x.index+1}</span><span><strong>${esc(x.name)}</strong><span class="session-overview-dose">${esc(x.dose)}${x.side?' · '+esc(x.side):''}</span><span class="session-overview-label">${esc(x.label)} · ${x.done} av ${x.total}</span>${x.sides?'<span class="session-overview-sides">'+esc(x.sides)+'</span>':''}${x.feedback?'<span class="session-overview-feedback">Ditt svar: '+esc(x.feedback)+'</span>':''}</span><span aria-hidden="true">→</span></button></li>`).join('')}</ol><div class="session-overview-actions"><button type="button" class="btn primary" data-overview-close>Fortsätt passet</button><button type="button" class="btn ghost" data-overview-pause>Pausa och fortsätt senare</button><button type="button" class="btn ghost" data-overview-end>Avsluta passet här</button></div><p class="session-overview-note">Registreringarna är ditt underlag till uppföljningen, inte en bedömning av din återhämtning.</p>`);
   dialog.querySelectorAll('[data-overview-exercise]').forEach(b=>b.onclick=()=>{if(busy||isBusy()||!current())return;const index=Number(b.dataset.overviewExercise);close(false);onSelect(index)});
   q('[data-overview-end]').onclick=()=>{confirming=true;render();q('#sessionOverviewTitle').focus()};
  }
  dialog.querySelectorAll('[data-overview-close]').forEach(b=>b.onclick=()=>close());
  q('[data-overview-pause]')?.addEventListener('click',()=>{if(busy||isBusy())return;close(false);onPause()});
 }
 function open(confirm=false,source=launch){
  if(busy||isBusy())return;const c=read();if(!sessionOverview(c?.exercises,c?.session).canFinish)return;
  onOpen?.();restoreFocus=true;context={...c,session:{...c.session}};confirming=confirm;opener=source;render();if(!dialog.open)dialog.showModal();q('#sessionOverviewTitle').focus();
 }
 launch.onclick=()=>open();finish.onclick=()=>open(true,finish);
 dialog.addEventListener('cancel',e=>{if(busy)e.preventDefault()});
 dialog.addEventListener('close',()=>{context=null;if(restoreFocus){const target=opener?.isConnected&&opener.getClientRects().length?opener:launch;if(target.getClientRects().length)target.focus({preventScroll:true})}});
 return {open,close,isBusy:()=>busy,destroy(){dialog.remove();launch.remove();finish.remove()}};
}
