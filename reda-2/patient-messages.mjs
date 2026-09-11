const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function mountPatientMessages(host,{api}){
 if(!host||!api.patientMessages)return null;
 let alive=true,busy=false,ticket=0,data=null,pending=null;
 const valid=()=>alive&&host.isConnected,q=s=>host.querySelector(s);
 host.innerHTML='<section class="card reda-messages"><div class="reda-message-heading"><h2>Meddelanden från din behandlare</h2><button class="btn ghost" data-refresh-messages>Uppdatera</button></div><p class="reda-message-status" role="status" aria-live="polite"></p><div class="reda-message-list"></div><form class="reda-reply" hidden><label>Ditt svar<textarea maxlength="1000" rows="3" required placeholder="Skriv ditt svar här."></textarea></label><button type="submit" class="btn primary">Skicka svar till behandlaren</button></form><p class="sub">Här får du svar i Reda. Meddelanden bevakas inte i realtid. Använd klinikens vanliga kontaktväg när du behöver snabb kontakt.</p></section>';
 const status=text=>{if(valid())q('.reda-message-status').textContent=text};
 function setBusy(value){busy=value;host.querySelectorAll('button,textarea').forEach(el=>el.disabled=value)}
 async function refresh(message=''){
  if(busy)return;const request=++ticket;status('Hämtar meddelanden…');
  try{const result=await api.patientMessages();if(!valid()||request!==ticket)return;data=result;
   q('.reda-message-list').innerHTML=data.messages.length?data.messages.map(m=>'<div class="dash-bubble '+(m.kind==='patient'?'from-patient':'')+'"><b>'+esc(m.kind==='patient'?'Ditt svar':'Din behandlare')+'</b><p>'+esc(m.body)+'</p><small>'+esc(new Date(m.created_at).toLocaleString('sv-SE'))+'</small></div>').join(''):'<p>Du har inga meddelanden ännu.</p>';
   q('.reda-reply').hidden=!data.reply_to;status(message||(data.reply_to?'Du kan svara på behandlarens senaste meddelande.':data.messages.length?'Senaste 20 meddelandena visas.':''));
  }catch(e){if(valid()&&request===ticket){data=null;q('.reda-message-list').replaceChildren();q('.reda-reply').hidden=true;status(message?message+' Uppdatera för att läsa dialogen.':'Meddelandena kunde inte hämtas. Försök med Uppdatera.')}}
 }
 q('[data-refresh-messages]').onclick=()=>refresh();
 q('form').onsubmit=async e=>{
  e.preventDefault();if(busy||!data?.reply_to)return;const body=q('textarea').value.trim(),messageId=data.reply_to;
  if(body.length<5){status('Skriv ett svar på minst fem tecken.');return}
  const signature=JSON.stringify([messageId,body]);if(pending?.signature!==signature)pending={signature,id:crypto.randomUUID()};const requestId=pending.id;
  setBusy(true);status('Skickar ditt svar…');
  try{await api.patientReply(messageId,requestId,body);if(!valid())return;pending=null;q('textarea').value='';setBusy(false);await refresh('Ditt svar är levererat i Reda till din behandlare.');}
  catch(e){if(valid()){status(e.message||'Svaret kunde inte skickas. Texten är kvar; försök igen.');if(e.code==='40001'){data=null;q('.reda-reply').hidden=true;pending=null}}}
  finally{if(valid())setBusy(false)}
 };
 refresh();return {refresh,isBusy:()=>busy,destroy(){alive=false;++ticket;host.replaceChildren()}};
}
