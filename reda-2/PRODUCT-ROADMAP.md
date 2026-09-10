# Reda · den verkligt stora utvecklingen

Detta dokument är produktkravet, inte en idélista. Reda ska ersätta merparten av manuellt mailande, skapande och justerande av hemprogram utan att ta kliniska beslut från behandlaren.

## Produktprincip
**Behandlaren bedömer, ordinerar och beslutar progression. Reda gör ordinationen snabb att skapa, entydig att följa och enkel att utvärdera.**

Patientens normala flöde: öppna → förstå → träna → logga → följ aktuell nivå → avstämning på klinik eller distans → ny klinisk bedömning → ny version.

Klinikens normala flöde: välj blueprint → ange få individuella förutsättningar → granska färdigt förslag → dela. Mål: en vanlig plan ska kunna granskas och delas på cirka 60–90 sekunder efter klinisk bedömning.

## 1. Klinisk blueprintmotor
- Blueprints beskriver funktioner/delmål, inte bara fasta listor av övningar.
- Samma blueprint ska kunna ge olika övningsvarianter, dos, stöd och presentation.
- Separata dimensioner: aktuell belastningstolerans, praktisk kapacitet, träningsvana/presentationsbehov, miljö/utrustning och patientens faktiska mål.
- Ålder och kön får aldrig ensamma styra svårighetsgrad eller ton.
- Inget automatiskt byte till nästa nivå. Progression kräver behandlarbeslut.
- Om inga godkända alternativ matchar ska systemet flagga detta, inte hitta på en övning.

## 2. Övningsgraf och variantsystem
Varje övningsfamilj ska ha kliniskt granskade varianter med stabila ID:n. Variant äger:
- utgångsläge och stöd
- sida
- rörelseinstruktion
- dosram
- utrustning
- animationsspecifikation
- kort cue
- fördjupad hjälp
- tillåtna föregående/nästa varianter för behandlarens progressionsträd

Exempel: höftlyft kan ha högre underlag, standard, paus, band, extern belastning, unilateral och fot upphöjd. Att en variant ligger senare i grafen betyder inte att appen får låsa upp den.

## 3. Patientpresentation som egen dimension
Minst tre presentationsprofiler: tydlig guidning, standard och träningsvan. De ändrar språk, detaljnivå och hjälp, aldrig den kliniska dosen. Patienten ska kunna välja mer hjälp utan att ordinationen ändras.

## 4. Rörelseillustrationer
- Ingen filmning av behandlare krävs.
- Varje godkänd variant ska ha en kontrollerad rörlig illustration med rätt stöd, sida, utrustning, rörelse och pauser.
- Samma rörelsedata ska kunna renderas som demonstration, långsam visning, stilla steg och träningsguidning.
- Generativ AI får användas i produktionsflödet för att skapa material, men patienten ska se en versionslåst, kliniskt granskad illustration. Ingen fri videogenerering vid varje öppning.
- Reduced-motion och stillbildsalternativ ska finnas.

## 5. Patientappen
- Idag, Mitt program, Uppföljning.
- En övning i taget under pass.
- Allt som behövs för genomförandet: variant, sida, stöd, utrustning, dos, vila och hjälp.
- Påbörjat, delvis genomfört, genomfört, överhoppat och planerad vila skiljs åt.
- Patienten kan markera lätt/lagom/tung och problem, men detta ändrar aldrig programmet automatiskt.
- Planerad avstämning och budskapet att nästa progression beslutas vid klinisk uppföljning är en permanent del av planen.

## 6. Klinikens snabbflöde
- Favoritblueprints och senast använda först.
- Lokal/snabb strukturerad input samt senare säker AI-tolkning av diktat.
- Förslag ska bygga endast på godkända övningsvarianter och behandlarens val.
- Detaljredigering finns som sekundärt läge.
- Förhandsvisning visar exakt patientens version.
- En godkänd plan publiceras utan separat PDF eller manuellt träningsmail.

## 7. Säker distribution och versionshantering
Före verkliga patienter krävs separat backend med autentisering, behörighet, säker lagring, återställning och revisionslogg. Publika URL-fragment är endast prototyp.
- Patient har en stabil åtkomst till aktuell godkänd plan.
- Ny planversion ersätter inte pågående pass mitt i ett träningspass.
- Historik bevaras.
- Kliniken kan se mottagen/synkroniserad status utan falska kvitton.
- Patientidentifierbara hälsouppgifter ska inte ligga i det publika GitHub-repot.

## 8. Uppföljning och klinikdashboard
Inför återbesök ska Reda sammanfatta:
- följsamhet mot planerade pass
- delvisa/överhoppade övningar
- återkommande problem per övning
- patientens belastningsskattning
- patientens mål
- aktuell programversion
Dashboarden ska prioritera avvikelser och minska, inte skapa, en ny inkorg.

