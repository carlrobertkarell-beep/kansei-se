// Shared process rules. Completion is derived from evidence, never from a progress percentage.
const present=x=>typeof x==='string'&&x.trim().length>1;
const stable=x=>Array.isArray(x)?x.map(stable):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,stable(x[k])])):x;
export const planFingerprint=p=>JSON.stringify(stable(p?Object.fromEntries(['schema','blueprintId','blueprintName','authoring','context','exercises','goal','clinicianNote','presentation','schedule','reviewDate','careJourney','progressionDraft','progressionFrame','planOptions'].map(k=>[k,p[k]??null])):null));
export function planReadiness({audience='clinic',patient={},profile={},plan={},saved=null,active=null,reviewed='',sessions=[],responses=[],checks=[],careIssues=[],activationEnabled=false,deliveryMode='digital',selfConfirmed=false,selfNeedsAssessment=false}={}){
 const worksheet=audience==='worksheet',self=audience==='self',c=plan.context||{},fingerprint=planFingerprint(plan),same=r=>!!r&&planFingerprint(r.payload)===fingerprint;
 const steps=[],add=(id,label,done,detail,action,phase='prepare',blocked=false)=>steps.push({id,label,state:done?'done':blocked?'blocked':'todo',detail,action,phase});
 if(!worksheet)add('context',self?'Dina mål och förutsättningar':'Patientens mål och förutsättningar',present(plan.goal)&&(!self?present(profile.focus):selfConfirmed&&!selfNeedsAssessment)&&['stage','capacity','equipment'].every(k=>!!c[k])&&typeof c.floorOK==='boolean'&&typeof c.band==='boolean',self?(selfNeedsAssessment?'Rehab för besvär behöver bedömas tillsammans med en behandlare.':'Välj mål, startläge och var du vill träna.'):'Mål, fokus och praktiska förutsättningar ska vara angivna.','context','prepare',self&&selfNeedsAssessment);
 if(!worksheet&&!self&&deliveryMode!=='clinic')add('contact','Kontakt för digital överlämning',!!patient.auth_user_id||present(profile.email),'En ny anslutning använder e-post. Telefon räcker för registrering men inte för digital inbjudan.','contact');
 const problems=[...(plan.warnings||[]),...checks];
 add('plan','Övningar och dosering',!!plan.exercises?.length&&!problems.length&&!!plan.schedule?.days?.length,problems.length?problems.join(' '):'Övningar, dosering och träningsdagar ska vara valda.','plan');
 if(!worksheet&&!self)add('followup','Uppföljning och kontaktupplägg',!!(plan.reviewDate||plan.careJourney?.checkpoints?.some(x=>x.date))&&!careIssues.length,careIssues.length?careIssues.join(' '):'Välj nästa avstämning. Distansupplägg kräver även dokumenterad bedömning.','followup');
 const reviewedCurrent=reviewed===fingerprint||same(active);
 add('review',self?'Granska ditt upplägg':'Granska patientens innehåll',reviewedCurrent,'Kontrollera det aktuella innehållet. Ändringar gör att granskningen behöver göras igen.','review');
 if(!worksheet&&!self)add('saved','Aktuellt planutkast sparat',same(saved)||same(active),'Ett tidigare sparat utkast räcker inte om planen har ändrats.','save');
 const prepare=steps.filter(x=>x.phase==='prepare'),ready=prepare.every(x=>x.state==='done');
 if(!worksheet&&!self){
  const digital=deliveryMode!=='clinic';
  add('handover',digital?'Planen tillgänglig i Reda':'Överlämning på kliniken',digital&&same(active),digital?(activationEnabled?'Aktivera den granskade planen när underlaget är klart.':'Digital överlämning är inte öppnad för den här kliniken.'):'Utskrift är inte en bekräftelse på att patienten fått planen. Överlämna och gå igenom den tillsammans.',digital?'activate':'print','after',digital&&!activationEnabled&&!same(active));
  if(digital){
   add('first_session','Första passet registrerat',same(active)&&sessions.some(x=>x.plan_id===active.id&&x.status==='completed'),'Gäller den aktiva planversionen. Saknad registrering bevisar inte utebliven träning.','activity','after');
   add('response','Patientens återkoppling',same(active)&&responses.some(x=>x.plan_id===active.id),'Visar om återkoppling finns för den aktiva planversionen.','activity','after');
  }
 }
 const extras=[];
 if(!worksheet){if(!c.trainingHistory)extras.push({label:self?'Din träningsvana':'Tidigare träningsvana',detail:'Hjälper EI att skilja en ny start från fortsatt träning.',action:'context'});if(!plan.clinicianNote&&!self)extras.push({label:'Individuella råd',detail:'Gör det tydligare hur patienten ska genomföra just sin plan.',action:'advice'});if(c.capacity==='supported')extras.push({label:self?'Kontrollera stöd och utförande':'Kontrollera stödbehovet',detail:'Granska att övningarnas stöd och placering fungerar i träningsmiljön.',action:'review'});}
 const pendingAfter=steps.find(x=>x.phase==='after'&&x.state!=='done');
 return {audience,steps,extras,ready,completed:prepare.filter(x=>x.state==='done').length,total:prepare.length,next:prepare.find(x=>x.state!=='done')||(pendingAfter?.state==='todo'?pendingAfter:null)||null,fingerprint};
}
