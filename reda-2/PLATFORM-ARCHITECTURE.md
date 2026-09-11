# Reda · arbetsytor, assistent och godkända åtgärder

Utvecklingsspecifikation 2026-09-11. Organisationsgränser, arbetsytebyte och teamroller är implementerade enligt [WORKSPACES.md](WORKSPACES.md). Övriga delar är målarkitektur och prioriterad backlog, inte en leverans av betalning eller autonom support. Aktuell befintlig implementation beskrivs i INTELLIGENCE-WORKFLOW.md och RUNTIME.md.

## Utgångspunkt

Dagens data binds främst till `clinician_id`, patient och planversion. Det är inte samma sak som en organisationsplattform med team, ekonomibehörighet och separata säljare. Befintlig AI-dialog tolkar ett begränsat frågekontrakt och förklarar sparad plan. Den är inte en generell klinikassistent, analysmotor eller fri planförskrivare.

Produktens område är rehabilitering och hållbar vardagsträning. Avancerade gamla exempel får finnas kvar som utvecklingshistorik, men styr inte den nya onboardingens målval, marknadsföring eller leveransordning.

## Arbetsytor och behörigheter

Föreslagna enheter: organisation, medlemskap, roll/tilldelning, kundrelation, planens ursprung, stödperiod, säljarrelation, betalningshändelse, supportärende, åtgärdsförslag och godkännande.

| Arbetsyta/roll | Tillgång |
|---|---|
| Klinikägare | Organisation, team, abonnemang och egen ekonomi. Klinisk läsrätt kräver separat vårdroll och relevant tilldelning. |
| Behandlare | Tilldelade patienter, planer och kliniska ärenden inom aktuell klinik. Inte ekonomi som standard. |
| Administration | Tillåtna administrativa uppgifter och supportstatus. Inte hälsofritext eller ordination. |
| Ekonomiansvarig | Klinikens fakturor, betalningar och definierade ekonomimått. Inte medicinska detaljer. |
| Patient/privatperson | Egna behöriga planer och relationer. Kontextbyte ska visa vilken klinik eller Redatjänst personen använder. |
| Redas plattformsägare | Plattformsekonomi och drift. Ingen automatisk tillgång till andra klinikers medicinska uppgifter. |
| Redas support | Begränsad teknisk information. Extra åtkomst måste vara motiverad, tidsbegränsad, särskilt tillåten och spårbar. |

Kansei är en klinikorganisation. Redas direktverksamhet är en annan arbetsyta/säljarkontext. Kundens klinikrelation får inte omvandlas till Redas direktrelation genom ett köp eller ett globalt användar-ID. Eventuell delning eller överlämning får ett uttryckligt tillstånd och ett versionsbundet kvitto.

Servern ska kontrollera både organisation, aktuellt medlemskap, roll och objekttilldelning i varje läsning och åtgärd. Att skicka `organization_id` från klienten är inte bevis på behörighet. Rader som hör ihop ska inte kunna peka på olika organisationer. Köer, bilagor, exporter, AI-kontext, cachenycklar och loggar behöver samma gräns. Organisation eller roll får inte väljas av modellen.

Migration ska ske stegvis: inventera befintliga ägare → skapa verifierad Kansei-organisation → bind befintliga relationer entydigt → kontrollera fullständighet → inför serverkrav/behörighetsregler → byt läsning och skrivning. Ingen automatisk sammanslagning av användare enbart efter namn eller mejl. Det införda organisationsblocket och dess verifierade migreringsväg beskrivs i WORKSPACES.md.

## Två planvägar

**Klinikplan:** klinisk bedömning, ansvarig behandlare, sparad ordination och en förhandsgodkänd ram. Motorn får pröva progression inom den ramen. Utanför ramen krävs behörig klinisk bedömning. Ett ekonomiskt godkännande ersätter inte den.

**Självguidat träningsupplägg:** separat användningsområde och granskat urval innan en lämplig plan kan köpas. Underlag: mål i vardagen, tidigare träning, genomförbar tid/frekvens, miljöer, utrustning, stödbehov, förståelse/preferenser och sådana hälsouppgifter som faktiskt behövs för lämpligheten. Diagnostiska slutsatser får inte hittas på från ett formulär. Osäkerhet eller uppgifter utanför tjänstens omfattning ger ingen planförsäljning och en lämplig kontaktväg.

