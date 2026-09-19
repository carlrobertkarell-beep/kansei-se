# EI autonom progression · klinikgränssnitt

Reda har redan en serverägd automatisk exekveringsväg som är avstängd globalt som standard. Detta block gör mandatet uttryckligt i klinikgränssnittet: behandlaren kan, efter att ha granskat hela progressionsramen, välja **granskningsläge** eller **autonom ram**.

Autonom ram betyder inte fri AI. EI får endast gå till exakt nästa kompletta ordination som behandlaren redan lagt i ramen. Servern kräver fortfarande tillräckliga uppföljda träningsdagar, minsta tid på nivån, kontrollerat utförande, accepterad belastningsskattning, nästa-dag-svar, oförändrade förutsättningar och inga öppna granskningsärenden. Försämring, hjälpbehov, ändrad miljö, ofullständigt underlag eller en öppen session stoppar eller eskalerar beslutet.

Arbetsytans serverinställning `automatic_enabled` är fortsatt den överordnade kill-switchen. Om den inte är öppnad nekas autonomt godkännande även om klienten visar knappen. En autonom övergång skapar exakt nästa förgodkända planversion, bevarar historiken och skriver ett engine decision + audit event.
