export function nextStep(p,today){
 if(p.open_count>0&&p.codes?.includes('changed_symptoms'))return 'Bedöm ändrade besvär';
 if(p.new_reply)return 'Bedöm patientens svar';
 if(p.open_count>0&&p.codes?.includes('changed_environment'))return 'Stäm av förutsättningarna';
 if(p.open_count>0)return p.connected?'Granska kontaktförslag':'Planera kontakt';
 if(p.followup_status==='waiting')return p.followup_date<=today?'Följ upp kontakten':'Invänta uppföljningen';
 if(p.patient_status==='archived')return 'Visa historiken';
 if(!p.plan_id)return p.draft_version?'Fortsätt utkastet':'Förbered första planen';
 if(!p.care_focus||!p.care_goal)return 'Komplettera fokus och mål';
 if(p.needs_review)return 'Granska nästa åtgärd';
 return 'Se patientens översikt';
}
export function functionLabel(report){return report?({better:'Patienten uppger bättre funktion',stable:'Patienten uppger oförändrad funktion',worse:'Patienten uppger sämre funktion',unknown:'Patienten kan inte jämföra funktionen'}[report.function]||'Funktionssvar saknas'):'Återkoppling saknas'}
export const stageLabels={protected:'Skyddad fas',build:'Uppbyggnad',higher:'Högre belastning'};