En godkänd självguidningspolicy måste ange vilka användare, planer och förändringar som tillåts, vilka uppgifter som saknas och när flödet avbryts. Ägarens önskemål om automatisering är inte kliniskt underlag för policyvärden. Ålder väljer inte dos, motivation är inte bevis på tolerans och ett köpt abonnemang är inte ett progressionstillstånd. Definiera avsett ändamål och pröva den medicinska/regulatoriska bedömningen av faktisk funktion innan denna väg byggs för drift.

Motivationsstödet ska kunna hjälpa användaren välja realistiska dagar, förstå varför en övning ingår och hitta tillbaka efter avbrott. Ändrad miljö, utrustning eller träningslängd får bara ändra ordination där aktuell policy tillåter det. Inga straffande sviter eller automatiska ökningar som belöning för registrering.

## Assistentens tre sammanhang

1. **Support:** produktkunskap, verifierad drift-/synkstatus och godkända hjälpfunktioner. Börja med vanliga ärenden; visa vad assistenten faktiskt kan göra.
2. **Klinik och verksamhet:** förklara definierade mått, sammanfatta behöriga ärenden och förbereda åtgärder.
3. **Träning:** förklara personens sparade plan och verifierade motorbeslut. Återkoppling måste bekräftas före sparning. Ingen fri dosförskrivning.

Gemensam användarupplevelse är möjlig, men datatillgång, verktyg och ansvar ska vara separata. Fritext, bilagor, patientdata och externa dokument är underlag och får inte ge assistenten nya instruktioner eller rättigheter. Modellens fråga körs aldrig som fri SQL eller godtycklig kod.

## Dashboard och precisa ekonomisvar

Klinikens startvy: obearbetade bedömningsärenden, förändrade förutsättningar, inkomna svar, ofullständigt underlag och kommande slut på godkänd ram. Visa senaste synktid, datatäckning och ansvar. ”Ingen registrering” betyder inte säkert utebliven träning.

Ägarens ekonomivy: månadsintäkt, betalda perioder, återbetalningar, obetalda fakturor, använda platser, avslut och support-/AI-kostnad. Medicinsk prioritet ska inte påverkas av hur mycket personen betalar.

| Fråga | Serverkontrakt och svar |
|---|---|
| Mina tio högst betalande kunder | Begär period och vid behov avgränsning. Summera genomförda betalningar minus återbetalningar i samma valuta, ange momsvisning och källa. Exkludera obetalda fakturor/testköp. Använd bara säljarens tillåtna data. |
| Genomsnitt för den här gruppen | Fråga vilket mått som avses om det är oklart. Visa definition, tidsperiod, nämnare, bortfall och uppdateringstid. Hitta inte på innebörden av otydliga ord. |
| Vilka behöver uppföljning? | Visa faktiska öppna kliniska ärenden med skäl, tid, ansvar och underlag. Separera saknad data från rapporterad försämring. |
| Vem kan få en fortsättning? | Klinisk lämplighet och aktuell ram först. Separat kommersiellt förslag först när inga öppna hinder finns. Ingen ny medicinsk rekommendation enbart från köpdata. |

Börja med ett fåtal granskade parameterstyrda rapportfunktioner. Varje svar har källhänvisning till tillgänglig vy, mätdefinition och beräkningsperiod. Saknas betalningsintegration ska svaret säga att betaldata saknas. Man får inte beräkna ”intäkt” som antal patienter gånger ett listpris.

## Åtgärder och godkännande

Läsande analyser kan köras i den behöriga sessionen. En förberedd åtgärd ska visa mottagare/mål, exakt ändring eller meddelande, skäl, källdata med version, behörighetskrav, eventuell kostnad och sista giltighetstid. Ägaren eller rätt behörig roll kan **godkänna, neka eller begära omarbetning**. Omarbetning skapar en ny revision; gammalt godkännande gäller inte den nya texten.

