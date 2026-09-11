# Exercise Intelligence — nästa arbetsflöde

Implementerat 2026-09-11. Denna beskrivning ersätter äldre uppgifter om att redigeraren bara klarar ett dossteg. Patientaktivering, automatisk tillämpning, betalning och externa AI-frågor har inte öppnats av detta arbete.

## En hel väg, granskad av behandlaren

Klinikredigeraren förbereder 2–12 kompletta ordinationssteg. Från senaste steget kan behandlaren ändra en eller flera övningar: kompatibel biblioteksvariant, omgångar, repetitioner eller hålltid inom befintlig dosform, vila, rörelsecykel, individuell belastning och individuellt rörelseomfång. Ett variantbyte hämtar variantens instruktion, rörelse, dos och sidupplägg; tidigare individuell vikt och rörelseomfång nollställs och måste bedömas på nytt. Det är ett fullständigt variantbyte, inte bara en ny rubrik.

Varje tillagt steg har namn, klinisk motivering och en före/efter-jämförelse. Alla värden bestäms av behandlaren. Inga universella progressionsprocent, smärtgränser eller tidsgränser är förifyllda. Patienten väljs inte till en nivå utifrån ålder.

Redigeraren visar hela kedjan, tillåter att sista steget tas bort och behåller redan sparade villkor. Ett påbörjat steg måste läggas till innan hela ramen kan sparas. Utkastet hör till den aktuella ordinationen: förändrade mål, förutsättningar, övningar eller veckoplan kräver ny ram. Sparande innebär inte godkännande. Under Uppföljning visas varje fullständig ordination och dess skillnader; godkännande sker uttryckligen i granskningsläge.

Motorn behåller tidigare skydd för patient-/planbindning, nästa-dag-svar, nytt underlag per steg, återhämtning, annan träning, öppna pass, granskningsärenden, idempotens och planversionsbyte. Rörelseomfång ingår nu i definitionen av en faktisk förändring även på servern. Instruktioner och hjälpsvar visar det individuella rörelseomfånget. Illustrationen är fortfarande en biblioteksillustration; den mäter inte patientens rörelse och skalas inte automatiskt till den textangivna vinkeln.

## Jämför motorn med klinisk bedömning

Ett sparat beslut kan bedömas som instämmer, avvikande bedömning eller otillräckligt underlag, med motivering. Bedömningen sparas en gång och identiska nätverksomförsök ger samma resultat. Förändrad bedömning kräver en ny prövning; historiken skrivs inte över.

Bedömningen aktiverar ingen plan, ändrar inga regler och löser inget patientärende. Den tränar inte automatiskt om en modell. Översikten visar absoluta antal bedömda beslut, inte en påstådd träffsäkerhet eller representativ kvalitetsnivå. En dokumenterad serie fiktiva och därefter kliniskt granskade fall behövs för att kalibrera reglerna.

## Kliniköversikt

Klinikens inloggade startsida visar en gemensam ärendelista för behandlarens patienter. Statusfilter: att hantera, nya, kvitterade, bedömda. Orsaksfilter: förändrade besvär/funktion, ändrade förutsättningar, kontaktönskemål och utförandehjälp.

Förändrade besvär visas först, sedan förutsättningar, kontakt och utförande. Äldst först inom varje grupp. Detta är arbetsordning, inte medicinsk triage eller akutövervakning. Antal räknas över hela behandlarens ärendemängd; listan hämtas i sidor om 25. Olösta ärenden för arkiverade patienter döljs inte.

Varje rad visar den ursprungliga återkopplingen och planversionen. Behandlaren kan kvittera eller dokumentera bedömning direkt, eller öppna den aktiva patientens uppföljning. Kvitterat är fortfarande olöst. Fel vid hämtning visas uttryckligen och ersätter den föregående listan; ett hämtningsfel presenteras aldrig som noll ärenden. Inga meddelanden, bokningar eller försäljning utlöses från översikten.

## Planhjälp och AI-dialog

Planens förklaringar, dos, individuella rörelseomfång och instruktion ett steg i taget fungerar utan externa AI-anrop. Ytterligare val hjälper patienten förstå vad den kan göra när nivån känns lätt eller utrustning saknas: lämna återkoppling eller kontakta kliniken, utan att hitta på en ny dos/övning.

Den förberedda AI-kopplingen stöder följdfrågor med vald övning och högst två tidigare användarfrågor. Högst fyra frågor med svar visas i den öppna vyn. Denna samtalsinformation sparas inte i webbläsarlagring eller Supabase. Historiska frågor används för sammanhang, aldrig som ny bekräftad återkoppling. Citat i tolkningar måste finnas i den aktuella frågan. Patienten lämnar själv svaren i ordinarie formulär; AI fyller inte i eller sparar dem automatiskt.

