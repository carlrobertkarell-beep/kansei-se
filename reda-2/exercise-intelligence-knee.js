/* Reda Exercise Intelligence · Knee v1. Clinician-selected context, never autonomous progression. */
(function(root){'use strict';const D=root.RedaData,C=root.RedaClinical;if(!D||!C)return;
const dose=(sets,reps,rest=60,hold=0,tempo=5)=>({sets,reps,rest,hold,tempo});
const add=e=>{if(!D.exercises.some(x=>x.id===e.id))D.exercises.push(e)};
const v=(id,name,support,steps,cue,dose,pose,tags={},why='')=>({id,name,support,steps,cue,dose,pose,tags,why});
add({id:'leg_press',name:'Benpress',region:'Knä & höft',equipment:'Benpressmaskin',purpose:'Bygga mätbar benstyrka med extern belastning när gymmiljö och kapacitet tillåter.',variants:[
 v('bilateral','Benpress · två ben','Gym · två ben',['Ställ in maskinen enligt genomgången.','Pressa kontrollerat genom det ordinerade rörelseutslaget.','Sänk vikten lugnt tillbaka utan att tappa positionen.'],'Belastning och rörelseutslag är delar av ordinationen.',dose(3,8,90,0,7),'leg-press.bilateral',{load:4,gym:true},'Ger möjlighet att bygga benstyrka med en tydligt doserbar extern belastning.'),
 v('single','Benpress · ett ben','Gym · ett ben',['Ställ in sits och fotposition enligt genomgången.','Pressa med träningssidan genom ordinerat rörelseutslag.','Sänk kontrollerat tillbaka.'],'Behåll bäcken och knäposition stabila.',dose(4,6,120,0,7),'leg-press.single',{load:6,gym:true},'Ökar den ensidiga kapaciteten när bilateral belastning inte längre är tillräckligt specifik.')
]});
add({id:'knee_extension_machine',name:'Knäextension i maskin',region:'Knä',equipment:'Knäextensionsmaskin',purpose:'Doserbar quadricepsbelastning med möjlighet att styra rörelseutslag och extern vikt.',variants:[
 v('controlled','Kontrollerad knäextension','Gym · maskin',['Ställ in maskinen så att knäleden och maskinens axel linjerar enligt genomgången.','Sträck knät genom det ordinerade rörelseutslaget.','Sänk vikten långsamt tillbaka.'],'Rörelseutslag och vikt är behandlarvalda.',dose(3,10,90,0,7),'knee-extension.machine',{load:4,gym:true},'Ger en direkt och mätbar quadricepsbelastning som kan doseras mer exakt än en mycket lätt hemövning.'),
 v('heavy_slow','Tung långsam knäextension','Gym · maskin',['Ställ in den ordinerade vikten och rörelsebanan.','Sträck knät kontrollerat utan att accelerera vikten.','Sänk tillbaka långsamt enligt tempot.'],'Samma tempo genom hela setet.',dose(4,6,120,0,9),'knee-extension.machine-heavy',{load:6,gym:true},'Används när målet är högre quadricepskapacitet och patienten redan tolererar enklare belastning.')
]});
add({id:'spanish_squat',name:'Spanish squat',region:'Knä',equipment:'Kraftigt band eller rem',purpose:'Knädominant belastning med extern support som kan användas för isometrisk eller långsam styrketräning.',variants:[
 v('iso','Isometrisk Spanish squat','Band/rem bakom knävecken',['Fäst remmen säkert och inta den position ni gått igenom.','Sätt dig bakåt till ordinerad knävinkel och håll kroppen upprätt.','Håll tiden och res dig lugnt.'],'Vinkeln och hålltiden är behandlarvalda.',dose(5,1,90,30,5),'spanish-squat.iso',{load:3,band:true},'Ger en tydlig knädominant belastning utan att programmet behöver stanna vid mycket lågintensiva quadricepsövningar.'),
 v('dynamic','Dynamisk Spanish squat','Band/rem bakom knävecken',['Fäst remmen säkert och inta startpositionen.','Sänk kontrollerat till ordinerat djup.','Res dig upp med samma kontroll.'],'Håll bålen upprätt och följ ordinerat djup.',dose(4,8,90,0,8),'spanish-squat.dynamic',{load:5,band:true},'Bygger vidare från isometrisk tolerans till mer dynamisk knädominant kapacitet.')
]});
add({id:'rear_foot_split_squat',name:'Bakre fot upphöjd split squat',region:'Knä & höft',equipment:'Bänk · eventuella vikter',purpose:'Högre unilateral benbelastning för träningsvana patienter.',variants:[
 v('body','Kroppsvikt','Bakre fot på bänk',['Placera bakre foten på bänken och hitta den fotposition ni valt.','Sänk kroppen genom ordinerat rörelseutslag.','Res dig kontrollerat på främre benet.'],'Kontrollera främre benet genom hela rörelsen.',dose(3,8,90,0,7),'split-squat.rfess',{load:4},'Ger större ensidigt krav än vanlig stolresning eller bilateral knäböj.'),
 v('loaded','Med extern belastning','Bakre fot på bänk · vikter',['Håll den ordinerade belastningen och inta startpositionen.','Sänk kontrollerat till ordinerat djup.','Res dig med främre benet utan att tappa positionen.'],'Belastning och djup ändras separat.',dose(4,6,120,0,8),'split-squat.rfess-loaded',{load:6,gym:true},'För en träningsvan patient som behöver en plan som faktiskt bygger vidare mot hög benkapacitet.')
]});
add({id:'single_leg_squat_box',name:'Enbensknäböj mot box',region:'Knä & höft',equipment:'Box eller bänk',purpose:'Unilateral kontroll och styrka med styrbart djup.',variants:[
 v('high','Hög box','Box/bänk',['Stå på träningssidan framför boxen.','Sänk dig kontrollerat tills du lätt nuddar boxen.','Res dig tillbaka utan att använda det andra benet.'],'Boxhöjden styr svårighetsgraden.',dose(3,6,90,0,7),'single-leg-squat.box-high',{load:4},'Gör den ensidiga belastningen tydlig samtidigt som djupet kan doseras exakt.'),
 v('low','Lägre box','Box/bänk',['Stå stabilt på träningssidan.','Sänk dig till den lägre boxhöjden med kontroll.','Res dig tillbaka och återställ balansen.'],'Djup före fart.',dose(3,8,90,0,8),'single-leg-squat.box-low',{load:5},'Ökar krav på knä- och höftkapacitet utan att automatiskt gå över till hopp eller löpning.')
]});
add({id:'pogos',name:'Pogo-hopp',region:'Knä & vad',equipment:'Plant underlag',purpose:'Låg amplitud plyometrisk belastning inför återgång till löpning eller idrott när behandlaren bedömer att det är lämpligt.',variants:[
 v('bilateral','Två ben · låg amplitud','Plant underlag',['Stå med jämn vikt på båda benen.','Gör små rytmiska hopp med kort markkontakt.','Avsluta setet om rytm eller kontroll tydligt försämras.'],'Låg höjd, jämn rytm.',dose(3,20,90,0,3),'pogo.bilateral',{load:6,impact:true},'Introducerar snabbare kraftutveckling när målet är löpning eller idrott och styrkebasen redan är tillräcklig.')
]});
C.blueprints.knee_pf.advancedSlots=['knee_extension_machine','leg_press','rear_foot_split_squat','single_leg_squat_box'];
C.blueprints.knee_pf.performanceSlots=['leg_press','rear_foot_split_squat','single_leg_squat_box','pogos'];
C.blueprints.knee_oa.advancedSlots=['leg_press','chair','step_up','calf'];
C.blueprints.knee_tendon.advancedSlots=['spanish_squat','knee_extension_machine','split_squat','leg_press'];
C.blueprints.knee_tendon.performanceSlots=['knee_extension_machine','rear_foot_split_squat','single_leg_squat_box','pogos'];
root.RedaExerciseIntelligence={version:'knee-1.0',rule:'clinician_context_only'};
})(typeof window!=='undefined'?window:globalThis);