## 9. AI i Reda
AI får hjälpa till med strukturering och presentation, men kliniska regler är deterministiska och behandlarstyrda.
- Diktat → strukturerat utkast → behandlargranskning.
- AI får inte själv diagnostisera, ordinera ny behandling eller progrediera.
- AI får föreslå formuleringar och matcha till redan godkända alternativ inom tydliga ramar.
- All AI-användning med verkliga patientdata kräver separat säkerhets- och integritetsarkitektur.

## 10. Produktionskrav före ersättning av gamla Reda
1. Klinisk granskning av blueprintbank, varje övningsvariant och animation.
2. Test på verklig iPhone/iPad/Android och med representativa patienter.
3. Säker backend och autentisering.
4. Testad programversionering, backup och återställning.
5. Kontrollerad migrering av gamla program; gamla Reda tas inte bort innan detta är verifierat.
6. Patientinformation om vad som sparas, skickas och syns för kliniken måste vara entydig.
7. Tillgänglighetsgranskning och felhantering.

## Nuvarande utvecklingsordning
**A.** Utöka blueprintbank + övningsgraf + snabbordination.  
**B.** Bygg animationsspecifikation och kvalitetssäkrat illustrationsbibliotek.  
**C.** Bygg säker patientdistribution, programversioner och synk.  
**D.** Bygg klinikdashboard och återbesökssammanfattning.  
**E.** Lägg till säker diktat/AI-assistans och automatiserad leverans.  
**F.** Pilot med fiktiva data → intern klinikpilot → liten patientpilot → kontrollerad migrering.

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


## Beslutad affärsriktning · klinik och distans
Reda ska kunna användas av personer som aldrig besökt Kansei fysiskt. Personlig rehabilitering erbjuds med behandlarbedömning och planerade avstämningar, på klinik, på distans eller i ett kombinerat upplägg. Progression kräver ett behandlarbeslut, men beslutet kräver inte per automatik ett fysiskt återbesök.

Första tänkta distansprodukt: en avgränsad period om 6–8 veckor för en tydlig målgrupp, med första bedömning, individuell startplan, två avstämningar och avslutande uppföljning. Pris och tjänstens exakta omfattning ska fastställas och valideras inför en senare pilot. Ingen försäljning eller patientaktivering är öppnad.

Fristående träningsprogram utan individuell behandlarkontakt är en möjlig separat framtida produkt. Det ska inte blandas ihop med personlig vård. Automatisk individuell progression, generell programbutik och abonnemang ingår inte i den första distansprodukten.

### Levererat · kontaktplanering
- Versionsbunden careJourney i befintligt planinnehåll: kontaktupplägg, 6/8 veckor eller löpande klinikuppföljning, periodstart, dokumenterad bedömningsmarkering och planerade kontakter via klinik/video/telefon.
- Behandlaren begär datumförslag och granskar dem. Datumen skapar inga bokningar eller möteslänkar.
- Gränssnittet kan spara ett ofullständigt utkast. Aktiveringsknappen kräver komplett distansplanering och behandlarens bekräftelse av genomförd bedömning. Detta är ett stöd i gränssnittet, inte en ny serverregel eller en ersättning för journalföring.
- Patientvyn och uppföljningen visar samma planerade kontakter. Passerade datum markeras utan att påstå genomfört besök eller ändra träningsnivån.
- Befintlig schema 6-plan läses in inför nya ändringar. Kontaktplanering, måltext, individuellt råd och presentationsnivå behåller sparade övningsvarianter, dos och belastning. Byte av patient återställer personliga fält; patientbyte spärras medan sparning/aktivering pågår.
- Landningssidan beskriver båda kontaktsätten och anger att distansförsäljning ännu inte öppnat. Gamla patientportalen är kvar.

### Nästa steg för en säljbar distansprodukt
1. Sluttesta säker distribution och patientflöde med internt testkonto.
2. Definiera målgrupp, bedömningsunderlag, när fysisk undersökning behövs och hur försämring hanteras; behandlargranskning krävs.
3. Bygga säker insamling av inledande underlag och avstämningssvar, genomförandestatus och beslut. De ska ha egna behörigheter/revisionsspår, inte läggas i publika formulär eller låtsas vara träningspass.
4. Bokning/videosamtal, information och villkor, fastställt pris och betalning efter att lämpligt upplägg bedömts. Inga boknings- eller leveranskvitton utan verifierad tjänst.
5. Klinisk och regulatorisk genomgång, faktisk mobiltestning och därefter begränsad betald pilot med uppföljning av resultat, upplevelse och behandlartid.
