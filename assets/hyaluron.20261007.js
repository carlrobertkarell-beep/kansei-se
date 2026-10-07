// Open the disclosure targeted by an in-page link, including a shared URL.
(function(){
 function reveal(){
  var id;try{id=decodeURIComponent(location.hash.slice(1));}catch(e){return;}
  if(!id)return;
  var target=document.getElementById(id);if(!target)return;
  var details=target.closest('details');if(details)details.open=true;
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',reveal);else reveal();
 window.addEventListener('hashchange',reveal);
})();
