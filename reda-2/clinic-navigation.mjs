// Navigation owns visibility only. Patient forms and their unsaved work stay mounted.
export function mountClinicNavigation(app,{canNavigate=()=>true,onNavigate=()=>{}}={}){
 const byId=id=>document.getElementById(id);
 const icons={patients:'<circle cx="9" cy="8" r="3"/><path d="M3 20v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6m2 3a5 5 0 0 1 3 4v2"/>',attention:'<path d="M9 5h11M9 12h11M9 19h11m-17-14 1 1 2-2m-3 8 1 1 2-2m-3 8 1 1 2-2"/>',ei:'<path d="M4 7h16M4 17h16"/><circle cx="9" cy="7" r="3"/><circle cx="15" cy="17" r="3"/>',team:'<path d="M3 21h18M5 21V4h14v17M9 8h2m2 0h2M9 12h2m2 0h2M10 21v-5h4v5"/>',patient:'<path d="M8 4h8l4 4v12H4V4h4m0 8h8m-8 4h5"/>'};
 const labels={patients:'Patienter',attention:'Att hantera',ei:'EI och mandat',team:'Team och åtkomst',patient:'Öppen patient'};
 const sidebar=document.createElement('aside');sidebar.className='clinic-navigation';sidebar.setAttribute('aria-label','Klinikens navigation');
 sidebar.innerHTML='<button type="button" class="clinic-menu" aria-expanded="false" aria-controls="clinicNavPanel">Meny <span aria-hidden="true">☰</span></button><div id="clinicNavPanel" class="clinic-nav-panel"><p class="clinic-nav-label">Arbetsyta</p><nav aria-label="Huvudmeny">'+Object.entries(labels).map(([id,label])=>'<button type="button" data-clinic-view="'+id+'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">'+icons[id]+'</svg><span>'+label+'</span></button>').join('')+'</nav></div>';
 const content=document.createElement('div');content.className='clinic-content';content.id='clinicContent';
 const page=(id,title,description)=>{const el=document.createElement('section');el.id=id;el.className='clinic-page';el.tabIndex=-1;if(title){const h=document.createElement('h2');h.textContent=title;el.append(h);const p=document.createElement('p');p.className='clinic-page-intro';p.textContent=description;el.append(p)}content.append(el);return el};
 const pages={patients:page('registryPage'),patient:page('patientPage'),ei:page('eiPage','EI och mandat','Se vad EI får göra i den här arbetsytan.'),team:page('teamPage','Team och åtkomst','Hantera arbetsytans medlemmar och behörigheter.')};
 pages.patients.append(byId('decisionDashboard'),byId('clinicInbox'));
 pages.patient.append(byId('backToDashboard'),byId('clinicalWorkspace'));
 pages.ei.append(byId('eiSettings'));
 pages.team.append(byId('workspaceEmpty'),byId('workspaceTeam'));
 const bar=app.querySelector('.workspace-bar'),message=byId('workspaceMessage');
 content.prepend(message);sidebar.querySelector('.clinic-nav-panel').append(bar);
 app.prepend(sidebar,content);app.classList.add('with-navigation');
 let current='patients',lastList='patients',clinical=false,hasDashboard=false,hasPatient=false,availableEI=false;
 const menu=sidebar.querySelector('.clinic-menu'),panel=sidebar.querySelector('.clinic-nav-panel');
 const mobile=matchMedia('(max-width: 760px)');
 function closeMenu(){app.classList.remove('menu-open');menu.setAttribute('aria-expanded','false')}
 function show(view,{focus=false}={}){
  if(!(view in labels)||(!clinical&&view!=='team')||(view==='patient'&&!hasPatient)||(view==='ei'&&!availableEI))return;
  current=view;if(view==='patients'||view==='attention')lastList=view;
  const list=view==='patients'||view==='attention';
  app.dataset.clinicPage=view;
  app.classList.toggle('dashboard-mode',hasDashboard&&list);
  app.classList.toggle('patient-mode',hasDashboard&&view==='patient');
  byId('backToDashboard').classList.toggle('hidden',view!=='patient'||!hasDashboard);
  for(const [key,el] of Object.entries(pages))el.hidden=key==='patients'?!list:key==='patient'?!(view==='patient'||(list&&!hasDashboard)):key!==view;
  sidebar.querySelectorAll('[data-clinic-view]').forEach(b=>{if(b.dataset.clinicView===view)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});
  closeMenu();
  if(focus){const el=list?pages.patients:pages[view];el.focus({preventScroll:true});el.scrollIntoView({block:'start'})}
 }
 sidebar.querySelectorAll('[data-clinic-view]').forEach(b=>b.onclick=()=>{
  if(!canNavigate())return;
  const view=b.dataset.clinicView;
  if(view!==current)onNavigate(view);
  show(view,{focus:true});
 });
 menu.onclick=()=>{const open=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(open));app.classList.toggle('menu-open',open)};
 sidebar.addEventListener('keydown',e=>{if(e.key==='Escape'&&mobile.matches&&menu.getAttribute('aria-expanded')==='true'){closeMenu();menu.focus();e.preventDefault()}});
 // A hidden mobile disclosure must also disappear from keyboard navigation.
 function responsive(){panel.inert=mobile.matches&&menu.getAttribute('aria-expanded')!=='true'}
 new MutationObserver(responsive).observe(menu,{attributes:true,attributeFilter:['aria-expanded']});
 mobile.addEventListener('change',responsive);responsive();
 function setBusy(busy){sidebar.querySelectorAll('[data-clinic-view]').forEach(b=>b.disabled=busy)}
 function setPatient(value){hasPatient=value;sidebar.querySelector('[data-clinic-view="patient"]').hidden=!value}
 function configure(workspace,{dashboard=false,ei=false}={}){
  clinical=!!workspace?.clinical_access;hasDashboard=dashboard&&clinical;availableEI=ei&&clinical;setPatient(false);
  sidebar.querySelectorAll('[data-clinic-view]').forEach(b=>{b.hidden=b.dataset.clinicView==='patient'||(b.dataset.clinicView==='ei'?!availableEI:b.dataset.clinicView==='attention'?!hasDashboard:b.dataset.clinicView==='patients'?!clinical:false)});
  show(clinical?'patients':'team');
 }
 configure(null);
 return {configure,show,setBusy,setPatient,returnToList(){show(lastList)},get view(){return current}};
}
