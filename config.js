// Kansei sajtconfig. Ändra värdena här, spara, klart, alla sidor uppdateras.
window.KANSEI = {
  kampanjSlut: "30 september",   // visas i alla "t.o.m."-texter
  bokning: "https://www.bokadirekt.se/places/kansei-rehabcenter-48847"            // målet för generella Boka tid-knappar (tjänstespecifika länkar påverkas inte)
  ,halsningsvideo: ""             // sätt till "/assets/halsning.mp4" när videon är uppladdad
};

// Inkorgen för patientloggar. Tomt = lokal inkorg i webbläsaren (för test).
// Fyll i från Supabase-projektet (Settings > API) så skickas loggar dit i stället, utan mejl.
window.KANSEI.inkorg = {
  url: "",          // t.ex. "https://xyzabc.supabase.co"
  anonKey: "",      // "anon public"-nyckeln, är avsedd att ligga i klienten
  tabell: "loggar"
};

// Omdömen: ändra här när antalet växer, alla sidor uppdateras.
window.KANSEI.omdomen = { antal: 301, betyg: "4,8" };
document.addEventListener('DOMContentLoaded', function(){
  var o = window.KANSEI.omdomen || {};
  document.querySelectorAll('[data-omd-antal]').forEach(function(e){ e.textContent = o.antal; });
  document.querySelectorAll('[data-omd-betyg]').forEach(function(e){ e.textContent = o.betyg; });
  document.querySelectorAll('[data-count="289"]').forEach(function(e){ e.setAttribute('data-count', String(o.antal)); if(e.textContent==='0') e.textContent = '0'; });
  // Reda i huvudnavigationen är produkt-/informationsingången. Patientportalen nås separat från Reda-sidan.
  document.querySelectorAll('a.nav-reda').forEach(function(a){ a.href='/reda-rehab/'; a.setAttribute('title','Reda · rehabilitering mellan besöken'); });
});

// Startsidan: Reda ska vara en tydlig del av rehabiliteringskedjan utan att störa gamla patientportalen /reda/.
document.addEventListener('DOMContentLoaded', function(){
  if (location.pathname !== '/' && location.pathname !== '/index.html') return;
  var card = document.getElementById('planKort'); if (!card) return;
  var points = card.querySelector('.plan-punkter');
  if (points) points.innerHTML = '<li>Din individuella plan från behandlaren, i mobilen</li><li>Rätt variant, sida, dos och stöd samlat på ett ställe</li><li>Exercise Intelligence knyter ihop mål, utförande och återkoppling</li>';
  var h = card.querySelector('h3'); if (h) h.textContent = 'Reda håller ihop rehabiliteringen mellan besöken';
  var p = card.querySelector('.plan-text p'); if (p) p.textContent = 'Reda samlar din plan, hjälper dig genom träningen och följer hur kroppen svarar. Vi kallar grunden Exercise Intelligence: din kapacitet, ditt mål och din vardag ska prägla upplägget. Nästa version förbereds för lansering, med automatisk progression under utveckling inom behandlarens ramar.';
  var a = card.querySelector('.plan-text .btn');
  if (a) { a.href='/reda-rehab/'; a.textContent='Läs om Reda →'; }
  if (!card.querySelector('.reda-portal-link')) {
    var old=document.createElement('a'); old.className='reda-portal-link'; old.href='/reda/'; old.textContent='Har du redan ett Reda-program? Öppna patientportalen →'; old.style.cssText='display:block;margin-top:12px;font-size:.86rem;color:var(--dim,#5B6B75);text-decoration:underline;text-underline-offset:3px';
    card.querySelector('.plan-text').appendChild(old);
  }
});

