/* Local presentation preferences only. No account, exercise or health data is stored here. */
(function(root){'use strict';
 const key='reda-presentation-v1',defaults={theme:'dark',text:'standard',motion:'system'};
 const allowed={theme:['dark','light','system'],text:['standard','large'],motion:['system','still']};
 function normalize(value){return Object.fromEntries(Object.entries(defaults).map(([k,v])=>[k,allowed[k].includes(value?.[k])?value[k]:v]))}
 function read(){try{return normalize(JSON.parse(root.localStorage.getItem(key)))}catch{return {...defaults}}}
 let value=read();const media=root.matchMedia('(prefers-color-scheme: dark)'),reduced=root.matchMedia('(prefers-reduced-motion: reduce)');
 function apply(){const d=root.document.documentElement,theme=value.theme==='system'?(media.matches?'dark':'light'):value.theme;d.dataset.redaTheme=theme;d.dataset.redaText=value.text;d.dataset.redaMotion=value.motion;d.style.colorScheme=theme;root.document.querySelector('meta[name="theme-color"]')?.setAttribute('content',theme==='dark'?'#141816':'#f5f7f2');root.dispatchEvent(new CustomEvent('reda:preferences',{detail:{...value}}))}
 root.RedaPreferences={get:()=>({...value}),set(patch){value=normalize({...value,...patch});let saved=true;try{root.localStorage.setItem(key,JSON.stringify(value))}catch{saved=false}apply();return saved},reducedMotion:()=>value.motion==='still'||reduced.matches};
 media.addEventListener('change',()=>{if(value.theme==='system')apply()});root.addEventListener('storage',e=>{if(e.key===key||e.key===null){value=read();apply()}});apply();
})(window);
