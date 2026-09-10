# Reda · beslutad produktmodell

Uppdaterad 2026-09-10 efter Carl-Roberts korrigering. Detta ersätter tidigare krav på ett distanspaket med två avstämningar och en avslutande kontakt, och principen att varje progressionssteg kräver ett nytt behandlarbeslut. Äldre leveransnoteringar längre ned är historik, inte överordnade produktkrav.

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
2. Säker insamling av uppföljt träningssvar och övrig belastning. Serverägd, versionsbunden ram med verkligt godkännande och bestående bedömningsärenden. Konflikter ska lösas på servern, inte via klientflaggor.
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
