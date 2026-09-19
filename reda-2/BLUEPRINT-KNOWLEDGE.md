# Blueprint knowledge layer · v2.6

Det kliniska biblioteket innehåller nu de första riktiga progressionsgraferna för knäartros, knä/senbelastning, axelbelastning och Achilles. Varje nod har en namngiven rehabiliteringsroll och explicita ordinationsändringar. Kanter anger endast `advance` eller `regress`.

Graferna beskriver behandlarstyrda rehabvägar, inte diagnosbeslut. De väljs först när motsvarande blueprint redan ingår i patientens ordination. EI får alltså inte använda grafen för att avgöra att en patient *har* knäartros, tendinopati eller annan diagnos.

En separat validator kontrollerar slots, grafstart, övningsreferenser och kanter. Nästa iteration ska lägga motsvarande grafer för patellofemoralt knä, höft/GTPS, nacke och ländrygg och därefter bryta ut grafbiblioteket från JavaScript till versionshanterad klinisk data så att innehållet kan kvalitetssäkras oberoende av UI-kod.
