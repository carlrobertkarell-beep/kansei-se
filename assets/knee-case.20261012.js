(()=>{
 const viewer=document.querySelector('[data-knee-viewer]');if(!viewer)return;
 const tabs=[...viewer.querySelectorAll('[role="tab"]')],panels=[...viewer.querySelectorAll('[role="tabpanel"]')];
 const anatomySwitch=viewer.querySelector('[data-knee-anatomy]'),findingSwitch=viewer.querySelector('[data-knee-findings]'),status=viewer.querySelector('.knee-state');
 let selected=0,anatomy=false,findings=false;
 function render(){
  panels.forEach((panel,i)=>{panel.hidden=i!==selected;const picture=panel.querySelector('.knee-picture');picture.dataset.anatomy=String(anatomy);picture.dataset.findings=String(findings);picture.querySelector('.knee-anatomy').setAttribute('aria-hidden',String(!anatomy));picture.querySelector('.knee-findings').setAttribute('aria-hidden',String(!findings));if(i!==selected)panel.querySelectorAll('video').forEach(video=>video.pause());});
  tabs.forEach((tab,i)=>{tab.setAttribute('aria-selected',String(i===selected));tab.tabIndex=i===selected?0:-1});
  anatomySwitch.setAttribute('aria-checked',String(anatomy));findingSwitch.setAttribute('aria-checked',String(findings));
  status.textContent=tabs[selected].querySelector('strong').textContent+' · '+(anatomy?'anatomisk illustration':'ultraljudsbild')+(findings?' med markering':'');
 }
 function select(index,focus=false){if(index<0||index>=tabs.length)return;selected=index;render();if(focus)tabs[index].focus();}
 tabs.forEach((tab,index)=>{tab.addEventListener('click',()=>select(index));tab.addEventListener('keydown',event=>{let next=index;if(event.key==='ArrowRight'||event.key==='ArrowDown')next=(index+1)%tabs.length;else if(event.key==='ArrowLeft'||event.key==='ArrowUp')next=(index+tabs.length-1)%tabs.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=tabs.length-1;else return;event.preventDefault();select(next,true)})});
 anatomySwitch.addEventListener('click',()=>{anatomy=!anatomy;render()});findingSwitch.addEventListener('click',()=>{findings=!findings;render()});
 document.querySelectorAll('[data-knee-select]').forEach(link=>link.addEventListener('click',()=>{const index=panels.findIndex(panel=>panel.dataset.key===link.dataset.kneeSelect);select(index);findings=true;render()}));
 const initial=new URLSearchParams(location.search).get('bild');if(initial){selected=Math.max(0,panels.findIndex(panel=>panel.dataset.key===initial));findings=true;}
 render();
})();
