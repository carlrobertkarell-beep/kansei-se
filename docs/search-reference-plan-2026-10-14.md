# Kansei som kunskapskälla i sök och AI

Datum: 14 oktober 2026. Syfte: göra klinikens publicerade kunskap lättare att upptäcka, bedöma och använda som källa för frågor om ultraljud, artros och ledinjektioner. Google avgör vilka källor som visas; en publicering är inte ett bevis på förbättrad placering eller AI-citering.

## Vad granskningen visar

- Användarens skärmbild av sökningen ”synovial injektion” visar ett brett svar om intraartikulära injektioner, med hyaluronsyra, Arthrosamid och kortison. Synovial som anatomiskt ord och Sinovial som produktnamn behöver förklaras. En enskild skärmbild mäter inte hela Kanseis synlighet och avslöjar inte Googles orsaker till källvalet.
- Kanseis befintliga sidor täcker behandlingsprocess, ultraljudsvägledning, eftervård och riktlinjer. En samlad produktguide om Sinovial HL 64 och Sinogel saknades vid granskningen.
- Aktuella produktspecifikationer i IBSA:s bruksanvisningar anger natriumkondroitin i Sinogel. Den tidigare benämningen kondroitinsulfat korrigeras på berörda sidor.
- Search Console-data och URL-inspektion kunde inte hämtas: GSC Wizard returnerade `payment_required`, med besked att provperioden eller abonnemanget saknar giltighet. Faktisk indexering, frågedata och utveckling är därför inte fastställda i denna granskning.

## Genomförda innehållsförbättringar

| Sida | Ansvar i besökarens läsning |
|---|---|
| `/hyaluronsyra/sinovial-sinogel/` | Samlad produktguide: begrepp, innehåll, forskningsläge, bedömning, risker och vanliga frågor. |
| `/injektioner/` | Förklarar ledinjektion/intraartikulär injektion och jämför olika behandlingsalternativ. |
| `/hyaluronsyra/` | Behandling på Kansei, preparatval, aktuella priser och bokning. |
| `/hyaluronsyra/kna/`, `/hoft/`, `/axel/` | Bedömning och forskningsläge för respektive led. |
| `/hyaluronsyra/infor-och-efter/` | Praktisk patientinformation och eftervård. |
| `/kunskapsbank/` och relevanta befintliga artiklar | Vägar till produktguiden från den läsning besökaren redan använder. |
| `/team/carl-robert-karell/` | Klinisk kontakt, legitimation, utbildning och koppling till innehållet. |

En gemensam guide används för de två närliggande preparaten. Det skapas inte en sida för varje stavning eller sökordsvariant. Innehållet är tillgängligt direkt i HTML. Internlänkar, canonical, sitemap och FAQ-data ska stämma med synliga uppgifter. FAQ-data innebär inget löfte om utökade sökresultat eller AI-citering.

## Nästa arbete som kräver klinikens egna underlag

1. **Originalmaterial från kliniken.** Förstärk redan relevanta sidor med godkända, anonymiserade ultraljudsexempel och korta filmer där Carl-Robert visar vad en undersökning faktiskt besvarar. Förklara bildens fynd, begränsning och betydelse för nästa steg. Patientexempel visar ett kliniskt resonemang, inte generell behandlingseffekt.
2. **Verkliga externa hänvisningar.** Använd de faktiska kontakter som redan finns med hänvisande vårdgivare, utbildningsanordnare och leverantörer för sakliga presentationer eller material de själva bedömer som användbart. Korrekt namn, yrkesroll, klinik och webbadress hjälper läsaren att identifiera källan. Inga betalda länkar eller påhittade rekommendationer.
3. **Samma tjänsteuppgifter på andra plattformar.** Användaren uppdaterar Bokadirekt och Google enligt överenskommelsen i prisarbetet. Hemsidans bokningslöften måste fortsatt stämma med faktisk bokningsbarhet, preparat och pris.
4. **Mät och prioritera från Search Console.** När anslutningen fungerar, inspektera de centrala sidorna, kontrollera Google-vald canonical och senaste genomsökning, samt lämna in aktuell sitemap. Indexeringsbegäran för den nya guiden görs i Search Consoles gränssnitt; URL Inspection API begär inte indexering. Kontrollera även inställningen för inkludering i generativa AI-funktioner om den visas i kontots Search Console.

