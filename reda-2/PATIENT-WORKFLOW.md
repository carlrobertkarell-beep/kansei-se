# Patientstart och klinisk överblick

## Vad vi försöker lösa

En patientlista med namn och statistik räcker inte när kliniken har 1 000 patienter och 400 aktiva planer. Behandlaren behöver kunna förstå vem personen är i behandlingen, vad som hänt och vad som ska göras, utan att läsa hela kortet.

Denna version ersätter namnfrågan med ett patientflöde: sök befintlig person, fyll i eller hämta uppgifter, granska eventuella dubbletter och fortsätt till planen. Uppgifterna återanvänds i listan och planstarten. Befintliga utkast kan återupptas.

## Jämförelse med etablerade system, kontrollerad 11 september 2026

| System | Verifierad funktion | Konsekvens för Reda |
| --- | --- | --- |
| [Jane](https://jane.app/features/intake-forms) | Formulär före besöket, automatiskt sparade på patienten, rapport över ofärdiga formulär. | Uppgifter ska registreras en gång och följa med till nästa arbetsmoment. Reda har ännu inget automatiskt patientformulär. |
| [Cliniko](https://www.cliniko.com/features/health-records/) | Sökbar historik, anpassade patientfält, tydliga medicinska noteringar, fästa anteckningar och utkast. | Visa behandlingsfokus, mål och en kort relevant notering direkt i arbetslistan. Låt sparade utkast gå att fortsätta. |
| [Physitrack med PPMP](https://support.physitrack.com/article/327-ppmp-integration-guide) | Öppnar vald patient i Physitrack från journalsystemet när integrationen är aktiverad. | En framtida direktkoppling ska föra användaren till rätt person utan ny registrering. |
| [Bokadirekt API & Webhooks](https://business.bokadirekt.se/funktioner/api-webhooks) | Läsåtkomst till kunder och bokningar; OAuth2 och API-nycklar med avgränsade behörigheter. OpenAPI-specifikation delas vid uppstart. | En riktig koppling är möjlig att utreda. Ingen anslutning eller specifikation för Kanseis konto finns i detta projekt. |

Detta är en jämförelse av dokumenterade flöden, inte ett belägg för att Reda redan är bättre eller snabbare. Nästa användbarhetstest bör mäta tiden att hitta rätt patient, förklara läget och slutföra en uppgift samt antalet uppgifter som skrivs in igen.

## Genomfört

- Namn, e-post, telefon, behandlingsfokus, patientens mål, kort notering, planerad kontakt, källa och externt kund-ID. Namn krävs för en intern patientpost; saknad information framgår i överblicken. Detta är inte en fullständig journalinskrivning.
- CSV/TSV UTF-8 upp till 2 MB och 10 000 rader: kontroll av kolumner, sökning i filen och val av en person. Högst 25 träffar renderas. Endast valda och granskade fält för vald person lämnar webbläsaren. Ingen fil eller kontaktlista sparas lokalt i webbläsarlagring.
- Serverkontroll av dubbletter på namn, normaliserad kontaktuppgift och källsystemets ID. Ingen automatisk sammanslagning. Delad familjekontakt får användas efter aktiv granskning; samma externa ID stoppas. Kontrollen gäller egna tilldelade patienter i vald arbetsyta.
- Återförsök återanvänder samma begäran. Samtidiga profiländringar kräver aktuell revision. Uppdaterad profil gör tidigare beslutsunderlag inaktuellt.
- Patientens mål och kontaktadress följer med till planstarten. Kliniska övningar, dosering eller grundplan väljs inte automatiskt från importerad text. En ändring av patientens mål skriver inte om en redan aktiverad ordination.
- Arbetslistan visar fokus, mål, aktuell fas/planversion, patientrapporterad funktion med datum och planversion, registrerade pass senaste 14 dagarna, senaste pass, anslutningsstatus, relevant notering och nästa steg.
- Separata arbetslistor för åtgärdsbehov, uppföljning, kommande kontakter, planer att förbereda, aktiva och arkiverade patienter. Sökning omfattar namn, kontaktuppgifter, fokus, mål och kund-ID. Endast en sida om 25 patienter hämtas.
- Namnet öppnar snabböversikten. För patienter utan aktiv plan går huvudknappen direkt till att förbereda eller fortsätta utkastet.

## Integrationsgräns

Filimport är en engångsöverföring. Valet "Bokadirekt" anger källa, inte att en koppling är aktiv. Produktens befintliga patientaktiverings-, försäljnings- och automationsspärrar ändras inte.

För livekopplingen behövs Bokadirekts specifikation och kontoåtkomst. Börja med läsbehörighet för kunder och bokningar. Bevara källsystemets kund-ID per organisation och behandlare, visa när data hämtades, låt användaren granska matchningen och hantera ändrade uppgifter utan att skriva över kliniska bedömningar. Nästa kontakt får bara kallas bokat besök när uppgiften kommer från en verifierad bokning. Ingen synk eller mottagningsadress ska byggas mot gissade API-fält.

## Tekniskt

Migration: `secure/patient-intake.sql`. Privata profiler och återförsökskvitton saknar direkt browseråtkomst. RPC:erna kontrollerar aktiv session, MFA, klinisk medlemsroll, organisation och tilldelning. Låsordning: organisation, seriell patientstart per behandlare, patient. Skrivningar återkontrollerar behörighet efter lås. Profilrevision ingår i beslutsunderlagets ögonblicksbild. Befintliga beslut och patientdialoger behåller sina granskningsregler.

Verifiering: importformat och trasiga filer, dubbletter och återförsök, konflikt vid profiländring, behörighet mellan arbetsytor/roller, planstart med förifylld kontakt och mål samt mobil- och skrivbordsvyer. Samtliga provpatienter är fiktiva.
