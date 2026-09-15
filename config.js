// Kansei sajtconfig. Ändra värdena här, spara, klart, alla sidor uppdateras.
window.KANSEI = {
  kampanjSlut: "30 september",
  bokning: "https://www.bokadirekt.se/places/kansei-rehabcenter-48847",
  halsningsvideo: ""
};

// Inkorgen för patientloggar. Oförändrad av Kansei-webbtestet.
window.KANSEI.inkorg = {
  url: "",
  anonKey: "",
  tabell: "loggar"
};

window.KANSEI.omdomen = { antal: 301, betyg: "4,8" };

// Staging design layer. Explicit allow-list so Reda, clinic workspace and patient routes are never touched.
(function(){
  var path = location.pathname.replace(/index\.html$/,'');
  var redesignedServices = [
    '/naprapati/','/ultraljud/','/prp/','/hyaluronsyra/','/kortison/',
    '/akupunktur/','/rehabilitering/','/injektioner/','/skuldra/'
  ];
  if (redesignedServices.indexOf(path) !== -1) {
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/assets/services.f69fa4d8bd34.css';
    document.head.appendChild(link);
  }
})();

document.addEventListener('DOMContentLoaded', function(){
  var o = window.KANSEI.omdomen || {};
  document.querySelectorAll('[data-omd-antal]').forEach(function(e){ e.textContent = o.antal; });
  document.querySelectorAll('[data-omd-betyg]').forEach(function(e){ e.textContent = o.betyg; });
  document.querySelectorAll('[data-count="289"]').forEach(function(e){ e.setAttribute('data-count', String(o.antal)); if(e.textContent==='0') e.textContent = '0'; });

  // Reda remains the inherited public product/information entry. No patient/clinic behavior is changed here.
  document.querySelectorAll('a.nav-reda').forEach(function(a){
    a.href='/reda-rehab/';
    a.setAttribute('title','Reda · rehab och träning. Kommer snart.');
  });

  // The listed mobile number is private. Do not present it as a normal call channel.
  // 1177/112 links are intentionally untouched.
  document.querySelectorAll('a[href^="tel:+46733988588"],a[href^="tel:0733988588"],a[href^="tel:+46%2073%20398%2085%2088"]').forEach(function(a){
    a.href='sms:+46733988588';
    if (/073|73 398|ring|telefon/i.test(a.textContent)) a.textContent='Skicka SMS';
    a.setAttribute('aria-label','Skicka SMS till Kansei');
  });
});

// Snabb väg till bokning högst upp på mobil: pris och tjänstens egen bokningsknapp direkt under rubriken.
document.addEventListener('DOMContentLoaded', function(){
  if (window.innerWidth > 860) return;
  var head = document.querySelector('header.page'); if (!head) return;
  var h1 = head.querySelector('h1'); if (!h1 || head.querySelector('.snabb-cta')) return;
  var egenL = [].slice.call(head.querySelectorAll('a[href*="bokadirekt"]')).filter(function(a){ return !a.closest('.tf-fot') && a.getBoundingClientRect().top < window.innerHeight * 0.95; });
  var egen = egenL.length > 0;
  if (!egen) {
    var n = head.nextElementSibling, steg = 0;
    while (n && steg < 2) {
      if (n.querySelectorAll) {
        var ls = [].slice.call(n.querySelectorAll('a[href*="bokadirekt"]'));
        if (ls.some(function(a){ return a.getBoundingClientRect().top < window.innerHeight * 0.95; })) { egen = true; break; }
      }
      n = n.nextElementSibling; steg++;
    }
  }
  if (egen && !head.querySelector('.tf-fot')) return;
  var st = document.createElement('style');
  st.textContent = '.snabb-cta{display:flex;align-items:center;gap:12px;margin:14px 0 4px;flex-wrap:wrap}.snabb-cta .tf-pris{font-family:var(--display,Georgia,serif);font-size:1.5rem;color:var(--ink,#10202A)}.snabb-cta .btn{white-space:nowrap}header.page.har-snabb .tjfakta .tf-fot{display:none}';
  document.head.appendChild(st);
  var tf = head.querySelector('.tf-fot');
  var el;
  if (tf) { el = tf.cloneNode(true); el.className = 'snabb-cta'; head.classList.add('har-snabb'); }
  else if (!document.body.classList.contains('kodad') && !/\/blogg\//.test(location.pathname) && !/^\/reda\/?/.test(location.pathname)) {
    el = document.createElement('div'); el.className = 'snabb-cta';
    el.innerHTML = '<a class="btn btn-teal" href="' + (window.KANSEI.bokning || 'https://www.bokadirekt.se/places/kansei-rehabcenter-48847') + '" target="_blank" rel="noopener" data-cta="snabb-generell">Boka tid →</a><span style="font-size:.86rem;color:var(--dim,#5B6B75)">Ingen remiss krävs</span>';
  }
  if (el) { var intro = head.querySelector('.intro'); (intro || h1).insertAdjacentElement('afterend', el); }
});
