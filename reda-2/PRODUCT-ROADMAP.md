## Rörelseguide och hjälp i övningen · 2026-09-12

Rörelsestudio 5 och hjälp kopplad till aktuell övning utvecklas som ett gemensamt block. Patientens förståelse kan registreras eller lämnas över som ett ärende med källövning, planversion och öppnade förklaringar. Se [flöde och gränser](secure/EXERCISE-HELP.md), [prova fiktiv guide](exercise-guide.html) och [rörelsegranskning](motion-reference.html). Klinisk granskning av rörelserna och verkligt distributionsprov återstår. Därefter prioriteras förberedda återbesök och diktat till granskningsbara utkast.

# Reda · produktplan och leveranshistorik

## Aktuell riktning · kliniker och vardagsträning · 2026-09-11

Detta avsnitt ersätter äldre kommersiella rekommendationer och prestationsinriktning nedan. Reda byggs för rehabilitering och hållbar träning i vardagen, hemma/gym/ute eller kombinationer. Hyrox, CrossFit och elitperiodisering är inte prioriterad positionering. Befintliga avancerade testfall och bibliotek tas inte bort eller ändrar redan sparade planer.

Tre ingångar: Kanseis patienter, andra klinikers egna patienter och privatpersoner som köper direkt av Reda. Kliniker behöver separata arbetsytor och teamroller. Kansei och Redas direktverksamhet separeras också. Självguidat träningsupplägg behöver en egen granskad onboarding och policy, inte bara dagens klinikmotor utan behandlare.

Abonnemang är nu huvudspår för privatpersoner och kliniker, med engångsplan som alternativ. Progression ingår i en betald stödperiod/licens; ingen extra avgift per ökning och ingen betalspärr för säkerhetsinformation. [Aktuell affärsmodell och prishypoteser](BUSINESS-MODEL.md) ersätter tidigare råd att undvika abonnemang.

[Plattformsarkitektur och acceptanskrav](PLATFORM-ARCHITECTURE.md) beskriver organisationsisolering, roller, betalrättigheter, läsande AI-analyser, support och godkända åtgärder. Organisationsisolering, arbetsytebyte och teamroller är nu implementerade; se [WORKSPACES.md](WORKSPACES.md). Onboarding av externa kliniker och övrig plattformsfunktion är fortsatt planerade delar.

Offentliga Reda-sidan är nu en avgränsad kommer-snart-presentation. Samma budskap finns på Kanseis startsida och rehabiliteringssida. En supportsida ger självhjälp och manuell kontakt. Den tidigare interaktiva demonstrationen finns kvar som ett tydligt historiskt, oindexerat utvecklingsexempel i `reda-rehab/forhandsvisning.html` med sina befintliga tester. Den länkas inte från den nya marknadssidan.

Organisations- och rollmodell har fått sitt första sammanhängande block. Nästa block: stödperioder/säljare och kontrollerad provisionering → läsande assistent och godkännandekö. Rörelsekvalitet, klinisk granskning, distributionsprov och skuggläge fortsätter som kvalitetskrav före pilot. Betalning, ny patientaktivering, patienternas externa AI och automatisk tillämpning är fortsatt av. API-anslutningen är tekniskt verifierad med fiktiva data; se INTELLIGENCE-WORKFLOW.md för faktiskt driftläge.

---

Följande avsnitt är daterad historik. Ovanstående riktning och de aktuella statusdokumenten gäller vid skillnader.

## Nästa arbetsflöde · 2026-09-11

Flerstegsvägar med ändringsjämförelser, individuellt rörelseomfång, klinisk bedömning av motorbeslut, gemensam kliniköversikt och förberedd följdfrågedialog finns nu i koden. Se [INTELLIGENCE-WORKFLOW.md](INTELLIGENCE-WORKFLOW.md) för aktuell omfattning, testmetod och kvarvarande driftsteg. Äldre begränsningar om enstegsredigerare och avsaknad av kliniköversikt nedan är ersatta. Patientaktivering, automatisk tillämpning, AI-anrop och försäljning har inte öppnats.

