# Autonom regression inom godkänd korridor

Regressionsmotorn skiljer strikt på belastningsreaktioner som får hanteras inom en redan godkänd korridor och nya patientsignaler som ska eskaleras.

En automatisk regression kan endast gå **ett steg bakåt** till en ordination som redan finns i den godkända ramen. Den kräver ett definierat observationsfönster och ett minsta antal fördefinierade belastningssignaler, exempelvis `för tung` och/eller nästa-dag `sämre`. Otillräckligt underlag ger `hold`.

Ny/förändrad symtombild eller uttryckligt hjälpbehov ger `escalate`, inte regression. Om patienten redan befinner sig på ramens första steg eskaleras behov av ytterligare regression eftersom EI då skulle behöva lämna behandlarens mandat.

Detta modellager exekverar ännu ingen planändring i databasen. Nästa serverblock ska binda `regress` till samma versions-, audit- och concurrency-regler som autonom `advance` innan funktionen kan öppnas i produktion.
