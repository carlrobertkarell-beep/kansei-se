/* Reda 2.0 · curated interface examples, NOT prescriptions. One variant owns all instructions. */
(function (root) {
  'use strict';
  const variant = (id, name, support, steps, cue, dose, pose, notes = '') => ({id, name, support, steps, cue, dose, pose, notes});
  const rep = (sets, reps, rest = 60) => ({sets, reps, hold: 0, rest, tempo: 5});
  const hold = (sets, seconds, rest = 45) => ({sets, reps: 1, hold: seconds, rest, tempo: 5});
  const exercises = [
    {id:'chair', name:'Uppresning från stol', region:'Ben', equipment:'Stadig stol', purpose:'Öva på att resa dig och sätta dig kontrollerat.', variants:[
      variant('support','Hög stol med handstöd','Handstöd tillåtet',['Sitt på en stadig, hög stol med fötterna i golvet.','Luta dig lite framåt och res dig. Använd händerna som stöd vid behov.','Sätt dig lugnt och kontrollerat igen.'],'Handstödet är en del av den här varianten.',rep(2,8),'chair-support'),
      variant('free','Stol utan handstöd','Utan handstöd',['Sitt på en stadig stol, med fötterna under knäna.','Luta dig framåt och res dig utan hjälp av händerna.','Sätt dig kontrollerat tillbaka på stolen.'],'Behåll kontrollen på vägen ned.',rep(3,10),'chair-free')
    ]},
    {id:'extension', name:'Benspark från stol', region:'Ben', equipment:'Stadig stol', purpose:'Träna framsidan av låret med stöd av stolen.', variants:[
      variant('easy','Utan vikt','Sittande',['Sitt stadigt med fötterna i golvet.','Sträck det valda benet i den rörelse som din behandlare har visat.','Sänk tillbaka foten långsamt.'],'Låt låret ligga kvar mot stolen.',rep(2,12),'extension'),
      variant('pause','Med paus i toppläget','Sittande',['Sitt stadigt och sträck det valda benet.','Stanna i toppläget i tre sekunder.','Sänk tillbaka foten kontrollerat.'],'Tre sekunders paus, sedan långsamt tillbaka.',{...rep(3,12),tempo:8},'extension-pause')
    ]},
    {id:'calf', name:'Tåhävning med stöd', region:'Ben', equipment:'Stol eller stabil bänk', purpose:'Träna vadmusklerna med ett stabilt stöd.', variants:[
      variant('both','Två ben med stöd','Båda benen samtidigt',['Stå med båda fötterna i golvet och håll i ett stabilt stöd.','Lyft hälarna lugnt. Håll kvar stödet.','Sänk hälarna kontrollerat till golvet.'],'Håll i stödet under hela rörelsen.',rep(2,12),'calf-both'),
      variant('single','Ett ben med stöd','Ett ben i taget',['Håll i ett stabilt stöd och stå på det ben som ska tränas.','Lyft hälen kontrollerat. Det andra benet är avlastat.','Sänk hälen tillbaka till golvet.'],'Stödet hjälper dig att hålla balansen.',rep(3,12),'calf-single')
    ]},
    {id:'bridge', name:'Höftlyft', region:'Höft & bål', equipment:'Träningsmatta', purpose:'Träna höftens sträckning i ryggliggande.', variants:[
      variant('low','Två ben, lågt lyft','Ryggliggande',['Ligg på rygg med böjda knän och fötterna i underlaget.','Lyft bäckenet lugnt till den höjd du fått visad.','Sänk långsamt tillbaka.'],'Båda fötterna ligger kvar i underlaget.',rep(2,10),'bridge'),
      variant('pause','Två ben med paus','Ryggliggande',['Ligg på rygg med böjda knän och båda fötterna i underlaget.','Lyft bäckenet och stanna i tre sekunder.','Sänk tillbaka kontrollerat.'],'Låt lyftet komma från höfterna.',{...rep(3,10),tempo:8},'bridge-pause')
    ]},
    {id:'row', name:'Rodd med gummiband', region:'Axel', equipment:'Gummiband med säkert fäste', purpose:'Träna draget med armar och skuldror.', variants:[
      variant('light','Lätt band','Stående',['Fäst bandet säkert framför dig och håll en ände i varje hand.','Dra armbågarna bakåt nära kroppen.','För händerna tillbaka långsamt.'],'Stå stadigt och låt axlarna vara avslappnade.',rep(2,12),'row'),
      variant('build','Fler repetitioner','Stående',['Stå stadigt och kontrollera att bandet är säkert fäst.','Dra armbågarna bakåt nära kroppen.','Släpp fram händerna med kontroll.'],'Använd det band som din behandlare valt.',rep(3,15),'row')
    ]},
    {id:'rotation', name:'Utåtrotation med band', region:'Axel', equipment:'Gummiband med säkert fäste', purpose:'Träna axelns utåtrotation med armbågen nära kroppen.', variants:[
      variant('light','Lätt band, arm intill','Armbågen intill kroppen',['Stå med bandet säkert fäst vid sidan av dig.','Behåll armbågen intill kroppen och vrid underarmen utåt.','Gå långsamt tillbaka till utgångsläget.'],'Armbågen stannar kvar nära sidan.',rep(2,12),'rotation'),
      variant('build','Arm intill, fler repetitioner','Armbågen intill kroppen',['Håll i bandet med armbågen böjd och nära sidan.','Vrid underarmen utåt i den rörelse du fått visad.','Återgå långsamt utan att flytta armbågen.'],'Välj band efter din ordination.',rep(3,15),'rotation')
    ]},
    {id:'balance', name:'Enbensstående med stöd', region:'Balans', equipment:'Stabil bänk', purpose:'Öva balans med möjlighet att hålla i ett stöd.', variants:[
      variant('support','Med handstöd','Handstöd tillåtet',['Ställ dig nära ett stabilt stöd och håll i det.','Lyft ena foten lite från golvet.','Stå kvar under den angivna tiden, sätt sedan ned foten.'],'Använd stödet. Du ska inte behöva riskera att falla.',hold(2,20),'balance'),
      variant('light','Lätt handstöd','Stöd inom räckhåll',['Stå vid ett stabilt stöd.','Lyft den ena foten och håll lätt i stödet.','Stå kvar angiven tid, sätt sedan ned foten lugnt.'],'Behåll stödet nära under hela övningen.',hold(2,30),'balance')
    ]},
    {id:'abduction', name:'Benlyft åt sidan', region:'Höft & bål', equipment:'Stabil bänk', purpose:'Träna höftens rörelse åt sidan med stöd.', variants:[
      variant('support','Stående med stöd','Handstöd',['Håll i en stabil bänk med kroppen upprätt.','För det valda benet lugnt åt sidan.','För tillbaka benet utan att luta överkroppen.'],'Gör hellre ett litet, kontrollerat lyft.',rep(2,10),'abduction'),
      variant('build','Stående, fler repetitioner','Handstöd',['Stå stadigt med händerna på ett stöd.','Lyft det valda benet åt sidan med kontroll.','För tillbaka benet långsamt.'],'Håll överkroppen stilla.',rep(3,12),'abduction')
    ]}
  ];
  // Base variants predate clinical tags; constraints must also cover these entries.
  for (const e of exercises) for (const v of e.variants) {
    if (e.id === 'bridge') v.tags = {...v.tags, floor:true};
    if (e.id === 'row' || e.id === 'rotation') v.tags = {...v.tags, band:true};
  }
  const templates = [
    {id:'chair', name:'Stol & stående', detail:'Fyra exempelövningar för ben och balans.', items:[['chair','support','simultaneous'],['extension','easy','both'],['calf','both','simultaneous'],['balance','support','both']]},
    {id:'shoulder', name:'Axel & skuldror', detail:'Två bandövningar att anpassa efter undersökning.', items:[['row','light','simultaneous'],['rotation','light','both']]},
    {id:'hip', name:'Höft & bål', detail:'Tre exempelövningar med och utan matta.', items:[['bridge','low','simultaneous'],['abduction','support','both'],['chair','support','simultaneous']]}
  ];
  root.RedaData = {version:'2.0-prototype.1', exercises, templates};
})(typeof window !== 'undefined' ? window : globalThis);