Uppdaterad 2026-09-11 efter Carl-Roberts korrigering. Detta ersätter tidigare krav på ett distanspaket med två avstämningar och en avslutande kontakt, och principen att varje progressionssteg kräver ett nytt behandlarbeslut. Äldre leveransnoteringar längre ned är historik, inte överordnade produktkrav.

## Senaste utvecklingsblocket · 2026-09-11

De tre valda delarna är implementerade som ett sammanhängande utvecklingsblock: serverägd progression, begränsad AI-dialog med ärendehantering och omarbetade rörelseillustrationer. Se [runtime och verifiering](RUNTIME.md) för faktisk omfattning, driftläge och kvarvarande arbete. Automatisk tillämpning och modelltrafik är fortsatt av; ingen patientaktivering sker.

[Affärslinje och kalkyl](BUSINESS-MODEL.md): inkluderad start efter besök och frivillig digital fortsättning, prisförslag 690 kr/åtta veckor. Pris, köpflöde och periodrättigheter är inte aktiverade. Behandlarminuter per period är ett centralt pilotmått.

Fortsatt prioritet: kliniskt granskade testfall och rörelser → jämförelse av skuggbeslut → modellval och svensk dialogutvärdering → fullständigt distributionsprov → kontrollerad pilot efter separat klartecken. Avancerad periodisering, journalintegration och resten av rörelsebiblioteket återstår.

Nedan följer tidigare beslut och leveranshistorik; påståenden om dåvarande tekniska läge ersätts av den daterade runtimebeskrivningen ovan.

## Exercise Intelligence · gemensamt produktbegrepp
Exercise Intelligence är Redas system för att knyta ihop förutsättningar, övningsval, genomförande, återkoppling och nästa steg. Namnet ska beskriva ett faktiskt sammanhängande beteende. Kundens löfte är att förstå sin plan och få en relevant väg framåt; behandlarens värde är bättre precision, mindre rutinadministration och tydligt underlag när egen bedömning behövs.

Gemensamma regler på alla nivåer:
- Sparad ordination och planversion är sanningskälla. Presentation, hjälptexter och AI-förklaringar får inte skapa en alternativ dos.
- Aktuell tolerans, kapacitet, träningsbakgrund, mål och miljö är olika dimensioner. Ålder väljer inte svårighetsgrad. Hyrox är nu ett uttryckligt mål i förslagsmotorn, inte ett färdigt periodiseringssystem.
- Utförandestöd kan vara kort eller stegvis utan att byta övning eller dos. Rörelsedemonstrationen kan pausas och visas långsammare eller som stillbilder.
- Patientens aktiva övning är en sammanhängande mobilspelare: namn, dos, sida, stor illustration och markering av utförd omgång i samma vy. Global navigation lämnar plats åt passet. En hel demonstration spelas en gång och stannar; instruktioner, lokal uppläsning, rörelsedelar och hjälp öppnas i separata paneler. Förstoring använder samma illustration och kan stängas med knapp eller Escape. Visning är aldrig ett kvitto på förståelse eller utförd träning.
- Läsposition och visningshastighet hålls i sidans minne per planversion, planalternativ och övning. Sidbyte bevarar läspositionen; omladdning återställer den. Vila visas bara när den är angiven i doseringen. Timern markerar aldrig nästa omgång eller fortsätter träningen automatiskt. Patientens upplevelse av övningen och nästa handling visas i samma spelare.
- Den fiktiva förhandsvisningen använder samma spelare och omgångsmodell som patientvyn. Den skickar inga uppgifter och lagrar inget. Mobilkontrollen granskar hela skärmen i 360 × 640, 390 × 844, 430 × 932 samt liggande läge och förstorad text. Klinisk granskning och prov med verkliga användare kvarstår.
- Efter ett avslutat pass rapporteras kroppens svar, funktion, återhämtning, annan belastning, genomförande och kontaktönskemål. Osäkerhet är ett giltigt svar och får inte tolkas som normalt utfall.
- Nästa progressionssteg kräver serverägd och giltig ram samt aktuellt underlag. Rapporterade svar är ännu inte automatiskt kopplade till progressionsmotorns prövningar.
- Försäljning är en frivillig fortsättningsväg. Ingen automatisk försäljning vid försämring, ingen obligatorisk serie avstämningar och inget obegränsat personligt chattlöfte.

