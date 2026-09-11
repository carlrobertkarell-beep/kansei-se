# Patientens nästa steg

Detta block knyter ihop granskning av plan, patientens dagsvy och orsaken bakom ett svårt pass. Det är en vidareutveckling av den befintliga klinikprodukten. Patientaktivering, inbjudningar, automatisk progression, extern patient-AI och försäljning förblir stängda.

## Genomfört

- Granskningen samlar instruktion, sida, dos, vila, veckoplan och planerade kontakter. Kliniker kan spara den granskade planen och förbereda utskrift från sammanfattningen. Sparat utkast är inte digital överlämning. Utskriftsdialogen bevisar inte mottagande.
- Dagsvyn använder Stockholms datum och aktuell planversion. Den skiljer planerad träningsdag, annan dag, sparat påbörjat pass och avslutat pass. Den ändrar inte ordination eller veckoplan.
- När ett avslutat pass har bekräftats av servern erbjuds två val: huvudsakligt hinder och önskemål om hjälp, med valfri specifik övning. Patienten kan vänta och återvända samma dag.
- Svaren sparas separat från nästa-dag-svaren, utan kopia i webbläsarlagring. Varje svar hör till exakt pass och planversion. Övningens namn hämtas ur den ordinationen på servern. Återförsök ger samma kvitto; andra svar kan inte skriva över det första.
- Ett rapporterat hinder skapar ett ärende i befintlig klinikkö. Neutral återkoppling skapar ingen extra arbetsuppgift. Signaler om besvär prioriteras före praktiska hinder. Uppgifterna är patientrapporterade, inte diagnoser eller automatisk triage.
- EI förbereder olika åtgärder för tidsbrist, ork, utförande och utrustning. Ursprungssvaret visas nära förslaget. Kliniker kan öppna planen för anpassning. Ingen ny dos eller alternativ övning aktiveras av svaren.
- Nya svar gör en tidigare klinikergranskning inaktuell. Olösta ärenden stoppar progressionsprövning enligt befintliga regler. Snabba svar ersätter aldrig nästa-dag-underlaget.

## Drift och kontroll

`secure/session-reflections.sql` körs efter `secure/fast-workflows.sql`. Den lägger till svarstabellen med RLS, endast SELECT för autentiserade klienter, en privat skrivfunktion med levande session och kontroll av patientägarskap efter lås, samt en publik invoker-wrapper. Den återanvänder organisation–patient–pass som låsordning. Befintliga roller, patientkopplingar och produktionsflaggor ändras inte.

Ett ärende har exakt en källa: nästa-dag-svar eller direkt återkoppling. Båda källorna visas i dashboard, inkorg och patientens kliniska uppföljning. Listorna behåller befintlig paginering; nya svar hämtas inte individuellt för samtliga patienter. Klinikeråtgärder binds till en ögonblicksbild som inkluderar ny återkoppling.

Verifiering omfattar Stockholms dygnsgräns, planversioner, serverkvitton, tappade svar, fel vid sparande av pass, ägarskap, MFA, arbetsytor, föråldrade beslut, ärendehantering och separering från progressionsunderlag. Webbläsar- och databastester använder enbart fiktiva patienter.

## Nästa produktbevis

En framtida patientpilot måste mäta hela kedjan: granskad plan → faktisk digital åtkomst eller utskrift → första pass → återkoppling → klinikerbeslut. Tid att komma igång, återkommande användning, förändring i patientens mål och klinikerns minuter per ärende är primära mått. Nedladdningar och tid i appen är inte tillräckliga effektmått.

Barnspåret behöver prövas separat med familjer och barnkompetens. Första hypotes: barn 8–12 år som inte trivs i organiserad idrott väljer korta, åldersanpassade rörelseaktiviteter och genomför dem med telefonen undanlagd. Pröva kvarstående rörelse efter nyhetseffekten, förälderns arbetsinsats, tillgänglighet och betalare innan en publik barntjänst byggs. Allmän rörelse och behandling av barns besvär behöver egna flöden. Ingen barnprodukt eller barnbehandling lanseras i detta block.