Föreslaget tillståndsflöde: utkast → väntar på godkännande → godkänt → utfört. Alternativa slut är nekat, utgånget, inaktuellt eller misslyckat. Idempotent serveråtgärd och revisionslogg behövs. Kontrollera rättigheter, aktuell plan/ram, mottagare och invändningar igen precis före körning. En ny försämring efter godkännandet stoppar ett progressionserbjudande.

| Åtgärd | Första tillåtna nivå |
|---|---|
| Förklara en hjälpartikel, visa synkstatus eller räkna ett behörigt mått | Läsning, inga externa sidoeffekter. |
| Förbereda kontakt eller progressionserbjudande | Utkast med mottagare, innehåll och kliniska villkor synliga. |
| Skicka ett meddelande eller ändra en administrativ uppgift | Uttryckligt godkännande från rätt roll för den exakta åtgärden. |
| Ändra ordination utanför en redan godkänd ram | Behörig klinisk granskning och ny plan/ram, inte bara ägarklick. |
| Återbetalning, avtal, behörighetsändring, export eller borttagning | Separat verifierat flöde med adekvat roll och kontroll; inte öppet allmänt chattverktyg. |

AI ska förbereda tillräckligt väl för ett snabbt beslut. Den ska inte be om ett nytt godkännande för varje rutinmässigt motorsteg som redan ligger i en giltig klinisk ram. Schemalagda sammanställningar kan senare skapa interna förslag enligt ägarens inställningar; de innebär inte tillstånd att kontakta patienter automatiskt.

## Support som löser problem

Offentligt nu: sökbara via webbläsaren och expanderbara hjälpsvar, programlänk och tydligt mejlsteg. Ingen låtsaschatt eller påstådd automation.

Nästa implementation: användarvalt problem → kunskapsartikel → behörig statuskontroll → tillåten åtgärd med kvitto → fråga om det fungerade. Om det inte går: erbjud överlämning med ärendekategori, felkod, produktversion, redan provade steg och användargranskad sammanfattning. Ingen tyst bifogning av hela journaler eller konversationer. Kliniska frågor går till ansvarig vårdkontakt, tekniska till Redas support; andras patientärenden ska inte rutinmässigt hamna hos Carl-Robert.

Mät lösta och återöppnade ärenden, felaktigt markerat löst, eskalering och faktisk handläggningstid. ”AI svarade” räknas inte som ”problemet löst”. Ge alltid en rimlig väg vidare utan att tvinga användaren genom upprepad misslyckad chatt.

## Leveransordning och acceptans

1. **Offentlig presentation och självhjälp:** kommer snart på Reda, Kanseis startsida och rehabsida; korrekt logga; gamla programvägen kvar; mobil/desktop och utan JavaScript.
2. **Organisation och roller:** två fiktiva kliniker och separat direktverksamhet; negativa tester för listor, enskilda objekt, relationer, filer, export, AI, återkallat medlemskap och samtidiga arbetsytor. Migreringskontroll före drift. Ingen ny klinik släpps in före detta.
3. **Stödperioder och säljare:** en säljare per köp; inga dubbla rättigheter/debiteringar; läsning efter avslut; serverkontrollerad aktiv tid och klinikplatser. Först fiktiva betalhändelser.
4. **Läsande assistent och godkännandekö:** tre definierade rapporter ovan, verkliga källor, isolerade behörigheter, föråldrade förslag, nekande/omarbetning, dubbelklick och återkallad behörighet provas. Inga patientutskick i första blocket.
5. **Självguidat träningsspår:** granskat användningsområde, onboarding, lämplighet och tillåtna steg; användartest med vardagsmål och flera miljöer. Bedömningsgränser och säkerhetsutfall provas innan köp kan öppnas.
6. **Betalning och kontrollerad pilot:** kostnadsuppföljning, kvitton/friskvårdsavgränsning, villkor, avbrott, uppsägning, återbetalning och distributionsprov. Patientaktivering och försäljning kräver fortfarande separat klartecken.

Arbetet med rörelseillustrationer, verkligt distributionsprov, skuggbeslut, klinisk granskning, större historik och återställning finns kvar. Den nya affärsmodellen ersätter inte dessa kvalitetskrav.
