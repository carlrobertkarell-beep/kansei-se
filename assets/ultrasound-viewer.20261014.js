// Independent, shared anatomy and finding controls for every patient case.
(()=>{
 document.querySelectorAll('[data-patient-viewer]').forEach((root,viewerIndex)=>{
  const tabs=[...root.querySelectorAll('[role="tab"]')];
  const panels=[...root.querySelectorAll('.reader-panel')];
  const select=root.querySelector('[data-patient-select]');
  const toggle=root.querySelector('[data-patient-toggle]');
  const findingToggle=root.querySelector('[data-patient-findings]');
  const area=root.querySelector('.patient-toggle-area');
  const state=root.querySelector('[data-patient-state]');
  const comparison=root.querySelector('.detail-comparison');
  const decoded=new WeakMap();
  const pictures=[...root.querySelectorAll('.patient-picture')];
  pictures.forEach((picture,index)=>{if(!picture.id)picture.id='patient-picture-'+viewerIndex+'-'+index});
  let activeId=select?.value||tabs[0]?.dataset.patientPanel||tabs[0]?.getAttribute('aria-controls')||panels[0]?.id;
  let enabled=false,findings=false,ready=false,failed=false,token=0,active=root;
  function decode(image){
   if(!decoded.has(image))decoded.set(image,image.decode?image.decode():new Promise((resolve,reject)=>{
    if(image.complete&&image.naturalWidth)resolve();
    else{image.addEventListener('load',resolve,{once:true});image.addEventListener('error',reject,{once:true})}
   }));return decoded.get(image);
  }
  function updateComparison(shown){
   if(!comparison)return;
   comparison.querySelectorAll('.detail-window').forEach(window=>{
    const side=window.dataset.detailSide;
    const source=root.querySelector('#view-'+side+' '+(shown?'.anatomy-layer img':'.original'));
    const image=window.querySelector('img');if(!source||!image)return;
    const [x,y,width,height]=window.dataset[shown?'cropAnatomy':'cropUltrasound'].split(',').map(Number);
    image.src=source.src;image.style.width=1280/width*100+'%';image.style.height=960/height*100+'%';
    image.style.left=-x/width*100+'%';image.style.top=-y/height*100+'%';
   });
  }
  function mode(){
   const shown=enabled&&ready,mode=shown?'anatomy':'ultrasound';
   root.dataset.anatomy=String(shown);root.dataset.findings=String(findings);
   toggle.disabled=!ready;toggle.setAttribute('aria-checked',String(shown));
   findingToggle.setAttribute('aria-checked',String(findings));
   const targets=[...active.querySelectorAll('.patient-picture')].map(p=>p.id).join(' ');
   toggle.setAttribute('aria-controls',targets);findingToggle.setAttribute('aria-controls',targets);
   findingToggle.hidden=!active.querySelector('.patient-finding');
   const tab=tabs.find(t=>(t.dataset.patientPanel||t.getAttribute('aria-controls'))===activeId);
   const name=tab?.querySelector('strong')?.textContent||'';
   state.textContent=(name?name+' · ':'')+(shown?'Anatomisk illustration':'Ultraljud')+(findings?' med markering':'')+(failed?' · anatomivyn kunde inte laddas':'');
   pictures.forEach(picture=>{
    picture.dataset.mode=mode;picture.dataset.findings=String(findings);
    const overlay=picture.querySelector('.patient-overlay,.anatomy-layer');
    overlay?.setAttribute('aria-hidden',String(!shown));
    picture.querySelectorAll('.story-scan,.original').forEach(image=>image.setAttribute('aria-hidden',String(shown)));
    picture.querySelectorAll('.patient-finding').forEach(layer=>layer.setAttribute('aria-hidden',String(!(findings&&layer.dataset.findingMode===mode))));
   });updateComparison(shown);
  }
  function prepare(){
   const current=++token,images=[...active.querySelectorAll('.patient-overlay img,.anatomy-layer img')];
   ready=false;failed=false;mode();if(!images.length)return;
   Promise.all(images.map(decode)).then(()=>{
    if(current!==token)return;
    requestAnimationFrame(()=>requestAnimationFrame(()=>{if(current!==token)return;ready=true;mode()}));
   }).catch(()=>{if(current!==token)return;failed=true;mode()});
  }
  function show(id=activeId){
   activeId=id;
   panels.forEach(panel=>{panel.hidden=panel.id!==activeId;if(panel.hidden)panel.querySelectorAll('video').forEach(video=>video.pause())});
   tabs.forEach(tab=>{const selected=(tab.dataset.patientPanel||tab.getAttribute('aria-controls'))===activeId;tab.setAttribute('aria-selected',String(selected));tab.tabIndex=selected?0:-1});
   active=panels.find(panel=>!panel.hidden)||root;
   area.hidden=!active.querySelector('.patient-overlay,.anatomy-layer');
   if(comparison&&active.querySelector('.patient-picture'))active.querySelector('.panel-media')?.append(comparison);
   prepare();
  }
  toggle.addEventListener('click',()=>{if(!ready)return;enabled=!enabled;mode()});
  findingToggle.addEventListener('click',()=>{findings=!findings;mode()});
  tabs.forEach((tab,index)=>{
   tab.addEventListener('click',()=>show(tab.dataset.patientPanel||tab.getAttribute('aria-controls')));
   tab.addEventListener('keydown',event=>{
    let next;if(event.key==='ArrowRight'||event.key==='ArrowDown')next=(index+1)%tabs.length;
    else if(event.key==='ArrowLeft'||event.key==='ArrowUp')next=(index+tabs.length-1)%tabs.length;
    else if(event.key==='Home')next=0;else if(event.key==='End')next=tabs.length-1;else return;
    event.preventDefault();show(tabs[next].dataset.patientPanel||tabs[next].getAttribute('aria-controls'));tabs[next].focus({preventScroll:true});
   });
  });select?.addEventListener('change',()=>show(select.value));show();
 });
})();
