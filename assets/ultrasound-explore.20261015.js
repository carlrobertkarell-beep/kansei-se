(()=>{
 'use strict';
 document.querySelectorAll('[data-atlas-demo]').forEach(root=>{
  const anatomy=root.querySelector('[data-atlas-anatomy]'),findings=root.querySelector('[data-atlas-findings]');
  const status=root.querySelector('[data-atlas-state]'),badge=root.querySelector('[data-atlas-badge]');
  const image=root.querySelector('.atlas-demo-reveal img'),layer=root.querySelector('.atlas-demo-reveal');
  let painted=false,marked=false;
  function render(){
   root.dataset.anatomy=String(painted);root.dataset.findings=String(marked);
   anatomy.setAttribute('aria-checked',String(painted));findings.setAttribute('aria-checked',String(marked));
   layer.setAttribute('aria-hidden',String(!painted));
   root.querySelector('.atlas-original').setAttribute('aria-hidden',String(painted));
   root.querySelectorAll('.atlas-demo-markers').forEach(m=>m.setAttribute('aria-hidden',String(!(marked&&m.dataset.mode===(painted?'anatomy':'ultrasound')))));
   badge.textContent=painted?'Anatomisk illustration':'Ultraljudsbild';
   status.textContent=(painted?'Anatomi är på. Stäng av för att se originalbilden.':'Slå på Anatomi för att se vävnaderna i färg.')+(marked?' Fynden är markerade.':' Prova Visa fynden.');
  }
  anatomy.addEventListener('click',()=>{painted=!painted;render()});
  findings.addEventListener('click',()=>{marked=!marked;render()});
  root.querySelector('.atlas-demo-controls').hidden=false;render();
  const decoded=image.decode?image.decode():new Promise((resolve,reject)=>{
   if(image.complete&&image.naturalWidth)resolve();else{image.addEventListener('load',resolve,{once:true});image.addEventListener('error',reject,{once:true})}
  });
  decoded.then(()=>{anatomy.disabled=false;painted=true;render()}).catch(()=>{status.textContent='Anatomilagret kunde inte laddas. Du kan fortfarande se originalbilden och fynden.'});
 });
 const root=document.querySelector('[data-atlas-catalogue]');if(!root)return;
 const input=root.querySelector('[data-atlas-search]'),links=[...root.querySelectorAll('[data-atlas-region]')];
 const entries=[...root.querySelectorAll('[data-atlas-entry]')],groups=[...root.querySelectorAll('[data-atlas-group]')];
 const status=root.querySelector('[data-atlas-results]'),empty=root.querySelector('[data-atlas-empty]');
 const normalize=s=>s.toLocaleLowerCase('sv').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
 const valid=new Set(links.map(a=>a.dataset.atlasRegion));
 let region='alla';
 function render(){
  const words=normalize(input.value.trim()).split(/\s+/).filter(Boolean);let count=0;
  entries.forEach(entry=>{const match=(region==='alla'||entry.dataset.region===region)&&words.every(w=>normalize(entry.dataset.search+' '+entry.textContent).includes(w));entry.hidden=!match;if(match)count++});
  groups.forEach(group=>{group.hidden=![...group.querySelectorAll('[data-atlas-entry]')].some(entry=>!entry.hidden)});
  links.forEach(link=>{if(link.dataset.atlasRegion===region)link.setAttribute('aria-current','true');else link.removeAttribute('aria-current')});
  empty.hidden=count>0;
  const label=links.find(link=>link.dataset.atlasRegion===region)?.dataset.label||'Alla områden';
  status.textContent=count+' av '+entries.length+' bildexempel · '+label+(words.length?' · sökning: '+input.value.trim():'');
 }
 function fromUrl(){const value=new URLSearchParams(location.search).get('omrade');region=valid.has(value)?value:'alla';render()}
 links.forEach(link=>link.addEventListener('click',event=>{
  if(event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
  event.preventDefault();region=link.dataset.atlasRegion;
  const url=new URL(location.href);if(region==='alla')url.searchParams.delete('omrade');else url.searchParams.set('omrade',region);
  url.hash='exempel';history.pushState({},'',url);render();
 }));
 input.addEventListener('input',render);
 root.querySelector('[data-atlas-reset]').addEventListener('click',()=>{input.value='';region='alla';const url=new URL(location.href);url.searchParams.delete('omrade');history.replaceState({},'',url);render();input.focus()});
 window.addEventListener('popstate',fromUrl);root.querySelector('.atlas-search').hidden=false;fromUrl();
})();
