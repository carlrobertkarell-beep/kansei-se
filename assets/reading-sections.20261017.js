/* In-page orientation only: no storage, tracking or network requests. */
(()=>{
 'use strict';
 const main=document.querySelector('main'),header=document.querySelector('.site-header');
 if(!main||!header)return;
 const sections=[...main.querySelectorAll('[data-reading-section]')];
 if(sections.length<3)return;
 const bar=document.createElement('details');bar.className='reading-position';bar.hidden=true;
 const summary=document.createElement('summary');
 const row=document.createElement('span');row.className='wrap reading-position-row';
 const caption=document.createElement('span');caption.className='reading-position-caption';caption.textContent='Du läser';
 const current=document.createElement('span');current.className='reading-position-current';
 const action=document.createElement('span');action.className='reading-position-action';action.innerHTML='<span>Byt avsnitt </span><b aria-hidden="true">⌄</b>';
 row.append(caption,current,action);summary.append(row);
 const nav=document.createElement('nav');nav.className='wrap reading-position-links';nav.setAttribute('aria-label','Hoppa till ett avsnitt på sidan');
 const links=sections.map((section,index)=>{
  const a=document.createElement('a');a.href='#'+section.id;
  const number=document.createElement('span');number.textContent=String(index+1).padStart(2,'0');number.setAttribute('aria-hidden','true');
  a.append(number,document.createTextNode(section.dataset.readingTitle));nav.append(a);
  a.addEventListener('click',event=>{
   if(event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
   bar.open=false;
   requestAnimationFrame(()=>{const heading=section.querySelector('h2');if(heading){heading.tabIndex=-1;heading.focus({preventScroll:true});}});
  });
  return a;
 });
 bar.append(summary,nav);header.after(bar);document.body.classList.add('reading-ready');
 const existing=[...main.querySelectorAll('.case-page-nav a[href^="#"],.ha-page-nav a[href^="#"],.us-page-nav a[href^="#"],.us-area-aside nav a[href^="#"]')];
 let headerHeight=88,scheduled=false,active=-1;
 function update(){
  scheduled=false;
  const line=headerHeight+64;
  const visible=sections[0].getBoundingClientRect().top<=line+2&&main.getBoundingClientRect().bottom>Math.max(line,innerHeight*.5);
  bar.hidden=!visible&&!bar.open;
  let next=0;
  sections.forEach((section,index)=>{if(section.getBoundingClientRect().top<=line+2)next=index;});
  if(next===active)return;active=next;
  current.textContent=(next+1)+' / '+sections.length+' · '+sections[next].dataset.readingTitle;
  links.forEach((a,index)=>{if(index===next)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');});
  existing.forEach(a=>{
   const target=document.getElementById(a.hash.slice(1));
   if(target&&sections[next].contains(target))a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');
  });
 }
 function schedule(){if(!scheduled){scheduled=true;requestAnimationFrame(update);}}
 function resize(){headerHeight=Math.ceil(header.getBoundingClientRect().height);document.body.style.setProperty('--reading-header',headerHeight+'px');document.body.style.setProperty('--reading-clearance',(headerHeight+64)+'px');schedule();}
 window.addEventListener('scroll',schedule,{passive:true});window.addEventListener('resize',resize,{passive:true});
 bar.addEventListener('toggle',schedule);
 document.addEventListener('click',event=>{if(bar.open&&!bar.contains(event.target)){bar.open=false;schedule();}});
 bar.addEventListener('keydown',event=>{if(event.key==='Escape'&&bar.open){bar.open=false;summary.focus();event.preventDefault();}});
 if('ResizeObserver' in window){new ResizeObserver(resize).observe(header);new ResizeObserver(schedule).observe(main);}
 resize();
})();
