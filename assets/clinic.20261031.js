/* Kansei / Framåt. One runtime for static routes and the portable review file.
   No cookies, analytics requests or persistent health selections. Guidance scripts load on demand. */
(function () {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => Array.from(root.querySelectorAll(s));
  const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const arrow = '';
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
    function startReady(opener,area,screen,pattern,intent){
      if(!guideController)guideController=window.KanseiGuide(guideContext());
      guideController.start(opener,area,screen,pattern,intent);
    }
    function requestGuide(opener,area=null,screen=null,pattern=null,intent=null){
      const guideStyle='/assets/booking-guide.20261107.css';
      if(!$('link[href="'+guideStyle+'"]')){
        const style=document.createElement('link');style.rel='stylesheet';style.href=guideStyle;document.head.append(style);
      }
      if(window.KanseiGuide && window.KanseiAreas && window.KanseiGuideRoutes){startReady(opener,area,screen,pattern,intent);return;}
      const ticket=++requestTicket;
      content.innerHTML='<h2 id="guide-title" tabindex="-1">Bokningshjälp</h2><p class="guide-loading" role="status">Öppnar guiden…</p><p class="guide-small">Du kan också läsa om besöken eller boka direkt utan guiden.</p><div class="guide-error-links"><a class="text-link" href="/boka/">Se besök och priser '+arrow+'</a><a class="text-link" href="'+booking+'" target="_blank" rel="noopener noreferrer">Öppna Bokadirekt '+arrow+'</a></div>';
      openDialog(guide,opener);$('#guide-title',content)?.focus({preventScroll:true});
      Promise.all([loadScript(featureUrls.areaSrc,'KanseiAreas'),loadScript(featureUrls.guideSrc,'KanseiGuide'),loadScript('/assets/guide-routes.20261107.js','KanseiGuideRoutes')]).then(()=>{
        if(abort.signal.aborted || !guide.open || ticket!==requestTicket)return;
        startReady(opener,area,screen,pattern,intent);
      }).catch(()=>{
        if(abort.signal.aborted || !guide.open || ticket!==requestTicket)return;
        const loading=$('.guide-loading',content);if(loading)loading.textContent='Guiden kunde inte öppnas. Du kan fortfarande välja besök och boka via länkarna nedan.';
      });
    }
    if(guide && currentRoute==='/hjalp-mig-boka/'){
      const entry={'#ultraljud':'investigate','#injektioner':'injection'}[location.hash];
      const entryLink=entry && $('[data-guide-intent="'+entry+'"]');
      if(entryLink)requestGuide(entryLink,null,null,null,entry);
    }
    $$('[data-area]').forEach(b=>listen(b,'click',e=>{e.preventDefault();requestGuide(b,b.dataset.area,null,b.dataset.initialPattern||null);}));
    $$('[data-start-guide]').forEach(b=>listen(b,'click',e=>{e.preventDefault();requestGuide(b,null,null,null,b.dataset.guideIntent||null);}));
    $$('[data-services]').forEach(b=>listen(b,'click',e=>{e.preventDefault();requestGuide(b,null,'services');}));
    $$('[data-care]').forEach(b=>listen(b,'click',e=>{e.preventDefault();requestGuide(b,null,'care');}));

    listen(document.body,'click',event=>{
      const a=event.target.closest('a');if(!a)return;
      if(window.KanseiMeasure===true){
        let destination=null;try{destination=new URL(a.href,location.href);}catch{}
        if(destination?.hostname==='www.bokadirekt.se' && /48847/.test(destination.pathname) && a.dataset.measure!=='ignore' && (a.dataset.measure==='booking_click' || destination.pathname.startsWith('/boka-tjanst/') || /\bboka\b|lediga tider|välj tid|öppna bokadirekt/i.test(a.getAttribute('aria-label') || a.textContent || '')) && !/omdöme|recension|betyg|reviews|ratings/i.test(a.getAttribute('aria-label') || a.textContent || '')){
          const serviceId=destination.pathname.startsWith('/boka-tjanst/')?destination.pathname.match(/-(\d+)\/?$/)?.[1]:null;
          const service=({'3263299':'naprapathy','1946824':'ultrasound','3409516':'hyaluron','3478216':'hyaluron','3409514':'prp','3409513':'consultation','1952697':'wellness'})[serviceId] || 'general';
          const placement=a.dataset.placement || (a.closest('.site-header')?'header':a.closest('.footer')?'footer':a.closest('#guide-dialog')?'guide':a.closest('#site-menu')?'menu':'content');
          // A fixed service category only; no raw URL, body area, symptom or booking outcome.
          document.dispatchEvent(new CustomEvent('kansei:booking-intent',{detail:{event:'booking_click',service,audience:a.dataset.audience==='clinician'?'clinician':'visitor',placement:['header','footer','guide','menu','content','price_list','article_visit','case_card','service_card'].includes(placement)?placement:'content',version:'business-v3'}}));
        }
      }
      if(a.closest('dialog') && !a.closest('dialog').classList.contains('menu-minimal') && !a.hasAttribute('data-close'))closeDialog(a.closest('dialog'));
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
    const visual=$('.finder-visual'),hoverLabel=$('#finder-hover-label'),defaultFinderLabel=hoverLabel?.innerHTML;
    const setHover=k=>{if(visual && hoverLabel){visual.classList.add('is-active');hoverLabel.textContent=$('[data-area="'+k+'"]>span:nth-child(2)')?.textContent || 'Vi ser hela dig.';}};
    const resetHover=()=>{if(visual && hoverLabel){visual.classList.remove('is-active');hoverLabel.innerHTML=defaultFinderLabel;}};
    $$('.area-item[data-area]').forEach(b=>{listen(b,'pointerenter',()=>setHover(b.dataset.area));listen(b,'focus',()=>setHover(b.dataset.area));listen(b,'pointerleave',()=>{if(document.activeElement!==b)resetHover();});listen(b,'blur',resetHover);});

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

/* Native dialog with a short, cancellable transition; no layout jump or library. */
(()=>{'use strict';
 const dialog=document.querySelector('#site-menu'),buttons=[...document.querySelectorAll('[data-site-menu]')];
 const injectionNav=document.querySelector('.desktop-nav a[href="/hyaluronsyra/"]');
 if(injectionNav){
  injectionNav.href='/injektioner/';injectionNav.textContent='Injektioner';injectionNav.removeAttribute('aria-current');
 }
 // Keep the image overview discoverable from every public clinic menu.
 const imageMenu=dialog?.querySelector('.menu-secondary');
 if(imageMenu&&!imageMenu.querySelector('a[href="/ultraljud/bilder/"]')){
  const link=document.createElement('a');link.href='/ultraljud/bilder/';link.textContent='Ultraljud i bild';
  if(location.pathname==='/ultraljud/bilder/')link.setAttribute('aria-current','page');
  imageMenu.append(link);
 }
 // Present a small first level; keep existing destinations in focused detail panes.
 if(dialog){
  const body=dialog.querySelector('.site-menu-body'),primary=dialog.querySelector('.menu-primary'),bottom=dialog.querySelector('.menu-bottom');
  if(body&&primary&&bottom){
   const element=(tag,className,text)=>{const el=document.createElement(tag);if(className)el.className=className;if(text)el.textContent=text;return el;};
   const graphic=(paths,className,viewBox='0 0 24 24')=>{
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('viewBox',viewBox);svg.setAttribute('class',className);svg.setAttribute('aria-hidden','true');svg.setAttribute('focusable','false');
    paths.forEach(d=>{const path=document.createElementNS(svg.namespaceURI,'path');path.setAttribute('d',d);svg.append(path);});return svg;
   };
   const chevron=()=>graphic(['m9 6 6 6-6 6'],'menu-chevron');
   const existing=new Map();dialog.querySelectorAll('a[href]').forEach(a=>{if(!existing.has(a.getAttribute('href')))existing.set(a.getAttribute('href'),a);});
   function route(href,label,copy=false){
    const source=existing.get(href),a=source?(copy?source.cloneNode(true):source):element('a');
    a.href=href;a.className='menu-route';a.replaceChildren(element('span','',label),chevron());return a;
   }
   const sections=['.menu-secondary','.menu-practical'].map(selector=>dialog.querySelector(selector)).filter(Boolean);
   const contact=bottom.querySelector('p'),book=bottom.querySelector('.button'),help=existing.get('/hjalp-mig-boka/');
   const brand=dialog.querySelector('.site-menu-head>a');
   if(brand){brand.replaceChildren(element('span','menu-brand-name','Kansei'),element('span','menu-brand-caption','Naprapati & Rehabcenter'));brand.setAttribute('aria-label','Kansei Naprapati & Rehabcenter, startsida');}
   const stage=element('div','menu-stage'),views=new Map(),choices=new Map();
   const root=element('section','menu-view menu-view-root');root.dataset.menuView='root';root.id='menu-view-root';root.setAttribute('aria-label','Meny');views.set('root',root);
   const navigation=element('nav','menu-root-nav');navigation.setAttribute('aria-label','Välj besök eller klinikinformation');
   [['ultraljud','Ultraljud'],['injektioner','Injektioner'],['naprapati','Naprapati'],['kliniken','Kliniken & ditt besök']].forEach(([key,label])=>{
    const button=element('button','menu-choice'+(key==='kliniken'?' menu-choice-practical':''));button.type='button';button.dataset.menuTarget=key;button.setAttribute('aria-controls','menu-view-'+key);
    button.append(element('span','',label),chevron());choices.set(key,button);navigation.append(button);
   });
   const art=element('div','menu-root-art');art.setAttribute('aria-hidden','true');
   art.append(graphic([
    'M218 24C165-8 94 24 70 84s-17 116 28 143c45 27 111 16 139-34s31-137-19-169Z',
    'M201 48C161 26 116 51 98 96s-13 82 19 104c32 22 75 10 95-26s25-102-11-126Z',
    'M184 74C157 61 135 80 125 110s-6 51 14 63c20 12 42 2 55-20s14-65-10-79Z'
   ],'menu-contours','0 0 280 280'));
   root.append(navigation,art,element('p','menu-root-location','Upplandsgatan 26 · Odenplan'));stage.append(root);
   function pane(key,title,description){
    const view=element('section','menu-view');view.id='menu-view-'+key;view.dataset.menuView=key;view.hidden=true;view.inert=true;view.setAttribute('aria-labelledby','menu-title-'+key);
    const back=element('button','menu-back');back.type='button';back.dataset.menuBack='';back.setAttribute('aria-label','Tillbaka till menyn');back.append(chevron(),element('span','','Tillbaka'));
    const heading=element('h2','menu-view-title',title);heading.id='menu-title-'+key;heading.tabIndex=-1;
    const intro=element('p','menu-view-intro',description),links=element('nav','menu-route-list');links.setAttribute('aria-label',title);
    view.append(back,heading,intro,links);views.set(key,view);stage.append(view);return {view,links};
   }
   const us=pane('ultraljud','Ultraljud','Välj det område du vill undersöka.');
   us.links.append(route('/ultraljud/axel/','Axel'),route('/ultraljud/kna/','Knä'),route('/ultraljud/','Alla områden'));
   const injections=pane('injektioner','Injektioner','Läs om hyaluron och PRP, se priser och boka.');
   injections.links.append(route('/hyaluronsyra/','Hyaluron'),route('/prp/','PRP (ACP)'),route('/injektioner/','Alla injektioner'));
   const nap=pane('naprapati','Naprapati','Undersökning, behandling och rehabilitering.');
   nap.links.append(route('/naprapati/','Om naprapati & rehab'),route('/priser/','Besök och priser',true));
   const clinic=pane('kliniken','Kliniken & ditt besök','Praktisk information inför ditt besök.');
   clinic.links.append(route('/priser/','Priser'),route('/om-oss/','Om kliniken'),route('/kontakt/','Kontakt & hitta hit'),route('/patientinformation/','Inför besöket'));
   const more=element('details','menu-more');more.append(element('summary','','Mer på Kansei'));sections.forEach(section=>more.append(section));if(contact){contact.className='menu-contact';more.append(contact);}clinic.view.append(more);
   if(book){book.textContent='Boka besök';book.setAttribute('aria-label','Boka besök på Bokadirekt');}
   if(help)help.className='menu-booking-help';
   bottom.replaceChildren(...[book,help].filter(Boolean));dialog.append(bottom);body.replaceChildren(stage);
   dialog.classList.add('menu-refined','menu-minimal');dialog.dataset.menuActive='root';
   dialog.querySelector('[data-site-close]')?.setAttribute('autofocus','');
   dialog.querySelectorAll('a[href^="/"]').forEach(a=>{if(a.getAttribute('href')===location.pathname.replace(/index\.html$/,'').replace(/\/?$/,'/'))a.setAttribute('aria-current','page');});

   const reduced=()=>matchMedia('(prefers-reduced-motion: reduce)').matches;
   let opener=null,closing=false,timer=null,current='root',lastChoice=null,rootScroll=0,viewToken=0,animations=[],destination=null;
   function stopPaneMotion(){viewToken++;animations.forEach(a=>a.cancel());animations=[];delete dialog.dataset.menuTransition;}
   function showOnly(key){views.forEach((view,name)=>{view.hidden=name!==key;view.inert=name!==key;});current=key;dialog.dataset.menuActive=key;}
   function reset(){stopPaneMotion();more.open=false;views.forEach(view=>view.scrollTop=0);showOnly('root');lastChoice=null;rootScroll=0;}
   function changeView(key){
    if(!views.has(key)||key===current||closing||dialog.dataset.menuTransition)return;
    const from=views.get(current),to=views.get(key),back=key==='root';
    if(!back){lastChoice=choices.get(key);rootScroll=from.scrollTop;}
    stopPaneMotion();const token=viewToken;current=key;dialog.dataset.menuActive=key;dialog.dataset.menuTransition='true';
    views.forEach(view=>{view.inert=true;if(view!==from&&view!==to)view.hidden=true;});to.hidden=false;to.scrollTop=back?rootScroll:0;
    const finish=()=>{if(token!==viewToken||closing)return;showOnly(key);const completed=animations;animations=[];completed.forEach(a=>a.cancel());delete dialog.dataset.menuTransition;const focus=back?lastChoice:to.querySelector('.menu-view-title');focus?.focus({preventScroll:true});if(back)focus?.scrollIntoView({block:'nearest',inline:'nearest',behavior:'instant'});};
    if(reduced()||typeof to.animate!=='function'){finish();return;}
    // Let the old view leave before the next one settles; keep the frame still.
    const direction=back?-1:1;
    animations=[from.animate([{opacity:1,transform:'translateX(0)'},{opacity:0,transform:'translateX('+(-6*direction)+'px)'}],{duration:180,easing:'cubic-bezier(.4,0,1,1)',fill:'both'}),to.animate([{opacity:0,transform:'translateX('+(8*direction)+'px)'},{opacity:1,transform:'translateX(0)'}],{duration:360,delay:60,easing:'cubic-bezier(.25,.1,.25,1)',fill:'both'})];
    Promise.all(animations.map(a=>a.finished.catch(()=>{}))).then(finish);
   }
   function finishClose(){clearTimeout(timer);if(dialog.open)dialog.close();}
   function close(){
    if(!dialog.open||closing)return;
    closing=true;stopPaneMotion();showOnly(current);dialog.classList.add('is-leaving');
    if(reduced()){finishClose();return;}
    timer=setTimeout(finishClose,500);
   }
   choices.forEach((button,key)=>button.addEventListener('click',()=>changeView(key)));
   dialog.querySelectorAll('[data-menu-back]').forEach(button=>button.addEventListener('click',()=>changeView('root')));
   buttons.forEach(button=>button.addEventListener('click',()=>{
    if(dialog.open){close();return;}
    clearTimeout(timer);destination=null;opener=button;closing=false;dialog.classList.remove('is-leaving');reset();document.body.classList.add('locked');
    buttons.forEach(b=>b.setAttribute('aria-expanded','true'));dialog.showModal();views.get('root').scrollTop=0;
   }));
   dialog.querySelector('[data-site-close]').addEventListener('click',close);
   dialog.addEventListener('animationend',event=>{if(event.target===dialog&&closing&&event.animationName==='minimal-menu-out')finishClose();});
   dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
   dialog.addEventListener('close',()=>{
    clearTimeout(timer);stopPaneMotion();closing=false;dialog.classList.remove('is-leaving');document.body.classList.remove('locked');buttons.forEach(b=>b.setAttribute('aria-expanded','false'));
    const next=destination;destination=null;if(opener?.isConnected)opener.focus({preventScroll:true});if(next)location.assign(next);
   });
   dialog.addEventListener('click',event=>{
    const a=event.target.closest('a[href]');
    if(a){
     if(event.defaultPrevented||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey||event.button!==0||a.hasAttribute('download'))return;
     const url=new URL(a.href,location.href);
     if((!a.target||a.target==='_self')&&['http:','https:'].includes(url.protocol)){event.preventDefault();destination=url.href;}
     close();return;
    }
    const rect=dialog.getBoundingClientRect();if(event.target===dialog&&(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom))close();
   });
   dialog.addEventListener('keydown',event=>{
    if(event.key!=='Tab')return;
    const items=[...dialog.querySelectorAll('a[href],button:not([disabled]),summary,[tabindex="0"]')].filter(el=>!el.closest('[inert],[hidden]')&&el.getClientRects().length);
    const first=items[0],last=items.at(-1);if(!first)return;
    if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
   });
  }
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
