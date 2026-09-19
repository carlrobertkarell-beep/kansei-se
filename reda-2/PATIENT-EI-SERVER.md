# Patient EI · serverbundet förändringsunderlag

Patientbootstrapen hämtar högst en föregående planversion och högst ett motorbeslut vars `result_plan_id` är exakt den aktiva planen. Patientens förändringsnotis kan därför inte råka förklara en manuell eller annan planversion med ett orelaterat EI-beslut.

Om inget sådant beslut finns är `latestDecision=null` och patientvyn faller tillbaka utan EI-förklaring. Historiken begränsas till föregående version för att hålla bootstrap liten även vid långvariga rehabförlopp. Databasens befintliga patient-RLS gäller även dessa read-only-frågor.
