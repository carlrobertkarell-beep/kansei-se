# EI evaluator worker

En betrodd service-worker claimar EI-jobb med `FOR UPDATE SKIP LOCKED`, vilket gör att flera worker-instanser kan arbeta parallellt utan att behandla samma köpost samtidigt. Batchstorlek är 1–100.

Workern får aldrig klinisk logik i TypeScript. Den anropar samma databasägda progressionsmotor som klinikvyn. Lyckade jobb markeras `done`. Fel går tillbaka till `pending` med kvadratisk minut-backoff (1, 4, 9, 16, 25 minuter; max 60) och blir `failed` efter fem försök.

Browserroller har varken läsning av kön eller execute på worker-RPC:erna. Service role är den enda exekverande rollen. Nästa driftssteg är att schemalägga Edge Function/worker med lämplig frekvens och observerbarhet; själva kö- och concurrency-modellen är oberoende av antal workerinstanser.
