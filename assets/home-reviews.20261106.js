/* One entrance count; the accessible values stay final and do not announce frames. */
(() => {
 'use strict';
 const root=document.querySelector('[data-home-reviews]');
 if(!root)return;
 const items=Array.from(root.querySelectorAll('[data-review-count]'));
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 let started=false,frame=0,observer=null;
 function render(progress){
  items.forEach(item=>{
   const value=Number(item.dataset.reviewCount)*progress;
   item.textContent=item.dataset.reviewDecimals==='1'?value.toFixed(1).replace('.',','):Math.round(value).toLocaleString('sv-SE');
  });
 }
 function finish(){cancelAnimationFrame(frame);frame=0;render(1);}
 function start(){
  if(started)return;started=true;observer?.disconnect();
  if(reduced.matches||document.hidden){finish();return;}
  const begin=performance.now();
  function step(now){const p=Math.min(1,(now-begin)/1650);render(1-Math.pow(1-p,4));if(p<1)frame=requestAnimationFrame(step);else frame=0;}
  render(0);frame=requestAnimationFrame(step);
 }
 if('IntersectionObserver'in window&&!reduced.matches){
  observer=new IntersectionObserver(entries=>{if(entries.some(entry=>entry.isIntersecting))start();},{threshold:.22});
  observer.observe(root.querySelector('.hr-summary'));
 }
 reduced.addEventListener('change',()=>{if(reduced.matches){started=true;observer?.disconnect();finish();}});
 document.addEventListener('visibilitychange',()=>{if(document.hidden&&frame)finish();});
 addEventListener('beforeprint',finish);
})();
