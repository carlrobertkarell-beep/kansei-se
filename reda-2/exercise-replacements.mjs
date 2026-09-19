const words=s=>String(s||'').toLocaleLowerCase('sv-SE').replace(/[^a-zåäö0-9 ]/g,' ').split(/\s+/).filter(x=>x.length>2);
const regionTokens=s=>new Set(words(s));
const equipmentPenalty=(candidate,current)=>{const a=new Set(words(candidate?.equipment)),b=new Set(words(current?.equipment));return [...a].some(x=>!b.has(x))?1:0};
export function replacementCandidates(current,library,{compatible=()=>true,limit=5}={}){
 if(!current||!Array.isArray(library))return[];
 const region=regionTokens(current.region),purpose=new Set(words(current.purpose||current.why)),name=new Set(words(current.name));
 return library.filter(e=>e.id!==current.id&&e.variants?.some(compatible)).map(e=>{const er=regionTokens(e.region),ep=new Set(words(e.purpose)),en=new Set(words(e.name));let score=0;for(const x of region)if(er.has(x))score+=6;for(const x of purpose)if(ep.has(x))score+=3;for(const x of name)if(en.has(x))score+=1;score-=equipmentPenalty(e,current);return {id:e.id,name:e.name,region:e.region||'',purpose:e.purpose||'',equipment:e.equipment||'',score,reason:score>=6?'Samma område · passar valda förutsättningar':score>=3?'Liknande funktion · passar valda förutsättningar':'Passar valda förutsättningar'}}).filter(x=>x.score>0).sort((a,b)=>b.score-a.score||a.name.localeCompare(b.name,'sv-SE')).slice(0,limit);
}
