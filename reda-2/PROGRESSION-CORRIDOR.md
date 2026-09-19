# Automatisk progressionskorridor · första modellagret

Första korridormodellen tar en färdig ordination och förbereder deterministiska dossteg utan att ändra originalplanen. Steg 0 är alltid en exakt kopia av aktuell ordination. Därefter förbereds små dossteg i repetitioner och omgångar inom samma övning/variant/sida.

Detta är medvetet ett konservativt första lager. Modellen byter ännu inte övningsvariant, extern belastning eller klinisk riktning automatiskt. Sådana steg ska komma från blueprintens kuraterade progressionsgraf, inte från generiska regler.

Korridoren är ett utkast till progressionsram och får inte aktiveras utan befintlig ramvalidering och behandlarens godkännande. `corridorDiff` gör varje steg granskningsbart som en explicit skillnad mot föregående ordination.
