export const REDA_CLINICAL_KNOWLEDGE_VERSION='2026.09.19.1';
export const blueprintMeta={
 knee_pf:{domain:'knee',label:'Patellofemoralt knä',review:'clinical'},
 knee_oa:{domain:'knee',label:'Knäartros',review:'clinical'},
 knee_tendon:{domain:'knee',label:'Knä/senbelastning',review:'clinical'},
 shoulder_load:{domain:'shoulder',label:'Axelbelastning',review:'clinical'},
 hip_gtps:{domain:'hip',label:'Höft / GTPS',review:'clinical'},
 achilles:{domain:'achilles',label:'Achilles',review:'clinical'},
 neck:{domain:'neck',label:'Nacke',review:'clinical'},
 lumbar:{domain:'lumbar',label:'Ländrygg',review:'clinical'}
};
export function knowledgeManifest(blueprints){return Object.entries(blueprints||{}).map(([id,b])=>({id,version:REDA_CLINICAL_KNOWLEDGE_VERSION,domain:blueprintMeta[id]?.domain||'other',nodes:b.progressionGraph?.nodes?.length||0,edges:b.progressionGraph?.edges?.length||0,hasRegression:!!b.progressionGraph?.edges?.some(e=>e.kind==='regress')}))}

if(typeof globalThis!=='undefined')globalThis.RedaClinicalKnowledgeVersion=REDA_CLINICAL_KNOWLEDGE_VERSION;
