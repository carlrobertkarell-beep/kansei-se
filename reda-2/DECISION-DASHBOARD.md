# Klinikens arbetsöverblick

Byggd 2026-09-11 för en patientstock som kan innehålla 1 000 patienter och 400 aktiva ordinationer. Den ersätter den tidigare fullständigt hämtade sidolistan som klinikens startsida.

## Överblick och arbetsordning

Databasen räknar hela behandlarens tilldelade patientstock i vald arbetsyta. Den skickar högst 25 patientrader per anrop. Sökning är skiftlägesoberoende och behandlar söktext bokstavligt. Stabil sortering har patient-ID som sista skiljekriterium. Arkiverade patienter går att söka och deras olösta signaler kan fortfarande behöva hanteras.

Fyra antal: behöver dig, planerad uppföljning, har aktiv plan, patienter totalt. Aktiv plan betyder en aktiv ordination för en aktiv patientrelation. Det är inte samma mått som registrerad träning, betalning eller kundstatus. Senaste registrerade pass och återkoppling visas separat. Frånvaro av registrering är inte bevis på utebliven träning.

Flera signaler hör till en patientrad. Nya förändringssignaler kommer före kontakt- och utförandefrågor; sedan uppföljningsdatum och stabil namnordning. Detta är arbetsordning, inte validerad medicinsk triage. En ny signal bryter igenom en tidigare planerad uppföljning. Kvitterade signaler med en framtida uppgift finns i väntelistan. Uppgifter för idag och tidigare återkommer i arbetskön.

Snabböversikten visar mål, aktuell version, datum, samlade signaler med originalkategorier och planversion, EI-prövning, övningsinstruktion och de tio senaste åtgärderna. Öppna hela patienten och gå tillbaka utan att förlora sökning eller sida.

## EI ger ett granskningsbart förslag

Förslagen i `engine/clinic-proposals.mjs` bygger på sparad återkoppling, plan och den befintliga regelmotorns resultat. De är inte fria generativa modellsvar och gör inga externa AI-anrop. Varje förslag har motivering, redigerbar anteckning och en förklaring av knappens verkan.

- Uppföljning: skapa/uppdatera en intern uppgift med datum och kvittera de visade nya signalerna. Inget meddelande skickas och ingen tid bokas.
- Genomförd uppföljning: spara behandlarens dokumentation och avsluta uppgiften. Olösta patientsignaler ligger kvar för bedömning.
- Bedömda signaler: avsluta samtliga visade olösta signaler uttryckligen, med behandlarens anteckning. Avsluta även eventuell tillhörande uppgift.
- EI-prövning: spara instämmande, avvikande eller osäker bedömning av det sparade motorbeslutet. Detta är en utvärderingsanteckning och aktiverar ingen plan.
- Förberedd ram: visa hela den redan sparade progressionskedjan och godkänn den i granskningsläge. Servern hämtar ramen från den aktuella planens `progressionDraft`; klienten eller en modell får inte leverera en annan ram till snabbåtgärden.
- Nytt underlag: pröva mot den godkända ramen och visa det sparade motorresultatet. En redan automatiskt tillämpad normal progression skapar ingen ny godkännandepunkt.

Efter en hanteringsåtgärd visar sidan kvittot och öppnar nästa tillgängliga patient på sidan. Prövning och ramgodkännande stannar på samma patient så resultatet går att läsa. Ett fel visas som ett fel; gamla antal ersätts inte med en låtsad tom arbetskö.

## Samma behörighet hela vägen

RPC:erna kräver en levande autentiserad session, MFA, aktiv behandlarbehörighet i vald organisation och egen patienttilldelning. Ägar-, admin- och ekonomirole räcker inte. Skrivning låser organisationen och sedan patienten, som befintliga kliniska skrivvägar.

En granskning binds med ett serverberäknat fingeravtryck till aktuell plan, aktivitet, återkoppling, samtliga olösta signaler, senaste motorbeslut, ram och uppföljningsuppgift. Nytt underlag eller en konkurrerande åtgärd ger `40001` och kräver att behandlaren läser om förslaget. Samma begärans-ID och identiskt innehåll ger samma kvitto utan dubbla uppgifter eller auditposter. Ett återförsök kontrollerar fortfarande aktuell behörighet. Kvittot är oföränderligt och anteckningen sparas på servern. Inga patientuppgifter läggs i webbläsarlagring av dashboarden.

## Driftgräns och verifiering

Det här blocket öppnar inte patientaktivering, inbjudningar, försäljning, automatisk progression eller externa patientfrågor till AI. Meddelandeutkast och ett godkänn/skicka-flöde med leveransstatus ingår ännu inte; gränssnittet säger därför uttryckligen när kontakten är en intern arbetsuppgift.

Kontrollerna använder fiktiva uppgifter: 1 000 patienter, 400 aktiva planer, sökning och sidgränser; grupperade och nytillkomna signaler; planbyte; återförsök; samtidiga godkännanden; MFA och återkallad behörighet; fel och fördröjda svar vid byte av arbetsyta; ett komplett snabbåtgärdsflöde; mobil- och skrivbordslayout. Databastesterna körs i en tom, separat CI-databas. Testdata importeras aldrig till produktionsprojektet.
