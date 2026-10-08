(()=>{document.querySelectorAll('[data-patient-viewer]').forEach(root=>{
 const modes=[...root.querySelectorAll('[data-patient-mode]')],select=root.querySelector('[data-patient-select]'),panels=[...root.querySelectorAll('.reader-panel')];
 function mode(value){modes.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.patientMode===value)));if(root.hasAttribute('data-paired-anatomy'))root.dataset.anatomy=String(value==='anatomy');else root.dataset.explained=String(value==='explained')}
 modes.forEach(b=>b.addEventListener('click',()=>mode(b.dataset.patientMode)));mode(modes[0]?.dataset.patientMode||'explained');
 function show(){panels.forEach(p=>{p.hidden=select&&p.id!==select.value;if(p.hidden)p.querySelectorAll('video').forEach(v=>v.pause())});const active=panels.find(p=>!p.hidden),hasAnnotation=!!active?.querySelector('.scan-annotation');if(!root.hasAttribute('data-paired-anatomy'))root.querySelector('.patient-choice').hidden=!hasAnnotation;}
 if(select)select.addEventListener('change',show);if(panels.length)show();
 });})();