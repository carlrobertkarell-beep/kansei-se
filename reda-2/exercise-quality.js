/* Reda Exercise Intelligence · prescription quality layer. Clinical metadata, never autonomous progression. */
(function(root){'use strict';const D=root.RedaData;if(!D)return;
const profiles={
'leg_press.bilateral':{target:'Benstyrka',pattern:'Bilateral press',rom:'Ordinerat knä- och höftutslag',tempo:'3 sek ned · kontrollerat upp',load:'RPE 6–8/10 enligt ordination',measure:'Vikt × repetitioner'},
'leg_press.single':{target:'Unilateral benstyrka',pattern:'Ensidig press',rom:'Ordinerat knä- och höftutslag',tempo:'3 sek ned · kontrollerat upp',load:'RPE 7–8/10 enligt ordination',measure:'Vikt × repetitioner per sida'},
'knee_extension_machine.controlled':{target:'Quadricepskapacitet',pattern:'Öppen kedja',rom:'Behandlarvalt rörelseutslag',tempo:'2 sek upp · 3 sek ned',load:'RPE 6–8/10',measure:'Vikt × repetitioner'},
'knee_extension_machine.heavy_slow':{target:'Hög quadricepskapacitet',pattern:'Tung långsam styrka',rom:'Behandlarvalt rörelseutslag',tempo:'3 sek upp · 3 sek ned',load:'RPE 7–9/10',measure:'Vikt × repetitioner'},
'spanish_squat.iso':{target:'Knäextensortolerans',pattern:'Isometrisk knädominant',rom:'Ordinerad knävinkel',tempo:'Statiskt håll',load:'Hålltid och vinkel styr dosen',measure:'Sekunder × vinkel'},
'spanish_squat.dynamic':{target:'Knädominant styrka',pattern:'Dynamisk squat',rom:'Ordinerat djup',tempo:'3 sek ned · kontrollerat upp',load:'Band/rem + kroppsvikt',measure:'Repetitioner × djup'},
'rear_foot_split_squat.body':{target:'Unilateral benkapacitet',pattern:'Split squat',rom:'Ordinerat djup',tempo:'3 sek ned · kontrollerat upp',load:'Kroppsvikt',measure:'Repetitioner × djup'},
'rear_foot_split_squat.loaded':{target:'Hög unilateral benstyrka',pattern:'Belastad split squat',rom:'Ordinerat djup',tempo:'3 sek ned · kraftfullt kontrollerat upp',load:'RPE 7–9/10',measure:'Extern vikt × repetitioner'},
'single_leg_squat_box.high':{target:'Unilateral kontroll',pattern:'Enbens squat till box',rom:'Boxhöjd styr djup',tempo:'Kontrollerad nedsänkning',load:'Kroppsvikt',measure:'Boxhöjd × repetitioner'},
'single_leg_squat_box.low':{target:'Unilateral styrka',pattern:'Djupare enbens squat',rom:'Lägre box enligt ordination',tempo:'3 sek ned · kontrollerat upp',load:'Kroppsvikt',measure:'Boxhöjd × repetitioner'},
'pogos.bilateral':{target:'Elastisk kapacitet',pattern:'Låg amplitud plyometrik',rom:'Låg hopphöjd',tempo:'Kort markkontakt · jämn rytm',load:'Kroppsvikt',measure:'Kontakter × rytmkvalitet'},
'cable_er.side':{target:'Rotatorcuffkapacitet',pattern:'Utåtrotation',rom:'Ordinerat rotationsutslag',tempo:'2 sek ut · 3 sek tillbaka',load:'RPE 6–8/10',measure:'Kabelvikt × repetitioner'},
'cable_er.elevated':{target:'Cuff i högre armposition',pattern:'Utåtrotation i elevation',rom:'Armposition + rotation behandlarvalda',tempo:'Kontrollerat båda riktningar',load:'RPE 6–8/10',measure:'Kabelvikt × repetitioner'},
'landmine_press.two':{target:'Presskapacitet',pattern:'Sned pressbana',rom:'Ordinerad pressbana',tempo:'Kontrollerat ned · aktivt upp',load:'RPE 6–8/10',measure:'Vikt × repetitioner'},
'landmine_press.single':{target:'Unilateral presskapacitet',pattern:'Enarms sned press',rom:'Ordinerad pressbana',tempo:'Kontrollerat ned · aktivt upp',load:'RPE 7–8/10',measure:'Vikt × repetitioner per sida'},
'loaded_carry.suitcase':{target:'Axel-, grepp- och bålkapacitet',pattern:'Unilateral carry',rom:'Gångsträcka',tempo:'Lugn jämn gång',load:'Vikt som tillåter bibehållen hållning',measure:'Kg × meter'},
'standing_calf_loaded.bilateral':{target:'Plantarflexionsstyrka',pattern:'Rakknä vadpress',rom:'Fullt tolererat hälutslag',tempo:'3 sek upp · 3 sek ned',load:'RPE 7–9/10',measure:'Vikt × repetitioner'},
'standing_calf_loaded.single':{target:'Unilateral plantarflexionsstyrka',pattern:'Enbens vadpress',rom:'Fullt tolererat hälutslag',tempo:'3 sek upp · 3 sek ned',load:'RPE 7–9/10',measure:'Vikt × repetitioner per sida'},
'seated_calf_loaded.heavy':{target:'Soleuskapacitet',pattern:'Böjt knä plantarflexion',rom:'Fullt tolererat hälutslag',tempo:'3 sek upp · 3 sek ned',load:'RPE 7–9/10',measure:'Vikt × repetitioner'},
'hip_thrust.bilateral':{target:'Höftsträckarstyrka',pattern:'Belastad höftsträckning',rom:'Ordinerat toppläge',tempo:'2 sek upp · 3 sek ned',load:'RPE 7–9/10',measure:'Vikt × repetitioner'},
'hip_thrust.single':{target:'Unilateral höftkapacitet',pattern:'Ensidig höftsträckning',rom:'Ordinerat toppläge',tempo:'Kontrollerat båda riktningar',load:'Kroppsvikt/ordinerad belastning',measure:'Repetitioner per sida'},
'lateral_step_down_loaded.loaded':{target:'Frontalplanskapacitet',pattern:'Lateral step-down',rom:'Steghöjd + djup',tempo:'3 sek ned · kontrollerat upp',load:'Extern vikt enligt ordination',measure:'Vikt × repetitioner × steghöjd'}
};
for(const e of D.exercises)for(const v of e.variants||[]){const p=profiles[`${e.id}.${v.id}`];if(p){v.prescription=p;v.focus=v.focus||v.cue;v.qualityVersion=1;}}
root.RedaExerciseQuality={version:'1.0',profiles,get:(e,v)=>profiles[`${e}.${v}`]||null};
})(typeof window!=='undefined'?window:globalThis);