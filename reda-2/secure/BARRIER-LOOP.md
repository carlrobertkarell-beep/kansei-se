# Vardagshinder från rapport till utfall

Tidsbrist och saknad plats/utrustning får en egen, beständig uppföljningskedja. En sparad rapport för aktuell plan skapar en riktad fråga i patientens Reda. Målskattningens redan angivna förutsättningar används direkt när de finns; inga fritextsvar tolkas av en extern modell.

Patientens svar kopplas till ursprungligt ärende och plan. EI förbereder granskbara alternativ från befintlig övningslogik. Tidsförslaget minskar en omgång där fler finns, utan löfte om en uppmätt passtid. Utrustningsalternativ begränsas av patientens faktiska svar. Sido-, dos- och instruktionsändringar visas i den gemensamma granskningen. Behandlaren väljer datum för uppföljning av uteblivet svar och godkänner ändringen. Publicering, ärendekoppling och uppföljning sparas atomärt.

Ett registrerat avslutat pass med minst en omgång i den nya ordinarie planen gör resultatfrågan tillgänglig. Alternativpass, gamla planversioner och enbart öppnad plan räknas inte som prövad ändring. Patienten kan även ange att upplägget inte har kunnat prövas. Svaret sparas en gång och visas med datum i aktivitetsloggen.

Ett positivt svar kan avsluta just det praktiska hindret. Det sker bara när inga andra olösta signaler, obearbetade meddelanden eller uttryckliga kontaktönskemål finns. Det innebär ingen bedömning av tillfrisknande. Den automatiska noteringen anger EI som källa och tillskriver inte behandlaren en ny manuell bedömning. En orörd systemuppgift kan avslutas samtidigt; en uppgift som behandlaren ändrat lämnas kvar. Övriga utfall återöppnar ursprungsärendet och lägger fram det nya svaret för behandlaren. Administrativ schemaläggning respekterar klinikens mandat.

Vid nya symtomsignaler eller planbyte erbjuds ingen inaktuell snabbändring eller resultatfråga. Redan sparad historik och identiska omförsök bevaras. Dashboardens underlagstoken ändras när en ny uppgift sparas. Kontroll av aktiv session, patientägarskap, klinik, MFA och aktuellt underlag följer befintliga serverregler. Den privata tabellen har RLS och inga direkta browserrättigheter; patienten får en begränsad statusprojektion utan interna anteckningar eller överlämningskvitton.

Patientvyn prioriterar dagens steg, lyfter aktuell snabbfråga, visar sparade omgångar i passet och samlar detaljer bakom tydliga val. Mobilnavigation, tangentbordsfokus, tillräckliga träffytor och reducerad rörelse stöds. Nytt innehåll sparar inga hälsouppgifter i ny webbläsarlagring.

`barrier-loop.sql` är den hanterade migrationskällan. Den lägger inte in patienttestdata och ändrar inga driftsflaggor. Patientdistribution, klinisk automatisk tillämpning och extern AI är fortsatt spärrade enligt `CLINICAL-HANDOVER.md` och `INTELLIGENCE-WORKFLOW.md`. Ingen e-post eller push skickas av detta flöde; frågor visas när patienten använder Reda. Första tillämpningen gäller nyrapporterade hinder efter migrationen. Äldre signaler ligger kvar i vanlig ärendehantering.

Verifiering: avgränsade modelltester, isolerade PostgreSQL-tester och de riktiga patient-/klinikvyerna med fiktiva API-svar i GitHub Actions. Klinisk granskning och verkligt distributionsprov återstår före patientpilot.
