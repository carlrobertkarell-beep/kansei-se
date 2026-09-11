# Exercise Intelligence – runtime 2026-09-11

## Vad som är byggt

- Serverägda progressionsramar med klinikerns MFA-godkännande, fullständiga steg, aktuellt plan-ID och separat körläge. Klinikvyn kan granska, godkänna i granskningsläge och återkalla. Ändrad publicerad plan återkallar föregående ram.
- SQL-motorn härleder underlaget från sparade pass och efterföljande svar. Den använder alla relevanta rader i perioden, inte klinikvyns begränsade historik. Saknad/okänd miljö, återhämtning, annat träningsarbete, ansträngning, fullständiga omgångar, dagar och nästa-dagssvar hanteras. Patientvyns `light` motsvarar policyns `easy`.
- Patientens nya fråga om utrustning/stöd/förutsättningar ger explicit svar. Gamla sexfältssvar är läsbara men räknas inte som bekräftat oförändrad miljö.
- Bestående ärenden från försämring, ändrad miljö, önskad kontakt och svårt utförande. Kvittens håller spärren kvar. Bedömning kräver en anteckning. Den kliniska hanteringen finns per vald patient; en klinikövergripande prioriterad inkorg och journalintegration återstår.
- Granskningsläge sparar beslut utan ordinationsändring. Automatisk tillämpning finns som separat servertransaktion: lås patienten, kontrollera giltigt godkännande och aktuellt underlag, historisera gammal plan och skapa exakt nästa godkända version. Nästa steg får en ny starttid och använder inte den gamla nivåns evidens.
- Pågående pass blockerar versionsbyte. Servern äger nya pass tidsstämplar. Avslutade pass kan inte öppnas eller ändras igen; samma avslut kan levereras på nytt. Rent klientstyrt `clientUpdatedAt` ignoreras i jämförelsen av identiska omsändningar.
- `reda-dialogue` har en verklig OpenAI Responses-integration med strikt schema, serverbehörighet, planminimering, kvoter, tidsgräns och validering. Modellen väljer ämne/övning och extraherar explicit citerade svar. Den skriver ingen klinisk förklaring som visas fritt, och den ändrar aldrig ordination eller sparar en rapport.
- Patienthjälpen fungerar utan modell: varför övningen finns, exakt sparad instruktion och ordinerad dos. Egen AI-fråga visas bara om backend är öppnad och konfigurerad. En föreslagen tolkning kräver att patienten själv lämnar svar i den vanliga återkopplingen.
- Rörelseillustration v4: ny figur med kläder, form, skuggning och närmare utsnitt; mjukare övergång från handstöd; fast kontakt mot stol/golv/steg; sju familjer, 14 varianter inklusive benpress och split squat med bakre fot på bänk. Övriga varianter behåller sin befintliga renderare. Det är utvecklingsmaterial, inte kliniskt godkänd rörelseproduktion.

## Driftläge

`private.reda_engine_settings` innehåller två separata brytare. **automatic_enabled=false och ai_enabled=false** vid installation. Ingen migration slår på dem. Ingen patient är aktiverad och inga utskick, bokningar eller betalningar sker av detta arbete.

Ramar godkänns i granskningsläge från klinikvyn. Automatisk tillämpning kan inte godkännas via RPC medan den privata brytaren är av. Den publika simuleringen i `progression-engine.js` förblir ett rent utvecklingsverktyg; SQL-rutinen är auktoritativ i den anslutna appen. De använder samma policyformat, men ett godkänt serverobjekt är ett separat krav. `policy.mode=simulation-only` är det äldre serialiseringsformatet, inte en flagga som klienten kan ändra för att få automatisk drift.

En serverprövning kan anropas efter ett sparat svar, inför ett nytt pass och från kliniken. Inga tidsstyrda nattjobb gör en patient tyngre mellan två besök. Appen väntar på en pågående prövning innan den skapar ett nytt pass. Samma request-ID återger samma beslut vid omsändning. Om ett svar saknas avvaktar motorn; ett ärende från en äldre plan kan fortsatt blockera.

## Införande

SQL-källor, testade tillsammans med grundschemat i en tom PostgreSQL-databas:
1. `secure/progression-runtime.sql`
2. `secure/dialogue-runtime.sql`

Infört med Supabase MCP som namngivna hanterade migrationer:
- `20260911045221 exercise_intelligence_progression_runtime`
- `20260911045230 exercise_intelligence_dialogue_runtime`

