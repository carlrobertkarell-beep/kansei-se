/* Native dialog with a short, cancellable transition; no layout jump or library. */
(()=>{'use strict';
 const dialog=document.querySelector('#site-menu'),buttons=[...document.querySelectorAll('[data-site-menu]')];
 const reduced=()=>matchMedia('(prefers-reduced-motion: reduce)').matches;
 let opener=null,closing=false,timer=null;
 function close(){if(!dialog?.open||closing)return;closing=true;dialog.classList.add('is-leaving');
  const finish=()=>{clearTimeout(timer);dialog.close();};if(reduced())finish();else timer=setTimeout(finish,185);}
 if(dialog){
  buttons.forEach(b=>b.addEventListener('click',()=>{if(dialog.open){close();return;}opener=b;closing=false;dialog.classList.remove('is-leaving');document.body.classList.add('locked');b.setAttribute('aria-expanded','true');dialog.showModal();dialog.scrollTop=0;}));
  dialog.querySelector('[data-site-close]').addEventListener('click',close);
  dialog.addEventListener('cancel',e=>{e.preventDefault();close();});
  dialog.addEventListener('close',()=>{clearTimeout(timer);closing=false;dialog.classList.remove('is-leaving');document.body.classList.remove('locked');buttons.forEach(b=>b.setAttribute('aria-expanded','false'));if(opener?.isConnected)opener.focus({preventScroll:true});});
  dialog.addEventListener('click',e=>{const r=dialog.getBoundingClientRect();if(e.target===dialog&&(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom))close();});
  dialog.addEventListener('keydown',e=>{if(e.key!=='Tab')return;const items=[...dialog.querySelectorAll('a[href],button:not([disabled])')].filter(x=>x.getClientRects().length);const first=items[0],last=items.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}});
 }
 const search=document.querySelector('[data-library-search]'),filters=[...document.querySelectorAll('[data-topic]')],cards=[...document.querySelectorAll('[data-library-card]')];let topic='Alla';
 const norm=s=>s.toLocaleLowerCase('sv').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
 function apply(){const q=norm(search?.value.trim()||'');let n=0;cards.forEach(c=>{c.hidden=(topic!=='Alla'&&c.dataset.category!==topic)||!norm(c.dataset.search||c.textContent).includes(q);if(!c.hidden)n++;});const count=document.querySelector('[data-library-count]');if(count)count.textContent=n+' '+(n===1?'artikel':'artiklar');const empty=document.querySelector('[data-library-empty]');if(empty)empty.hidden=n!==0;}
 search?.addEventListener('input',apply);filters.forEach(b=>b.addEventListener('click',()=>{topic=b.dataset.topic;filters.forEach(x=>x.setAttribute('aria-pressed',String(x===b)));apply();}));document.querySelector('[data-library-reset]')?.addEventListener('click',()=>{search.value='';topic='Alla';filters.forEach(x=>x.setAttribute('aria-pressed',String(x.dataset.topic==='Alla')));apply();search.focus();});
 document.querySelectorAll('.contents-mobile a').forEach(a=>a.addEventListener('click',()=>{a.closest('details').open=false;}));
 const nav=[...document.querySelectorAll('.editorial-aside nav a')];if(nav.length&&'IntersectionObserver'in window){const obs=new IntersectionObserver(es=>{for(const e of es)if(e.isIntersecting){nav.forEach(a=>a.removeAttribute('aria-current'));nav.find(a=>a.hash==='#'+e.target.id)?.setAttribute('aria-current','location');}},{rootMargin:'-100px 0px -60% 0px'});nav.forEach(a=>{const t=document.getElementById(a.hash.slice(1));if(t)obs.observe(t);});}
})();
// Share the established canonical article URL, not the protected preview address.
document.querySelectorAll('button.dela').forEach(button=>button.addEventListener('click',async()=>{
 const url=document.querySelector('link[rel=canonical]')?.href;if(!url)return;
 try{if(navigator.share){await navigator.share({title:document.title,url});return;}if(navigator.clipboard?.writeText){await navigator.clipboard.writeText(url);button.textContent='Länken är kopierad';return;}}
 catch(e){if(e.name==='AbortError')return;}
 let result=button.nextElementSibling;if(!result?.classList.contains('share-result')){result=document.createElement('p');result.className='share-result';result.setAttribute('role','status');button.after(result);}result.textContent='Artikelns länk: '+url;
}));
