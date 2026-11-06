/* One drag surface; the image itself is a keyboard-accessible slider. */
(() => {
 'use strict';
 document.querySelectorAll('[data-home-diagnostic]').forEach(root=>{
  const stage=root.querySelector('[data-diagnostic-stage]'),image=root.querySelector('[data-diagnostic-anatomy]');
  const state=root.querySelector('[data-diagnostic-state]'),modes=Array.from(root.querySelectorAll('[data-diagnostic-mode-button]'));
  const findings=root.querySelector('[data-diagnostic-findings-button]'),marker=root.querySelector('.hd-findings');
  if(!stage||!image||!findings||!modes.length)return;
  let position=50,mode='original',marked=false,ready=false,pointer=null,dragStart=null,dragging=false;
  stage.setAttribute('role','slider');stage.tabIndex=-1;
  stage.setAttribute('aria-label','Andel illustrerad anatomi');
  stage.setAttribute('aria-valuemin','0');stage.setAttribute('aria-valuemax','100');
  stage.setAttribute('aria-describedby','home-diagnostic-hint');stage.setAttribute('aria-disabled','true');
  stage.querySelectorAll('img').forEach(img=>{img.draggable=false;});
  stage.addEventListener('dragstart',event=>event.preventDefault());
  function render(announce=false){
   const split=mode==='original'?0:mode==='anatomy'?100:position;
   stage.style.setProperty('--hd-split',split+'%');stage.setAttribute('aria-valuenow',String(split));
   stage.setAttribute('aria-valuetext',split+' procent illustrerad anatomi, '+(100-split)+' procent ultraljud');
   root.dataset.diagnosticMode=mode;root.dataset.diagnosticFindings=String(marked);
   modes.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.diagnosticModeButton===mode)));
   findings.setAttribute('aria-pressed',String(marked));marker.setAttribute('aria-hidden',String(!marked));
   image.parentElement.setAttribute('aria-hidden',String(split===0));
   if(announce)state.textContent=(mode==='compare'?'Jämförelse av original och illustrerad anatomi.':mode==='anatomy'?'Illustrerad anatomi visas.':'Ultraljudsbilden visas.')+(marked?' Kalk och rupturområdet är markerade.':'');
  }
  function setPosition(value){
   if(!ready)return;
   position=Math.max(0,Math.min(100,Math.round(value)));mode=position===0?'original':position===100?'anatomy':'compare';
   root.classList.add('has-compared');render();
  }
  modes.forEach(button=>button.addEventListener('click',()=>{
   if(button.disabled)return;mode=button.dataset.diagnosticModeButton;
   if(mode==='compare'&&(position===0||position===100))position=50;render(true);
  }));
  findings.addEventListener('click',()=>{marked=!marked;render(true);});
  stage.addEventListener('keydown',event=>{
   if(!ready)return;
   const current=Number(stage.getAttribute('aria-valuenow')),step=event.shiftKey?10:2;let next=null;
   if(event.key==='ArrowRight'||event.key==='ArrowUp')next=current+step;
   if(event.key==='ArrowLeft'||event.key==='ArrowDown')next=current-step;
   if(event.key==='PageUp')next=current+10;if(event.key==='PageDown')next=current-10;
   if(event.key==='Home')next=0;if(event.key==='End')next=100;
   if(next!==null){event.preventDefault();setPosition(next);}
  });
  function fromPointer(event){const box=stage.getBoundingClientRect();if(box.width)setPosition((event.clientX-box.left)/box.width*100);}
  stage.addEventListener('pointerdown',event=>{
   if(!ready||!event.isPrimary||event.button!==0)return;
   pointer=event.pointerId;dragStart={x:event.clientX,y:event.clientY};dragging=event.pointerType!=='touch';stage.setPointerCapture(pointer);
   if(dragging){stage.focus({preventScroll:true});stage.classList.add('is-dragging');fromPointer(event);}
  });
  stage.addEventListener('pointermove',event=>{
   if(event.pointerId!==pointer)return;
   if(!dragging){const dx=Math.abs(event.clientX-dragStart.x),dy=Math.abs(event.clientY-dragStart.y);if(dx<6||dx<=dy)return;dragging=true;stage.classList.add('is-dragging');}
   fromPointer(event);
  });
  function endPointer(event){
   if(event.pointerId!==pointer)return;
   if(event.type==='pointerup'&&!dragging&&dragStart&&Math.abs(event.clientX-dragStart.x)<6&&Math.abs(event.clientY-dragStart.y)<6)fromPointer(event);
   if(stage.hasPointerCapture(pointer))stage.releasePointerCapture(pointer);
   pointer=null;dragStart=null;dragging=false;stage.classList.remove('is-dragging');
  }
  stage.addEventListener('pointerup',endPointer);stage.addEventListener('pointercancel',endPointer);
  stage.addEventListener('lostpointercapture',()=>{pointer=null;dragStart=null;dragging=false;stage.classList.remove('is-dragging');});
  root.querySelector('[data-diagnostic-ui]').hidden=false;render();
  function enable(){if(ready||!image.naturalWidth)return;ready=true;root.classList.add('is-ready');stage.tabIndex=0;stage.setAttribute('aria-disabled','false');modes.forEach(button=>{button.disabled=false;});mode='compare';render();state.textContent='Dra direkt över bilden för att jämföra. Med tangentbord: använd piltangenterna.';}
  function failed(){if(!ready)state.textContent='Originalbilden visas. Läs hela undersökningen via länken till patientfallet.';}
  image.addEventListener('load',enable,{once:true});image.addEventListener('error',failed,{once:true});
  if(image.complete&&image.naturalWidth)enable();else{
   let requested=false;
   function load(){if(requested)return;requested=true;image.loading='eager';if(image.complete&&image.naturalWidth)enable();else if(image.decode)image.decode().then(enable).catch(()=>{if(image.complete&&!image.naturalWidth)failed();});}
   if('IntersectionObserver'in window){const loader=new IntersectionObserver(entries=>{if(entries.some(entry=>entry.isIntersecting)){loader.disconnect();load();}},{rootMargin:'400px 0px'});loader.observe(root);}else load();
  }
 });
})();
