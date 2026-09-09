/* Reda 2.5 · deeper clinician-owned exercise families. No automatic progression. */
(function(root){'use strict';const D=root.RedaData,C=root.RedaClinical;if(!D||!C)return;
const dose=(sets,reps,rest=60,hold=0,tempo=5)=>({sets,reps,rest,hold,tempo});
const addExercise=e=>{if(!D.exercises.some(x=>x.id===e.id))D.exercises.push(e);};
const addVariant=(id,v)=>{const e=D.exercises.find(x=>x.id===id);if(e&&!e.variants.some(x=>x.id===v.id))e.variants.push(v);};
const v=(id,name,support,steps,cue,dose,pose,tags={})=>({id,name,support,steps,cue,dose,pose,tags});
/* Knä: PFSS, artros och patellarsena */
addExercise({id:'step_down',name:'Step-down',region:'Knä & höft',equipment:'Lågt steg',purpose:'Kontrollerad excentrisk knäbelastning som del av behandlarvald plan.',variants:[
 v('support','Lågt steg med stöd','Handstöd tillåtet',['Stå med hela foten på ett lågt steg.','Sänk motsatt häl mot golvet med stöd vid behov.','Res dig tillbaka kontrollerat.'],'Knäets kontroll före djup.',dose(2,6,60,0,7),'step-down.supported',{load:2}),
 v('free','Step-down','Utan handstöd',['Stå stabilt på steget.','Sänk motsatt häl mot golvet inom ordinerat djup.','Res dig tillbaka utan att tappa kontrollen.'],'Djupet bestäms vid besöket.',dose(3,8,75,0,7),'step-down.standard',{load:3})
]});
addVariant('extension',v('band','Benspark med lätt band','Sittande · gummiband',['Sitt stadigt med bandet placerat enligt instruktionen.','Sträck knät kontrollerat.','Sänk långsamt tillbaka.'],'Bandmotståndet är ordinerat.',dose(3,10,60,0,7),'knee-extension.band',{load:3,band:true}));
addVariant('extension',v('band_loaded','Benspark med högre motstånd','Sittande · gummiband',['Sitt stadigt och kontrollera bandets fäste.','Sträck knät genom ordinerat rörelseutslag.','Sänk tillbaka långsamt.'],'Öka inte motståndet utan ny plan.',dose(4,8,75,0,8),'knee-extension.band-loaded',{load:4,band:true}));
addExercise({id:'wall_sit',name:'Väggsitt',region:'Knä',equipment:'Vägg',purpose:'Isometrisk knäbelastning inom behandlarvalt rörelseutslag.',variants:[
 v('high','Hög position','Rygg mot vägg',['Placera ryggen mot väggen.','Glid ned till den höjd ni valt.','Håll tiden och res dig lugnt.'],'Högre position ger mindre knävinkel.',dose(4,1,60,25,5),'wall-sit.high',{load:2}),
 v('deep','Djupare position','Rygg mot vägg',['Placera ryggen mot väggen.','Glid ned till ordinerat djup.','Håll tiden och res dig kontrollerat.'],'Djupet är en del av ordinationen.',dose(4,1,75,30,5),'wall-sit.deep',{load:3})
]});
/* Achilles: rak knäled, soleus och långsam återgång */
addExercise({id:'heel_raise_ecc',name:'Tåhävning med långsam sänkning',region:'Vad / Achilles',equipment:'Stabilt stöd',purpose:'Kontrollerad vad- och senbelastning med tydligt tempo.',variants:[
 v('both','Två ben','Stabilt stöd',['Lyft hälarna med båda benen.','Stanna kort i toppläget.','Sänk långsamt tillbaka enligt tempot.'],'Den långsamma sänkningen är viktigare än höjden.',dose(3,10,60,0,8),'calf-raise.eccentric-bilateral',{load:2}),
 v('single','Ett ben','Stabilt stöd',['Stå på träningssidan nära stödet.','Lyft hälen kontrollerat.','Sänk långsamt tillbaka.'],'Använd stödet för balans.',dose(4,8,75,0,8),'calf-raise.eccentric-unilateral',{load:4})
]});
/* Höft / GTPS */
addExercise({id:'clam',name:'Clamshell',region:'Höft',equipment:'Matta · eventuellt band',purpose:'Lokal höftabduktionsbelastning i sidliggande.',variants:[
 v('body','Utan band','Sidliggande',['Ligg på sidan i den position ni gått igenom.','Lyft översta knät utan att rulla bäckenet bakåt.','Sänk lugnt tillbaka.'],'Liten rörelse med stabilt bäcken.',dose(3,10,45,0,6),'clam.body',{load:1,floor:true}),
 v('band','Med band','Sidliggande · band',['Placera bandet enligt instruktionen.','Öppna knät mot bandet med bäckenet stilla.','Sänk tillbaka långsamt.'],'Motståndet är behandlarvalt.',dose(3,12,60,0,7),'clam.band',{load:2,floor:true,band:true})
]});
/* Axel: cuff och elevation */
addExercise({id:'isometric_er',name:'Isometrisk utåtrotation',region:'Axel',equipment:'Vägg eller handduk',purpose:'Låg-rörelse axelbelastning inom behandlarvald nivå.',variants:[
 v('wall','Mot vägg','Armbåge intill kroppen',['Placera underarmen mot väggen enligt instruktionen.','Bygg upp ett jämnt tryck utan synlig rörelse.','Släpp trycket lugnt.'],'Jämnt tryck utan att lyfta axeln.',dose(4,1,45,20,5),'shoulder-er.isometric',{load:0})
]});
addVariant('scaption',v('mid','Kontrollerat armlyft','Stående · utan vikt',['För armen i scapularplanet.','Lyft till den höjd ni valt vid undersökningen.','Sänk långsamt tillbaka.'],'Höjden är individuell.',dose(3,10,60,0,6),'scaption.short',{load:2}));
/* Bål, nacke och ländrygg */
addExercise({id:'dead_bug',name:'Dead bug',region:'Bål',equipment:'Matta',purpose:'Bålkontroll i ryggliggande som del av behandlarvald plan.',variants:[
 v('heel','Hälkontakt','Ryggliggande',['Ligg i startpositionen ni gått igenom.','Sänk en häl mot underlaget utan att tappa bålkontrollen.','Återgå och växla sida.'],'Kontroll före räckvidd.',dose(2,8,45,0,6),'dead-bug.heel',{load:1,floor:true}),
 v('alternating','Växelvis arm och ben','Ryggliggande',['Håll startpositionen stabil.','För motsatt arm och ben enligt ordination.','Återgå kontrollerat och växla sida.'],'Bäckenet ligger stilla.',dose(3,8,60,0,7),'dead-bug.alternating',{load:2,floor:true})
]});
addExercise({id:'chin_nod',name:'Lätt nickning',region:'Nacke',equipment:'Stol',purpose:'Lågintensiv kontrollövning för nacke.',variants:[
 v('seated','Sittande','Sittande',['Sitt bekvämt med blicken framåt.','Gör en liten nickning enligt instruktionen.','Återgå utan att pressa in i ytterläge.'],'Mycket liten rörelse.',dose(2,6,30,3,5),'chin-nod.seated',{load:1})
]});
/* Blueprints: bredare, fortfarande behandlarstyrda. */
C.blueprints.knee_pf.slots=['extension','chair','step_up','step_down','calf'];
C.blueprints.knee_oa.slots=['chair','extension','step_up','calf','balance'];
C.blueprints.knee_tendon.slots=['quad_iso','wall_sit','split_squat','step_down','calf'];
C.blueprints.shoulder_load.slots=['isometric_er','rotation','row','scaption'];
C.blueprints.hip_gtps.slots=['bridge','clam','abduction','side_step','chair'];
C.blueprints.achilles.slots=['calf','soleus','heel_raise_ecc','balance'];
C.blueprints.neck.slots=['neck_rotation','chin_nod','row'];
C.blueprints.lumbar.slots=['lumbar_extension','bridge','bird_dog','dead_bug'];
root.RedaClinicalLibrary={version:'2.5.0',progression:'clinician_only'};
})(typeof window!=='undefined'?window:globalThis);
