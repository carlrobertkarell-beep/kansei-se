const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const phaseLabels={needs_review:'Behöver din bedömning',awaiting_patient:'Inväntar patientsvar',scheduled:'Uppföljning planerad',needs_resolution:'Återstår att bedöma',handled:'Hanterat',none:'Ingen hjälpuppgift'};
export function clinicWorkflow(s){
 if(!s||s.phase==='none')return '';
 const detail={needs_review:s.new_reply?'Ett nytt patientsvar behöver bedömas.':'Sparad återkoppling behöver bedömas. Reda lägger nya signaler i din arbetslista automatiskt.',awaiting_patient:'En fråga är levererad i Reda. Patienten kan svara. Ärendet är fortfarande öppet.',scheduled:'Uppföljningen ligger i din arbetslista. Ett planerat datum innebär inte att kontakten har skett.',needs_resolution:'Kontakt eller uppföljning är registrerad, men signaler eller dialog återstår att bedöma. Avsluta först när behovet är hanterat.',handled:'Tidigare signaler är markerade som hanterade. Nya signaler öppnar arbetsflödet igen.'}[s.phase];
 return `<section class="support-workflow" data-support-phase="${esc(s.phase)}"><p class="eyebrow">Hjälp och uppföljning</p><h4>${esc(phaseLabels[s.phase]||'Kontrollera status')}</h4><p>${esc(detail||'Uppdatera underlaget för att kontrollera nästa steg.')}</p>${s.due_date?`<p><strong>${s.overdue?'Försenad uppföljning':'I din arbetslista'} · ${esc(s.due_date)}</strong></p>`:''}<small>${Number(s.pending_signals||0)} signaler kvar att bedöma · ${s.responsibility==='patient'?'Nästa svar: patienten':'Nästa åtgärd: du'}</small></section>`;
}
export function patientSupportText(s){
 return ({needs_review:{title:'Ditt svar finns hos kliniken',detail:'Kliniken behöver bedöma din återkoppling. Här visas när det finns en fråga att besvara eller när ärendet har hanterats.'},awaiting_patient:{title:'Din behandlare har en fråga',detail:'Öppna meddelandena och svara, så får behandlaren det underlag som behövs för att hjälpa dig vidare.'},scheduled:{title:'Kliniken har en uppföljning att göra',detail:'En uppgift finns hos kliniken. Det innebär inte att ett besök är bokat. Bekräftad tid får du separat.'},needs_resolution:{title:'Din återkoppling följs fortfarande upp',detail:'Kontakt eller uppföljning har registrerats. Kliniken behöver fortfarande avsluta bedömningen av din återkoppling.'},handled:{title:'Din återkoppling är markerad som hanterad',detail:'Det betyder att behandlaren har avslutat ärendet, inte att dina besvär måste vara borta. Följ din aktuella plan och berätta om du behöver mer hjälp.'}})[s?.phase]||null;
}
export function mountPatientSupport(host,{api,patientId,onMessages}){
 if(!host||!api.patientSupport)return null;
 let alive=true,ticket=0;
 host.innerHTML='<section class="card support-workflow"><div data-support-content></div><p role="status" data-support-status></p><button type="button" class="btn ghost" data-support-refresh>Uppdatera hjälpstatus</button></section>';
 const q=s=>host.querySelector(s);
 async function refresh(){const n=++ticket;q('[data-support-status]').textContent='Hämtar hjälpstatus…';
  try{const s=await api.patientSupport(patientId);if(!alive||n!==ticket||!host.isConnected)return;const t=patientSupportText(s);host.hidden=!t;q('[data-support-status]').textContent='';q('[data-support-content]').innerHTML=t?'<p class="eyebrow">Din hjälp och återkoppling</p><h3>'+esc(t.title)+'</h3><p>'+esc(t.detail)+'</p>'+(s.reply_to?'<button type="button" class="btn primary" data-support-reply>Öppna frågan och svara</button>':'')+'<p class="sub">Meddelanden bevakas inte i realtid. Använd klinikens vanliga kontaktväg när du behöver snabb kontakt.</p>':'';q('[data-support-reply]')?.addEventListener('click',()=>onMessages?.())}
  catch{if(alive&&n===ticket){host.hidden=false;q('[data-support-content]').replaceChildren();q('[data-support-status]').textContent='Hjälpstatusen kunde inte hämtas. Dina sparade svar är kvar. Försök med Uppdatera hjälpstatus.'}}
 }
 q('[data-support-refresh]').onclick=refresh;refresh();return {refresh,destroy(){alive=false;++ticket;host.replaceChildren()}};
}
