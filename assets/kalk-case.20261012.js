function updateDetailComparison(anatomy){
 const mode=anatomy?'anatomy':'ultrasound';
 document.querySelectorAll('.detail-window').forEach(window=>{
  const side=window.dataset.detailSide;
  const source=document.querySelector('#view-'+side+' '+(anatomy?'.anatomy-layer img':'.original'));
  const image=window.querySelector('img');
  if(!source||!image)return;
  const [x,y,width,height]=window.dataset[anatomy?'cropAnatomy':'cropUltrasound'].split(',').map(Number);
  image.src=source.src;
  image.style.width=1280/width*100+'%';image.style.height=960/height*100+'%';
  image.style.left=-x/width*100+'%';image.style.top=-y/height*100+'%';
  window.dataset.mode=mode;
 });
}

const tabs=[...document.querySelectorAll('[role="tab"]')];
const panels=[...document.querySelectorAll('[role="tabpanel"]')];
const bar=document.querySelector('.modebar'), status=document.querySelector('.mode-status');
const anatomyToggle=document.getElementById('anatomy-toggle');
let selected=0, anatomy=false;
const comparison=document.querySelector('.detail-comparison');
const states={kalk:{ultrasound:'Höger axel · originalbild',anatomy:'Höger axel · anatomisk illustration'},frisk:{ultrasound:'Vänster axel · frisk jämförelsesida',anatomy:'Vänster axel · anatomisk illustration'}};
function updateMode(){const p=panels[selected],pic=p.querySelector('.patient-picture');if(!pic)return;const mode=anatomy?'anatomy':'ultrasound';pic.dataset.mode=mode;anatomyToggle.setAttribute('aria-checked',String(anatomy));status.textContent=states[p.dataset.side][mode];pic.querySelector('.anatomy-layer').setAttribute('aria-hidden',String(!anatomy));updateDetailComparison(anatomy);}
function activate(i,focus=false){selected=i;tabs.forEach((t,j)=>{t.setAttribute('aria-selected',String(j===i));t.tabIndex=j===i?0:-1});panels.forEach((p,j)=>{p.hidden=j!==i;p.querySelectorAll('video').forEach(v=>v.pause())});bar.hidden=i>1;if(i<2){panels[i].querySelector('.panel-media').append(comparison);updateMode()}if(focus)tabs[i].focus()}
tabs.forEach((t,i)=>{t.addEventListener('click',()=>activate(i));t.addEventListener('keydown',e=>{let n=i;if(e.key==='ArrowRight')n=(i+1)%tabs.length;else if(e.key==='ArrowLeft')n=(i+tabs.length-1)%tabs.length;else if(e.key==='Home')n=0;else if(e.key==='End')n=tabs.length-1;else return;e.preventDefault();activate(n,true)})});
anatomyToggle.addEventListener('click',()=>{anatomy=!anatomy;updateMode()});
activate(0);
