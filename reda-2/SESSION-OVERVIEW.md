# Passöversikt och uttryckligt avslut · 2026-09-18

Patienten kan öppna hela sitt pågående pass från spelarens rubrik, återvända till en övning, pausa eller uttryckligen avsluta i förtid. Översikten visar ordinationen, registrerade omgångar, sida, överhoppade övningar och den egna belastningsskattningen. Att öppna eller byta vy registrerar ingen träning.

Översikten är en läsvy över samma pass och planversion, inklusive ett eventuellt redan godkänt passalternativ. Den föreslår ingen ny dos. Kvarvarande omgångar markeras aldrig automatiskt som genomförda eller överhoppade. Ett avslut utan registrerade omgångar beskrivs uttryckligen så i patientens historik; saknade uppgifter tolkas inte som noll.

Avslut i förtid har ett eget bekräftelsesteg. Paus behåller ett öppet pass. Om patienten går direkt till den sista övningen men har oregistrerade övningar kvar leder nästa-knappen till översikten, inte till ett tyst avslut. Det vanliga sekventiella flödet behåller sin direkta avslutning när övningarna har hanterats. Helt registrerade övningar kan inte råka märkas som överhoppade när patienten återvänder till dem.

Sparandet använder befintlig synkkö, återställning och API. Dubbelklick eller navigering under avslut skapar inte ytterligare avslut. Återkopplingsfrågorna visas först efter serverbekräftat avslut. Misslyckad synk behåller samma pass-ID och de verkliga markeringarna för återförsök; inget nytt pass startas innan avslutet har synkats.

## Verifiering

14 rena modell-/historiktester samt webbläsarfall med fiktiv patient: läsvy utan mutation, separata sidor, överhoppade omgångar, navigering, paus/fortsättning, normalt helt pass, bekräftat delvis avslut, fel vid sparande och återförsök, exakt passbundet svar, tangentbord, osäker text samt 320/390/1440 pixlars vyer. Ljust och mörkt tema använder patientappens gemensamma färgvariabler. Testerna kontaktar inte produktionsdatabasen.

Ingen ändring av databas, behörigheter, patientaktivering, AI-anslutning, progressionsmandat, utskick eller försäljning. Verkliga telefoner och hela distributionskedjan behöver fortfarande provas före patientpilot. Lokalt kan webbläsartesten rendera endast lokala kodfiler utan navigering via REDA_INLINE_TEST=1; CI kör den vanliga HTTP-vägen.
