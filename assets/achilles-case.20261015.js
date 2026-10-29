// The clinic reader model, including a native movie panel and independent overlays.
(()=>{
 'use strict';
 const viewer=document.querySelector('[data-achilles-viewer]');if(!viewer)return;
 const tabs=[...viewer.querySelectorAll('[role=tab]')],panels=[...viewer.querySelectorAll('[role=tabpanel]')];
 const controls=viewer.querySelector('[data-achilles-controls]');
 const anatomySwitch=viewer.querySelector('[data-knee-anatomy]'),findingSwitch=viewer.querySelector('[data-knee-findings]'),findingLabel=viewer.querySelector('[data-knee-findings-label]'),status=viewer.querySelector('.knee-state'),enlarge=viewer.querySelector('[data-knee-enlarge]');
 const zoom=document.getElementById('knee-zoom'),zoomFrame=zoom.querySelector('[data-knee-zoom-frame]'),zoomTitle=zoom.querySelector('[data-knee-zoom-title]'),zoomAnatomy=zoom.querySelector('[data-knee-zoom-anatomy]'),zoomFindings=zoom.querySelector('[data-knee-zoom-findings]');
 const ready=panels.map(()=>false),failed=panels.map(()=>false);
 let selected=0,anatomy=false,findings=false;
 function paint(picture,shown,marked){
  picture.dataset.anatomy=String(shown);picture.dataset.findings=String(marked);
  picture.querySelector('.knee-anatomy').setAttribute('aria-hidden',String(!shown));
  picture.querySelector('.knee-original').setAttribute('aria-hidden',String(shown));
  picture.querySelector('.knee-findings').setAttribute('aria-hidden',String(!marked));
 }
 function render(){
  panels.forEach((panel,i)=>{
   panel.hidden=i!==selected;
   const picture=panel.querySelector('.knee-picture');
   if(picture){
    if(!picture.id)picture.id='achilles-picture-'+panel.dataset.key;
    paint(picture,anatomy&&ready[i],findings);
    panel.querySelector('.achilles-legend').hidden=!findings;
   }
   if(i!==selected)panel.querySelectorAll('video').forEach(v=>v.pause());
  });
  tabs.forEach((tab,i)=>{tab.setAttribute('aria-selected',String(i===selected));tab.tabIndex=i===selected?0:-1});
  const picture=panels[selected].querySelector('.knee-picture');controls.hidden=!picture;
  if(!picture){if(zoom.open)zoom.close();return;}
  const shown=anatomy&&ready[selected],label=panels[selected].dataset.key==='healthy'?'Visa senan':'Visa fynden';
  anatomySwitch.disabled=!ready[selected];anatomySwitch.setAttribute('aria-checked',String(shown));
  anatomySwitch.setAttribute('aria-controls',picture.id);
  findingSwitch.setAttribute('aria-checked',String(findings));findingSwitch.setAttribute('aria-controls',picture.id);findingLabel.textContent=label;
  status.textContent=tabs[selected].querySelector('strong').textContent+' · '+(shown?'anatomisk illustration':'ultraljudsbild')+(findings?' med markering':'')+(failed[selected]?' · anatomivyn kunde inte laddas':'');
  if(zoom.open){
   paint(zoomFrame.querySelector('.knee-picture'),shown,findings);
   zoomAnatomy.disabled=!ready[selected];zoomAnatomy.setAttribute('aria-checked',String(shown));
   zoomFindings.setAttribute('aria-checked',String(findings));zoomFindings.querySelector('[data-knee-zoom-findings-label]').textContent=label;
  }
 }
 function select(index,focus=false){if(index<0||index>=tabs.length)return;selected=index;render();if(focus)tabs[index].focus({preventScroll:true})}
 const toggleAnatomy=()=>{if(!ready[selected])return;anatomy=!anatomy;render()};
 const toggleFindings=()=>{findings=!findings;render()};
 tabs.forEach((tab,index)=>{
  tab.addEventListener('click',()=>select(index));
  tab.addEventListener('keydown',event=>{
   let next;if(event.key==='ArrowRight'||event.key==='ArrowDown')next=(index+1)%tabs.length;
   else if(event.key==='ArrowLeft'||event.key==='ArrowUp')next=(index+tabs.length-1)%tabs.length;
   else if(event.key==='Home')next=0;else if(event.key==='End')next=tabs.length-1;else return;
   event.preventDefault();select(next,true);
  });
 });
 anatomySwitch.addEventListener('click',toggleAnatomy);findingSwitch.addEventListener('click',toggleFindings);
 enlarge.addEventListener('click',()=>{
  const original=panels[selected].querySelector('.knee-picture');if(!original)return;
  const picture=original.cloneNode(true);picture.removeAttribute('id');
  zoomFrame.dataset.key=panels[selected].dataset.key;zoomFrame.replaceChildren(picture);
  zoomTitle.textContent=tabs[selected].querySelector('strong').textContent+'. Förstorad bild';zoom.showModal();render();
 });
 zoom.querySelector('[data-knee-zoom-close]').addEventListener('click',()=>zoom.close());
 zoom.addEventListener('close',()=>enlarge.focus({preventScroll:true}));
 zoomAnatomy.addEventListener('click',toggleAnatomy);zoomFindings.addEventListener('click',toggleFindings);
 const initial=new URLSearchParams(location.search).get('bild');if(initial){const i=panels.findIndex(p=>p.dataset.key===initial);if(i>=0){selected=i;findings=initial!=='doppler'}}
 render();
 panels.forEach((panel,i)=>{
  const image=panel.querySelector('.knee-anatomy img');if(!image)return;
  image.loading='eager';
  const decoded=new Promise((resolve,reject)=>{
   if(image.complete){image.naturalWidth?resolve():reject(new Error('Anatomy image unavailable'));return;}
   const cleanup=()=>{image.removeEventListener('load',onload);image.removeEventListener('error',onerror)};
   const onload=()=>{cleanup();image.naturalWidth?resolve():reject(new Error('Anatomy image unavailable'))};
   const onerror=()=>{cleanup();reject(new Error('Anatomy image unavailable'))};
   image.addEventListener('load',onload);image.addEventListener('error',onerror);
  });
  decoded.then(()=>{ready[i]=true;render()}).catch(()=>{failed[i]=true;render()});
 });
})();