### Implementerat i Exercise Intelligence-blocket
- Gemensam presentationsmodell i klinik, patientvy och publik demonstration. Den förklarar sparade förutsättningar och instruktioner; den påstår inte att återge en språkmodells resonemang.
- Klinikpanelen lyfter saknad individuell belastning för identifierade övningar med yttre vikt. Detta är en granskningsuppmaning, ännu ingen generell aktiveringsspärr.
- Sex korta frågor i patientvyn, med kvitto först efter serverbekräftelse. Misslyckad sparning behåller svaren och samma begäran i den öppna sidan. Dessa svar skrivs inte till webbläsarlagring.
- Separat databasmodell för svar per avslutat pass, serverbunden patient, rapportör och planversion, idempotens och revisionsspår. Stängda delvisa pass och äldre planversioner är tillåtna. Tidigast nästa kalenderdag i Stockholm och högst 14 dagar efter passet är en produktregel för rapportering, inte ett kliniskt progressionsvillkor.
- Behandlarvyn visar svar för vald planversion och lyfter försämring eller hjälpbehov. Inget svar markerar ett ärende som omhändertaget eller bokar kontakt. Hämtfel visas separat så träningen fortfarande kan användas.
- Samma begrepp på Kanseis startsida, rehabsida, Redas landningssida och progressionslaboratorium. Publik sexfrågorsdemonstration är fiktiv och lämnar inga sparade svar.

### Nästa mätbara steg
1. Serverägd godkänd ram och observationskoppling med sessions-, steg- och ramversion. Befintliga svar ska inte retroaktivt bli progressionstillstånd.
2. Bestående undantagsärenden med ansvar, kvittens och hantering; mät behandlarminuter per aktiv person och mängden onödiga respektive missade avvikelser.
3. Skuggläge mot granskade fall, sedan begränsad automatisk tillämpning. Mät överensstämmelse med behandlarens beslut innan patientdrift.
4. AI-dialog som samlar strukturerat underlag och förklarar verifierade beslut. Ingen språkmodell är ansluten ännu.
5. Kliniskt granskad rörelseproduktion, variantövergångar och aktivitetsspecifik belastning; befintliga nya kontroller ersätter inte bättre illustrationer.

Sparade svar är oföränderliga i detta block. Rättelseflöde, större historik, samtidig användning på flera enheter och faktisk mejl-/inloggningskedja behöver fortsatt arbete före pilot. Inga patienter aktiveras.

## Värdet och affären
Reda ska ge patienten ett starkt stöd och göra Kansei tydligt annorlunda. Det ska samtidigt minska manuellt planarbete och löpande kontakt, inte bygga ett nytt online-PT-jobb åt behandlaren.

En första bedömning leder till en startplan och en förberedd väg framåt. När ingen ny kontakt är bokad kan personen fortsätta inom sin aktuella plan. När en ny progressionsperiod är relevant ska två frivilliga vägar finnas:
- Digital progressionsplan: motorn bär det löpande arbetet inom godkända ramar. Ingen serie av obligatoriska samtal ingår som grundmodell.
- Fysiskt återbesök: analys, behandling när det är relevant och uppdatering av träningen i Reda.

Ett redan bokat relevant återbesök ska inte konkurrera med ett automatiskt köperbjudande. Nya eller försämrade besvär ska leda till rätt bedömningsväg före försäljning. En redan ordinerad plan och historik ska inte låsas bakom förnyad betalning. En avslutad ram betyder inte att rehabiliteringen är färdig.

Nya kunder utan tidigare besök är nästa ingång, efter att fortsatt träning från en känd bedömning fungerar. Digitalt inledande underlag behöver bedömas för lämplighet; generiska program får inte presenteras som individuellt undersökt rehabilitering.

