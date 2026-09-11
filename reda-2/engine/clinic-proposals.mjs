/* EI working proposals are derived from saved evidence. Approval stays with the clinician. */
export const caseLabels={changed_symptoms:'Förändrade besvär eller funktion',changed_environment:'Ändrade förutsättningar',requested_contact:'Patienten önskar kontakt',execution_help:'Hjälp med utförandet'};
export const actionLabels={send_message:'Godkänn och skicka i Reda',follow_up:'Lägg i min arbetslista',complete_follow_up:'Spara genomförd uppföljning',resolve_cases:'Spara som bedömt',review_agree:'Spara min bedömning',review_disagree:'Spara avvikande bedömning',review_uncertain:'Spara att underlaget är otillräckligt',approve_frame:'Godkänn ramen i granskningsläge',evaluate:'Pröva underlaget'};
export function rowReason(p,today){
 if(p.open_count)return (p.codes||[]).map(c=>caseLabels[c]||c).join(' · ');
 if(p.new_reply)return 'Nytt svar från patienten';
 if(p.followup_status==='waiting')return 'Uppföljning '+(p.followup_date<=today?'idag eller försenad':p.followup_date);
 if(p.pending_messages)return 'Dialog med patienten behöver bedömas';
 if(p.pending_count)return 'Kvitterad återkoppling behöver bedömas';
 if(p.review_date&&p.review_date<=today)return 'Planerad avstämning behöver följas upp';
 if(p.missing_response)return 'Återkoppling saknas efter senaste passet';
 if(p.quiet)return 'Ingen ny registrering på sju dagar';
 if(!p.decision_applied&&!p.decision_reviewed&&['advance','complete','review'].includes(p.decision_action))return 'EI-prövning att ta ställning till';
 if(p.patient_status==='archived')return 'Arkiverad patient';
 if(!p.plan_id)return 'Ingen aktiv plan';
 return 'Inget nytt i arbetskön';
}
const nextDate=(day,n)=>{const date=new Date(day+'T12:00:00Z');date.setUTCDate(date.getUTCDate()+n);return date.toISOString().slice(0,10)};
export function propose(data){
 const p=data.patient,cases=data.cases||[],today=data.today,hasNew=cases.some(c=>c.status==='open');
 const follow=(title,note,why,due=today)=>({action:'follow_up',title,note,why,due,effect:'Lägger en uppföljning i din arbetslista och kvitterar nya signaler. Du ansvarar för kontakten. Ingen bokning eller patientkommunikation skickas.'});
 const ask=(title,message,why,fallback)=>p.connected&&p.patient_status==='active'?{action:'send_message',title,note:message,why,due:nextDate(today,1),effect:'Levererar det visade meddelandet i patientens Reda och lägger en uppföljning i din arbetslista. Patienten kan svara här. Inget mejl eller sms skickas.'}:fallback;
 if(hasNew||cases.length&&p.followup_status!=='waiting'){
  if(cases.some(c=>c.code==='changed_symptoms'))return follow('Följ upp den förändrade återkopplingen','Följ upp patientens rapport om förändrade besvär eller funktion och bedöm behovet av fortsatt åtgärd.','Patientens sparade svar beskriver en förändring. Ärendet behöver din bedömning innan det kan avslutas.');
  if(cases.some(c=>c.code==='changed_environment'))return ask('Fråga vad som har förändrats','Hej! Du har angett att förutsättningarna för träningen har ändrats. Vad har förändrats, och vilken övning gäller det? Svara här i Reda så kan vi stämma av din plan.','Patienten har rapporterat ändrade träningsförutsättningar. Förslaget samlar in det som behöver klargöras.',follow('Stäm av de ändrade förutsättningarna','Stäm av vilka träningsförutsättningar som har ändrats och om den aktuella ordinationen fortfarande är genomförbar.','Patienten har rapporterat ändrade förutsättningar. Ingen alternativ övning är godkänd genom detta förslag.'));
  if(cases.some(c=>c.code==='requested_contact'))return ask('Besvara patientens kontaktönskemål','Hej! Jag har fått ditt önskemål om kontakt. Vad vill du ha hjälp med? Svara gärna här i Reda så följer vi upp det.','Patienten har bett om kontakt. Ett svar kan skickas direkt i Reda.',follow('Följ upp patientens kontaktönskemål','Kontakta patienten med anledning av det sparade kontaktönskemålet.','Patienten har uttryckligen bett om kontakt.'));
  return ask('Hjälp patienten beskriva svårigheten','Hej! Vilken övning är svår att utföra, och i vilken del av rörelsen fastnar du? Beskriv gärna här i Reda så går vi igenom instruktionen tillsammans.','Återkopplingen säger att utförandet är svårt. En riktad fråga klargör vilken hjälp patienten behöver.',follow('Gå igenom utförandet med patienten','Stäm av vilken del av utförandet som är svår och gå igenom instruktionen i den aktuella planen.','Återkopplingen beskriver svårigheter med utförandet. Planens sparade instruktion finns i underlaget.'));
 }
 if(p.new_reply)return {action:'follow_up',title:'Bedöm patientens svar',note:'',due:today,why:'Ett nytt svar finns i dialogen nedan. Läs det och välj om du vill svara, planera fortsatt uppföljning eller dokumentera din bedömning.',effect:'Sparar din fortsatta hantering i arbetslistan. Dialogen behöver bedömas innan progression kan fortsätta.'};
 if(p.followup_status==='waiting')return {action:'complete_follow_up',title:'Dokumentera när uppföljningen är genomförd',note:'',why:p.followup_note||'En uppföljning finns i din arbetslista.',effect:'Markerar arbetsuppgiften som genomförd med din anteckning. Kvarvarande patientsignaler behöver fortfarande bedömas.'};
 if(data.prepared_frame&&!data.frame&&p.patient_status==='active')return {action:'approve_frame',title:'Granska och godkänn den förberedda vägen',note:'Jag har granskat samtliga förberedda steg och villkor för patienten och godkänner ramen i granskningsläge.',why:'En komplett progressionsram finns i den sparade aktuella ordinationen. Steg och villkor visas nedan.',effect:'Godkänner den visade ramen i granskningsläge. EI kan pröva underlaget; automatisk tillämpning är inte öppnad.'};
 if(p.patient_status==='active'&&data.frame&&(!data.decision||new Date(p.last_response)>new Date(data.decision.created_at)||new Date(p.last_session)>new Date(data.decision.created_at)))return {action:'evaluate',title:'Låt EI pröva det aktuella underlaget',note:'Pröva aktuellt sparat underlag mot den godkända progressionsramen.',why:'Det finns underlag som ännu inte ingår i den senaste EI-prövningen.',effect:'Sparar en ny prövning mot ramens villkor. Resultatet visas här direkt.'};
 if(p.patient_status==='active'&&data.decision&&!p.decision_reviewed&&['advance','complete'].includes(data.decision.action)&&!data.decision.applied)return {action:'review_agree',title:'Ta ställning till EI:s prövning',note:data.decision.action==='advance'?'Jag instämmer i att det sparade underlaget uppfyller villkoren för nästa steg i den godkända ramen.':'Jag instämmer i EI:s prövning av ramens sista steg.',why:'EI har prövat underlaget mot en tidigare godkänd ram. Kontrollera resultatet och välj ditt ställningstagande.',effect:'Sparar din bedömning för utvärdering av EI. Den aktiverar ingen ny plan och avslutar inga patientärenden.'};
 if(p.review_date&&p.review_date<=today)return follow('Följ upp planens avstämning','Följ upp avstämningen som är angiven i den aktuella planen. Dokumentera vad som redan har genomförts.','Planen innehåller ett passerat datum. Reda vet inte om kontakten redan har skett.');
 if(p.missing_response)return follow('Komplettera återkopplingen','Stäm av om patienten kan lämna nästa-dag-återkoppling för det senaste registrerade passet.','Ett avslutat pass finns, men dess nästa-dag-svar saknas. Det är inte samma sak som utebliven träning.',nextDate(today,1));
 if(p.quiet)return follow('Stäm av hur träningen fungerar','Stäm av hur träningen fungerar och om patienten behöver hjälp att registrera passen.','Ingen ny registrering har kommit in på sju dagar. Det säger inte säkert om patienten har tränat.',nextDate(today,1));
 if(p.patient_status==='active'&&data.decision&&!p.decision_reviewed&&data.decision.action==='review')return follow('Komplettera underlaget för EI-prövningen','Stäm av det underlag som EI har markerat för bedömning innan en ny prövning görs.','Den sparade prövningen anger att underlaget behöver bedömas eller kompletteras.');
 return {action:null,title:p.plan_id?'Fortsätt följa patienten':'Förbered patientens plan',why:p.plan_id?'Inget nytt kräver ett ställningstagande i den här arbetskön.':'Patienten har ännu ingen aktiv ordination.',effect:p.plan_id?'Du kan öppna hela uppföljningen eller lägga en egen uppföljning.':'Öppna ordinationen för att förbereda planen.'};
}
export function receiptText(r){
 if(r.action==='send_message')return 'Meddelandet är levererat i Reda. Uppföljning '+r.due_date+'.';
 if(r.action==='follow_up')return 'Uppföljning sparad till '+r.due_date+'.'+(r.case_count?' '+r.case_count+' signaler kvitterade.':'');
 if(r.action==='resolve_cases')return r.case_count+' signaler'+(r.message_count?' och '+r.message_count+' meddelanden':'')+' sparade som bedömda.';
 if(r.action==='complete_follow_up')return 'Uppföljningen är dokumenterad som genomförd.';
 if(r.action==='approve_frame')return 'Progressionsramen är godkänd i granskningsläge.';
 if(r.action==='evaluate')return 'En ny EI-prövning är sparad.';
 return 'Din bedömning av EI-prövningen är sparad.';
}
