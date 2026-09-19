# B2B scope · organisation → enhet

Organisationsägare/admin kan nu begära aggregerad EI-flotta för hela organisationen eller en specifik enhet. Vanliga användare får endast enhetsscope där de har aktiv unit membership. Endpointen kräver fortsatt behandlarbehörighet + MFA och returnerar endast antal.

Första fleet-aggregatet skiljer på automatisk ram utan öppet review case, öppna review cases, shadow-ram och aktiva patienter utan godkänd ram. Den är avsiktligt enklare än den fulla klinikdashboardens operativa state-maskin; nästa iteration ska återanvända en gemensam serverklassificerare så att organisations- och behandlarvyer aldrig divergerar.

Klientmodellen har scope-alternativ och breadcrumb för `organisation / enhet / behandlare`. Nästa block lägger behandlarfilter och samma scope på EI Quality.