Pris är inte beslutat. Referensen är 890 kr för ett 45-minutersbesök. Ett digitalt erbjudande ska bära AI-/infrastrukturkostnad och verklig undantagstid och ge ett tydligt värde för personen. Mät behandlarminuter per aktiv person och period, kostnad per prövning, andel som kräver bedömning, faktisk användning och relevant måluppfyllelse före prissättning. Intäkt är inte samma sak som lönsamhet. Obegränsad personlig chatt ska inte smygas in i omfattningen.

## Motorns ansvar
Behandlaren bedömer utgångspunkten och godkänner en begränsad progressionsväg i förväg. Motorn prövar stegen mot tillräckligt och aktuellt underlag. Ett nytt besök ska inte krävas bara för ett redan förberett steg.

Motorn behöver skilja mellan:
1. Nästa steg inom ramen.
2. Behållen ordination medan mer tid eller underlag behövs.
3. Behov av ny bedömning eller ändrade förutsättningar.
4. Slut på den godkända ramen och behov av en fortsatt väg.

Ingen kalenderstyrd ökning och ingen belöning i form av tyngre träning bara för att personen kryssat av pass. Träningssvar, teknik/utförande, svaret efter träningen, återhämtning, övrig träning och målriktning ska vägas in. Okänt är inte samma sak som normalt. Inga universella smärtgränser utan kliniskt underlag.

## Från vardagsfunktion till prestation
Separata dimensioner: aktuell tolerans, faktisk kapacitet, träningsvana, stöd/presentation, tillgänglig miljö och utrustning, mål, samlad träningsbelastning och återhämtning. Ålder väljer inte nivå.

Vardagsfunktionen kan behöva handstöd, stora tydliga instruktioner och funktionsmål. Avancerad träning behöver relevanta belastningssteg, träningsvolym, ansträngningsmål och senare periodisering mot aktivitet/tävling. Hyrox kräver att löpning och stationer ingår i den totala belastningsbilden. Det befintliga övningsbiblioteket och den nya simuleringen utgör inte ett färdigt prestationssystem för alla dessa mål.

Första tekniska ramen lagrar kompletta ordinationssteg. Klinikens första editor förbereder ett dossteg för en vald övning. Därefter behövs granskade variantövergångar, extern vikt/intensitet, rörelseutslag, frekvens och kombinerade krav mellan övningar. En hög träningsvana är aldrig i sig tillstånd till ett avancerat steg.

## AI:s roll
AI ska så småningom bära mycket av dialogen: förstå patientens återkoppling, ställa rätt följdfråga, förklara nästa steg, hjälpa med praktiska hinder och sammanfatta undantag för behandlaren. Det är mer än att skriva ett program en gång.

Språkmodell och progressionsmotor får olika ansvar. AI får inte hitta på en ordination utanför den verifierade ramen. Motorn kontrollerar tillåtna steg, datakvalitet och giltighet. Patientfritext och modellresultat är underlag, inte instruktioner till systemet. Strukturerade uppgifter måste valideras. Vid osäker tolkning ska modellen fråga eller lämna uppgiften okänd, inte fylla i ett lugnande svar.

Ingen språkmodell är ansluten i detta block. Det finns ett begränsat förklaringskontrakt till en framtida språkmodell. Innan verkliga uppgifter behandlas behövs säker serverintegration, dataminimering, behörigheter, revisionsspår och validering av modellens beteende.

## Levererat i detta block
- Kontaktplanering är frivillig. Distans kräver fortfarande registrerad bedömning i gränssnittet men inte sex/åtta veckor eller tre bokade kontakter.
- Versionsbunden, regelbaserad progressionskärna med kompletta steg, giltighetstid och explicita villkor. Saknade svar, historik från fel steg/version, motstridiga dubletter, pågående pass, samlad belastning och förändrade besvär hanteras separat.
- Behandlaren kan förbereda ett nästa dossteg med egna villkor och spara det med planutkastet. Ändrad ordination gör ramen inaktuell. Den körs inte i patientvyn.
- Interaktivt utvecklingsrum: /reda-2/progression-lab.html. Fiktiva fall för vardagsfunktion, Hyrox och avancerad styrka, återkoppling och prövning genom flera steg. Alla doser och villkor är testdata.
- Landningssidan beskriver den nya riktningen och de två fortsättningsvägarna. Digital försäljning är inte öppen.

