/* Curated booking information; no diagnosis. */
window.KanseiAreas = Object.freeze({
  back: {
    label: 'Nacke & rygg', question: 'Vad känner du i nacke eller rygg?',
    service: 'Naprapatisk bedömning', page: '/naprapati/',
    focus: 'Vi går igenom var besvären sitter, hur rörelser påverkar dem och om känsel eller styrka har förändrats.',
    imaging: 'Muskuloskeletalt ultraljud används inte för att undersöka ryggradens diskar. Behov av annan bilddiagnostik avgörs efter medicinsk bedömning.',
    patterns: [
      ['neck', 'Stel eller öm i nacken', 'Till exempel när jag vrider huvudet.', '/blogg/nacksparr-vad-gor-jag-nu/'],
      ['lower', 'Ont i ländryggen', 'Vid sittande, rörelse eller belastning.', '/blogg/ryggskott-forsta-48-timmarna/'],
      ['radiating', 'Besvären strålar ut', 'Till en arm eller ett ben.', '/blogg/ischias-nar-ar-det-brattom/'],
      ['recurring', 'Återkommande ryggbesvär', 'Jag vill förstå hur jag ska hantera dem.', '/blogg/diskbrack-symtom-forlopp-behandling/'],
      ['injury', 'Nya besvär efter en olycka', 'Efter fall, slag eller annan skada.', null, true]
    ]
  },
  shoulder: {
    label: 'Axel', question: 'Vad känner du i axeln?',
    service: 'Naprapati eller ultraljud', page: '/naprapati/',
    routes: Object.freeze({lifting:'ultraljud', night:'ultraljud', stiff:'naprapati', rehab:'ultraljud', unclear:'naprapati'}),
    focus: 'Vi undersöker rörlighet, styrka och vilka rörelser som väcker besvären. Vi går också igenom hur länge besvären har funnits och vad du har provat.',
    imaging: 'Vid vissa axelbesvär är en riktad ultraljudsundersökning ett lämpligt första besök. Vid tydlig stelhet eller när besvären är svåra att beskriva börjar vi i stället med en klinisk naprapatisk bedömning.',
    patterns: [
      ['lifting', 'Ont när jag lyfter armen', 'Till exempel över axelhöjd.', '/blogg/ont-i-axeln-nar-du-lyfter-armen/'],
      ['night', 'Värk på natten', 'Eller svårt att ligga på axeln.', '/blogg/ont-i-axeln-impingement-eller-nagot-annat/'],
      ['stiff', 'Axeln har blivit stel', 'Jag kommer inte lika långt i rörelsen.', '/blogg/frusen-skuldra-faser-och-behandling/'],
      ['rehab', 'Besvär trots rehabilitering', 'Jag vill få en ny bedömning.', '/blogg/ont-i-axeln-impingement-eller-nagot-annat/'],
      ['injury', 'Plötslig svaghet efter en skada', 'Till exempel svårt att lyfta armen efter ett fall.', null, true]
    ]
  },
  elbow: {
    label: 'Armbåge', question: 'Vad känner du vid armbågen?',
    service: 'Klinisk bedömning', page: '/naprapati/',
    focus: 'Vi undersöker rörelse, grepp, styrka och hur belastning påverkar armbågen. Vid känselbesvär behöver även nervfunktion bedömas.',
    imaging: 'Ultraljud kan komplettera undersökningen av vissa senor och ytliga strukturer. Behovet avgörs av frågeställningen.',
    patterns: [
      ['outside', 'Ont på utsidan när jag greppar', 'Vid lyft, racketspel eller vardagsarbete.', '/blogg/tennisarmbage-behandling-som-fungerar/'],
      ['inside', 'Ont på insidan', 'Till exempel vid grepp eller belastning.', '/blogg/musarm-nar-armen-sager-ifran/'],
      ['movement', 'Ont när jag böjer eller sträcker', 'Rörelsen är öm eller begränsad.', '/blogg/musarm-nar-armen-sager-ifran/'],
      ['tingling', 'Stickningar mot handen', 'Som återkommer vid vissa positioner.', '/blogg/domningar-i-handen-pa-natten/'],
      ['injury', 'Nya besvär efter fall eller slag', 'Särskilt om rörelsen är tydligt begränsad.', null, true]
    ]
  },
  hand: {
    label: 'Hand & handled', question: 'Vad känner du i hand eller handled?',
    service: 'Klinisk bedömning', page: '/naprapati/',
    focus: 'Vi går igenom rörelse, grepp och belastning. Vid domningar behöver vi även undersöka känsel och nervfunktion.',
    imaging: 'Ultraljud kan besvara vissa frågor om senor och andra ytliga strukturer. Det ersätter inte bedömning av en misstänkt skelettskada.',
    patterns: [
      ['night', 'Domningar på natten', 'Handen somnar eller fingrarna sticker.', '/blogg/domningar-i-handen-pa-natten/'],
      ['thumb', 'Ont vid tummen', 'Vid grepp eller upprepade rörelser.', '/blogg/musarm-nar-armen-sager-ifran/'],
      ['load', 'Ont när jag belastar handleden', 'Till exempel i träning eller arbete.', '/blogg/musarm-nar-armen-sager-ifran/'],
      ['stiff', 'Stelhet eller nedsatt grepp', 'Besvär som har kommit successivt.', '/blogg/karpaltunnelsyndrom-domningar-i-handerna/'],
      ['injury', 'Ont efter att jag tagit emot mig', 'Nya besvär efter fall eller skada.', null, true]
    ]
  },
  hip: {
    label: 'Höft & ljumske', question: 'Vad känner du vid höften?',
    service: 'Klinisk bedömning', page: '/naprapati/',
    focus: 'Vi undersöker höftens rörlighet, styrka och gång eller annan belastning. Vi bedömer också om besvären kan ha samband med rygg eller närliggande områden.',
    imaging: 'Vid en relevant frågeställning kan ultraljud komplettera undersökningen av mjukdelar runt höften. Alla orsaker till höftsmärta syns inte med ultraljud.',
    patterns: [
      ['side', 'Ont på höftens utsida', 'Till exempel vid sidoläge eller promenad.', '/blogg/ont-i-hoften-artros-trokanterit-eller-rygg/'],
      ['groin', 'Ont i ljumsken', 'Vid rörelse, gång eller träning.', '/blogg/ont-i-hoften-artros-trokanterit-eller-rygg/'],
      ['stiff', 'Stel efter att ha suttit', 'Svårt att komma igång eller röra höften.', '/blogg/ont-i-hoften-artros-trokanterit-eller-rygg/'],
      ['buttock', 'Ont i sätet', 'Ibland med besvär längre ned i benet.', '/blogg/ischias-nar-ar-det-brattom/'],
      ['injury', 'Smärta efter ett fall', 'Eller nytillkommen svårighet att stödja på benet.', null, true]
    ]
  },
  knee: {
    label: 'Knä', question: 'Vad känner du i knät?',
    service: 'Klinisk bedömning', page: '/naprapati/',
    focus: 'Vi undersöker rörlighet, styrka, belastning och eventuell svullnad. Vi går igenom hur besvären började och vad du vill kunna göra.',
    imaging: 'Riktat ultraljud kan ge information om vissa strukturer kring knät, men visar inte alla menisk-, korsbands- eller broskskador. Undersökningsmetod väljs efter frågeställningen.',
    patterns: [
      ['stairs', 'Ont i trappor eller när jag reser mig', 'Främst vid belastning av knät.', '/blogg/loparkna-eller-hopparkna/'],
      ['running', 'Ont vid träning eller löpning', 'Besvären kommer i samband med aktivitet.', '/blogg/loparkna-eller-hopparkna/'],
      ['swelling', 'Knät svullnar återkommande', 'Utan aktuell stor skada eller feber.', '/blogg/knaartros-vad-du-kan-gora/'],
      ['arthritis', 'Jag har konstaterad artros', 'Jag vill diskutera träning och behandlingsalternativ.', '/blogg/knaartros-vad-du-kan-gora/'],
      ['injury', 'Knät har låst sig eller nyligen skadats', 'Till exempel efter en vridning.', null, true]
    ]
  },
  foot: {
    label: 'Fot & fotled', question: 'Vad känner du i fot eller fotled?',
    service: 'Klinisk bedömning', page: '/naprapati/',
    focus: 'Vi undersöker gång, belastning, rörlighet och styrka. Du får beskriva när besvären märks mest och hur de har utvecklats.',
    imaging: 'Ultraljud kan komplettera undersökning av vissa senor och mjukdelar. Misstänkta skelettskador kan behöva annan utredning.',
    patterns: [
      ['heel', 'Ont under hälen', 'Till exempel under de första stegen på morgonen.', '/blogg/halsporre-plantarfasciit-sa-blir-du-av-med-den/'],
      ['achilles', 'Ont eller stelt i hälsenan', 'På morgonen eller i samband med träning.', '/blogg/halsenesmarta-vila-racker-inte/'],
      ['ankle', 'Fotleden känns instabil', 'Återkommande besvär efter en tidigare stukning.', '/rehabilitering/'],
      ['forefoot', 'Ont i framfoten', 'Vid gång, stående eller träning.', '/naprapati/'],
      ['injury', 'En ny skada eller ett plötsligt knäpp', 'Med svårighet att belasta eller skjuta ifrån.', null, true]
    ]
  }
});
