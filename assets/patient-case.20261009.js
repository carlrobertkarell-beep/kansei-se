(()=>{
document.querySelectorAll('[data-patient-viewer]').forEach((root,viewerIndex)=>{
 const select=root.querySelector('[data-patient-select]'),tabs=[...root.querySelectorAll('[data-patient-panel]')],panels=[...root.querySelectorAll('.reader-panel')],paired=root.hasAttribute('data-paired-anatomy'),toggle=root.querySelector('[data-patient-toggle]'),label=root.querySelector('[data-toggle-label]'),state=root.querySelector('[data-patient-state]'),area=root.querySelector('.patient-toggle-area'),hint=root.querySelector('[data-patient-hint]');
 let activeId=select?.value||tabs[0]?.dataset.patientPanel||panels[0]?.id,enabled=paired?root.dataset.anatomy==='true':root.dataset.explained!=='false',timer,hideTimer,visible=false,interacted=false,offered=false;
 const storageKey='kansei-viewer-hint:'+location.pathname+':'+viewerIndex;
 try{offered=sessionStorage.getItem(storageKey)==='1'}catch{}
 const pictures=[...root.querySelectorAll('.patient-picture,.frame')];
 pictures.forEach((picture,index)=>{if(!picture.id)picture.id='patient-picture-'+viewerIndex+'-'+index});
 if(toggle){toggle.disabled=false;toggle.setAttribute('aria-controls',pictures.map(p=>p.id).join(' '))}
 function mode(){
  root.dataset[paired?'anatomy':'explained']=String(enabled);
  if(toggle)toggle.setAttribute('aria-pressed',String(enabled));
  if(label)label.textContent=paired?(enabled?'Visa ultraljud':'Visa anatomi'):(enabled?'Dölj markeringar':'Visa markeringar');
  if(state)state.textContent=paired?(enabled?'Anatomisk illustration':'Ultraljud'):(enabled?'Ultraljud med markeringar':'Ultraljud');
  root.querySelectorAll('.patient-overlay').forEach(el=>el.setAttribute('aria-hidden',String(!enabled)));
  root.querySelectorAll('.patient-picture .story-scan').forEach(el=>el.setAttribute('aria-hidden',String(paired&&enabled)));
  root.querySelectorAll('.patient-finding').forEach(el=>el.setAttribute('aria-hidden',String(paired&&enabled)));
  if(!paired)root.querySelectorAll('.scan-annotation').forEach(el=>el.setAttribute('aria-hidden',String(!enabled)));
 }
 function dismiss(){clearTimeout(timer);clearTimeout(hideTimer);toggle?.classList.remove('needs-discovery');if(hint)hint.hidden=true}
 function discover(){
  clearTimeout(timer);
  if(!visible||offered||interacted||area?.hidden||!hint||!toggle||document.hidden)return;
  timer=setTimeout(()=>{
   if(!visible||interacted||area.hidden||document.hidden)return;
   offered=true;try{sessionStorage.setItem(storageKey,'1')}catch{}
   hint.hidden=false;toggle.classList.add('needs-discovery');hideTimer=setTimeout(dismiss,7000);
  },3500);
 }
 function show(id=activeId){
  activeId=id;panels.forEach(p=>{p.hidden=p.id!==activeId;if(p.hidden)p.querySelectorAll('video').forEach(v=>v.pause())});
  tabs.forEach(b=>{const active=b.dataset.patientPanel===activeId;b.setAttribute('aria-selected',String(active));b.tabIndex=active?0:-1});
  const active=panels.find(p=>!p.hidden);
  if(area&&panels.length)area.hidden=paired?!active?.querySelector('.patient-overlay'):!active?.querySelector('.scan-annotation');
  dismiss();discover();
 }
 toggle?.addEventListener('click',()=>{interacted=true;offered=true;try{sessionStorage.setItem(storageKey,'1')}catch{}dismiss();enabled=!enabled;mode()});
 tabs.forEach((b,index)=>{
  b.addEventListener('click',()=>show(b.dataset.patientPanel));
  b.addEventListener('keydown',event=>{
   let next;if(event.key==='ArrowRight')next=(index+1)%tabs.length;else if(event.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=tabs.length-1;else return;
   event.preventDefault();show(tabs[next].dataset.patientPanel);tabs[next].focus({preventScroll:true});
  });
 });
 select?.addEventListener('change',()=>show(select.value));
 if('IntersectionObserver'in window&&toggle){
  const observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;if(visible)discover();else dismiss()},{threshold:1});observer.observe(toggle);
 }
 document.addEventListener('visibilitychange',()=>{if(document.hidden)dismiss();else discover()});
 mode();if(panels.length)show();
});
})();
