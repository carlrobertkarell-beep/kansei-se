import test from 'node:test';
import assert from 'node:assert/strict';
import {parsePatientFile,mappedPatient} from '../../reda-2/patient-import.mjs';
import {nextStep,functionLabel} from '../../reda-2/patient-glance.mjs';
test('Swedish export preserves quoted separators, names and leading phone zeroes',()=>{
 const f=parsePatientFile('\uFEFFFörnamn;Efternamn;E-post;Telefon;Kund-ID;Behandlingsfokus\r\nÅsa;Öberg;asa@example.test;070 123 45 67;00042;"Knä; vänster"\r\n');
 assert.deepEqual(mappedPatient(f.rows[0],f.mapping),{name:'Åsa Öberg',email:'asa@example.test',phone:'070 123 45 67',external_id:'00042',focus:'Knä; vänster',goal:''});
});
test('mapping is explicit, rejects malformed files, and does not infer ambiguous columns',()=>{
 const f=parsePatientFile('Namn,Email,E-post,Anteckning\n"Bo ""Bosse"" Test",first@example.test,second@example.test,"Två\nrader"');
 assert.equal(f.mapping.email,-1);assert.equal(mappedPatient(f.rows[0],f.mapping).email,'');f.mapping.email=2;assert.equal(mappedPatient(f.rows[0],f.mapping).email,'second@example.test');assert.equal(mappedPatient(f.rows[0],f.mapping).name,'Bo "Bosse" Test');
 for(const text of ['Namn;Email\nBo','Namn;Email\n"Bo;a@example.test','Namn;Email\n"Bo"x;a@example.test','Namn;Email\nB\uFFFD;a@example.test'])assert.throws(()=>parsePatientFile(text));
});
test('large registry import is bounded and keeps individual rows available for review',()=>{
 const f=parsePatientFile('Namn\tKund-ID\n'+Array.from({length:1000},(_,i)=>`Fiktiv ${i}\t${i}`).join('\n'));assert.equal(f.rows.length,1000);assert.equal(mappedPatient(f.rows[999],f.mapping).external_id,'999');assert.throws(()=>parsePatientFile('x'.repeat(2_000_001)));
});
test('glance keeps patient reports separate from clinical conclusions and prioritizes new evidence',()=>{
 assert.equal(functionLabel({function:'better'}),'Patienten uppger bättre funktion');assert.equal(functionLabel(null),'Återkoppling saknas');
 assert.equal(nextStep({open_count:1,codes:['changed_symptoms'],followup_status:'waiting'},'2026-09-11'),'Bedöm ändrade besvär');
 assert.equal(nextStep({patient_status:'active',draft_version:2},'2026-09-11'),'Fortsätt utkastet');
});