## Nästa utvecklingsordning
1. Klinisk genomgång av modellens tillåtna steg, observationsvillkor och eskalering för en första avgränsad målgrupp. Granska rörelserna parallellt; utöka de fem nya referensfamiljerna efter godkännande.
2. Insamlingen av uppföljt träningssvar finns i Exercise Intelligence-blocket ovan. Nästa del är en serverägd, versionsbunden ram med verkligt godkännande och bestående bedömningsärenden. Konflikter ska lösas på servern, inte via klientflaggor.
3. Kör motorn i skuggläge mot kliniska fall: jämför vad den föreslår med vad behandlaren beslutar. Mät både missade avvikelser och onödiga larm.
4. Anslut AI för strukturerad dialog och tydliga förklaringar inom samma kontrakt. Kliniken får undantag med skäl och underlag, inte en osorterad inkorg.
5. Säker tillämpning: en idempotent servertransaktion kontrollerar aktuell planversion, ramversion, återkallat godkännande och öppna pass. Nästa steg blir ny historiserad ordination. Perioden och träningsunderlaget nollställs för nästa steg; gammal historik finns kvar.
6. Fortsatt digital period: tydlig omfattning, rimlig svarsförväntan, pris/betalning och relation till bokade återbesök. Återkommande besvär hanteras före köp. Modellens faktiska undantagstid måste passa affären.
7. Klinisk/regulatorisk genomgång, faktisk mobiltestning och kontrollerad patientpilot. Ingen användaraktivering före separat klartecken. Gamla Reda behålls under verifierad övergång.

Verkligt distributionsprov, serverkonflikter, större historik, backup/återställning, illustrationer och journalintegration ligger fortsatt kvar. De är inte bortprioriterade eller klara genom denna modelländring.

## Tidigare leveranshistorik
Äldre text om att all progression sker vid avstämning beskriver dåvarande beteende. Produktmodellen ovan gäller framåt. Den aktiverade patientappen ligger fortfarande kvar på sin publicerade ordination tills den nya motorn validerats och anslutits säkert.

## Levererat i nästa block · 2026-09-10
- Fördjupningen från PR 15 ingår: separata rörelsespecifikationer och metadata för avancerade varianter i knä, axel, vad/Achilles och höft. Illustrationerna är fortsatt märkta för klinisk granskning.
- Klinikvyn kan justera tillåtna varianter, sida, omgångar, repetitioner, hålltid, vila, tempo och behandlarangiven belastning direkt i förslaget. Variantbyte följer med till instruktion, rörelse och metadata.
- Motorn släpper inte längre golv-, band- eller gymbegränsningar när ingen variant passar. Ofullständiga förslag markeras och kan inte aktiveras i gränssnittet.
- Patientens omgångar markeras i ordning, separat per sida. Paus behåller pågående pass i den öppna sidan. Felaktiga synkkvitton har tagits bort; ändringar skickas i ordning och kan provas igen. Ingen garanti för återställning efter omladdning eller stängd flik ännu.
- Patienten kan rapportera lätt/lagom/för tungt. Kliniken ser tunga och överhoppade övningar inför återbesöket.
- Redas publika startsida visar fiktiva nivåexempel genom samma planeringsmotor. Inga patienter aktiverade av detta arbete.

### Kvar före patientpilot
- Klinisk granskning av alla dosramar, varianter och rörelser, särskilt avancerade varianter.
- Återupptagning efter omladdning och versionsbyte levererad i blocket nedan; kvar är konflikter mellan samtidiga enheter och återställning om lokal lagring rensas.
- Uppföljning mot planerade dagar, historiska planversioner och mål levererad i blocket nedan; större historik och verifiering genom hela det verkliga flödet återstår.
- Säker diktat/AI-strukturering och senare koppling till journalappen.
- Verifiering på faktiska telefoner och representativa patienter; användaraktivering inväntar separat klartecken.

