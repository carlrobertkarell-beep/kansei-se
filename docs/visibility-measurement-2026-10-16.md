# Kansei: sökbarhet, AI-synlighet och bokningsintresse

Version 16 oktober 2026. Operativ dokumentation, inte en publik patienttext eller ett uppmätt rankingresultat.

## Vad den nya webbplatsmätningen gör

Den befintliga GA4-strömmen G-F1EVW66L9S återanvänds. Ett nytt versionsmärkt samtyckesskript ersätter, inte kompletterar, det tidigare skriptet. Den gamla filen lämnas kvar för cachekompatibilitet men refereras inte av de uppdaterade sidorna.

- `page_view`: visning av en offentlig kliniksida efter aktivt samtycke.
- `booking_click`: ett uttryckligt klick mot bokning, inte ett genomfört besök eller köp.
- `placement`: header, footer, guide, menu eller content. Ingen behandlingskod eller fritext.
- `referral_group`: chatgpt, perplexity, copilot, gemini, google, bing, other eller unknown. Endast strikt kontrollerad hänvisande domän, inte frågan, konversationen eller UTM-värden.
- `measurement_version`: 20261016, så mätförändringen går att skilja från en verklig trafikförändring.

Källgruppen hålls efter samtycke i sessionStorage i den aktuella fliken med en giltighetstid på 30 minuter. Gruppen tas bort när användaren avstår. Samtyckesvalet använder samma befintliga 180-dagarsinställning. GA4 skickar fortfarande bara den offentliga sidans huvudadress utan frågesträng/fragment och hänvisarens origin. Inga nya besökar-ID:n, patientuppgifter, formulärvärden, behandlingsval eller bokningsutfall har lagts till.

Omdömeslänkar och rena profil-/informationslänkar till Bokadirekt är uttryckligen undantagna. Förändringen kan därför sänka antalet rapporterade booking_click jämfört med en äldre mätperiod utan att verkliga bokningar har minskat.

Google-sökningens vanliga resultat, AI Overviews och AI Mode kan inte skiljas åt säkert med en vanlig google-referrer. De klassificeras därför som google, inte som säker AI-trafik. Saknad hänvisare är unknown, inte antagen AI-trafik. Hänvisningstrafik mäter besök, inte hur ofta en AI har citerat en sida utan att någon klickat.

## Kontoinställningar och avgränsningar

Google Analytics: kontrollera verkliga data i rätt egendom/ström efter publicering. Enhanced Measurement ska fortsatt vara avstängt enligt tidigare bekräftad konfiguration. Automatisk insamling av formulär, sökningar och råa länkar ska inte aktiveras. Lägg vid behov till händelsebaserade anpassade dimensioner för referral_group, measurement_version och placement. Dessa inställningar är inte gjorda av webbplatskoden. Jämför med insamlade faktiska händelser, inte bara lokala tester.

Search Console: GSC Wizard-kopplingen returnerade payment_required den 16 oktober. Detta blockerar hämtning via verktyget, inte webbplatsens indexering. När läsbehörighet är återställd: kontrollera URL-inspektion, Google-vald canonical, senaste genomsökning, sitemap och Search-resultat för ultraljud, hyaluron och naprapati. Håll varumärkessökningar åtskilda från övriga sökningar och jämför fullständiga perioder med samma land och enhet.

Google har en separat Generative AI performance report för visningar i AI Overviews och AI Mode. Rapporten kan saknas när underlaget är otillräckligt. Räkna inte frånvaron av rapporten som verifierat noll. Måttet är visningar, inte verifierade bokningar. Inställningen för inkludering i generativa AI-funktioner måste kontrolleras i kontot; den kan inte ersättas med robots.txt.

Bing Webmaster Tools: följ den tillgängliga AI Performance-rapporten separat från webbtrafiken. Kontrollera vilka sidor och citeringar som faktiskt rapporteras. Ingen Bing-inloggning, verifiering eller rapporthämtning har genomförts av denna kod.

Google Business Profile/Maps: profilstatus, korrekt kategori, kartplacering och möjliga dubbletter behöver granskas med rätt kontobehörighet. Webbplatsändringar betyder inte att dessa kontoinställningar är ändrade. Använd samma sökfrågor från fasta kontrollpunkter kring Odenplan/Vasastan och samma enhet/läge vid jämförelse. En kontroll hemifrån är inte ett områdesresultat.

