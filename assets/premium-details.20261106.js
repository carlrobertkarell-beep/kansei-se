/* Native disclosures keep their semantics; motion is an optional enhancement. */
(()=>{
 'use strict';
 if(document.documentElement.dataset.kanseiDetailsMotion)return;
 document.documentElement.dataset.kanseiDetailsMotion='ready';
 if(!('animate' in Element.prototype))return;
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 const running=new Map();
 const excluded='.contents-mobile,.mobile-contents,.ultrasound-contents,[data-no-motion]';
 function restore(details,state){
  for(const [property,value] of Object.entries(state.styles)){
   if(value.value)details.style.setProperty(property,value.value,value.priority);
   else details.style.removeProperty(property);
  }
 }
 function finish(details,state){
  if(running.get(details)!==state)return;
  running.delete(details);
  state.animation.onfinish=null;
  state.animation.cancel();
  details.open=state.open;
  restore(details,state);
 }
 document.querySelectorAll('main details').forEach(details=>{
  // Contents menus manage their own closing and scroll position. Native named
  // accordion groups retain the browser's mutual-exclusion behavior unchanged.
  if(details.matches(excluded)||details.hasAttribute('name')||details.closest('dialog'))return;
  const summary=[...details.children].find(child=>child.tagName==='SUMMARY');
  if(!summary)return;
  summary.addEventListener('click',event=>{
   if(event.defaultPrevented||event.button>0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
   if(event.target.closest('a,button,input,select,textarea'))return;
   if(reduced.matches)return;
   event.preventDefault();
   const previous=running.get(details);
   const open=previous?!previous.open:!details.open;
   const start=details.getBoundingClientRect().height;
   const styles=previous?.styles||Object.fromEntries(['height','overflow','box-sizing'].map(property=>[property,{
    value:details.style.getPropertyValue(property),priority:details.style.getPropertyPriority(property)
   }]));
   if(previous){
    previous.animation.onfinish=null;
    previous.animation.cancel();
    running.delete(details);
    restore(details,previous);
   }
   // Measure real native open/closed geometry, including each design's summary
   // padding and borders. Both measurements occur before the next paint.
   details.open=open;
   const end=details.getBoundingClientRect().height;
   details.open=true;
   if(Math.abs(end-start)<1){details.open=open;return;}
   details.style.setProperty('box-sizing','border-box');
   details.style.setProperty('overflow','hidden');
   const animation=details.animate([{height:start+'px'},{height:end+'px'}],{
    duration:Math.min(300,180+Math.abs(end-start)*.12),
    easing:'cubic-bezier(.22,.61,.36,1)',fill:'both'
   });
   const state={animation,open,styles};
   running.set(details,state);
   animation.onfinish=()=>finish(details,state);
  });
  // Respect an external close, for example an existing navigation handler.
  details.addEventListener('toggle',()=>{
   const state=running.get(details);
   if(state&&!details.open){state.open=false;finish(details,state);}
  });
 });
 function settle(){for(const [details,state] of [...running])finish(details,state);}
 // A viewport/font reflow must never leave content clipped to an old height.
 window.addEventListener('resize',settle,{passive:true});
 window.addEventListener('pagehide',settle);
 document.addEventListener('visibilitychange',()=>{if(document.hidden)settle();});
 if(reduced.addEventListener)reduced.addEventListener('change',()=>{if(reduced.matches)settle();});
 else reduced.addListener(()=>{if(reduced.matches)settle();});
})();
