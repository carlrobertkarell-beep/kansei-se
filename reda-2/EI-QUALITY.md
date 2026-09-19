# EI Analytics & Quality Assurance

Första QA-lagret mäter motorbeteende utan att skapa ett förenklat kliniskt `score`. Kärnmåtten är antal `advance`, `hold`, `regress`, `escalate`, faktiskt applicerade beslut, behandlargranskningar, explicita overrides och review cases som uppstår efter en autonom planändring.

`overrideRate` räknas endast bland beslut som faktiskt granskats av behandlare. `postChangeCaseRate` räknas endast bland applicerade beslut och betyder att ett review case senare skapats på den resulterande planversionen; det är en kvalitets-/säkerhetssignal men inte automatiskt bevis för att EI-beslutet var fel.

Måtten kan brytas ned per blueprint, men modellen producerar medvetet ingen ranking eller klinisk kvalitetspoäng. Nästa serverblock ska aggregera dessa mått organisationsvis och per kunskapsversion utan att exponera patientsvar i analytics.
