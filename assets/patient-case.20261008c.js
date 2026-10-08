(()=>{
document.querySelectorAll('[data-patient-viewer]').forEach(root=>{
 const modes=[...root.querySelectorAll('[data-patient-mode]')],select=root.querySelector('[data-patient-select]'),tabs=[...root.querySelectorAll('[data-patient-panel]')],panels=[...root.querySelectorAll('.reader-panel')],paired=root.hasAttribute('data-paired-anatomy'),choice=root.querySelector('.patient-choice');
 let activeId=select?.value||tabs[0]?.dataset.patientPanel||panels[0]?.id;
 function mode(value){
  modes.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.patientMode===value)));
  if(paired)root.dataset.anatomy=String(value==='anatomy');else root.dataset.explained=String(value==='explained');
 }
 function show(id=activeId){
  activeId=id;
  panels.forEach(p=>{p.hidden=p.id!==activeId;if(p.hidden)p.querySelectorAll('video').forEach(v=>v.pause())});
  tabs.forEach(b=>{const active=b.dataset.patientPanel===activeId;b.setAttribute('aria-selected',String(active));b.tabIndex=active?0:-1});
  const active=panels.find(p=>!p.hidden);
  if(choice&&panels.length)choice.hidden=paired?!active?.querySelector('.patient-overlay'):!active?.querySelector('.scan-annotation');
 }
 modes.forEach(b=>b.addEventListener('click',()=>mode(b.dataset.patientMode)));
 tabs.forEach((b,index)=>{
  b.addEventListener('click',()=>show(b.dataset.patientPanel));
  b.addEventListener('keydown',event=>{
   let next;
   if(event.key==='ArrowRight')next=(index+1)%tabs.length;
   else if(event.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;
   else if(event.key==='Home')next=0;
   else if(event.key==='End')next=tabs.length-1;
   else return;
   event.preventDefault();show(tabs[next].dataset.patientPanel);tabs[next].focus({preventScroll:true});
  });
 });
 if(select)select.addEventListener('change',()=>show(select.value));
 mode(modes[0]?.dataset.patientMode||'explained');if(panels.length)show();
});
})();
