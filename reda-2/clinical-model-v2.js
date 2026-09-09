/* Reda 2.2: curated exercise graph + blueprints. No automatic progression. */
(function(root){'use strict';
const D=root.RedaData, dose=(s,r,rest=60,hold=0,tempo=5)=>({sets:s,reps:r,rest,hold,tempo});
const v=(id,name,support,steps,cue,dose,pose,tags)=>({id,name,support,steps,cue,dose,pose,tags});
const x=(id,name,region,equipment,variants)=>({id,name,region,equipment,purpose:'Del av en behandlarvald träningsplan.',variants});
const extras=[
 x('quad_iso','Quadriceps isometriskt','Knä','Handduk', [v('easy','Avlastad isometrisk','Sittande eller liggande',['Placera benet som visat.','Spänn framsidan av låret jämnt.','Slappna av mellan hållen.'],'Jämn anspänning.',dose(3,5,45,10),'extension',{load:1})]),
 x('step_up','Step-up','Knä & höft','Steg', [v('support','Lågt steg med stöd','Handstöd tillåtet',['Placera hela foten på steget.','Res dig upp med kontroll.','Sänk tillbaka lugnt.'],'Använd stöd enligt ordination.',dose(2,8),'chair-support',{load:2}),v('free','Step-up','Utan handstöd',['Placera foten på steget.','Res dig upp kontrollerat.','Sänk tillbaka med kontroll.'],'Kontroll före höjd.',dose(3,10),'chair-free',{load:3})]),
 x('split_squat','Split squat','Knä & höft','Eventuellt stöd',[v('support','Kort med stöd','Handstöd tillåtet',['Stå i delad position nära stöd.','Sänk kroppen en kort sträcka.','Res dig kontrollerat.'],'Stödet ingår i varianten.',dose(2,8),'chair-support',{load:2}),v('free','Split squat','Utan handstöd',['Stå i delad position.','Sänk enligt ordinerat rörelseutslag.','Res dig kontrollerat.'],'Följ ordinerat djup.',dose(3,8,75),'chair-free',{load:3})]),
 x('soleus','Sittande tåhävning','Vad / Achilles','Stol',[v('body','Utan extra vikt','Sittande',['Sitt med foten i golvet.','Lyft hälen.','Sänk långsamt.'],'Jämnt tryck genom framfoten.',dose(3,15,45),'calf-both',{load:1}),v('loaded','Med ordinerad belastning','Sittande',['Placera belastningen som visat.','Lyft hälen kontrollerat.','Sänk långsamt.'],'Belastningen bestäms vid besöket.',dose(4,12),'calf-both',{load:3})]),
 x('side_step','Sidosteg med band','Höft','Gummiband',[v('light','Korta sidosteg','Band enligt ordination',['Placera bandet som visat.','Ta korta steg åt sidan.','Behåll kontrollen.'],'Små steg före stora.',dose(3,10),'abduction',{load:2,band:true}),v('loaded','Högre motstånd','Band enligt ordination',['Placera ordinerat band.','Ta kontrollerade sidosteg.','Behåll bäckenet stabilt.'],'Motståndet väljs vid besöket.',dose(4,10),'abduction',{load:3,band:true})]),
 x('scaption','Armlyft i scapularplanet','Axel','Eventuell lätt vikt',[v('short','Kort rörelse','Sittande eller stående',['För armen upp i den riktning ni gått igenom.','Stanna vid ordinerad höjd.','Sänk kontrollerat.'],'Rörelseutslaget är behandlarvalt.',dose(2,10,45),'rotation',{load:1}),v('loaded','Med ordinerad belastning','Stående',['Lyft armen kontrollerat.','Stanna vid ordinerad höjd.','Sänk långsamt.'],'Vikten bestäms vid uppföljning.',dose(3,10),'rotation',{load:3})]),
 x('neck_rotation','Nackrotation','Nacke','Ingen',[v('gentle','Lugn aktiv rotation','Sittande',['Sitt bekvämt.','Vrid huvudet lugnt inom ordinerat rörelseutslag.','Återgå och växla sida.'],'Ingen forcering.',dose(2,6,30),'rotation',{load:1})]),
 x('lumbar_extension','Stående ryggextension','Ländrygg','Stabilt underlag',[v('standing','Stående','Stående',['Stå stabilt.','Gör rörelsen i den riktning ni gått igenom.','Återgå lugnt.'],'Följ ordinerad riktning och dos.',dose(2,8,30),'chair-free',{load:1})]),
 x('wrist_extension','Handledsextension','Armbåge & underarm','Lätt vikt',[v('light','Lätt motstånd','Underarm stödd',['Stöd underarmen.','Lyft handen kontrollerat.','Sänk långsamt.'],'Underarmen ligger kvar mot stödet.',dose(3,12,45),'extension',{load:2}),v('ecc','Långsam sänkning','Underarm stödd',['Hjälp handen till startläget.','Sänk långsamt med träningssidan.','Återställ och upprepa.'],'Långsam sänkning.',dose(3,10,60,0,8),'extension',{load:3})]),
 x('nerve_slider','Nervmobilisering, slider','Nerv','Stol',[v('seated','Sittande slider','Sittande',['Sitt i utgångsläget som visat.','Växla mellan de två positionerna.','Undvik att hålla ytterläget.'],'Slider, inte stretch.',dose(2,8,30),'extension',{load:1})])
];
extras.forEach(e=>{if(!D.exercises.some(q=>q.id===e.id))D.exercises.push(e);});
const blueprints={
 knee_pf:{name:'Knä · patellofemoralt',slots:['extension','chair','step_up','calf'],goal:'Öka belastningstolerans och kontroll i knäets vardags- och träningsbelastning.'},
 knee_oa:{name:'Knä · artros / vardagsfunktion',slots:['chair','extension','calf','balance'],goal:'Stärka funktion, trygghet och belastningstolerans i vardagen.'},
 knee_tendon:{name:'Knä · patellarsena',slots:['quad_iso','chair','split_squat','calf'],goal:'Bygga tolerans för successiv belastning av knäets sträckapparat.'},
 shoulder_load:{name:'Axel · rotatorcuff / belastning',slots:['rotation','row','scaption'],goal:'Bygga kontrollerad axelbelastning inför vardag eller träning.'},
 shoulder_stiff:{name:'Axel · stelhet / kontroll',slots:['rotation','row'],goal:'Behålla rörelse och successivt återta funktion inom ordinerad nivå.'},
 hip_gtps:{name:'Höft · lateral höft / GTPS',slots:['bridge','abduction','side_step','chair'],goal:'Bygga höftkapacitet med en nivå som passar aktuell belastningstolerans.'},
 achilles:{name:'Fotled · Achilles',slots:['calf','soleus','balance'],goal:'Bygga vad- och senkapacitet stegvis inför vardag eller aktivitet.'},
 elbow:{name:'Armbåge · lateral belastning',slots:['wrist_extension','row'],goal:'Bygga lokal och proximal belastningstolerans enligt undersökningen.'},
 neck:{name:'Nacke · rörelse & kontroll',slots:['neck_rotation','row'],goal:'Öva rörelse och kontroll inom den riktning och dos som valts vid besöket.'},
 lumbar:{name:'Ländrygg · riktad plan',slots:['lumbar_extension','bridge','bird_dog'],goal:'Träna i den riktning och belastning som valts efter undersökningen.'}
};
const presentation={guided:{name:'Tydlig guidning',intro:'Du får steg-för-steg-instruktioner och kan alltid öppna mer hjälp.'},standard:{name:'Standard',intro:'Följ dosen och instruktionerna från besöket.'},concise:{name:'Träningsvan',intro:'Kort guidning. Följ ordinerad dos och variant.'}};
const progression={rule:'clinician_only',message:'Svårighetsgrad, belastning och dos ändras efter klinisk uppföljning. Appen låser inte upp nästa nivå automatiskt.'};
root.RedaClinical={version:'2.2',blueprints,presentation,progression};
})(window);
