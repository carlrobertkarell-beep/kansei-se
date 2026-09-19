# Patientens EI-upplevelse

När bootstrap-data innehåller föregående planversion och senaste EI-beslut kan patienten få en tydlig förändringsnotis: vad som ändrats per övning och varför den nya versionen finns. Texten beskriver att villkor i behandlarens upplagda plan uppfyllts; den framställer inte EI som en ny behandlare.

`Det här fungerar inte` leder direkt till patientens befintliga barriär-/hjälpflöde. Det skapar därmed samma review cases och eventdrivna EI-stoppsignaler som övrig patientåterkoppling, i stället för ett parallellt supportsystem.

Vyn är fail-closed: om bootstrap ännu inte exponerar föregående plan och senaste beslut visas ingen påhittad förklaring. Nästa serverblock ska lägga till just dessa två read-only-fält i patientbootstrapen.
