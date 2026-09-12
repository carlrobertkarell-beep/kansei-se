import {cleanProgression,createAuthoringTools} from './plan-authoring-model.mjs?v=2';

export const sideLabels={left:'Vänster',right:'Höger',both:'Båda sidor, en i taget',simultaneous:'Båda samtidigt'};
export function prescriptionFacts(x){
 const dose=x.dose?.label||[x.dose?.sets&&x.dose.sets+' omgångar',x.dose?.reps&&x.dose.reps+' repetitioner',x.dose?.hold&&'håll '+x.dose.hold+' sekunder'].filter(Boolean).join(' · ');
 return [
  ['Utförande',x.variantLabel],['Sida',sideLabels[x.side]],['Dos',dose?dose+(x.side==='both'?' per sida':''):null],
  ['Vila mellan omgångar',Number.isFinite(x.dose?.rest)?x.dose.rest+' sekunder':null],
  ['Ordinerad belastning',x.prescribedLoad],['Ordinerat rörelseomfång',x.prescribedRange],
  ['Utrustning',x.equipment],['Stöd',x.support]
 ].filter(([,value])=>value!==undefined&&value!==null&&value!=='');
}
export function supportFor(answers={}){
 const choices={
  execution:{title:'Vi tar övningen steg för steg',detail:'Öppna instruktionen med rätt utförande, sida och dos från din plan.',action:'guide',label:'Visa min instruktion',next:'Din behandlare kan se vilken övning som var oklar och ta ställning till hjälp med utförandet.'},
  time:{title:'Gör plats för nästa pass',detail:'Titta på träningsdagarna i din plan och välj en tid som brukar fungera. Lägg fram det du behöver i förväg.',action:'schedule',label:'Se mina träningsdagar',next:'Din behandlare får underlag för att bedöma ett kortare upplägg. Du följer din aktuella dos tills ni har kommit överens om en ändring.'},
  equipment:{title:'Se vad övningen behöver',detail:'Kontrollera utrustning och stöd i din egen instruktion. Berätta för behandlaren vad som saknas om ett annat utförande behövs.',action:'guide',label:'Visa utrustning och utförande',next:'Din behandlare kan granska alternativ för exempelvis träning hemma, utan band eller utan golvövningar.'},
  energy:{title:'Orken är en del av underlaget',detail:'Ditt svar hjälper behandlaren att förstå varför passet var svårt. Det blir inte en bedömning av din motivation.',action:'contact',label:'Kontakta kliniken',next:'Din behandlare behöver bedöma situationen innan dosen ändras.'},
  symptoms:{title:'Ta kontakt om du behöver hjälp med besvären',detail:'Svaren i Reda bevakas inte i realtid. Kontakta kliniken direkt för råd om besvären och träningen.',action:'contact',label:'Kontaktuppgifter',next:'Ditt svar behöver bedömas av en behandlare. Reda ändrar inte belastningen utifrån det här svaret.'},
  other:{title:'Hjälp oss förstå vad som saknas',detail:'Din behandlare kan ställa en följdfråga i Reda. Du kan också kontakta kliniken och beskriva vad som gjorde träningen svår.',action:'contact',label:'Kontakta kliniken',next:'Ditt svar finns som underlag för en personlig bedömning.'}
 };
 return choices[answers.barrier]||(answers.support==='yes'?{title:'Din önskan om hjälp är sparad',detail:'Kliniken kan läsa din önskan om kontakt. Om du behöver hjälp nu, kontakta kliniken direkt.',action:'contact',label:'Kontakta kliniken',next:'Ett sparat svar bokar ingen tid och skickar inget sms eller mejl.'}:{title:'Ta med det som fungerade',detail:'Samma tid eller plats kan göra det lättare att komma ihåg nästa planerade pass.',action:'schedule',label:'Se mina träningsdagar',next:'Svaren finns i din historik. Hur kroppen svarade följs upp separat nästa dag.'});
}
export function roundCount(plan){return (plan.exercises||[]).reduce((sum,x)=>sum+(Number(x.dose?.sets)||0)*(x.side==='both'?2:1),0)}

