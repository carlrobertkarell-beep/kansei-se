# Reda 2 · fungerande patient- och klinikprototyp

Aktuell produktmodell och leveransstatus finns i [PRODUCT-ROADMAP.md](PRODUCT-ROADMAP.md). Exercise Intelligence används i den säkra klinik-/patientvyn och den publika demonstrationen. [Databaskontrakt för återkoppling](secure/TRAINING-RESPONSES.md).

Nedan följer dokumentation för den ursprungliga lokala prototypen, byggd 2026-09-09. Fristående `/reda-2/`. Inga ändringar i `/reda/`, dess service worker, programkoder, konfiguration eller localStorage-nycklar.

## Prova
Öppna `index.html` för patientflödet och `klinik.html` för programredigeraren. Vid lokal utveckling: `python -m http.server 8000` i sajtens rot, sedan `/reda-2/`.

Allt är markerat som prototyp. Endast fiktiva uppgifter. Inga riktiga patientuppgifter ska matas in. Detta är inte en kliniskt godkänd patientportal.

## Byggt
- Fristående patientskal med Idag, Mitt program och Uppföljning. Ingen klinikmarknadsföring i träningsflödet.
- Enkel start, personlig testlänk via URL-fragment, och tydlig hänvisning för gamla Reda-koder.
- 8 övningar, 16 sammanhängande varianter och 3 fiktiva startmallar. Varje variant äger illustration, stöd, instruktion och grunddos.
- Kliniken styr sida, dos, hålltid, tempo i tidsstöd, vilotid, passdagar, individuella råd och uppföljningsdatum.
- Första passet har ingen automatisk halvering. Valbar, uttrycklig lägre startdos ändrar även den faktiskt visade dosen och räknaren.
- Träningsspelare, valfri rörelsedemo, förstoring, uppläsning, valfritt tidsstöd och vilotimer. Inga kameror eller automatiska rörelsemätningar.
- Genomförande måste markeras av användaren. Timers markerar aldrig pass/omgångar som genomförda.
- Vänster/höger per omgång är uttryckligt när båda sidor ska göras. Varianter som kräver båda benen samtidigt kan inte väljas som ensidiga.
- Pausa och återuppta. Delvisa pass, överhoppade övningar och avslutade pass räknas separat. Sviter och troféer är borttagna.
- Veckoplan med vilodagar. Belastningsskattning utan automatisk ordinationsändring.
- Säkerhetskopiering/import av enbart Reda 2-testformat. Ingen gammal logg läses eller raderas.
- Sammanställning och textnedladdning. Aldrig falsk status om att kliniken mottagit något.
- Separat programredigerare med omordning utan dragkrav, övningssökning, liveförhandsvisning, utskrift, export/import och testlänk efter explicit granskning.
- Separat lokal visning av importerad fiktiv testlogg för kliniken.

## Tekniskt
Data, ordinationsregler, illustrationer, patientvy, programredigerare och stilar ligger i separata filer. Inga externa JavaScript-bibliotek, externa typsnitt, spårningsskript eller serveranrop. CSP blockerar anslutningar (`connect-src 'none'`). Delningsdata ligger i URL-fragmentet. Fragmentet är INTE krypterat eller autentiserat.

Nycklar: `reda2-prototype-v1` och `reda2-prototype-studio-v1`. Preview-länkar sparar aldrig testdata. Flera samtidigt öppna patientflikar pausas vid externa ändringar för att undvika överskrivning. Lokal lagring kan rensas/falla bort och är inte ett skyddat patientregister.

Ingen service worker registreras här. Ingen cachning eller appinstallation utlovas. De gamla filerna är byte-oförändrade. `noindex` är inte åtkomstskydd.

## Viktiga återstående steg före patientdrift
1. Klinisk granskning av varje variant, illustrerad rörelse och dos. De nya tecknade rörelserna är schematiska prototypillustrationer, inte kvalitetssäkrade instruktionsfilmer.
2. Kontrollerad migrering av hela det gamla övningsbiblioteket, med tydliga variant-ID. Inget automatiskt tolkat byte av gamla ordinationer.
3. Separat plan för autentisering, behörigheter, säker lagring, återställning, loggöverföring och kvitto från kliniken. Inga verkliga patientuppgifter innan detta är klart.
4. Övergång från gamla koder/loggar med användarbekräftelse och testad återställning. Nuvarande portal ska vara kvar tills övergången är verifierad.
5. Test på verklig iPhone/iPad/Android och med patienter, inklusive läsbarhet och övningsförståelse. Ingen full WCAG-certifiering eller klinisk validering påstås.
6. Kalenderpåminnelser, full offlinefunktion och automatisk klinikinkorg är inte del av denna prototyp.

## Tester
`node --test .github/reda2-tests/core.test.cjs`
`python .github/reda2-tests/browser_test.py` (Playwright och Chromium behövs)

Enhetstester täcker ordinationssamstämmighet, import, delning, dosering och passstatus. Webbläsartester använder endast fiktiva testdata och ska inte skicka trafik till extern bokning eller analys.
