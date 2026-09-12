# Från hinder till hjälp och planförslag

Det här utvecklingsblocket kopplar patientens vardag till ett konkret nästa steg. Det använder sparade ordinationer och bibliotekets regler. Det är inte en ny extern AI-tjänst eller en öppning av patientaktivering.

## Patient

- **Hjälp med en övning** finns direkt på Idag. Övningsguiden visar den tillhandahållna planversionens utförande, sida, dos, vila, utrustning, individuella belastning och rörelseomfång. Stillbilder och instruktioner kan visas utan att starta eller registrera ett pass.
- Vid osäkerhet om utförande eller utrustning går guiden att öppna redan innan de två svaren sparas. Valen sparas först vid **Spara mina svar** genom befintligt validerat, idempotent flöde.
- Efter bekräftad sparning visas hjälp anpassad till hindret och vad kliniken kan göra sedan. Klinisk bedömning ersätts inte av en instruktion. Symtom och låg ork ger kontaktväg, ingen automatiskt ändrad dos.
- Det senaste sparade svaret för den aktuella planen går att öppna efter omladdning. Tillgängligt för kliniken betyder inte läst av en behandlare. Inga notifieringar, bokningar eller svarstider påstås.
- Samma guide går att använda i den befintliga interna förhandsvisningen av egen träning. Den publika självservicetjänsten är fortsatt stängd.

## Kliniker

- Ett tids- eller utrustningshinder från den aktiva planversionen kan öppna ett förberett anpassningsflöde från dashboarden.
- **Tidsbrist:** kandidat med en omgång mindre där det finns fler än en. Övningar, repetitioner, sida, vila och individuella ordinationer bevaras. Kandidaten är ett alternativ för klinisk granskning, inte en rekommendation om likvärdig behandlingseffekt.
- **Utrustning:** klinikern väljer vad som saknas. Kompatibla varianter kan föreslås; saknade ersättningar och befintliga varningar förblir synliga. Bytta varianter använder bibliotekets grunddos. Förlorad individuell belastning eller rörelsebegränsning visas i jämförelsen.
- Jämförelsen visar nuvarande och föreslagen ordination. **Använd förslaget** ändrar redigeringsytan, varefter befintligt gransknings-, sparnings- och utskriftsflöde används. Patienten får ingen ny ordination genom att en kandidat visas eller ett utkast sparas. Patientsignalen avslutas inte automatiskt.
- Nytt underlag, annan patient, annan aktiv plan eller ett nyare utkast stoppar automatisk förberedelse. En manuell ändring gör en tidigare kandidat inaktuell. Patient- och organisationsgränser använder befintliga kontrollerade API:er.

Ingen databasändring, patientinbjudan, aktivering, progression eller försäljningsöppning ingår. Kandidater och guideinnehåll skickas inte till någon extern AI. Inga nya patientuppgifter skrivs till webbläsarlagring.

## Verifiering

Ren modelltestning av bevarad dos, sida, belastning, oföränderlig källplan, varningar, symtomstopp och källbindning. Browserflöden använder fiktiva tjänster för patienthjälp, återupptagen kvittens, uteblivna sidoeffekter, klinikens jämförelse och utkast, nyare underlag samt mobil och desktop. De körs tillsammans med projektets befintliga databas-, behörighets- och regressionskontroller i CI.
