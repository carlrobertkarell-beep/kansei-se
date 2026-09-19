# B2B self-service onboarding

Organisationens owner/admin kan skapa och ändra klinikenheter genom revisionsskyddade RPC:er. Enhetsändringar får en separat audit-logg med before/after. Direkt tabellskrivning för browserroller är fortsatt stängd.

Onboardingmodellen är `Klinikenhet → Team → EI-läge → Patienter`. Shadow/granskningsläge är en avsiktlig introduktionsfas, inte ett fel- eller demo-läge. En ny organisation kan därför köra EI parallellt med behandlaren, samla QA-data och senare öppna autonomi per enhet.

Nästa block implementerar medlemsadministration och en readiness-modell för övergång `shadow → automatic`, där Reda visar observerade QA-mått och krav men organisationens behöriga admin fortfarande fattar aktiveringsbeslutet.
