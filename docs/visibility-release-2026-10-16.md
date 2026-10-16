# Leveranslogg — Kansei 16 oktober 2026

## Publicerat och verifierat

Webbplatsversion: `09e5e34b15a44a36229a975228f0c471729ad79c`.

137 offentliga HTML-sidor uppdaterades. Tyngdpunkten är gemensam teknik, sökbar navigation och mätning; det betyder inte att 137 medicinska artiklar har skrivits om.

Den publicerade versionen verifierades 16 oktober 2026 genom att hämta och jämföra innehållet på tio huvudsidor, det nya statistikskriptet och sitemap med den publicerade källkoden. Sitemap innehåller 137 adresser. GitHub Actions-körning 38942505130, jobb 117113394131, slutfördes utan fel.

IndexNow tog emot en avisering om nio ändrade huvudsidor med HTTP 200. Detta bekräftar mottagning, inte indexering, Google-inlämning, AI-citering eller förbättrad placering.

## Genomförda ändringar

- Rättade verksamhetstexter om behandlare och specialistmedverkan på naprapatisidan, behandlarpresentationen och jämförelseartikeln om vårdyrken. Synlig FAQ och motsvarande strukturerade svar är samstämmiga.
- Tydliggjorde kontakttextens tjänsteområden och kopplingen mellan ultraljud och information till hänvisande vårdgivare. Tog bort en upprepad text på ultraljudssidan.
- Lade bildbibliotekets meny­länk direkt i HTML, i stället för att vara beroende av en JavaScript-injektion. Befintlig kod undviker dubbla länkar.
- Enhetliggjorde kliniknamn i berörda metadata och strukturerade uppgifter, kopplade befintliga författarobjekt till behandlarpresentationen och lade till WebSite-beskrivning. Rättade naprapatitjänstens Service-beskrivning. Tillåtelse för stora bildförhandsvisningar lades till där indexeringsmetadata finns.
- Uppdaterade sitemap-datum endast för sidor med innehållsändringar. Befintliga bild-/videoelement och övriga datum behölls.
- Ersatte det tidigare GA4-skriptet på 137 sidor med en ny version; lade inte till en andra installation. Samma befintliga mät-ID och samtyckesval används.
- Klassificerade 651 uttryckliga bokningslänkar och undantog tre profil-/omdömeslänkar från booking_click. Ett klick är fortfarande bokningsintresse, inte en genomförd bokning.
- Lade till samtyckesbaserade källgrupper för identifierbara hänvisningar från ChatGPT, Perplexity, Copilot, Gemini, Google, Bing, annan webbplats och okänd källa. Frågor, konversationsinnehåll, UTM-värden och patientuppgifter används inte för källgrupperingen.
- Uppdaterade cookieinformationen och lade regressionskontroller i den befintliga SEO-kontrollen. Inga nya återkommande AI-körningar startades och inga befintliga workflowscheman ändrades.

## Bevarat

Inga bild-, video-, SVG- eller typsnittsfiler ändrades. Innehållet i ultraljudets under­sidor kontrollerades som oförändrat bortsett från nya mätattribut på bokningslänkar. Anatomilager, fyndmarkeringar och bilddesign behölls.

Befintliga aktuella behandlingspriser och möjligheten till direktbokning behölls. Inga patientuppföljningar, behandlingsresultat, filmer eller nya samarbeten fabricerades.

## Tester

Den befintliga statiska SEO-kontrollen och de nya synlighetskontrollerna passerade på releasekoden. Kontrollerna omfattar bland annat interna länkmål, sitemap/canonical, JSON-LD-syntax, indexeringsanvisningar, aktuella erbjudanden, mätinstallation och klassificering av bokningslänkar.

Åtta grupper av webbläsartester passerade: inget statistiknätverk före samtycke; en sidvisning efter godkännande; rensade adresser; korrekta bokningsklick utan omdömesklick; källgrupp genom intern navigation; stopp och rensning vid återkallande; domän-/tidsgränser; samt mobil- och datorlayout utan horisontell överströmning på de testade huvudsidorna. Skärmbilder granskades. Tredjepartstrafiken var simulerad i dessa tester, inte verklig insamling i GA4.

## Färdig mätgrund, inte ett uppmätt AI-resultat

`.github/kansei/visibility.py` innehåller 30 fasta frågor, fyra AI-tjänster och tre upprepningar: 360 planerade observationer per full omgång. Verktyget skiljer omnämnande, källhänvisning och rekommendation; räknar bara granskade genomförda svar; visar täckning; och håller modell, gränssnitt och sökläge separat. Saknade tester är inte nollresultat.

Antal verkliga flerplattformstester utförda i denna leverans: **0**. Självtester av rapportverktyget är inte tester av AI-tjänsternas svar. Resultatfiler ska hållas utanför detta publika repository.

## Kvarstående kontoberoenden

GSC Wizard returnerade payment_required; nya Search Console-rapportdata och URL-inspektioner kunde därför inte hämtas via den kopplingen. Detta är ett åtkomsthinder för verktyget, inte ett fel på webbplatsens indexering.

Faktisk GA4-insamling och eventuella anpassade dimensioner behöver verifieras i kontot. Google Business Profile-status, kategori, kartplacering och dubbletter är inte ändrade eller verifierade av webbplatsleveransen. Bing Webmaster-rapporter är inte hämtade. Genomförda Bokadirekt-bokningar är inte integrerade.

Ingen förstaplats, trafikökning, AI-citering eller bokningsökning påstås vara verifierad genom denna leverans.

Se även `visibility-measurement-2026-10-16.md` för mätmetod, kontroller och officiella källor.
