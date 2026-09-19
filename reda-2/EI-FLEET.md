# EI Fleet Management

Dashboarden får en överordnad EI-flotta: autonomt hanterade planer, planer som samlar evidens, planer där EI avvaktar, patienter som behöver behandlaren och ramar i granskningsläge. Patientrader får samma status som en kompakt etikett.

Kategoriseringen är operativ, inte medicinsk triage. En öppen patientsignal eller ett motorbeslut `review/blocked` går alltid till **Behöver dig**. En automatisk ram med `hold` visas som **EI avvaktar**. En automatisk ram utan sådan avvikelse visas som **EI autonomt**. Aktiv plan utan godkänd ram visas som **Samlar evidens** tills serverdashboarden exponerar full ramstatus.

Flottans totalsiffror ska komma från servern över hela patientpopulationen, inte räknas från den paginerade 25-radersvyn. UI:t accepterar därför ett separat `fleet`-objekt från dashboard-RPC:n; tills backendmigreringen är installerad visas nollor i delkategorierna i stället för påhittade totalsiffror.
