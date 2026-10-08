/* Copies clinic information only. No patient inputs, persistence or requests. */
(()=>{'use strict';
 const button=document.querySelector('[data-copy-referral]');
 const text=document.querySelector('#ref-share-text');
 const status=document.querySelector('.ref-copy-status');
 if(!button||!text||!status)return;
 button.addEventListener('click',async()=>{
  try{if(!navigator.clipboard?.writeText)throw new Error('Clipboard unavailable');
   await navigator.clipboard.writeText(text.textContent.trim());status.textContent='Informationen är kopierad. Du kan klistra in den till patienten.';
  }catch{status.textContent='Kopiera texten ovan eller dela länken: https://www.kansei.se/for-vardgivare/';}
 });
})();
