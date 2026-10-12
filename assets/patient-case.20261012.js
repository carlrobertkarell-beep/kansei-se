// Shared ultrasound reader: original image or the registered anatomy layer.
(()=>{
 document.querySelectorAll('[data-patient-viewer]').forEach((root,viewerIndex)=>{
  const tabs=[...root.querySelectorAll('[data-patient-panel]')];
  const panels=[...root.querySelectorAll('.reader-panel')];
  const select=root.querySelector('[data-patient-select]');
  const toggle=root.querySelector('[data-patient-toggle]');
  const area=root.querySelector('.patient-toggle-area');
  const state=root.querySelector('[data-patient-state]');
  const label=root.querySelector('[data-toggle-label]');
  let activeId=select?.value||tabs[0]?.dataset.patientPanel||panels[0]?.id;
  let enabled=false,ready=false,token=0,active=root;
  const decoded=new WeakMap();
  const pictures=[...root.querySelectorAll('.patient-picture')];
  pictures.forEach((picture,index)=>{if(!picture.id)picture.id='patient-picture-'+viewerIndex+'-'+index});
  if(label)label.textContent='Anatomi';
  if(toggle)toggle.setAttribute('aria-label','Anatomi');
  function decode(image){
   if(!decoded.has(image))decoded.set(image,image.decode?image.decode():new Promise((resolve,reject)=>{
    if(image.complete&&image.naturalWidth)resolve();
    else{image.addEventListener('load',resolve,{once:true});image.addEventListener('error',reject,{once:true})}
   }));
   return decoded.get(image);
  }
  function mode(){
   const shown=enabled&&ready;
   root.dataset.anatomy=String(shown);
   if(toggle){toggle.disabled=!ready;toggle.setAttribute('aria-checked',String(shown))}
   if(state)state.textContent=shown?'Anatomisk illustration':'Ultraljud';
   pictures.forEach(picture=>{
    const overlay=picture.querySelector('.patient-overlay');
    if(!overlay)return;
    overlay.setAttribute('aria-hidden',String(!shown));
    picture.querySelectorAll('.story-scan').forEach(image=>image.setAttribute('aria-hidden',String(shown)));
   });
  }
  function prepare(){
   const current=++token,images=[...active.querySelectorAll('.patient-overlay img')];
   ready=false;mode();
   if(!images.length)return;
   Promise.all(images.map(decode)).then(()=>{
    if(current!==token)return;
    requestAnimationFrame(()=>requestAnimationFrame(()=>{
     if(current!==token)return;
     ready=true;mode();
    }));
   }).catch(()=>{
    if(current!==token)return;
    ready=false;mode();
    if(state)state.textContent='Anatomivyn kunde inte laddas.';
   });
  }
  function show(id=activeId){
   activeId=id;
   panels.forEach(panel=>{panel.hidden=panel.id!==activeId;if(panel.hidden)panel.querySelectorAll('video').forEach(video=>video.pause())});
   tabs.forEach(tab=>{const selected=tab.dataset.patientPanel===activeId;tab.setAttribute('aria-selected',String(selected));tab.tabIndex=selected?0:-1});
   active=panels.find(panel=>!panel.hidden)||root;
   if(area)area.hidden=!active.querySelector('.patient-overlay');
   if(toggle)toggle.setAttribute('aria-controls',[...active.querySelectorAll('.patient-picture')].map(picture=>picture.id).join(' '));
   prepare();
  }
  toggle?.addEventListener('click',()=>{if(!ready)return;enabled=!enabled;mode()});
  tabs.forEach((tab,index)=>{
   tab.addEventListener('click',()=>show(tab.dataset.patientPanel));
   tab.addEventListener('keydown',event=>{
    let next;
    if(event.key==='ArrowRight')next=(index+1)%tabs.length;
    else if(event.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;
    else if(event.key==='Home')next=0;
    else if(event.key==='End')next=tabs.length-1;
    else return;
    event.preventDefault();show(tabs[next].dataset.patientPanel);tabs[next].focus({preventScroll:true});
   });
  });
  select?.addEventListener('change',()=>show(select.value));
  show();
 });
})();