## Mätning efter publicering

Först kontrollera indexering. Jämför sedan två perioder med samma längd och kompletta data, utan att använda dagens ofullständiga trafik. Prioritera visningar, klick, position per fråga/sida och faktiska bokningshändelser. Tolka lågvolymfrågor försiktigt.

Frågegrupper att undersöka: `sinovial`, `synovial injektion`, `sinogel`, `hyaluroninjektion`, `hyaluronsyra knä`, `ledinjektion`, samt `ultraljud knä/axel Stockholm`. Synovial och Sinovial ska räknas som olika skrivningar i mätningen även om samma guide kan besvara dem.

Dokumentera manuella AI-kontroller med datum, exakt fråga, språk/plats och vilka sidor som citerades. AI-svar varierar, så enstaka prov ska inte behandlas som ett stabilt resultat. AI-liknande frågeformer är inte bevis för en faktisk AI-citering. AI-assistentreferrer i GA4 är inte samma sak som Google AI Overview-trafik.

## Källor

- Google Search Central: https://developers.google.com/search/docs/appearance/ai-features
- Google Search Central, uppdaterad vägledning: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- IBSA, Sinovial HL 64: https://www.ibsa-sinovial.de/wp-content/uploads/2024/03/IFU_SINOVIAL_HL_1ago_5000004507_Rev01_DE_280923_VISIONE.pdf
- IBSA, Sinogel: https://www.ibsa-sinovial.de/wp-content/uploads/2024/03/IFU_SINOGEL_3ml_1ago_5000004509_Rev01_DE_280923_VISIONE.pdf
- Socialstyrelsen: https://www.socialstyrelsen.se/contentassets/f1aea0d977d64b18a57ea369fe17032e/2024-12-9337-bilaga-2-socialstyrelsens-icke-gora.pdf
- Pereira med flera, BMJ 2022: https://www.bmj.com/content/378/bmj-2022-069722
- EUROVISCO: https://pubmed.ncbi.nlm.nih.gov/39564753/

Googles vägledning ger stöd för användbart originalinnehåll och tekniskt tillgängliga sidor. Den garanterar inte att de ovanstående förändringarna ger högre ranking. Google anger uttryckligen att llms.txt och särskild AI-markup inte förbättrar synligheten i Google Search.

## Genomförande 15 oktober 2026

- Ledvisa hyaluronsidor och eftervården använder de befintliga, preparatspecifika bokningslänkarna för Sinovial HL 64 och Sinogel. Separat konsultation är fortsatt valfri. Priser och medicinska riktlinjer behålls.
- Knäsidan om hyaluron visar ett redan publicerat originalfynd och länkar direkt till samma fynd i ultraljudsvisaren. Det görs ingen koppling mellan bildens utseende och en utlovad injektionseffekt.
- Sidorna om quadricepssenan och axelns slemsäck har tydligare symtomfrågor, metodgränser, befintliga bildexempel, källor och fortsatt väg till undersökning. Bilden av ledvätska på quadricepssidan presenteras inte som en senskada. Axelfilmen presenteras inte som ett dokumenterat bursitfall.
- De befintliga ultraljudsfilmerna har VideoObject-data med fil, förhandsbild, uppmätt längd och datum från videofilens första tillägg i källkodshistoriken. Knä, kalkaxel, biceps och AC-led kompletterar hälsenans befintliga metadata.
- `sitemap.xml` innehåller nu bild- och videoposter som hämtas från faktiskt publicerad HTML och VideoObject-data. Efter nya bildfall körs `python .github/scripts/update-media-sitemap.py`. Kontroll utan skrivning: `python .github/scripts/update-media-sitemap.py --check`.
- Webbplatsens befintliga automatiska webbläsarkontroll omfattar även de sex uppdaterade undersöknings- och hyaluronsidorna.

Den nya hyaluronfilmen produceras av kliniken och ingår inte i denna publicering. Ingen ny mätning av Googleplaceringar eller AI-citeringar görs med dessa källkodsändringar; uppföljningen ovan kräver aktuella kontodata.

## Knäartros: från bild till plan, 15 oktober 2026

