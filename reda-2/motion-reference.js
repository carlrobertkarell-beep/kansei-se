(function(){'use strict';const F=window.RedaFigures;
const examples=[
 ['sit-to-stand.support','Uppresning från stol','Fötterna står kvar. Överkroppen kommer fram innan höften lämnar stolen.','Granska handstödet och övergången från sittande till stående.'],
 ['knee-extension.pause','Benspark från stol','Låret ligger stilla medan underbenet roterar kring knät.','Granska knäets läge, slutsträckning och pausen.'],
 ['calf-raise.bilateral','Tåhävning','Framfoten behåller kontakten med golvet när hälen lyfter.','Granska fotens rotation, kroppens förflyttning och handstödet.'],
 ['bridge.pause','Höftlyft','Skuldror och fötter ligger kvar när bäckenet höjs.','Granska bäckenets höjd, knävinkel och återgång till underlaget.'],
 ['step-up.supported','Step-up','Den främre foten står på steget när kroppen höjs och det bakre benet följer med.','Granska viktöverföring, fotplacering och återgång.'],
 ['leg-press.bilateral','Benpress','Rygg och bäcken ligger kvar mot stödet när plattan förs bort.','Granska fotkontakt, knäets rörelse och den kontrollerade återgången. Maskinens inställning anpassas individuellt.'],
 ['split-squat.rfess-loaded','Split squat med bakre fot på bänk','Främre foten står kvar medan kroppen sänks och höjs.','Granska avståndet till bänken, balans och rörelsedjup. Illustrationen visar yttre belastning, inte en ordinerad vikt.']
];
const root=document.getElementById('examples');examples.forEach(([key,name,cue,review],n)=>{
 const card=document.createElement('section');card.className='reference';card.innerHTML=`<div class="stage">${F.svg(key,0,'simultaneous',name)}</div><div class="details"><span class="number">0${n+1} / REFERENS</span><h2>${name}</h2><p>${cue}</p><div class="controls"><button class="primary play" type="button">Visa rörelsen</button><label><select aria-label="Hastighet för ${name}"><option value="7">Lugnt tempo</option><option value="12">Extra långsamt</option></select></label></div><div class="stills" role="group" aria-label="Rörelsens lägen för ${name}">${['Startläge','På väg','Slutläge'].map((x,i)=>`<button type="button" data-frame="${i/2}" aria-pressed="${i===0}">${x}</button>`).join('')}</div><p>${review}</p></div>`;
 root.append(card);const phase=document.createElement('p');phase.className='motion-phase';phase.textContent='Startläge';card.querySelector('.stage').append(phase);let stop=null;const stage=card.querySelector('.stage'),play=card.querySelector('.play');
 const pause=()=>{stop?.();stop=null;play.textContent='Visa rörelsen'};
 play.onclick=()=>{if(stop){pause();return}if(matchMedia('(prefers-reduced-motion: reduce)').matches){play.textContent='Välj ett stilla läge nedan';return}stop=F.animate(stage,key,{seconds:Number(card.querySelector('select').value),onPhase:label=>{if(phase.textContent!==label)phase.textContent=label}});play.textContent='Pausa rörelsen';card.querySelectorAll('[data-frame]').forEach(b=>b.setAttribute('aria-pressed','false'))};
 document.addEventListener('visibilitychange',()=>{if(document.hidden)pause()});new IntersectionObserver(entries=>{if(!entries[0].isIntersecting)pause()}).observe(card);
 card.querySelector('select').onchange=()=>{if(stop){pause();play.click()}};
 card.querySelectorAll('[data-frame]').forEach(b=>b.onclick=()=>{pause();stage.innerHTML=F.svg(key,Number(b.dataset.frame),'simultaneous',name);phase.textContent=b.textContent;stage.append(phase);card.querySelectorAll('[data-frame]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)))});
});})();
