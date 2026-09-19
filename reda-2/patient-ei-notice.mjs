const esc=s=>String(s??'');
export function planChangeNotice({current,previous,decision}={}){
 if(!current||!previous||current.id===previous.id)return null;
 const a=new Map((previous.payload?.exercises||[]).map(x=>[x.id,x])),changes=[];
 for(const x of current.payload?.exercises||[]){const old=a.get(x.id);if(!old){changes.push({name:x.name,detail:'Ny övning i planen'});continue}const bits=[];if(old.variantId!==x.variantId)bits.push('ny variant');if(old.side!==x.side)bits.push('sida ändrad');if(JSON.stringify(old.dose)!==JSON.stringify(x.dose))bits.push('dos ändrad');if(bits.length)changes.push({name:x.name,detail:bits.join(' · ')})}
 return {title:'Din plan har uppdaterats',changes:changes.slice(0,4),more:Math.max(0,changes.length-4),reason:decision?.code==='advance'?'Dina registrerade pass och uppföljningar uppfyllde villkoren i den plan din behandlare lagt upp.':decision?.code==='regress'?'Din plan har gått tillbaka till ett tidigare godkänt steg utifrån registrerade belastningsreaktioner.':'Din behandlingsplan har fått en ny version.'};
}
