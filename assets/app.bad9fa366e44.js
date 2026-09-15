/* Kansei / Framåt. One runtime for static routes and the portable review file.
   No cookies, analytics requests or persistent health selections. Guidance scripts load on demand. */
(function () {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => Array.from(root.querySelectorAll(s));
  const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const arrow = '<svg class="icon" aria-hidden="true"><use href="#i-arrow"/></svg>';
  const booking = 'https://www.bokadirekt.se/places/kansei-rehabcenter-48847';
  const featureUrls={...(document.currentScript?.dataset || {})};
  const preview = window.KanseiPreview || null;
  const reduced = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const normalize = s => s.toLocaleLowerCase('sv').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  const asset = path => preview?.assets[path] || path;
  let currentRoute = null, cleanup = () => {}, lastAnchor = null;


  const scriptLoads=new Map();
  function loadScript(path,ready){
    if(window[ready])return Promise.resolve();
    if(typeof path!=='string' || !/^\/assets\/[a-z0-9.\-]+\.js$/.test(path))return Promise.reject(new Error('Missing local feature URL'));
    if(scriptLoads.has(path))return scriptLoads.get(path);
    const pending=new Promise((resolve,reject)=>{
      const script=document.createElement('script');script.src=path;script.async=true;
      const timer=setTimeout(()=>{script.remove();reject(new Error('Feature timed out'));},8000);
      script.onload=()=>{clearTimeout(timer);window[ready]?resolve():reject(new Error('Feature unavailable'));};
      script.onerror=()=>{clearTimeout(timer);script.remove();reject(new Error('Feature unavailable'));};
      document.head.appendChild(script);
    }).catch(error=>{scriptLoads.delete(path);throw error;});
    scriptLoads.set(path,pending);return pending;
  }

  function canonical(path) {
    const clean = '/' + String(path || '/').split('?')[0].replace(/^\/+|\/+$/g, '') + '/';
    return clean === '//' ? '/' : clean;
  }
  function routeHref(path, anchor = '') { return '#'+path+(anchor ? '?section='+encodeURIComponent(anchor) : ''); }
  function parseHash() {
    const raw = location.hash.slice(1);
    if (!raw.startsWith('/')) return {path:raw ? '/' : (preview?.defaultRoute || '/'), anchor:raw};
    const [path, query=''] = raw.split('?');
    return {path:canonical(path), anchor:new URLSearchParams(query).get('section') || ''};
  }
  function jump(anchor, focus = false) {
    const target = document.getElementById(anchor);
    if (!target) return;
    if (focus) { const had = target.hasAttribute('tabindex'); if (!had) target.setAttribute('tabindex','-1'); target.focus({preventScroll:true}); if (!had) target.addEventListener('blur',()=>target.removeAttribute('tabindex'),{once:true}); }
    target.scrollIntoView({behavior:reduced()?'instant':'smooth',block:'start'});
  }
  function prepareLinks(root = document) {
    if (!preview) return;
    $$('a[data-route]', root).forEach(a => { const path=preview.aliases[a.dataset.route] || a.dataset.route; if(preview.pages[path]){a.href = routeHref(path, a.dataset.destinationAnchor || '');}else{a.href='https://www.kansei.se'+path+(a.dataset.destinationAnchor?'#'+a.dataset.destinationAnchor:'');a.target='_blank';a.rel='noopener noreferrer';a.removeAttribute('data-route');} });
    $$('a[data-anchor]',root).forEach(a => { a.href=routeHref(currentRoute || '/',a.dataset.anchor); });
  }
  function navigate(path, anchor = '') {
    if (!preview) { location.href=path+(anchor?'#'+anchor:''); return; }
    const desired=routeHref(canonical(path),anchor);
    if (location.hash !== desired) location.hash=desired;
    else if (anchor) jump(anchor,true);
    else window.scrollTo({top:0,behavior:'instant'});
  }
  function portableRender() {
    let {path,anchor}=parseHash(); path=preview.aliases[path] || path;
    const page=preview.pages[path] || preview.pages['/404/'];
    if (!page) return;
    if (currentRoute===path) {if(anchor && anchor!==lastAnchor)jump(anchor,true);lastAnchor=anchor;return;}
    cleanup();
    $$('dialog[open]').forEach(d=>d.close());
    const body = page.body.replace(/src="(\/assets\/[^"<>]+)"/g,(_,p)=>'src="'+asset(p)+'"');
    document.body.classList.remove('locked');
    document.body.innerHTML=body;
    currentRoute=path; lastAnchor=anchor;
    document.title=page.title;
    window.scrollTo({top:0,behavior:'instant'});
    mount();
    $('#main')?.focus({preventScroll:true});
    if(anchor)requestAnimationFrame(()=>jump(anchor,true));
  }

  function mount() {
    const abort=new AbortController();
    const observers=[];
    const listen=(el,name,fn,options={})=>{if(el)el.addEventListener(name,fn,{...options,signal:abort.signal});};
    cleanup=()=>{abort.abort();observers.forEach(o=>o.disconnect());};
    prepareLinks();
    const guide=$('#guide-dialog'),menu=$('#menu-dialog'),content=$('#guide-content');
    const openers=new WeakMap();
    function openDialog(dialog,opener){
      if(!dialog)return;
      [guide,menu].forEach(other=>{if(other && other!==dialog && other.open)other.close();});
      openers.set(dialog,opener || document.activeElement);
      document.body.classList.add('locked');
      if(!dialog.open)dialog.showModal();
      dialog.scrollTop=0;
    }
    function closeDialog(dialog){if(dialog?.open)dialog.close();}
    [guide,menu].filter(Boolean).forEach(dialog=>{
      listen($('[data-close]',dialog),'click',()=>closeDialog(dialog));
      listen(dialog,'close',()=>{
        if(!guide?.open && !menu?.open)document.body.classList.remove('locked');
        if(dialog===guide){guideController?.reset();requestTicket++;}
        const opener=openers.get(dialog);
        if(opener?.isConnected && !guide?.open && !menu?.open && (document.activeElement===document.body || dialog.contains(document.activeElement)))opener.focus({preventScroll:true});
      });
      listen(dialog,'keydown',event=>{
        if(event.key!=='Tab')return;
        const stops=$$('a[href],button:not([disabled]),summary,[tabindex="0"]',dialog).filter(e=>e.getClientRects().length);
        if(!stops.length)return;
        if(event.shiftKey && (document.activeElement===stops[0] || document.activeElement===$('#guide-title'))){event.preventDefault();stops[stops.length-1].focus();}
        else if(!event.shiftKey && document.activeElement===stops[stops.length-1]){event.preventDefault();stops[0].focus();}
      });
      listen(dialog,'click',event=>{
        const r=dialog.getBoundingClientRect();
        if(event.target===dialog && (event.clientX<r.left || event.clientX>r.right || event.clientY<r.top || event.clientY>r.bottom))closeDialog(dialog);
      });
    });
    $$('[data-menu]').forEach(b=>listen(b,'click',()=>openDialog(menu,b)));

    let guideController=null,requestTicket=0;
    function guideContext(){return {$,$$,escapeHTML,arrow,areas:window.KanseiAreas||{},prepareLinks,listen,guide,content,openDialog};}
    function startReady(opener,area,screen,pattern){
      if(!guideController)guideController=window.KanseiGuide(guideContext());
      guideController.start(opener,area,screen,pattern);
    }
    function requestGuide(opener,area=null,screen=null,pattern=null){
      if(window.KanseiGuide && window.KanseiAreas){startReady(opener,area,screen,pattern);return;}
      const ticket=++requestTicket;
      content.innerHTML='<h2 id="guide-title" tabindex="-1">Bokningshjälp</h2><p class="guide-loading" role="status">Öppnar guiden…</p><p class="guide-small">Du kan också läsa om besöken eller boka direkt utan guiden.</p><div class="guide-error-links"><a class="text-link" href="/boka/">Se besök och priser '+arrow+'</a><a class="text-link" href="'+booking+'" target="_blank" rel="noopener noreferrer">Öppna Bokadirekt '+arrow+'</a></div>';
      openDialog(guide,opener);$('#guide-title',content)?.focus({preventScroll:true});
      Promise.all([loadScript(featureUrls.areaSrc,'KanseiAreas'),loadScript(featureUrls.guideSrc,'KanseiGuide')]).then(()=>{
        if(abort.signal.aborted || !guide.open || ticket!==requestTicket)return;
        startReady(opener,area,screen,pattern);
      }).catch(()=>{
        if(abort.signal.aborted || !guide.open || ticket!==requestTicket)return;
        const loading=$('.guide-loading',content);if(loading)loading.textContent='Guiden kunde inte öppnas. Du kan fortfarande välja besök och boka via länkarna nedan.';
      });
    }
    $$('[data-area]').forEach(b=>listen(b,'click',e=>{e.preventDefault();requestGuide(b,b.dataset.area,null,b.dataset.initialPattern||null);}));
    $$('[data-start-guide]').forEach(b=>listen(b,'click',e=>{e.preventDefault();requestGuide(b);}));
    $$('[data-services]').forEach(b=>listen(b,'click',e=>{e.preventDefault();requestGuide(b,null,'services');}));
    $$('[data-care]').forEach(b=>listen(b,'click',e=>{e.preventDefault();requestGuide(b,null,'care');}));

    listen(document.body,'click',event=>{
      const a=event.target.closest('a');if(!a)return;
      if(window.KanseiMeasure===true && a.dataset.measure){document.dispatchEvent(new CustomEvent('kansei:booking-intent',{detail:{event:a.dataset.measure,placement:a.dataset.placement||'content',version:'business-v1'}}));}
      if(a.closest('dialog') && !a.hasAttribute('data-close'))closeDialog(a.closest('dialog'));
      if(event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button!==0 || a.target==='_blank')return;
      if(preview && a.dataset.route){event.preventDefault();navigate(a.dataset.route,a.dataset.destinationAnchor || '');}
      else if(a.dataset.anchor){event.preventDefault();if(preview)navigate(currentRoute,a.dataset.anchor);else{history.pushState(null,'','#'+a.dataset.anchor);jump(a.dataset.anchor,true);}}
    });

    const methods=[
      {image:'/bilder/k068f5396b9.webp',alt:'Klinisk undersökning av rörlighet på behandlingsbänken.',caption:'KLINISK UNDERSÖKNING / KANSEI',heading:'Ditt besvär.<br>I sitt sammanhang.',text:'Vi börjar med att lyssna, undersöka rörelsen och förstå vad som begränsar dig. Bedömningen blir grunden för det vi gör sedan.',link:'/naprapati/',label:'Så går besöket till'},
      {image:'/bilder/k2eea6033d6.webp',alt:'Ultraljudsundersökning med prob och skärm.',caption:'MUSKULOSKELETALT ULTRALJUD / KANSEI',heading:'Se mer.<br>Förstå bättre.',text:'När frågeställningen motiverar det kompletterar vi med ultraljud. Vi förklarar bilderna och väger samman fynden med din funktion och dina besvär.',link:'/ultraljud/',label:'Utforska ultraljud'},
      {image:'/bilder/k0d80f0e3b7.webp',alt:'Behandlaren arbetar med patienten på behandlingsbänken.',caption:'BEHANDLING OCH PLAN / KANSEI',heading:'En plan.<br>För din vardag.',text:'Nästa steg ska vara tydligt. Vi går igenom vad du kan göra hemma och hur behandlingen och uppföljningen kan anpassas efter dina förutsättningar.',link:'/rehabilitering/',label:'Mer om behandling och rehab'}
    ];
    const tabs=$$('[data-method]');
    const panel=$('#method-panel');
    function selectMethod(index,focus=false){
      const m=methods[index];if(!m || !panel)return;
      tabs.forEach((t,i)=>{t.setAttribute('aria-selected',String(i===index));t.tabIndex=i===index?0:-1;});
      panel.setAttribute('aria-labelledby',tabs[index].id);
      const im=$('#method-image');im.removeAttribute('srcset');im.removeAttribute('sizes');im.src=asset(m.image);im.alt=m.alt;
      $('#method-caption').textContent=m.caption;$('#method-number').textContent=String(index+1).padStart(2,'0');$('#method-heading').innerHTML=m.heading;$('#method-text').textContent=m.text;
      const a=$('#method-link');a.dataset.route=m.link;a.href=preview?routeHref(m.link):m.link;a.removeAttribute('target');a.removeAttribute('rel');a.innerHTML=escapeHTML(m.label)+' '+arrow;
      panel.classList.remove('changed');void panel.offsetWidth;panel.classList.add('changed');if(focus)tabs[index].focus({preventScroll:true});
    }
    tabs.forEach((t,i)=>{listen(t,'click',()=>selectMethod(i));listen(t,'keydown',event=>{let n=null;if(event.key==='ArrowRight')n=(i+1)%tabs.length;if(event.key==='ArrowLeft')n=(i+tabs.length-1)%tabs.length;if(event.key==='Home')n=0;if(event.key==='End')n=tabs.length-1;if(n!==null){event.preventDefault();selectMethod(n,true);}});});
    const visual=$('.finder-visual'),hoverLabel=$('#finder-hover-label');
    const setHover=k=>{if(visual && hoverLabel){visual.classList.add('is-active');hoverLabel.textContent=$('[data-area="'+k+'"]>span:nth-child(2)')?.textContent || 'Vi ser hela dig.';}};
    const resetHover=()=>{if(visual && hoverLabel){visual.classList.remove('is-active');hoverLabel.innerHTML='Vi ser<br>hela dig.';}};
    $$('.area-item').forEach(b=>{listen(b,'pointerenter',()=>setHover(b.dataset.area));listen(b,'focus',()=>setHover(b.dataset.area));listen(b,'pointerleave',()=>{if(document.activeElement!==b)resetHover();});listen(b,'blur',resetHover);});

    $$('[data-service-filter]').forEach(b=>listen(b,'click',()=>{
      $$('[data-service-filter]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
      $$('[data-service-card]').forEach(card=>{card.hidden=b.dataset.serviceFilter!=='all' && !card.dataset.categories.split(' ').includes(b.dataset.serviceFilter);});
    }));
    let category='all';
    const search=$('#knowledge-search');
    function searchKnowledge(){
      const query=normalize(search?.value.trim() || '');let count=0;
      $$('[data-article]').forEach(a=>{a.hidden=(category!=='all' && a.dataset.category!==category) || !normalize(a.dataset.search).includes(query);if(!a.hidden)count++;});
      if($('#search-count'))$('#search-count').textContent=count+' '+(count===1?'guide':'guider');
      if($('#no-results'))$('#no-results').hidden=count!==0;
    }
    listen(search,'input',searchKnowledge);
    $$('[data-knowledge-filter]').forEach(b=>listen(b,'click',()=>{category=b.dataset.knowledgeFilter;$$('[data-knowledge-filter]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));searchKnowledge();}));
    listen($('[data-clear-search]'),'click',()=>{if(search){search.value='';searchKnowledge();search.focus();}});
    listen($('[data-reset-search]'),'click',()=>{if(search)search.value='';category='all';$$('[data-knowledge-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.knowledgeFilter==='all')));searchKnowledge();search?.focus();});
    $$('[data-faq-filter]').forEach(b=>listen(b,'click',()=>{$$('[data-faq-filter]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));$$('[data-faq-category]').forEach(x=>{x.hidden=b.dataset.faqFilter!=='all' && x.dataset.faqCategory!==b.dataset.faqFilter;});}));

    const dock=$('#booking-dock'),top=$('.hero') || $('.service-cover') || $('.page-top') || $('main'),footer=$('.service-conclusion') || $('.footer');
    let topVisible=true,footerVisible=false;
    if('IntersectionObserver' in window && top && footer){const o=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.target===top)topVisible=e.isIntersecting;if(e.target===footer)footerVisible=e.isIntersecting;});if(dock)dock.hidden=topVisible||footerVisible;},{threshold:0});o.observe(top);o.observe(footer);observers.push(o);}
    const progress=$('.reading-progress'),article=$('.article-body');
    function readProgress(){if(progress && article){const r=article.getBoundingClientRect();const length=Math.max(r.height-innerHeight+150,1);progress.style.transform='scaleX('+Math.min(1,Math.max(0,(150-r.top)/length))+')';}}
    if(progress){listen(window,'scroll',readProgress,{passive:true});listen(window,'resize',readProgress);readProgress();}
    const tocLinks=$$('.deep-sticky nav a[data-anchor]');
    const tocTargets=$$('.deep-section[id]');
    if(tocLinks.length && 'IntersectionObserver' in window){
      const visible=new Map();
      const tocObserver=new IntersectionObserver(entries=>{
        entries.forEach(e=>visible.set(e.target.id,e.isIntersecting));
        const first=tocTargets.find(t=>visible.get(t.id));
        if(first)tocLinks.forEach(a=>{if(a.dataset.anchor===first.id)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');});
      },{rootMargin:'-110px 0px -55% 0px',threshold:0});
      tocTargets.forEach(t=>tocObserver.observe(t));observers.push(tocObserver);
    }
    $$('.mobile-contents a[data-anchor]').forEach(a=>listen(a,'click',()=>{
      const d=a.closest('details');if(d)d.open=false;
    }));
    prepareLinks();
  }
  if(preview){window.addEventListener('hashchange',portableRender);portableRender();}
  else{currentRoute=canonical(location.pathname.replace(/index\.html$/,''));mount();}
})();