Modellen klassificerar avsikt/övning och tolkar uttryckligt angivna kategorier. Synliga kliniska instruktioner återges från den sparade ordinationen. Den ger inte fri klinisk rådgivning, nya diagnoser eller autonoma dosändringar. Om en tolkad kategori innehåller försämring tar kontaktvägen företräde även om modellens avsiktsklassificering säger något annat. Ett dåligt modellsvar kan fortfarande missa symtom; detta är därför inte en validerad triagetjänst.

### Modellval och mätning

Första utvärderingskandidat: `gpt-5.6-terra`, låg reasoning-nivå, Responses API med strikt JSON-schema, `store:false`, 1 800 output-token-tak och 15 sekunders timeout. Kandidaten valdes för den avgränsade språk-/klassificeringsuppgiften utifrån aktuell officiell dokumentation; den är inte utsedd efter uppmätt resultat i Reda. Ingen dold standardmodell slås på i produktion. Edge Function kräver fortfarande explicit `OPENAI_REDA_MODEL`, API-nyckel och befintlig avstängd AI-flagga.

22 svenska fiktiva fall finns i `evals/dialogue-fixtures.mjs`: vanlig instruktion, dos, sida, vila, lätt nivå, hög träningsvana, utrustning, förenkling, följdfrågor, progression, förändrade besvär, negation, återhämtning, annan träning och försök att kringgå planen.

- `node reda-2/evals/run-dialogue.mjs` kontrollerar förfrågningarna utan nätverksanrop.
- `node reda-2/evals/run-dialogue.mjs --live-fixtures` använder endast dessa fasta fiktiva fall och kräver `OPENAI_API_KEY`. Ingen Supabase-koppling, patientaktivering eller ändring av produktionsflaggor ingår. Redovisar fall-id, utfall, svarstid och tokenanvändning; ingen nyckel eller frågetext skrivs i rapporten.

En API-nyckel var inte tillgänglig i utvecklingsmiljön. Enhetstester och simulerade providersvar är kontrollerade; verklig modellkvalitet, svarstid och kostnad är **inte uppmätta**. Att `store:false` används innebär inte automatiskt att leverantörens övriga loggning upphör. Avtal, kontoinställningar, datahantering och information till patienten måste vara klara innan verklig hälsofritext används.

Officiella källor kontrollerade 2026-09-11: [modell](https://developers.openai.com/api/docs/models/gpt-5.6-terra), [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs), [datahantering](https://developers.openai.com/api/docs/guides/your-data).

## Ekonomisk riktning

Det tidigare förslaget i `BUSINESS-MODEL.md` kvarstår: inkluderad startplan, frivillig digital fortsättning som huvudsakligen drivs av motorn, fysiskt återbesök när ny analys/behandling behövs. Förslaget 690 kr/åtta veckor är inte ett öppnat erbjudande eller ett godkänt slutpris. Inga schemalagda betalda avstämningar läggs till här. Arbetsflödet ska minska tiden att förbereda en hel väg och hitta verkliga undantag. Målet om högst fem behandlarminuter i snitt per köpt period återstår att mäta.

## Kvar före drift med patienter

- Klinisk granskning av hela progressionskedjor för olika kapaciteter och mål.
- Verklig fiktiv modellutvärdering med tillgänglig projektkonfiguration, följd av medvetet modellval.
- Distribution och återinloggning från start till mål när patientaktivering godkänns.
- Arbetsmängd och undantagsfrekvens under en kontrollerad pilot.
- Separat beslut om automatisk tillämpning, AI-anrop och eventuell försäljning.

## Verifiering och driftsatt backend

Första hela kvalitetskörningen på kodversion `2478d88a3fdcd44337cd1c50ec4a7c3339a8d17c`: [GitHub Actions 34569472238](https://github.com/carlrobertkarell-beep/kansei-se/actions/runs/34569472238), godkänd. 155 Node-tester, isolerad PostgreSQL med ägar-/MFA-/sessionskontroller, två samtidiga databasanslutningar samt samtliga tidigare och nya webbläsarflöden gick igenom. Nya flöden omfattar flerstegsutkast, ärendepaginering/filter/fel, ärendebedömning, motorbedömning och lokal samtalshistorik. Providersvar i webbläsartesterna är simulerade.

Supabase-migration `20260911062158 exercise_intelligence_clinic_workflow` är applicerad från `secure/clinic-intelligence.sql`. `reda-dialogue` version 2 är driftsatt med JWT-verifiering; innehållets SHA-256 är `248c820d140b2e16dab296e65b5f321df14d50a8097d4298145673a84fdfe794`.

Efterkontroll: en befintlig patient, tre befintliga planer, noll pass, noll träningssvar och noll motorbedömningar. Automatisk tillämpning och AI-frågor är fortsatt avstängda. Ny bedömningstabell har RLS, browserklienten saknar direkt INSERT och anonym åtkomst till kliniköversikten är nekad. Inga nya säkerhetsvarningar från Supabase. Tidigare varning om läckta lösenord och äldre RLS-prestandaråd kvarstår; index på den nya tomma tabellen är ännu oanvända.
