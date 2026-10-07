(()=>{
  const root=document.querySelector('.ultrasound-hub');if(!root)return;
  const directories=[...root.querySelectorAll('.hub-directory')];
  const links=[...root.querySelectorAll('.hub-region,.hub-directory-link')];
  const input=root.querySelector('#ultrasound-search'),status=root.querySelector('#search-status');
  const normalize=s=>s.toLocaleLowerCase('sv').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
  let saved=null;
  function search(){
    const query=normalize(input.value.trim());
    if(query&&!saved)saved=directories.map(d=>d.open);
    let count=0;
    links.forEach(a=>{const match=!query||query.split(/\s+/).every(w=>normalize(a.textContent).includes(w));a.hidden=!match;if(match)count++});
    directories.forEach((d,i)=>{d.hidden=!!query&&![...d.querySelectorAll('a')].some(a=>!a.hidden);d.open=query?!d.hidden:saved?saved[i]:d.open});
    if(!query)saved=null;
    status.textContent=query?(count?`${count} ingångar matchar din sökning.`:'Ingen träff. Prova en kroppsdel eller kontakta oss för hjälp.'):'Välj ett område eller sök efter dina besvär.';
  }
  input.addEventListener('input',search);
  root.querySelector('#clear-ultrasound-search').addEventListener('click',()=>{input.value='';search();input.focus()});
  root.querySelector('.hub-search').hidden=false;search();
  function revealHash(){
    let id;try{id=decodeURIComponent(location.hash.slice(1))}catch{return}
    const target=document.getElementById(id);if(!target)return;
    for(let el=target;el;el=el.parentElement)if(el.tagName==='DETAILS')el.open=true;
    requestAnimationFrame(()=>target.scrollIntoView({block:'start'}));
  }
  window.addEventListener('hashchange',revealHash);if(location.hash)revealHash();
})();
