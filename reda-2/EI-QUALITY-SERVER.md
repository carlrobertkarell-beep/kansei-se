# EI Quality · organisationsnivå

`reda_ei_quality(days)` aggregerar endast den aktiva organisationens motorbeslut och kräver behandlarbehörighet + MFA. Den returnerar action mix, applicerade beslut, behandlarreviews/overrides, review cases efter applicerad planändring samt nedbrytning per blueprint och klinisk kunskapsversion.

Inga patientnamn, fritextsvar eller enskilda träningssvar returneras. Perioden är 1–365 dagar. UI-renderaren visar måtten som QA-signaler och undviker en sammanvägd kvalitetspoäng.

För att kunskapsversionsanalysen ska bli komplett måste framtida skapade planer stämplas med `clinicalKnowledgeVersion`; äldre planer visas som `unknown`, vilket är avsiktligt och gör historisk datakvalitet synlig.
