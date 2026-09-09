# Reda · den verkligt stora utvecklingen

Detta dokument är produktkravet, inte en idélista. Reda ska ersätta merparten av manuellt mailande, skapande och justerande av hemprogram utan att ta kliniska beslut från behandlaren.

## Produktprincip
**Behandlaren bedömer, ordinerar och beslutar progression. Reda gör ordinationen snabb att skapa, entydig att följa och enkel att utvärdera.**

Patientens normala flöde: öppna → förstå → träna → logga → följ aktuell nivå → återbesök → ny klinisk bedömning → ny version.

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
- Återbesök och budskapet att nästa progression beslutas vid klinisk uppföljning är en permanent del av planen.

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