Bokadirekt: ingen färdigbokningshändelse eller åtkomst till bokningsutfall finns i denna leverans. Bekräftade bokningar måste föras in som ett separat, verifierat aggregerat mått via en tillåten integration eller egen sammanställning. Skicka inte patientidentitet eller hälsouppgifter till GA4 för att försöka koppla ihop detta.

## Jämförbar AI-mätning

Verktyget `.github/kansei/visibility.py` innehåller 30 fasta frågor, tio per tjänsteområde. Samma fråga ska testas i ChatGPT, Gemini, Copilot och Perplexity med tre oberoende upprepningar: 360 planerade tester per omgång.

Frågorna ska ställas i nya konversationer, utan att Kansei föreslås i förväg. Håll språk och angiven plats lika. Dokumentera gränssnitt, synlig modellbeteckning (eller not_disclosed), sökläge, tid med tidszon och en lokal hänvisning till det sparade svaret/skärmbilden. Ett API-resultat får inte etiketteras som ett test av konsumentgränssnittet. Resultatfiler ska hållas utanför detta publika repository.

Mät tre separata utfall: namnet förekommer, en Kansei-sida citeras, Kansei rekommenderas som mottagning. En rekommendation kräver ett granskat citat ur svaret som faktiskt rekommenderar mottagningen; en fotnotslänk räcker inte. Granska länkarnas faktiska mål. Räkna återkommande källdomäner separat, men anta inte att alla källor är klinikkonkurrenter.

Ej genomförda tester är pending. Tekniskt misslyckade tester är error. Endast completed och reviewed ingår i nämnaren för synlighetsmåtten. Täckningen mot de 360 planerade testerna redovisas alltid. Saknat underlag visas som streck, inte som 0 procent. Modell, gränssnitt och sökläge särredovisas. Inget sammanslaget påhittat AI-poängtal eller garanterad Googleplacering beräknas.

```sh
python3 .github/kansei/visibility.py --questions
python3 .github/kansei/visibility.py --template /saker-lokal-plats/omgang.json
python3 .github/kansei/visibility.py --report /saker-lokal-plats/omgang.json --output /saker-lokal-plats/rapport-2026-10-16
```

Rapporten producerar JSON och Markdown med täckning, utfall per tjänst/modell/område samt de domäner och Kansei-sidor som verkligen citerats i granskat underlag. Att skapa mallen genomför inga tester och kontaktar inga AI-tjänster. Ingen återkommande körning har startats.

## Prioritering från resultat till ändring

1. Inte genomsökt/indexerad eller fel vald canonical: åtgärda upptäckt/teknik först, inte fler texter om samma ämne.
2. Visningar men svag klickfrekvens på rätt frågor: jämför sidans löfte, sökresultat och konkurrerande sidor innan rubrik/snutt ändras.
3. Besök men svagt bokningsintresse: testa besökstyp, prisförståelse och vägen till rätt bokning. Ett omdömesklick är inte bokningsintresse.
4. Konkurrent citerad: dokumentera exakt fråga, svar och citerad sida. Jämför vilket faktaunderlag Kansei saknar; orsaken till algoritmens val är en hypotes, inte känd intern rankingdata.
5. Filmer, verklig uppföljning och externa hänvisningar: prioritera originalmaterial från kliniken. Publicera inte påhittade patientförlopp, effektresultat eller samarbetsrelationer. Utskick/nya omdömen får inte fabriceras.

Spara ändringsdatum och jämför lika långa kompletta perioder, men tillskriv inte automatiskt en förändring hela effekten. Trafik, bokningsintresse och bokningar hålls separat.

## Primärkällor

- Google AI-vägledning: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- Generativ AI-rapport: https://support.google.com/webmasters/answer/16984139
- GA4-konfiguration: https://developers.google.com/analytics/devguides/collection/ga4/reference/config
- OpenAI-sökrobotar: https://developers.openai.com/api/docs/bots

Dokumentationen ersätter inte kontroll av respektive konto. Inga positioner, AI-citeringar eller bokningar är uppmätta enbart genom denna leverans.
