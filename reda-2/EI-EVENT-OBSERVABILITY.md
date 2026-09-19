# Eventdriven EI · signaler och observability

Direkt-reflektion efter pass läggs nu också i EI-kön, men den befintliga progressionsmotorn räknar den inte som framgångsevidens. Reflektionens barriärer skapar redan review cases; eftersom motorn kontrollerar öppna review cases först blir resultatet `review/pending_review` och autonom progression stoppas.

Nästa-dagssvaret fortsätter vara den progressionsgrundande händelsen. Ett avslutat pass utan nästa-dagssvar behöver inte köra en full progression eftersom motorn ändå väntar på response; passets avslut fångas i patientflödet och nästa svar skapar det beslutsbara eventet. Detta minskar onödiga motorjobb vid stor volym.

Service role får `reda_worker_health()` med ködjup, processing, failed, done senaste 24 h, ålder på äldsta pending-jobb och attempts senaste 24 h. Browserroller saknar access. Dessa mätvärden är drifttelemetri och innehåller inga patientsvar.
