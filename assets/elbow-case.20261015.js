(()=>{
 const viewer=document.querySelector('[data-elbow-viewer]');if(!viewer)return;
 const tabs=[...viewer.querySelectorAll('[role=tab]')],panels=[...viewer.querySelectorAll('[role=tabpanel]')];
 const anatomySwitch=viewer.querySelector('[data-knee-anatomy]'),findingSwitch=viewer.querySelector('[data-knee-findings]'),status=viewer.querySelector('.knee-state');
 const zoom=document.getElementById('knee-zoom'),zoomFrame=zoom.querySelector('[data-knee-zoom-frame]'),zoomTitle=zoom.querySelector('[data-knee-zoom-title]'),zoomAnatomy=zoom.querySelector('[data-knee-zoom-anatomy]'),zoomFindings=zoom.querySelector('[data-knee-zoom-findings]');
 const ready=panels.map(()=>false),failed=panels.map(()=>false);
 const hasFindings=index=>panels[index].dataset.findingsAvailable==='true';
 let selected=0,anatomy=false,findings=false;
 function render(){
  const shown=anatomy&&ready[selected],marked=findings&&hasFindings(selected);
  panels.forEach((panel,i)=>{
   panel.hidden=i!==selected;
   const picture=panel.querySelector('.knee-picture'),painted=anatomy&&ready[i],hasMarkers=findings&&hasFindings(i);
   picture.dataset.anatomy=String(painted);picture.dataset.findings=String(hasMarkers);
   picture.querySelector('.knee-anatomy').setAttribute('aria-hidden',String(!painted));
   picture.querySelector('.knee-original').setAttribute('aria-hidden',String(painted));
   picture.querySelector('.knee-findings').setAttribute('aria-hidden',String(!hasMarkers));
   if(!picture.id)picture.id='elbow-picture-'+panel.dataset.key;
   panel.querySelector('.elbow-legend').hidden=!hasMarkers;
  });
  tabs.forEach((tab,i)=>{tab.setAttribute('aria-selected',String(i===selected));tab.tabIndex=i===selected?0:-1;});
  anatomySwitch.disabled=!ready[selected];anatomySwitch.setAttribute('aria-checked',String(shown));
  anatomySwitch.setAttribute('aria-controls',panels[selected].querySelector('.knee-picture').id);
  findingSwitch.hidden=!hasFindings(selected);findingSwitch.setAttribute('aria-checked',String(marked));
  findingSwitch.setAttribute('aria-controls',panels[selected].querySelector('.knee-picture').id);
  status.textContent=tabs[selected].querySelector('strong').textContent+' · '+(shown?'anatomisk illustration':'ultraljudsbild')+(marked?' med fyndmarkeringar':'')+(failed[selected]?' · anatomivyn kunde inte laddas':'');
  if(zoom.open){
   const picture=zoomFrame.querySelector('.knee-picture');
   picture.dataset.anatomy=String(shown);picture.dataset.findings=String(marked);
   picture.querySelector('.knee-anatomy').setAttribute('aria-hidden',String(!shown));
   picture.querySelector('.knee-original').setAttribute('aria-hidden',String(shown));
   picture.querySelector('.knee-findings').setAttribute('aria-hidden',String(!marked));
   zoomAnatomy.disabled=!ready[selected];zoomAnatomy.setAttribute('aria-checked',String(shown));
   zoomFindings.hidden=!hasFindings(selected);zoomFindings.setAttribute('aria-checked',String(marked));
  }
 }
 function select(index,focus=false){if(index<0||index>=tabs.length)return;selected=index;render();if(focus)tabs[index].focus({preventScroll:true});}
 function switchAnatomy(){if(!ready[selected])return;anatomy=!anatomy;render();}
 function switchFindings(){if(!hasFindings(selected))return;findings=!findings;render();}
 tabs.forEach((tab,index)=>{
  tab.addEventListener('click',()=>select(index));
  tab.addEventListener('keydown',event=>{let next;
   if(event.key==='ArrowRight'||event.key==='ArrowDown')next=(index+1)%tabs.length;
   else if(event.key==='ArrowLeft'||event.key==='ArrowUp')next=(index+tabs.length-1)%tabs.length;
   else if(event.key==='Home')next=0;else if(event.key==='End')next=tabs.length-1;else return;
   event.preventDefault();select(next,true);
  });
 });
 anatomySwitch.addEventListener('click',switchAnatomy);findingSwitch.addEventListener('click',switchFindings);
 viewer.querySelector('[data-knee-enlarge]').addEventListener('click',()=>{
  const picture=panels[selected].querySelector('.knee-picture').cloneNode(true);
  picture.removeAttribute('id');zoomFrame.dataset.key=panels[selected].dataset.key;zoomFrame.replaceChildren(picture);
  zoomTitle.textContent=tabs[selected].querySelector('strong').textContent+'. Förstorad bild';zoom.showModal();render();
 });
 zoom.querySelector('[data-knee-zoom-close]').addEventListener('click',()=>zoom.close());
 zoomAnatomy.addEventListener('click',switchAnatomy);zoomFindings.addEventListener('click',switchFindings);
 const initial=new URLSearchParams(location.search).get('bild');
 if(initial){const index=panels.findIndex(panel=>panel.dataset.key===initial);if(index>=0){selected=index;findings=hasFindings(index);}}
 render();
 panels.forEach((panel,index)=>{
  const image=panel.querySelector('.knee-anatomy img');image.loading='eager';
  const decoded=image.decode?image.decode():new Promise((resolve,reject)=>{
   if(image.complete&&image.naturalWidth)resolve();else{image.addEventListener('load',resolve,{once:true});image.addEventListener('error',reject,{once:true});}
  });
  decoded.then(()=>{ready[index]=true;render();}).catch(()=>{failed[index]=true;render();});
 });
})();
