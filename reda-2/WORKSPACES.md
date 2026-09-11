# Reda · arbetsytor och team · 2026-09-11

Detta utvecklingsblock inför organisationsgränser i den anslutna kliniken. Det öppnar inte onboarding av nya kliniker, patientaktivering, försäljning eller AI för patienter. Införande och verifiering följs i PR #31.

## Levererad funktion

- Kansei är en klinikorganisation. Redas direktverksamhet är en separat organisation utan kliniska patienter eller ordinationsflöde.
- Samma person kan ha olika medlemskap och roller i flera arbetsytor. Varje flik väljer arbetsyta separat. Varken JWT, användarmetadata eller namn ger organisationsbehörighet.
- En patientrelation hör till en organisation och en ansvarig behandlare. Endast behandlaren med aktiv klinisk behörighet får se och arbeta med sina tilldelade patienter. Andra behandlare i samma klinik får inte automatiskt tillgång.
- Organisationsroller är ägare, administration, ekonomi och teammedlem. Behandlarbehörighet är ett separat tillstånd och kräver även ett i förväg godkänt behandlarkonto. Ägarskap ger ingen automatisk klinisk läsrätt.
- Teamvyn visar medlemmar och roller. Ägare kan granska och spara en exakt rolländring eller återkallelse för ett redan provisionerat medlemskap. Versionskontroll stoppar gamla formulär. Arbetsytan måste behålla en aktiv ägare. Ändringar loggas och de senaste 20 visas för ägaren.
- Patientlistan, redigeraren och översikten töms vid byte. Sena svar från föregående arbetsyta ignoreras. Redan påbörjade API-anrop behåller sin ursprungliga arbetsyta även om hämtning av inloggningen dröjer.
- Inloggning läser aktuella medlemskap. Den tidigare automatiska uppskrivningen av en behandlarprofil vid inloggning är borttagen. Återkallat medlemskap kan inte återställas genom att logga in igen.

Ekonomirollen är en behörighetsgräns inför kommande ekonomifunktioner; ingen intäktsdashboard eller fakturering påstås vara implementerad.

## Datagräns och serverkontroll

`reda_patients.organization_id` är organisationens ankare. Barnobjekt ärver organisationen genom patientrelationen. Sammansatta främmande nycklar binder ordination, planversion, pass, svar, ram, beslut, ärende och kliniskt ställningstagande till samma patient. En plan eller ett patientobjekt får inte byta identitet, relation, ansvarig eller version genom en vanlig uppdatering.

Klinikens dataanrop bär `x-reda-organization`. Det anger önskad kontext, aldrig behörighet. Servern kontrollerar live-session, MFA, aktiv organisation, aktivt medlemskap, klinisk behörighet och patienttilldelning. Saknad eller ogiltig kontext ger ingen klinisk åtkomst. RLS täcker tabelläsning och utkast; samma regler finns i de privata funktionerna för kliniköversikt, progressionsramar, bedömningar och motorprövning.

Patientens anrop härleder organisation från den egna patientrelationen och det faktiska plan-/pass-ID:t. Patienter kan fortsatt läsa befintliga egna planer och lämna svar om en behandlares medlemskap återkallas, men motorn blockerar progression med `clinician_authority`. En avstängd organisation ger ingen patientåtkomst. Patientdialogen får bara den egna aktuella planens minimerade kontext. Modell och klient får inte ange ett alternativt medlemskap som auktoritet.

Rolländringar tar organisationslås före medlemskapet. Kliniska skrivningar tar organisationslås före patient/plan/evidens och kontrollerar behörigheten efter låset. Det gör att en återkallelse och en samtidig skrivning får en bestämd ordning. Det som redan hämtats av en behörig klient kan inte göras osedd; nya serveranrop kontrolleras alltid igen.

Organisationer, medlemskap och rollhistorik saknar allmän tabellåtkomst. Smala funktioner lämnar bara den aktuella användarens arbetsytor och tillåtna teamuppgifter. Säkerhetsdefinierande funktioner ligger i `private`, har tom sökväg och uttryckliga exekveringsrättigheter. Inga RLS-policyer på äldre tabeller ligger kvar och breddar de nya reglerna med ett alternativt tillstånd.

`save-session` använder användarens autentiserade klient och `reda_sync_session`, som kontrollerar en verklig aktiv session i samma databastransaktion före skrivningen. `invite-patient`, `activate-plan` och den gamla tjänsteinterna aktiveringsrutinen är stängda. Den publika arbetsyteinformationen anger `activation_enabled=false`. Att öppna igen kräver ett eget granskat aktiveringsblock, inklusive inbjudans relation, organisationsgräns och omsändning.

## Migration och verifiering

`secure/organizations.sql` och `secure/organization-runtime.sql` ska tillämpas tillsammans i en atomär hanterad migration, efter tidigare runtime och clinic-intelligence. Första filen kräver exakt en aktiv behandlare som matchar den befintliga godkännandelistan och att alla äldre patientrelationer hör till den behandlaren. Oväntade ägare avbryter migrationen; ingen heuristisk hopslagning görs. Inga planpayloads eller historiska ID:n skrivs om.

Verifiera före/efter: antal och kontrollsummor för befintliga patienter (utan ny organisationskolumn), planer, pass, svar, ramar, beslut och ärenden; alla patienter har rätt organisation och medlemsrelation; automatiska motorsteg och patient-AI är av. Kör säkerhets- och prestandarådgivare. Driftsätt matchande Edge-funktioner före den nya klienten. Äldre klinikklienter utan arbetsytekontext får stängd åtkomst och behöver laddas om. Återgång till en klient utan kontext är ingen fungerande återställning av klinikflödet; behåll isoleringen och rätta framåt.

CI provar migrationen med bevarade planpayloads, två fiktiva kliniker och direktverksamhet, samma behandlare i båda klinikerna, olika tilldelningar, ägare utan klinikroll, administration/ekonomi, alla kliniska listor och relevanta RPC:er, manipulerade objektrelationer, återkallade medlemskap/sessioner, avstängd organisation, gamla rollrevisioner och samtidiga ägarändringar. Browserprov täcker sena svar efter arbetsytebyte, granskning av behörighetsändring, tömning av patientvyn och mobil layout. Befintliga patient-, ordinations- och motortester körs också.

Filer, export, RAG och generell AI-analys finns inte i dessa arbetsytor ännu och får inte beskrivas som färdigtestade funktioner. Deras framtida åtkomst måste använda samma datagräns och få egna negativa tester.

## Nästa delar

1. Kontrollerad organisations- och kontoprovisionering med accepterade medlemskap, verifierad behörighet och fullständigt inbjudningsflöde. Inga verkliga kliniker eller personer läggs till i detta block.
2. Flera samtidiga patientrelationer för samma inloggningsidentitet, patientens val av relation och kontrollerat byte av ansvarig behandlare. Den befintliga globala unikheten för patientens `auth_user_id` behålls tills hela patient- och distributionsflödet stödjer detta; appen förenar inte relationer automatiskt.
3. Betalda stödperioder, säljare och licensrättigheter med fiktiva betalhändelser, följt av läsande assistent och versionsbundna godkännanden. Klinikens kunder och Redas direktkunder ska behålla separata säljarrelationer.
4. Självguidat träningsspår, supportverktyg och kontrollerad pilot efter respektive funktionsgranskning. Ingen prislisteberäkning får presenteras som verklig intäkt.

Rörelseillustrationer, klinisk innehållsgranskning, hela distributionskedjan och test av återställning kvarstår som pilotkrav.
