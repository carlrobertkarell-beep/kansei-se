# EI-mandat per klinikenhet

Varje klinikenhet kan nu ha ett eget organisationsstyrt EI-mandat: automatisk progression, automatisk regression och ett maximalt antal autonoma steg innan ny klinisk kontroll krävs. Standardläget är konservativt: båda automatikflaggorna är av och maxgränsen är tre steg.

Endast organisationens owner/admin med MFA kan ändra mandatet. Skrivning använder revisionskontroll så två administratörer inte tyst skriver över varandra. Varje ändring sparar before/after i en separat audit-tabell.

Detta mandat är ett organisationslager ovanpå patientens behandlargranskade progressionsram och den globala kill-switchen. Autonomi kräver alltså samtliga nivåer: globalt öppet → enheten tillåter funktionen → behandlaren har godkänt patientens ram → evidensmotorn uppfyller kriterierna.