// Rehabiliteringssidan: synka den publika Reda-beskrivningen med den säkra patientportalen.
document.addEventListener('DOMContentLoaded', function(){
  if (location.pathname !== '/rehabilitering/' && location.pathname !== '/rehabilitering/index.html') return;
  var card = document.getElementById('planKort'); if (!card) return;
  var img = card.querySelector('.plan-lockup');
  if (img) { img.src='/bilder/reda/lockup.svg?v=cross-20260910'; img.alt='Reda'; }
  var points = card.querySelector('.plan-punkter');
  if (points) points.innerHTML = '<li>Din individuella plan från behandlaren, i mobilen</li><li>Nivå, variant och dos väljs för den aktuella perioden</li><li>Återkoppling om kroppen, genomförandet och annan belastning</li>';
  var label = card.querySelector('.plan-et'); if (label) label.textContent='Reda · Exercise Intelligence';
  var h = card.querySelector('h3'); if (h) h.textContent='Du ska veta vad du tränar, varför och vad vi följer upp';
  var p = card.querySelector('.plan-text p');
  if (p) p.textContent='Exercise Intelligence är grunden vi utvecklar för en plan som hänger ihop med ditt mål, din kapacitet och hur träningen fungerar. Nästa version av Reda visar tydligt utförande och samlar återkoppling efter passen. Automatisk progression utvecklas och testas inom behandlarens ramar; den är ännu inte aktiverad för patienter.';
  var a = card.querySelector('.plan-text .btn');
  if (a) { a.href='/reda-rehab/'; a.textContent='Se hur Reda fungerar'; }
});

// Snabb väg till bokning högst upp på mobil: pris och tjänstens egen bokningsknapp direkt under rubriken.
document.addEventListener('DOMContentLoaded', function(){
  if (window.innerWidth > 860) return;
  var head = document.querySelector('header.page'); if (!head) return;
  var h1 = head.querySelector('h1'); if (!h1 || head.querySelector('.snabb-cta')) return;
  // sidor som redan har en bokningsknapp i sidhuvudet, eller direkt efter det, får ingen extra
  var egenL = [].slice.call(head.querySelectorAll('a[href*="bokadirekt"]')).filter(function(a){ return !a.closest('.tf-fot') && a.getBoundingClientRect().top < window.innerHeight * 0.95; });
  var egen = egenL.length > 0;
  if (!egen) { var n = head.nextElementSibling, steg = 0; while (n && steg < 2) { if (n.querySelectorAll) { var ls = [].slice.call(n.querySelectorAll('a[href*="bokadirekt"]')); if (ls.some(function(a){ return a.getBoundingClientRect().top < window.innerHeight * 0.95; })) { egen = true; break; } } n = n.nextElementSibling; steg++; } }
  if (egen && !head.querySelector('.tf-fot')) return;
  var st = document.createElement('style');
  st.textContent = '.snabb-cta{display:flex;align-items:center;gap:12px;margin:14px 0 4px;flex-wrap:wrap}.snabb-cta .tf-pris{font-family:var(--display,Georgia,serif);font-size:1.5rem;color:var(--ink,#10202A)}.snabb-cta .btn{white-space:nowrap}header.page.har-snabb .tjfakta .tf-fot{display:none}';
  document.head.appendChild(st);
  var tf = head.querySelector('.tf-fot');
  var el;
  if (tf) { el = tf.cloneNode(true); el.className = 'snabb-cta'; head.classList.add('har-snabb'); }
  else if (!document.body.classList.contains('kodad') && !/\/blogg\//.test(location.pathname) && !/^\/reda\//.test(location.pathname)) {
    el = document.createElement('div'); el.className = 'snabb-cta';
    el.innerHTML = '<a class="btn btn-teal" href="' + (window.KANSEI.bokning || 'https://www.bokadirekt.se/places/kansei-rehabcenter-48847') + '" target="_blank" rel="noopener" data-cta="snabb-generell">Boka tid →</a><span style="font-size:.86rem;color:var(--dim,#5B6B75)">Ingen remiss krävs</span>';
  }
  if (el) { var intro = head.querySelector('.intro'); (intro || h1).insertAdjacentElement('afterend', el); }
});