## Utvecklingsblock 2026-09-10 · återupptagning och referensrörelser
- Patientvyn återläser påbörjade pass från servern på samma planversion och återanvänder samma client_session_id.
- Osynkade omgångar ligger i en separat kö per autentiserat konto på enheten. Kön innehåller pass-/plan-ID, övnings-ID, omgångar och skattning, inga namn, mejladresser eller planinnehåll. Den tas bort efter lyckad synk; utloggning blockeras medan osynkade markeringar finns.
- Vid byte av plan efter omladdning kan patienten uttryckligen spara och avsluta det äldre passet. Historiken behåller dess ursprungliga planversion. Ett öppet pass byter aldrig ordination mitt i genomförandet.
- Fem referensfamiljer har fått en ny renderare med fasta segmentlängder, definierade kontaktpunkter och separata start-, rörelse- och slutlägen. Endast de uttryckligen stödda varianterna ersätts; övriga varianter är kvar för fortsatt utveckling.
- Granskningssida: /reda-2/motion-reference.html. Inget här är kliniskt godkänt.
- Nya tester täcker geometri, serveråterupptagning, lokal kö, omladdning efter misslyckad synk, versionsbyte och dubbel start. Webbläsartesterna använder en fiktiv server.

### Fortsatt test före pilot
- Verklig mejlleverans genom Supabase/Resend, engångslänk i användarens e-postklient, patientinloggning och återkoppling till klinikvyn återstår som ett sammanhängande test. DNS i Resend är verifierad; detta är inte samma sak som verifierad leverans.
- Första öppning av appen kräver nätanslutning. Offlinekön skyddar redan påbörjade markeringar; den är inte en komplett offlineapp.
- Samtidig redigering från flera flikar/enheter, serverkonflikter och återställning när lagringen rensas kräver ett eget testblock.
- Klinisk granskning av de fem rörelserna innan metoden utökas till fler varianter.


## Utvecklingsblock 2026-09-10 · landningssida och återbesök
- Publika landningssidan har fått en ny struktur: undersökning och behandlare i första vyn, konkret programvisning och tydlig information om åtkomst. Den befintliga patientportalen är fortsatt länkad.
- Fiktiv visning går från plan till övning, registrerad omgång och uppföljning. Vardag/gym/löpning använder samma planeringsmotor som tidigare. Exemplet skriver inte till lagring eller backend. Ingen automatisk animation startar.
- Klinikens återbesöksvy visar målet och återbesöksdatumet från vald publicerad planversion. Historiska övningsnamn, varianter, doser och rapporter hämtas från samma version.
- Återbesöket lyfter tunga/överhoppade övningar, delvis genomförande och belastningsskattning per övning. Jämförelse med planerade dagar räknar högst en träningsdag per datum.
- Perioden omfattar högst 14 hela kalenderdagar i Stockholm, efter aktiveringsdagen och före nästa versions aktiveringsdag. Pågående dag är inte förfallen. En saknad registrering beskrivs inte som säkert utebliven träning.
- Den befintliga hämtningen av 30 pass är oförändrad. Om denna gräns kan göra perioden ofullständig visas detta och jämförelsen med planerade dagar döljs. Längre historik kräver fortsatt utveckling.
- Sena svar vid patientbyte får inte skriva över den valda patientens uppföljning.
- Tester använder fiktiva data. Ingen ändring av autentisering, databasbehörigheter, patientaktivering eller mejlutskick.

### Kvar i prioriterad ordning efter detta block
1. Klinisk granskning av referensrörelserna; sedan fortsatt produktion av återstående varianter och bättre stöd/sida/utrustning i hela biblioteket.
2. Verkligt distributionsprov med testkonto: mejl → engångslänk → genomfört pass → synk → återbesök. Resend är DNS-verifierat, inte därmed sluttestat.
3. Samtidiga flikar/enheter, konflikter och större historik. Säkerhetskopiering/återställning ska provas före pilot.
4. Favoriter/senast använda i snabbordination, säker diktat/AI-strukturering och senare journalintegration.
5. Test på riktiga telefoner och klinisk granskning innan användare aktiveras. Befintliga Reda migreras först efter verifierad pilot.