- Den befintliga knäsidans avsnitt `/ultraljud/kna/#artros` har en sammanhängande bildgenomgång med klinisk frågeställning, tre originalfynd och deras betydelse för fortsatt bedömning. Alla bilder och anatomilager är tidigare godkända och publicerade.
- Bildmaterialet kommer från olika personer. Därför presenteras det som separata undersökningsexempel. Ingen patientanamnes, behandling eller uppföljning har konstruerats; en eventuell framtida patientberättelse kräver bakgrund som hör till just den undersökningen.
- Befintliga bildkontroller används för att öppna rätt fynd med original, anatomi och markeringar. Inget nytt bildgränssnitt eller ny anatomisk illustration införs.
- Bildförhandsvisningar ger relevanta ingångar från knäartrosartikeln, kunskapsbankens svullnadssida och undersökningssidan om svullet knä. Hyaluronsidan länkar tillbaka till hela resonemanget och behåller sin direktlänk till originalfyndet.
- Kopplingen till hyaluron förklarar bedömning och ultraljudsvägledning. Bilderna används inte för att förutsäga effekt eller som ensam behandlingsindikation. Grundbehandling, valfri separat konsultation och informationen om Socialstyrelsens avrådan behålls.
- Knäavsnittet ligger på den befintliga kanoniska sidan. Ingen konkurrerande landningssida skapas. Bildinnehållet och länkarna finns direkt i HTML.

Kliniska källor: ESSR:s tekniska knäguide, 1177 för vårdpersonal: knäledsartros (godkänd 2026-01-15), Socialstyrelsens icke-göra-rekommendationer. Klinikens originalfynd följer Carl-Roberts tidigare bildbeskrivningar.

## Patientnytta i hyalurontexterna, 15 oktober 2026

På Carl-Roberts instruktion omarbetas de berörda ingångarna på hela webbplatsen. Möjlig smärtlindring och förbättrad vardagsfunktion vid knäartros framgår före bedömning och praktisk information. Upprepade formuleringar om vad behandlingen inte kan lova ersätts med en tydlig, samlad beskrivning av förväntningar.

Forskningsartiklar och ledvisa forskningsavsnitt behåller riktlinjer och viktiga begränsningar. EUROVISCO beskrivs som expertkonsensus, och stor metaanalys som jämförelse med placebo. För höft och glenohumeral artros bevaras uppgiften att bättre effekt respektive nytta inte har visats; mål med behandling skiljs från visad effekt. Inga knäresultat överförs till andra leder. Inga nya effektstorlekar, responderandelar, varaktigheter eller klinikresultat konstrueras.

Omfattning: hyaluronöversikt, knä/höft/axel, produktguide, injektioner, relevanta artros- och jämförelseartiklar, ultraljud knä och höft, startsida, tjänsteöversikt, behandlarpresentation och vårdgivarinformation. Bokning, priser, konsultationsvillkor, eftervård, riskinformation, bilder och sidlayout behålls. Det separata utkastet om axelns slemsäck ligger kvar på sin egen gren i väntan på bilder.

## Patientfall om knäartros, 15 oktober 2026

Efter granskning av ett konkret utkast gav Carl-Robert instruktionen att gå vidare och koppla ihop de relevanta bilderna med falltexten. Det tidigare avsnittet om knäfynd på `/ultraljud/kna/#artros` ersätts därför av det godkända, anonymiserade patientfallet: belastningsrelaterade knäbesvär och svullnad, måttlig artros på tidigare röntgen, tidigare fysioterapi/egenvård, ledvätska, osteofyter, lokal broskpåverkan samt bedömning och rehabiliteringsplan. Knäsidans övriga bildbibliotek omfattar fortfarande flera undersökningar.

Bilderna kopplas till fallresonemanget och öppnar rätt befintliga originalbild, anatomi och fynd i läsaren. Hyaluron beskrivs som ett möjligt komplement vid kvarstående artrosrelaterad smärta. Texten uppger inte att injektionen har genomförts eller att patienten fått ett visst behandlingsresultat. Uppföljning beskrivs som del av planen.

Hyaluronsidan för knä, knäartrosartikeln och båda sidorna om svullet knä får tydliga ingångar till patientfallet. WebPageElement-data följer den synliga fallbeskrivningen och refererar till de befintliga bildobjekten. Befintlig kanonisk URL, bildlager, bokningstjänster, priser och medicinska fördjupningar behålls.

I publiceringstexten anges ingen höger-/vänstersida för patienten; de befintliga undersökningsbildernas egna sidmarkeringar bevaras.
