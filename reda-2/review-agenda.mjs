const order={symptoms:0,contact:1,execution:2,exercise:3,training:4};
export function reviewAgenda({digest,delta,max=4}={}){
 if(!digest?.valid)return {valid:false,items:[]};
 const items=[],seen=new Set(),push=x=>{const key=x.kind+':'+(x.exerciseId||x.label);if(!seen.has(key)){seen.add(key);items.push(x)}};
 for(const f of digest.flags||[]){
  if(f.kind==='symptoms')push({kind:'symptoms',label:'Förändrade besvär eller funktion',detail:'Gå igenom patientens registrerade försämringssvar och sätt dem i kliniskt sammanhang.'});
  else if(f.kind==='contact')push({kind:'contact',label:'Patienten har bett om hjälp',detail:'Stäm av vad patienten vill ta upp. Registreringen är inte en bokning.'});
  else if(f.kind==='execution')push({kind:'execution',label:'Utförandet behöver stämmas av',detail:'Identifiera vilken övning eller instruktion som varit svår.'});
  else if(f.kind==='exercise')push({kind:'exercise',exerciseId:f.exerciseId,label:f.label,detail:f.detail||'Övningen har återkommande markeringar att granska.'});
 }
 for(const c of delta?.changes||[]){if(c.kind==='exercise')push({kind:'exercise',label:c.label,detail:'Registreringen har ändrats från '+c.before+' till '+c.after+'.'});else if(['symptoms','contact','execution'].includes(c.kind))push({kind:c.kind,label:c.label,detail:'Före: '+c.before+' · Nu: '+c.after+'.'})}
 items.sort((a,b)=>(order[a.kind]??9)-(order[b.kind]??9)||a.label.localeCompare(b.label,'sv-SE'));
 return {valid:true,items:items.slice(0,max),total:items.length,overflow:Math.max(0,items.length-max),empty:items.length===0};
}
