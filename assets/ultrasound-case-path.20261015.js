// Open an existing ultrasound view directly from its clinical narrative.
(()=>{
 document.querySelectorAll('[data-case-view]').forEach(link=>{
  link.addEventListener('click',event=>{
   if(event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
   const tab=link.dataset.caseTab?document.getElementById(link.dataset.caseTab):null;
   if(tab?.getAttribute('role')==='tab')tab.click();
   const viewer=document.querySelector('[data-patient-viewer],[data-knee-viewer],[data-elbow-viewer],[data-achilles-viewer]');
   const findings=viewer?.querySelector('[data-patient-findings],[data-knee-findings]');
   if(link.dataset.caseFindings==='true'&&findings&&!findings.hidden&&!findings.disabled&&findings.getAttribute('aria-checked')!=='true')findings.click();
   if(tab)tab.focus({preventScroll:true});
  });
 });
})();
