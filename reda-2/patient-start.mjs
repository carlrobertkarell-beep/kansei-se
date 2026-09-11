import {startProfiles} from './plan-authoring-model.mjs?v=2';
export const bodyAreas=['Knä','Axel','Höft / ljumske','Fot / fotled','Hälsena / vad','Armbåge','Hand / handled','Nacke','Ländrygg','Balans'];
export const goalChoices=['Klara vardagen lättare','Gå och klara trappor','Komma igång med hemträning','Återgå till promenader','Återgå till motion','Återgå till styrketräning','Förbättra balans och trygghet'];
export const sideChoices={left:'Vänster',right:'Höger',both:'Båda sidor',unspecified:'Ej sidbundet'};
export function intakeContext(profile='home',side='unspecified',included=false){return {...startProfiles[profile].values,side,includedInVisit:included}}
export function startRequirements(p,c,delivery='digital'){
 const missing=[];if((p.name||'').trim().length<2)missing.push('Fullständigt namn');
 if(delivery==='digital'&&!p.email?.trim()&&!p.phone?.trim())missing.push('E-post eller telefon, eller välj överlämning på kliniken');
 if((p.focus||'').trim().length<2)missing.push('Behandlingsområde');if((p.goal||'').trim().length<2)missing.push('Patientens mål');
 if(!c?.stage||!c?.capacity||!c?.trainingHistory||!c?.goalProfile||!c?.equipment)missing.push('Startläge för rehab');return missing;
}
