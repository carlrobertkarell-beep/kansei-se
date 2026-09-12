# Rörelseguide och hjälp inne i övningen

Patientspelaren visar aktuell omgångs sida, rörelsens fas och en separat demonstration. Uppspelningen registrerar inga repetitioner och dess visningshastighet är inte ordinerat tempo eller hålltid. Den individuella ordinationen ligger kvar som text. Fritext om rörelseomfång omvandlas aldrig till en påstått individuell animation.

Rörelsestudio 5 förbättrar den gemensamma figuren för de 14 uttryckligen stödda varianterna. De fem referensfamiljerna är uppresning från stol, sittande benspark, bilateral tåhävning, bilateralt höftlyft och step-up. Benpress och två RFESS-varianter använder samma illustration. Övriga varianter har kvar tidigare renderare. Kameran speglas inte för att antyda anatomisk sida; patientens sida anges uttryckligen och växlar med den ordinerade omgången.

## Patientens flöde

Under en övning kan patienten öppna **Osäker på något?** och välja startposition, utförande, sida, rörelseomfång eller dos. Förklaringen kommer från den sparade övningen, inklusive eventuellt godkänt passalternativ. Relevanta lägen och kontaktpunkter kan visas i demonstrationen. Saknade instruktioner fylls inte ut med nya kliniska råd.

En öppnad förklaring sparas inte automatiskt. Patienten väljer **Ja, nu förstår jag** eller ber behandlaren om hjälp, med valfri kommentar. Först efter serverkvittens visas sparat resultat. Under sparning låses byte av övning, passavslut och utloggning. Vid fel behålls val och kommentar i den öppna vyn; samma begäran återanvänds vid oförändrat återförsök. Ingen extra hälsodata skrivs till localStorage. Omladdning före kvittens kan därför förlora osparad frågetext.

## Server och klinik

`exercise-help.sql` inför en immutable återkoppling bunden till patientens verkliga serverpass, planversion och övning. Servern hämtar övningen och alternativet ur passets egen plan. Ett pågående äldre pass behåller sin historiska ordination. Nya rapporter på avslutade pass nekas; redan sparade kvittenser går att hämta igen.

Ett kvarstående hjälpbehov skapar ett riktigt `execution_help`-ärende och använder befintligt mandat för intern uppföljning. Dashboard, global inkorg och patientens uppföljning får samma källunderlag. Ärendet blockerar progression enligt befintliga regler. Att patienten förstår en senare förklaring stänger inte tidigare ärenden eller meddelanden. Ett tydlighetskvitto är patientens egen upplevelse, inte en klinisk bedömning eller ett bevis på korrekt utförande.

Varje rapport får egen händelse i aktivitetsloggen och gör tidigare granskningsunderlag inaktuellt. Befintliga datumfilter, stabil paginering och skillnaden mellan patientens och klinikens synliga information behålls. RLS, verifierad levande session, aktiv patient, arbetsyta och klinikens MFA gäller. Browsern saknar direkt skrivrättighet. Tabellen lagrar källövningen och hjälpversionen för spårbarhet; framtida förklaringsversioner måste behålla tidigare versioners betydelse.

## Granskning och drift

`exercise-guide.html` visar fem fiktiva exempel och samma hjälpkomponent. Den anropar ingen backend, kontaktar ingen och lagrar ingen återkoppling. `motion-reference.html` visar referensrörelsernas lägen och uppspelning. Geometritester och renderade bilder ersätter inte klinisk granskning av rörelserna eller test med patienter på riktiga telefoner.

Automatisk klinisk tillämpning, externa AI-frågor och patientdistribution öppnas inte av denna migration. Patientpilot kräver fortfarande klinisk granskning och det verkliga distributionsprovet enligt `CLINICAL-HANDOVER.md` och `../INTELLIGENCE-WORKFLOW.md`. Inga inbjudningar eller mejl skickas av utvecklingen eller CI.

## Verifiering

Enhetstester kontrollerar att hjälp följer sparad ordination och aktuell sida, saknade uppgifter samt rörelsegeometri och kamera. Isolerade databastester kontrollerar ägande, återförsök, oföränderlig källa, historiskt pass, godkänt alternativ, exakt en ärendekälla, logg och klinikens underlag. Webbläsartester använder de verkliga sidorna med fiktiva API-svar och provar förståelse, hjälpärende, förlorad kvittens, lås under sparning, reducerad rörelse, mobilvy och kliniköversikt.