Edge-funktionen `reda-dialogue` version 1 är driftsatt med JWT-kontroll. Efterkontrollen bekräftade båda brytarna av, RLS på alla fem nya tabeller, inga direkta sessionsskrivningar för browserrollen och inga nya patienter, planer, pass, svar, ramar eller ärenden skapade av införandet.

CI på `ce5551d170b46dc5922071e153e099aacce21b7d` är grön: 125 Node-tester, isolerade PostgreSQL-tester inklusive två samtidiga anslutningar, de nya och befintliga browserflödena samt SEO-regression. [Verifierad körning](https://github.com/carlrobertkarell-beep/kansei-se/actions/runs/34563747913).

Driftgranskningen visar inga nya säkerhetsvarningar på publika tabeller. De två privata tabellerna har avsiktligt ingen browserpolicy: åtkomst sker genom behörighetskontrollerade serverfunktioner. Supabase visar därför [RLS enabled, no policy](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy) som information. Den sedan tidigare avstängda [kontrollen av läckta lösenord](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection) återstår som Auth-varning. Äldre RLS-prestandaråd och oanvända index på den ännu tomma driftdatan kvarstår; inga behörigheter lättades för att tysta dem.

Edge-filer:
- `supabase/functions/reda-dialogue/index.ts`
- `engine/dialogue.mjs` (relativ import tre nivåer upp från funktionen)

Servermiljö för en senare AI-öppning: `OPENAI_API_KEY`, `OPENAI_REDA_MODEL` och valfri `OPENAI_REDA_ENDPOINT` (endast OpenAI:s standard- eller EU Responses-adress). Ingen nyckel finns i browserkod. Modellnamn är ett uttryckligt driftval; frånvaro betyder otillgänglig, aldrig ett simulerat AI-svar.

`store:false` används. Det befriar inte från att fastställa leverantörens databehandling, retention, avtalsgrund och eventuella regionala inställningar. En EU-adress ensam är inget bevis på konfigurerad EU-datalagring. Fritext kan fortfarande innehålla personuppgifter trots enkla kontrollmönster och uppmaning till dataminimering. Inga riktiga patientuppgifter har använts i modelltester.

Nuvarande teknisk kvot är 20 frågor/timme och 100/dygn per användare; kvotdata rensas för användaren efter sju dagar vid nästa förbrukande anrop. Inaktiv användares kvotdata kräver separat schemalagd gallring om en absolut retentionstid ska utlovas. Kvoten är en missbruksgräns, inte ett löfte om obegränsat stöd eller en beräknad AI-budget. Välj modell, utvärdera med svenska kliniskt granskade fiktiva frågor, mät kostnader och sätt projektbudget innan flaggan öppnas.

## Testernas omfattning

- Node: befintlig klinisk modell, policykontroller, dos/omgångar, återställning, återkoppling; ny strikt modellroutning, providerfel/refusal, dataminimering och rörelsegeometri.
- PostgreSQL: ägarskap, MFA, levande auth-session, rättigheter, versionsbindning, explicita villkor, avslutade oföränderliga pass, ärenden/kvittens/bedömning, skuggbeslut, exakt nästa version, idempotens, återkallning, serverklocka, modellens planåtkomst och kvoter. Två samtidiga separata PostgreSQL-anslutningar provas mot samma patient: exakt ett steg får publiceras och båda omsändningarna måste återge sina tidigare beslut. Automatisk/AI-brytare öppnas enbart i den tomma testdatabasen för att prova tillämpningen.
- Browser: fiktiva API-svar, blockerat externt nätverk, mobil/desktop, explicit godkännande, återkallning, ärendestatus, hjälpens reservflöde, AI-omförsök, ej automatiskt sparad tolkning och versionsbyte före nytt pass. Befintliga flödestester fortsätter köras.

Tester av programbeteende är inte bevis för klinisk lämplighet. Före pilot kvarstår representativa kliniska fall, modellutvärdering, medicinsk/regulatorisk bedömning, verkliga telefoner, faktiskt distributionsprov via e-post och återställning av driftdata. Samtidiga ändringar av ännu öppna pass från flera enheter behöver fortsatt konflikthantering; stängda pass är nu låsta. Alla varianter i rörelsebiblioteket är inte omritade.

Affärslinjen och kalkylen finns i [BUSINESS-MODEL.md](BUSINESS-MODEL.md).
