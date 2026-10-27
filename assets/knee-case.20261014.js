(()=>{
 const viewer=document.querySelector('[data-knee-viewer]');if(!viewer)return;
 const tabs=[...viewer.querySelectorAll('[role="tab"]')],panels=[...viewer.querySelectorAll('[role="tabpanel"]')];
 const anatomySwitch=viewer.querySelector('[data-knee-anatomy]'),findingSwitch=viewer.querySelector('[data-knee-findings]'),findingLabel=viewer.querySelector('[data-knee-findings-label]'),status=viewer.querySelector('.knee-state');
 const zoom=document.getElementById('knee-zoom'),zoomFrame=zoom?.querySelector('[data-knee-zoom-frame]'),zoomTitle=zoom?.querySelector('[data-knee-zoom-title]'),zoomAnatomy=zoom?.querySelector('[data-knee-zoom-anatomy]'),zoomFindings=zoom?.querySelector('[data-knee-zoom-findings]');
 const ready=panels.map(()=>false),failed=panels.map(()=>false);
 let selected=0,anatomy=false,findings=false;
 function render(){
  const shown=anatomy&&ready[selected];
  panels.forEach((panel,i)=>{
   panel.hidden=i!==selected;const picture=panel.querySelector('.knee-picture');
   const showAnatomy=anatomy&&ready[i];
   picture.dataset.anatomy=String(showAnatomy);picture.dataset.findings=String(findings);
   picture.querySelector('.knee-anatomy').setAttribute('aria-hidden',String(!showAnatomy));
   picture.querySelector('.knee-original').setAttribute('aria-hidden',String(showAnatomy));
   picture.querySelector('.knee-findings').setAttribute('aria-hidden',String(!findings));
   if(!picture.id)picture.id='knee-picture-'+panel.dataset.key;
   if(i!==selected)panel.querySelectorAll('video').forEach(video=>video.pause());
  });
  tabs.forEach((tab,i)=>{tab.setAttribute('aria-selected',String(i===selected));tab.tabIndex=i===selected?0:-1});
  anatomySwitch.disabled=!ready[selected];anatomySwitch.setAttribute('aria-checked',String(shown));
  anatomySwitch.setAttribute('aria-controls',panels[selected].querySelector('.knee-picture').id);
  findingSwitch.setAttribute('aria-checked',String(findings));
  findingSwitch.setAttribute('aria-controls',panels[selected].querySelector('.knee-picture').id);
  const label=panels[selected].dataset.orientationExample==='true'?'Visa brosket':'Visa fynden';
  if(findingLabel)findingLabel.textContent=label;
  status.textContent=tabs[selected].querySelector('strong').textContent+' · '+(shown?'anatomisk illustration':'ultraljudsbild')+(findings?' med markering':'');
  if(failed[selected])status.textContent+=' · anatomivyn kunde inte laddas';
  if(zoom?.open&&zoomFrame){
   const picture=zoomFrame.querySelector('.knee-picture');
   if(picture){picture.dataset.anatomy=String(shown);picture.dataset.findings=String(findings);picture.querySelector('.knee-anatomy').setAttribute('aria-hidden',String(!shown));picture.querySelector('.knee-original').setAttribute('aria-hidden',String(shown));picture.querySelector('.knee-findings').setAttribute('aria-hidden',String(!findings));}
   zoomAnatomy.disabled=!ready[selected];zoomAnatomy.setAttribute('aria-checked',String(shown));zoomFindings.setAttribute('aria-checked',String(findings));zoomFindings.querySelector('[data-knee-zoom-findings-label]').textContent=label;
  }
 }
 function select(index,focus=false){if(index<0||index>=tabs.length)return;selected=index;render();if(focus)tabs[index].focus({preventScroll:true});}
 function switchAnatomy(){if(!ready[selected])return;anatomy=!anatomy;render();}
 function switchFindings(){findings=!findings;render();}
 tabs.forEach((tab,index)=>{tab.addEventListener('click',()=>select(index));tab.addEventListener('keydown',event=>{
  let next=index;if(event.key==='ArrowRight'||event.key==='ArrowDown')next=(index+1)%tabs.length;else if(event.key==='ArrowLeft'||event.key==='ArrowUp')next=(index+tabs.length-1)%tabs.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=tabs.length-1;else return;
  event.preventDefault();select(next,true);
 })});
 anatomySwitch.addEventListener('click',switchAnatomy);findingSwitch.addEventListener('click',switchFindings);
 document.querySelectorAll('[data-knee-select]').forEach(link=>link.addEventListener('click',()=>{const index=panels.findIndex(panel=>panel.dataset.key===link.dataset.kneeSelect);select(index);findings=true;render();}));
 const initial=new URLSearchParams(location.search).get('bild');if(initial){selected=Math.max(0,panels.findIndex(panel=>panel.dataset.key===initial));findings=true;}
 if(zoom){
  viewer.querySelector('[data-knee-enlarge]')?.addEventListener('click',()=>{
   const picture=panels[selected].querySelector('.knee-picture').cloneNode(true);
   picture.removeAttribute('id');picture.querySelectorAll('[id]').forEach(element=>{
    const old=element.id,next=old+'-zoom';element.id=next;
    picture.querySelectorAll('[filter]').forEach(path=>{if(path.getAttribute('filter')==='url(#'+old+')')path.setAttribute('filter','url(#'+next+')');});
   });
   zoomFrame.dataset.key=panels[selected].dataset.key;zoomFrame.replaceChildren(picture);zoomTitle.textContent=tabs[selected].querySelector('strong').textContent+'. Förstorad bild';
   zoom.showModal();render();
  });
  zoom.querySelector('[data-knee-zoom-close]').addEventListener('click',()=>zoom.close());
  zoomAnatomy.addEventListener('click',switchAnatomy);zoomFindings.addEventListener('click',switchFindings);
 }
 render();
 // Decode all six small anatomy assets before enabling a switch. A missing layer
 // leaves the ultrasound image visible and does not break the remaining examples.
 panels.forEach((panel,index)=>{
  const image=panel.querySelector('.knee-anatomy img');image.loading='eager';
  const decoded=image.decode?image.decode():new Promise((resolve,reject)=>{
   if(image.complete&&image.naturalWidth)resolve();else{image.addEventListener('load',resolve,{once:true});image.addEventListener('error',reject,{once:true});}
  });
  decoded.then(()=>{ready[index]=true;render();}).catch(()=>{failed[index]=true;render();});
 });
})();
