# Blueprint progressionsgraf

Progressionskorridoren kan nu läsa en kuraterad `progressionGraph` från en blueprint. Grafens noder beskriver explicita förändringar per övnings-ID (dos, variant, sida eller andra redan stödda ordinationsfält) och kan därför representera kliniskt meningsfulla steg som inte går att härleda från generisk dosmatematik.

Grafen valideras för unika noder, giltig start och kanter som endast pekar på existerande noder. Korridoren följer `advance`-kanter och begränsas till högst sju framtida steg i en granskningsvy. Saknas graf används den konservativa doskorridoren som fallback.

Regression edges reserveras för nästa roadmap-block och följs inte av progressionskorridoren. En blueprint-graf är fortfarande ett utkast tills den gått genom progression-frame-validering och explicit kliniskt godkännande.
