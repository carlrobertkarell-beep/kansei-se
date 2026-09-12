# Godkända alternativ i samma plan

Klinikern förbereder högst tre alternativ från EI:s befintliga biblioteksförslag: en omgång mindre, utan band, utan golvövningar eller hemma. Övningsidentiteter och ordning behålls. Olösta ersättningar kan inte godkännas. Valda alternativ granskas tillsammans med synlig dosjämförelse och fullständiga instruktioner, sida och individuella ordinationer. Ett godkännande sparas i planutkastets `planOptions` och är bundet till grundplanens exakta kliniska innehåll. Grundplansändringar kräver ny granskning.

Patientens Idag visar endast godkända alternativ i den aktuella planversionen. Valet påverkar passets utförande och dos, inte grundplanen. En instruktion kan öppnas utan att träning registreras. Påbörjat pass behåller alternativet, även vid omladdning och offlineåterställning. `payload.optionId` följer med vid synkning och kan inte ändras efter start. Ett avslutat kortpass räknas utifrån dess godkända omgångar.

Databasen kontrollerar planens godkännandebindning, alternativa övningar, dosgränser och passets val. Okända alternativ och felaktiga omgångar nekas. Källversionen och dess alternativ kan inte skrivas om efter aktivering. Samma behörigheter, organisationsgränser, låsning och återförsök som för övriga planer och pass gäller. Ingen ny direkt skrivväg för patienter införs.

Dashboardens patientöversikt visar användning bland de senaste 30 registreringarna för aktuell plan och skiljer genomförda från delvis genomförda pass. Tre eller fler registrerade val av samma alternativ visas som en anledning till avstämning, inte som bevis för ett visst hinder eller som automatisk behandlingsändring. Återkopplingens ursprung visar vilket passalternativ den gällde.

Progressionsramar och vardagsalternativ kombineras inte i denna version. Alternativa pass blir därmed inte automatiskt underlag för progression av grunddoseringen. Patientaktivering, automatisk progression och publik självservice är fortsatt stängda. Inga inbjudningar eller betalflöden öppnas.

Verifiering finns i `plan-options.test.mjs`, `plan_options_database_test.sql` och `plan_options_browser_test.py`, tillsammans med befintliga regressions-, behörighets- och samtidighetskontroller. Patient- och klinikflöden testas mot fiktiva tjänster; produktionspatienter används inte som testdata.
