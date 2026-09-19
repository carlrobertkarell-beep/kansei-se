# Kliniskt kunskapslager · versionsgrund

Alla åtta kärnblueprints har nu minst tre progressionsnoder och explicita regressionsvägar: patellofemoralt knä, knäartros, knä/senbelastning, axelbelastning, höft/GTPS, Achilles, nacke och ländrygg.

`clinical-knowledge.mjs` introducerar en separat versionsidentitet för kliniskt innehåll (`2026.09.19.1`) och metadata per domän. `knowledgeManifest()` kan användas i QA/analytics för att veta exakt vilken kunskapsversion ett beslut byggde på.

Detta är första steget mot att skilja klinisk data från UI-kod. Nästa steg är att lagra själva graferna som versionshanterade dataobjekt och låta biblioteket konsumera dem, så att kliniska ändringar kan granskas och releasehanteras utan att röra rendering eller plannerlogik.
