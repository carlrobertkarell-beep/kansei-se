const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const roleLabels={owner:'Ägare',admin:'Administration',finance:'Ekonomi',member:'Teammedlem'};
const describe=m=>`${roleLabels[m.role]} · ${m.clinical_access?'behandlarbehörighet':'utan behandlarbehörighet'} · ${m.status==='active'?'aktiv':'återkallad'}`;
export function mountWorkspaceTeam(host,{api,workspace,onChanged,onBusy}){
 let destroyed=false,ticket=0,busy=false;
 const valid=n=>!destroyed&&n===ticket;
 async function load(message=''){
  const n=++ticket;
  host.innerHTML='<p role="status">Hämtar teamet…</p>';
  try{
   const data=await api.workspaceTeam();if(!valid(n))return;
   host.innerHTML='<details class="team-panel"><summary><span>Team och behörigheter</span><small>'+data.members.filter(m=>m.status==='active').length+' aktiva medlemmar</small></summary><p>En organisationsroll ger tillgång till verksamheten. Patientuppgifter kräver dessutom behandlarbehörighet och en egen patienttilldelning.</p><p class="workspace-message" role="status">'+esc(message)+'</p><div class="team-members"></div><p class="micro">Nya konton och anslutning av fler kliniker förbereds separat. Ingen inbjudan skickas från den här vyn.</p></details>';
   const list=host.querySelector('.team-members');
   for(const member of data.members){
    const row=document.createElement('div');row.className='team-member';
    row.innerHTML='<div><strong>'+esc(member.display_name)+(member.is_self?' · du':'')+'</strong><p>'+esc(describe(member))+'</p></div>';
    if(data.can_manage){
     const edit=document.createElement('details');edit.innerHTML='<summary>Ändra behörighet</summary><form><div class="team-fields"><label>Organisationsroll<select name="role">'+Object.entries(roleLabels).map(([v,l])=>'<option value="'+v+'"'+(member.role===v?' selected':'')+'>'+l+'</option>').join('')+'</select></label><label>Status<select name="status"><option value="active"'+(member.status==='active'?' selected':'')+'>Aktiv</option><option value="revoked"'+(member.status==='revoked'?' selected':'')+'>Återkallad</option></select></label></div><label class="team-check"><input type="checkbox" name="clinical"'+(member.clinical_access?' checked':'')+(!member.clinical_eligible||workspace.kind!=='clinic'?' disabled':'')+'> Behandlarbehörighet för tilldelade patienter</label>'+(!member.clinical_eligible?'<p class="micro">Kontot är inte godkänt som behandlare.</p>':'')+'<button type="submit" class="btn ghost">Granska ändring</button><div class="team-confirm" aria-live="polite"></div></form>';
     const form=edit.querySelector('form'),confirm=form.querySelector('.team-confirm');
     form.addEventListener('change',()=>confirm.replaceChildren());
     form.onsubmit=e=>{
      e.preventDefault();if(busy||!valid(n))return;
      const change={role:form.elements.role.value,status:form.elements.status.value,clinical_access:!form.elements.clinical.disabled&&form.elements.clinical.checked};
      confirm.innerHTML='<p><b>'+esc(member.display_name)+'</b><br>Nu: '+esc(describe(member))+'<br>Efter ändringen: '+esc(describe(change))+'</p><p>Ändringen gäller direkt i '+esc(workspace.name)+'.</p><button type="button" class="btn primary">Spara behörighet</button>';
      confirm.querySelector('button').onclick=async()=>{
       if(busy||!valid(n))return;busy=true;onBusy(true);host.querySelectorAll('button,input,select').forEach(e=>e.disabled=true);
       try{await api.updateMembership(member,change);if(valid(n))await onChanged('Behörigheten är sparad.');}
       catch(e){if(valid(n)){await load(e.message);host.querySelector('details').open=true}}
       finally{busy=false;onBusy(false)}
      };
     };row.append(edit);
    }list.append(row);
   }
   if(data.can_manage&&data.events.length){
    const events=document.createElement('details');events.className='team-audit';
    events.innerHTML='<summary>Senaste behörighetsändringarna</summary><ul>'+data.events.map(e=>'<li><time>'+esc(new Date(e.created_at).toLocaleString('sv-SE'))+'</time><p>'+esc(data.members.find(m=>m.user_id===e.member_id)?.display_name||'Tidigare medlem')+': '+esc(describe(e.before_state))+' → '+esc(describe(e.after_state))+'</p></li>').join('')+'</ul>';host.querySelector('.team-panel').append(events);
   }
  }catch(e){if(valid(n))host.innerHTML='<p role="alert">Teamet kunde inte hämtas. '+esc(e.message)+'</p>'}
 }
 load();return {destroy(){destroyed=true;++ticket;host.replaceChildren()},refresh:load};
}
