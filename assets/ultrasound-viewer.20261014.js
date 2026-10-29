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
  const decoded=new WeakMap(),loaded=new WeakSet();
  const pictures=[...root.querySelectorAll('.patient-picture')];
  pictures.forEach((picture,index)=>{if(!picture.id)picture.id='patient-picture-'+viewerIndex+'-'+index});
  let activeId=select?.value||tabs[0]?.dataset.patientPanel||tabs[0]?.getAttribute('aria-controls')||panels[0]?.id;
  let enabled=false,findings=false,ready=false,failed=false,token=0,active=root;
  // A loaded image is paintable even when a browser rejects HTMLImageElement.decode().
  // Do not permanently cache an unsuccessful load or make decode a switch prerequisite.
  function decode(image){
   if(!decoded.has(image)){
    image.loading='eager';
    const pending=new Promise((resolve,reject)=>{
     if(image.complete){image.naturalWidth?resolve():reject(new Error('Anatomy image unavailable'));return;}
     const cleanup=()=>{image.removeEventListener('load',onload);image.removeEventListener('error',onerror)};
     const onload=()=>{cleanup();image.naturalWidth?resolve():reject(new Error('Anatomy image unavailable'))};
     const onerror=()=>{cleanup();reject(new Error('Anatomy image unavailable'))};
     image.addEventListener('load',onload);image.addEventListener('error',onerror);
    }).then(()=>{loaded.add(image)}).catch(error=>{decoded.delete(image);throw error});
    decoded.set(image,pending);
   }
   return decoded.get(image);
  }
  const enlarge=document.createElement('button');enlarge.type='button';enlarge.className='patient-enlarge';enlarge.textContent='Förstora bilden';enlarge.setAttribute('aria-haspopup','dialog');
  const zoom=document.createElement('dialog');zoom.className='patient-reader-zoom';
  const zoomId='patient-reader-zoom-'+viewerIndex;zoom.setAttribute('aria-labelledby',zoomId+'-title');
  zoom.innerHTML='<div class="patient-zoom-head"><h2 id="'+zoomId+'-title">Förstorad bild</h2><button type="button" data-patient-zoom-close>Stäng</button></div><div class="patient-zoom-frame"></div><div class="patient-toggle-area"><div class="patient-toggle-row"><button type="button" class="patient-toggle" data-patient-zoom-anatomy role="switch" aria-checked="false"><span class="patient-switch-track" aria-hidden="true"><span class="patient-switch-thumb"></span></span><span>Anatomi</span></button><button type="button" class="patient-findings-toggle" data-patient-zoom-findings role="switch" aria-checked="false"><span class="patient-switch-track" aria-hidden="true"><span class="patient-switch-thumb"></span></span><span>Visa fynden</span></button><span class="patient-image-state" data-patient-zoom-state aria-live="polite"></span></div></div>';
  // Older readers place their controls directly in the area.
  (area.querySelector('.patient-toggle-row')||area).append(enlarge);root.append(zoom);
  const zoomFrame=zoom.querySelector('.patient-zoom-frame'),zoomAnatomy=zoom.querySelector('[data-patient-zoom-anatomy]'),zoomFindings=zoom.querySelector('[data-patient-zoom-findings]');
  function updateZoom(){
   if(!zoom.open)return;
   const picture=zoomFrame.querySelector('.patient-picture'),shown=enabled&&ready,mode=shown?'anatomy':'ultrasound';
   if(picture){
    picture.dataset.mode=mode;picture.dataset.findings=String(findings);
    picture.querySelector('.patient-overlay,.anatomy-layer')?.setAttribute('aria-hidden',String(!shown));
    picture.querySelectorAll('.story-scan,.original').forEach(image=>image.setAttribute('aria-hidden',String(shown)));
    picture.querySelectorAll('.patient-finding').forEach(layer=>layer.setAttribute('aria-hidden',String(!(findings&&layer.dataset.findingMode===mode))));
   }
   zoomAnatomy.disabled=!ready;zoomAnatomy.setAttribute('aria-checked',String(shown));
   zoomFindings.hidden=findingToggle.hidden;zoomFindings.setAttribute('aria-checked',String(findings));
   zoom.querySelector('[data-patient-zoom-state]').textContent=state.textContent;
  }
  enlarge.addEventListener('click',()=>{
   const original=active.querySelector('.patient-picture');if(!original)return;
   const picture=original.cloneNode(true),ids=new Map();
   [picture,...picture.querySelectorAll('[id]')].forEach(element=>{if(element.id){const next=element.id+'-zoom-'+viewerIndex;ids.set(element.id,next);element.id=next}});
   picture.querySelectorAll('*').forEach(element=>[...element.attributes].forEach(attribute=>{
    let value=attribute.value.replace(/url\(#([^\)]+)\)/g,(match,id)=>ids.has(id)?'url(#'+ids.get(id)+')':match);
    if((attribute.name==='href'||attribute.name==='xlink:href')&&value[0]==='#'&&ids.has(value.slice(1)))value='#'+ids.get(value.slice(1));
    if(attribute.name==='aria-labelledby'||attribute.name==='aria-controls')value=value.split(' ').map(id=>ids.get(id)||id).join(' ');
    if(value!==attribute.value)element.setAttribute(attribute.name,value);
   }));
   zoomFrame.replaceChildren(picture);
   const tab=tabs.find(t=>(t.dataset.patientPanel||t.getAttribute('aria-controls'))===activeId);
   zoom.querySelector('h2').textContent=(tab?.querySelector('strong')?.textContent||'Ultraljudsbild')+' · Förstorad bild';
   zoom.showModal();updateZoom();
  });
  zoom.querySelector('[data-patient-zoom-close]').addEventListener('click',()=>zoom.close());
  zoomAnatomy.addEventListener('click',()=>toggle.click());zoomFindings.addEventListener('click',()=>findingToggle.click());
  zoom.addEventListener('close',()=>{zoomFrame.replaceChildren();enlarge.focus({preventScroll:true})});
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
   });updateComparison(shown);enlarge.hidden=!active.querySelector('.patient-picture');updateZoom();
  }
  function prepare(){
   const current=++token,images=[...active.querySelectorAll('.patient-overlay img,.anatomy-layer img')];
   ready=images.length>0&&images.every(image=>loaded.has(image));failed=false;mode();if(!images.length||ready)return;
   Promise.all(images.map(decode)).then(()=>{
    if(current!==token)return;
    requestAnimationFrame(()=>requestAnimationFrame(()=>{if(current!==token)return;ready=true;mode()}));
   }).catch(()=>{if(current!==token)return;failed=true;mode()});
  }
  function show(id=activeId){
   if(id!==activeId&&zoom.open)zoom.close();
   activeId=id;
   if(select)select.value=id;
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
  });select?.addEventListener('change',()=>show(select.value));
  pictures.forEach(picture=>picture.querySelectorAll('.patient-overlay img,.anatomy-layer img').forEach(image=>decode(image).catch(()=>{})));show();
 });
})();
