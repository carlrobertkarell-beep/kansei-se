# Granskad överlämning och planändring

## Flöde

Behandlaren öppnar **Granska & lämna över** från planredigeraren eller **Granska färdigt planförslag** från patientöversikten. Aktuell serverversion och underlag hämtas. Övningar, sida, dos, instruktioner, ändringsjämförelse, behandlarens interna bedömning och patientens separata meddelande granskas före publicering. Dos kan justeras; ändring nollställer granskningsbekräftelsen.

En godkänd överlämning publicerar en ny planversion atomärt. En förlorad kvittens kan hämtas med samma request-id utan ny version. Nya patientsvar, ändrade planer eller andra underlagsändringar kräver ny granskning. EI:s nästa steg prövas även på nytt på servern. Om ordinationen exakt följer nästa godkända steg fortsätter resten av ramen i granskningsläge. Avvikelser avslutar den tidigare ramen så att den behöver bedömas på nytt.

Ett första utskick sker först efter publicering till den adress behandlaren granskat. Edge-funktionen skickar en inbjudan eller, för ett befintligt konto, en inloggningslänk. Ingen hälsodata ingår i mejlet. Provideracceptans är inte leveransbevis, läskvitto eller genomförd träning. Utskick kan misslyckas efter lyckad publicering; dashboarden erbjuder då nytt utskicksförsök utan en ny plan. En okänd providerkvittens kan innebära ett dubbelt mejl vid omförsök; exakt en extern leverans utlovas inte.

Patienten måste först verifiera sin e-post genom inloggningen. Servern kontrollerar aktuell inbjudan, klinik, plan och tidigare kontokoppling före patientåtkomst. Inbjudan gäller sju dagar. Utgången eller ersatt inbjudan ger ingen ny patientkoppling. Redan anslutna patienter behåller sitt konto och kan själva beställa ny inloggningslänk.

Patienten ser behandlarens överlämningstext och verkliga framsteg: tillgänglig plan, första avslutade pass och sparad direktåterkoppling. Ett saknat patientkort eller en ännu opublicerad plan ger begriplig feltext och återförsök. Ny plan före passstart måste visas innan patienten börjar. Påbörjade pass behåller sin ursprungliga version genom befintligt återhämtningsflöde.

## Driftsättning och kvarvarande distributionsprov

Migrationen `clinical-handover.sql` inför arbetsytans `patient_delivery_enabled=false`. Den ändrar inte befintliga patient-/planposter, automationsflaggor eller externa AI-flaggor. Endast operatör kan ändra distributionsflaggan. Gamla `activate-plan`-anrop är fortsatt spärrade; den nya vägen använder den granskade publiceringsfunktionen.

En faktisk patientpilot kräver fortfarande klinisk granskning enligt `INTELLIGENCE-WORKFLOW.md`, fungerande SMTP och tillåten redirect till `https://www.kansei.se/reda-2/patient.html`. Inga autentiseringsinställningar antas vara korrekta enbart för att frontend är publicerad. Före öppning: verifiera ett uttryckligen godkänt testutskick till en vald testadress, verifierad inloggning på mobil, återinloggning, första pass och klinikens kvittenser. Inga verkliga mottagare kontaktas av CI eller migrationen.

## Verifiering

Fiktiva modell-, PostgreSQL- och webbläsartester omfattar mottagarbindning, MFA, utgångna/stängda vägar, retry, publicerad plan trots mejlfel, gammalt underlag, historik, exakt manuellt godkänt progressionssteg samt patientens första pass. Testerna simulerar externa e-posttjänsten och bevisar inte faktisk leverans eller klinisk lämplighet.
