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
 const symptoms=[...root.querySelectorAll('[data-atlas-symptom]')];
 const entries=[...root.querySelectorAll('[data-atlas-entry]')],groups=[...root.querySelectorAll('[data-atlas-group]')];
 const status=root.querySelector('[data-atlas-results]'),empty=root.querySelector('[data-atlas-empty]');
 const normalize=s=>s.toLocaleLowerCase('sv').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
 const stop=new Set('jag mig min mitt mina du din ditt dina har far det ar i pa vid nar och att en ett med for kan inte som till den de man hur varfor vad sa av efter under om'.split(' '));
 const aliases={};
 [
  ['arm','armen','armar','armarna'],['axel','axeln','axlar','axlarna'],['kna','knat','knaet','knan'],
  ['smarta','ont','smartor','vark','varken'],['lyft','lyfta','lyfter','lyften'],['hand','handen','hander','handerna'],
  ['domning','domningar','domnar','somnar','stickningar'],['natt','natten','nattlig','nattliga'],
  ['svullnad','svullet','svullen','svullnar','svullnaden'],['lopning','loper','springer','springa','joggar','jogga','jogging'],
  ['gang','ga','gar','promenad','promenader','promenaden'],['grepp','greppa','griper','greppet'],
  ['halsena','halsenan','akillessena','akilles','achilles'],['hyaluron','hyaluronsyra','hyaluroninjektion','hyaluroninjektioner'],
  ['sinovial','synovial'],['bar','bara'],['utsida','utsidan'],['insida','insidan'],['ta','tar']
 ].forEach(list=>list.forEach(word=>aliases[word]=list[0]));
 const tokens=s=>normalize(s).split(/\s+/).filter(w=>w&&!stop.has(w)).map(w=>aliases[w]||w);
 // HTML textContent joins adjacent elements without spaces on minified pages.
 // Read the visible editorial blocks separately so "senor"+"Ont" stays two words.
 const entryWords=new Map(entries.map(entry=>[entry,tokens(entry.dataset.search+' '+[...entry.querySelectorAll('small,h4,p')].map(el=>el.textContent).join(' '))]));
 const valid=new Set(links.map(a=>a.dataset.atlasRegion)),validSymptoms=new Set(symptoms.map(a=>a.dataset.atlasSymptom));
 let region='alla',symptom='alla';
 function render(){
  const words=tokens(input.value);let count=0;
  entries.forEach(entry=>{
   const tags=(entry.dataset.symptoms||'').split(' '),haystack=entryWords.get(entry);
   const match=(region==='alla'||entry.dataset.region===region)&&(symptom==='alla'||tags.includes(symptom))&&words.every(w=>haystack.some(term=>term===w||term.startsWith(w)));
   entry.hidden=!match;if(match)count++;
  });
  groups.forEach(group=>{group.hidden=![...group.querySelectorAll('[data-atlas-entry]')].some(entry=>!entry.hidden)});
  links.forEach(link=>{if(link.dataset.atlasRegion===region)link.setAttribute('aria-current','true');else link.removeAttribute('aria-current')});
  symptoms.forEach(link=>{if(link.dataset.atlasSymptom===symptom)link.setAttribute('aria-current','true');else link.removeAttribute('aria-current')});
  empty.hidden=count>0;
  const label=links.find(link=>link.dataset.atlasRegion===region)?.dataset.label||'Alla områden';
  const symptomLabel=symptoms.find(link=>link.dataset.atlasSymptom===symptom)?.textContent.trim();
  status.textContent=count+' av '+entries.length+' bildfall · '+label+(symptom!=='alla'?' · '+symptomLabel:'')+(words.length?' · sökning: '+input.value.trim():'');
 }
 function fromUrl(){const params=new URLSearchParams(location.search),value=params.get('omrade'),s=params.get('besvar');region=valid.has(value)?value:'alla';symptom=validSymptoms.has(s)?s:'alla';render()}
 function navigate(){const url=new URL(location.href);for(const [key,value] of [['omrade',region],['besvar',symptom]]){if(value==='alla')url.searchParams.delete(key);else url.searchParams.set(key,value)}url.hash='exempel';history.pushState({},'',url);render()}
 function ordinary(event){return event.button===0&&!event.metaKey&&!event.ctrlKey&&!event.shiftKey&&!event.altKey}
 links.forEach(link=>link.addEventListener('click',event=>{if(!ordinary(event))return;event.preventDefault();region=link.dataset.atlasRegion;navigate()}));
 symptoms.forEach(link=>link.addEventListener('click',event=>{if(!ordinary(event))return;event.preventDefault();symptom=link.dataset.atlasSymptom;navigate()}));
 input.addEventListener('input',render);
 root.querySelector('[data-atlas-reset]').addEventListener('click',()=>{input.value='';region='alla';symptom='alla';const url=new URL(location.href);url.searchParams.delete('omrade');url.searchParams.delete('besvar');history.replaceState({},'',url);render();input.focus()});
 window.addEventListener('popstate',fromUrl);root.querySelector('.atlas-search').hidden=false;fromUrl();
})();
