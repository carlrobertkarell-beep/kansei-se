// Progressive enhancement for the clinician registry. Read-only: it reuses existing dashboard actions and never writes clinical data.
const host=document.getElementById('decisionDashboard');
if(host){
 let scheduled=false,lastSignature='';
 const label=row=>row.querySelector('.dash-row-action')?.textContent?.trim()||'Öppna patient';
 const name=row=>row.querySelector('.dash-patient-link')?.textContent?.trim()||'Patient';
 function enhance(){
  scheduled=false;
  const dash=host.querySelector('.clinic-dashboard'),rows=[...host.querySelectorAll('.dash-row')],metrics=host.querySelector('.dash-metrics');
  if(!dash||!metrics)return;
  let focus=host.querySelector('.clinician-focus');
  if(!focus){focus=document.createElement('section');focus.className='clinician-focus';focus.setAttribute('aria-label','Arbetsfokus');metrics.after(focus)}
  const attention=rows.filter(r=>r.classList.contains('needs-attention'));
  const first=attention[0]||rows[0];
  const signature=[rows.length,attention.length,name(first||{}),label(first||{})].join('|');
  if(signature===lastSignature)return;lastSignature=signature;
  if(!first){focus.innerHTML='<div><p class="eyebrow">Arbetsfokus</p><strong>Inget i den här listan kräver åtgärd.</strong><span>Byt arbetslista eller sök efter en patient.</span></div>';return}
  focus.innerHTML='<div class="focus-copy"><p class="eyebrow">Arbetsfokus</p><strong>'+escapeHTML(attention.length?attention.length+' patient'+(attention.length===1?'':'er')+' på sidan behöver dig':'Nästa patient i listan')+'</strong><span>'+escapeHTML(name(first))+' · '+escapeHTML(label(first))+'</span></div><button type="button" class="focus-next">Öppna '+escapeHTML(name(first))+' →</button>';
  focus.querySelector('.focus-next').onclick=()=>first.querySelector('.dash-row-action,.dash-patient-link')?.click();
  rows.forEach((row,i)=>{row.dataset.focusRank=String(i+1);const next=row.querySelector('.dash-next');if(next&&!next.querySelector('.dash-open-label')){const hint=document.createElement('span');hint.className='dash-open-label';hint.textContent=row.classList.contains('needs-attention')?'Att hantera':'Nästa steg';next.prepend(hint)}});
 }
 function escapeHTML(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
 const observer=new MutationObserver(()=>{if(!scheduled){scheduled=true;queueMicrotask(enhance)}});
 observer.observe(host,{childList:true,subtree:true});enhance();
}
