# Klinisk kunskapsversion på ordination

Nya planer som byggs av live-plannern stämplas med `clinicalKnowledgeVersion`. Värdet kommer från det separat versionshanterade kliniska kunskapslagret. Om kunskapsmodulen inte är laddad stämplas planen med `unknown` i stället för att klienten hittar på en version.

Versionsstämpeln följer planpayloaden genom planversionering och gör att EI QA kan bryta ned senare motorbeslut efter det kliniska regelverk som faktiskt användes när ordinationen skapades. Befintliga äldre planer migreras inte retroaktivt och förblir `unknown`.
