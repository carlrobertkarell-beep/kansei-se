# Klinikerfokus · 2026-09-18

Det här blocket gör patientöversikten snabbare att arbeta i utan att ändra klinisk logik, sortering eller data. Direkt under nyckeltalen visas ett arbetsfokus som använder den redan serverbestämda arbetsordningen. Om någon av de synliga patienterna är markerad som att den behöver behandlaren visas antal och den första patientens befintliga nästa steg. Knappen öppnar samma patientåtgärd som redan finns i raden.

Patientradernas nästa-steg-kolumn får en liten visuell etikett, så att namn, situation och åtgärd kan skannas snabbare. Förändringen är progressiv: om dashboarden inte har laddats gör den ingenting, och den observerar endast redan renderad DOM. Den gör inga API-anrop, skriver inga patientdata, ändrar ingen prioritering och skapar inga nya kliniska slutsatser.

På mobil ligger arbetsfokus kvar högst upp i patientlistan och använder samma befintliga detaljvy. Patientaktivering, automatisk progression, utskick, betalning och externa AI-anrop påverkas inte.