// Clinician candidates only. No patient plan is changed or saved by these functions.
export function adaptationOptions(P,D,plan,barrier){
 if(!plan?.exercises?.length)return [];
 const T=createAuthoringTools(P,D),options=[];
 if(barrier==='time'&&plan.exercises.some(x=>x.dose.sets>1)){
  let next=cleanProgression(plan);
  next.exercises.forEach((x,i)=>{if(x.dose.sets>1)next=P.editExercise(next,i,{sets:x.dose.sets-1})});
  options.push({id:'less-rounds',title:'En omgång mindre',detail:'Behåll övningarna och minska med en omgång där det finns fler än en. Bedöm om den lägre träningsvolymen passar behandlingsmålet.',plan:T.recheck(next)});
 }
 if(barrier==='equipment')for(const [id,title,changes]of [['band','Utan gummiband',{band:false}],['floor','Utan golvövningar',{floorOK:false}],['home','Träning hemma',{equipment:'home'}]]){
  const next=T.adapt(plan,changes);
  next.warnings=[...new Set([...(plan.warnings||[]).filter(w=>!w.endsWith(': välj en ersättning som passar de nya förutsättningarna.')),...next.warnings])];
  if(JSON.stringify(plan.exercises)===JSON.stringify(next.exercises)&&!next.warnings.length)continue;
  for(const x of next.exercises){const old=plan.exercises.find(e=>e.id===x.id);if(old?.side!==x.side)next.warnings.push(x.name+': sidan ändras från '+(sideLabels[old?.side]||'okänd')+' till '+(sideLabels[x.side]||'okänd')+'. Välj ett utförande med rätt sida.');}
  options.push({id,title,detail:'Välj först vad som faktiskt saknas. Bytta utföranden får bibliotekets grunddos. Individuell belastning och rörelseomfång måste bedömas på nytt.',plan:next});
 }
 return options;
}
export function changedPrescriptions(before,after){
 return (after.exercises||[]).flatMap(x=>{const old=before.exercises.find(y=>y.id===x.id);if(!old||JSON.stringify(old)===JSON.stringify(x))return [];const a=new Map(prescriptionFacts(old)),b=new Map(prescriptionFacts(x));return [{name:x.name,fields:[...new Set([...a.keys(),...b.keys()])].filter(k=>a.get(k)!==b.get(k)).map(label=>({label,before:a.get(label)||'Inte angivet',after:b.get(label)||'Behöver bedömas på nytt'}))}]});
}

export function adaptationRequest(detail){
 if(detail.cases?.some(c=>c.code==='changed_symptoms'))return null;
 const c=detail.cases?.find(c=>['time','equipment'].includes(c.reflection?.answers?.barrier)&&c.reflection?.plan_id===detail.patient?.plan_id&&c.reflection?.plan_version===detail.patient?.plan_version);
 if(!c||!detail.token)return null;
 return {patientId:detail.patient.patient_id,planId:detail.patient.plan_id,planVersion:detail.patient.plan_version,token:detail.token,caseId:c.id,reflectionId:c.reflection.id};
}
export function verifyAdaptation(request,detail,record){
 if(!request||request.patientId!==detail.patient?.patient_id||request.token!==detail.token||request.planId!==detail.patient?.plan_id||request.planVersion!==detail.patient?.plan_version)throw Error('Underlaget har ändrats. Öppna patienten igen från överblicken för ett nytt förslag.');
 const c=detail.cases?.find(c=>c.id===request.caseId&&c.reflection?.id===request.reflectionId);
 if(!c||c.reflection.plan_id!==request.planId||c.reflection.plan_version!==request.planVersion||detail.cases.some(c=>c.code==='changed_symptoms'))throw Error('Patientsignalerna har ändrats och behöver bedömas på nytt.');
 if(record?.id!==request.planId||record?.version!==request.planVersion||record?.status!=='active')throw Error('Ett annat planutkast eller en annan planversion är öppnad. Granska den innan du gör en anpassning från det här svaret.');
 return c.reflection;
}
