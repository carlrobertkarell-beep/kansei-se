# Slemsäcksbesvär i axeln – förberett innehåll och bildplan

Status: utkast för bildleverans, 15 oktober 2026. Sparat i webbplatsens källkod på `content/shoulder-bursa-prep-20261015`. Inte publicerat på huvudsidan. Carl-Robert tar fram bilderna.

## Vad som är förberett

- Patienttext för den befintliga adressen `/ultraljud/bursit-axel/`, med besvär, anatomi, undersökning, fyndens begränsningar och fortsatt plan.
- Sex vanliga frågor med motsvarande FAQ-data, lokal sidtitel, beskrivning, avsändare och medicinska källor.
- En inaktiv bildmall med längd- och tvärsnitt, original → anatomi → fynd. Mallen använder den befintliga bildvisarens struktur och aktiveras först med faktiska bilder.
- Kontextuell väg från kalkaxelartikeln och sidan om axelbesvär på natten. Axelns huvudsida länkar redan till slemsäckssidan.
- Det befintliga kalkaxelfallet behåller sin korrekta beskrivning som kalk och samtidig senskada.

## Underlag som fyller fallbeskrivningen

Välj i första hand bilder från samma undersökning. Om materialet kommer från olika personer presenteras varje exempel separat.

| Del | Uppgift som behövs |
|---|---|
| Klinisk fråga | Sida, var det gör ont, ungefärlig duration och vad som begränsar armen. |
| Längdsnitt | Originalbild och din beskrivning av det faktiska fyndet i slemsäcken. |
| Tvärsnitt | Samma område i ett andra plan, om det finns. Ange vad som ska pekas ut. |
| Närliggande sena | Vad som faktiskt bedömdes i rotatorkuffen; inga antagna normala fynd. |
| Jämförelse | Motsatt sida eller annan relevant jämförelse om den finns och tillför något. |
| Film | Kort originalsekvens under rörelse, eller Doppler, endast om den finns och tillför information. |
| Klinisk slutsats | Hur fynden stämmer med besvär och funktion, samt den verkliga fortsatta planen. |

Exakt ålder, patientnamn och andra identifierande uppgifter behövs inte. Använd avidentifierat material med klartecken för publicering.

## Bildpresentation och anatomi

- Originalbilden visas först. Anatomilagret följer samma vävnadsstil som klinikens godkända axelfall.
- Vävnadernas verkliga gränser styr lagret: deltoideus, slemsäck, relevant sena och synlig benkontur markeras bara när de kan identifieras i just bilden.
- Fyndmarkeringen visar endast det Carl-Robert har beskrivit. Vätska och väggförändring hålls isär; ruptur, kalk eller ökat blodflöde läggs endast till om underlaget visar det.
- En kort ”Titta efter”-text förklarar vad läsaren ska se. Teknisk beskrivning ligger i en utfällbar del.
- Jämförelse- och filmvyer läggs till när materialet motiverar dem. Inga tomma flikar visas.
- Exakta bildmått och koordinater bestäms från originalen. Ingen sträckning eller generell beskärning får flytta fynd och anatomilager från varandra.

## Kopplingar och publicering när bilderna finns

1. Fyll bara uppgifter som hör till den valda undersökningen. Saknad anamnes eller uppföljning ersätts inte med en konstruerad berättelse.
2. Bygg och registrera anatomilagren utifrån bilderna. Montera den färdiga bildsektionen vid `BURSA_CASE_INSERT`; lägg till lokal länk till `#bilder`.
3. Lägg till ImageObject-data med verkliga bildbeskrivningar. VideoObject, längd, förhandsbild och publiceringsdatum läggs till först för en verklig publicerad film.
4. Förhandsvisningar på relevanta ingångar kan då visa det egna bursitfallet. Bevara gränsen mot bicepssenans senskida, kalkaxel och ledartros. Kopplingen för detta innehåll är axelultraljud och klinisk bedömning.
5. Uppdatera synligt datum och dateModified vid den faktiska publiceringen. Uppdatera mediesitemap och kontrollera mobil, dator, original, anatomilager, fynd, förstoring och eventuell film före publicering.

Det färdiga textutkastet nedan är allmän patientinformation. Den individuella fallbeskrivningen tillkommer med bilderna och Carl-Roberts kliniska uppgifter.

---

## Slemsäcksbesvär i axeln – ultraljud och bedömning

Ont på axelns utsida när du lyfter armen eller ligger på sidan? Ultraljud kan bidra till bedömningen av slemsäcken och senorna under skuldertaket. Vi kopplar fynden till din rörlighet, styrka och smärta.

Du träffar Carl-Robert Kårell, legitimerad naprapat med utbildning inom muskuloskeletalt ultraljud, på Upplandsgatan 26 vid Odenplan.

### Ont när du lyfter armen eller ligger på axeln?

Smärta på axelns utsida, besvär när du når upp mot en hylla eller värk i sidoläge kan förekomma vid problem kring slemsäcken och rotatorkuffens senor. Symtomen överlappar flera tillstånd och behöver undersökas i sitt sammanhang.

Vi frågar om debut, belastning, sömn och vad armen har svårt att klara. Sedan bedöms rörlighet, styrka och smärtprovokation innan ultraljudet riktas mot den aktuella frågan.

#### Ett glidlager mellan vävnaderna.

Den subakromiala-subdeltoida slemsäcken ligger mellan delar av rotatorkuffen och vävnaderna ovanför. I en vanlig ultraljudsvy ses den mellan supraspinatussenan och deltoideusmuskeln. Den hjälper vävnaderna att glida när armen rör sig.

Bursit är en benämning på inflammation i en slemsäck, ofta kallad slemsäcksinflammation. Smärtans plats avgör inte ensam om slemsäcken bidrar till besvären.

### Vad kan ultraljudet visa?

Vi kan bedöma om den tillgängliga slemsäcken är utspänd, innehåller ökad vätska eller har förändrade väggar. Närliggande senor undersöks samtidigt när det är relevant för frågan.

Olika snitt hjälper oss att följa strukturerna. När det tillför information undersöks axeln också under rörelse, så att slemsäcken och senan kan följas när armen lyfts.

### Vad avgör bilden inte ensam?

Vätska eller förtjockning behöver vägas mot var det gör ont, vilka rörelser som provocerar och hur axeln fungerar. Ett bildfynd fastställer inte ensamt orsaken till smärtan eller vilken behandling som behövs.

Ultraljud ger inte en fullständig bild av alla djupa ledstrukturer. Vid en annan frågeställning kan annan utredning behövas. Läs om valet mellan ultraljud och MR.

### Vad betyder undersökningen för nästa steg?

Fynden förklaras under besöket och kopplas till den aktivitet du vill kunna göra bättre. Planen kan omfatta råd om belastning, anpassad rehabilitering och uppföljning av rörelse och funktion.

Vid kvarstående frågor, uttalad svaghet eller andra avvikande fynd kan vidare medicinsk bedömning behövas. En eventuell injektion bedöms separat och ingår inte automatiskt i undersökningen.

### Är det slemsäcken, kalk eller senan?

Kalkaxel gäller kalk i en sena. Bicepssenans senskida är ett annat utrymme än slemsäcken under skuldertaket. Flera fynd kan finnas samtidigt och behöver bedömas tillsammans.

Se våra separata undersökningsexempel om kalk och samtidig senskada samt bicepssena med vätska i senskidan.

### Axeln under rörelse.

Vårt kalkaxelfall visar supraspinatussenan under skuldertaket i både stillbild och film. I anatomivyn kan du känna igen vävnaderna innan du ser dem i rörelse.

Det publicerade fallet gäller kalk och en samtidig senskada. Filmen hjälper dig att förstå området och hur en dynamisk axelundersökning ser ut; den är inte ett dokumenterat bursitfall.

Se originalbild, anatomilager och filmen under axeltaket →

### Vanliga frågor om slemsäcken i axeln

**Kan ultraljud visa slemsäcksinflammation i axeln?**

Ultraljud kan visa vätska och förändringar i slemsäckens väggar som bidrar till bedömningen vid misstänkt bursit. Vi väger fynden mot dina besvär, den kliniska undersökningen och senorna i området.

**Är vätska i slemsäcken samma sak som vätska kring bicepssenan?**

Det är olika anatomiska utrymmen. Slemsäcken ligger ytligt om delar av rotatorkuffen. Bicepssenans senskida ligger kring senan på axelns framsida. På sidan om bicepssenan finns ett separat bildexempel.

**Är bursit och kalkaxel samma sak?**

Bursit gäller slemsäcken, medan kalkaxel innebär kalk i en sena. De kan förekomma i samma område. Undersökningen behöver därför väga ihop slemsäck, senor och axelns funktion. Läs om ultraljud vid kalkaxel.

**Behöver jag en injektion om slemsäcken är påverkad?**

Ett fynd avgör inte ensamt behandlingen. Anpassad belastning och rehabilitering kan ingå i planen. Eventuell injektionsbehandling kräver ett separat ställningstagande till nytta, risker och alternativ och ingår inte automatiskt i ultraljudsbesöket.

**Behöver jag remiss och vad kostar besöket?**

Ingen remiss behövs. Ultraljud av rörelseapparaten hos Kansei tar 45 minuter och kostar 1 290 kr. Riktad klinisk undersökning, ultraljud, genomgång av fynden och rekommendationer om nästa steg ingår. Separat skriftligt utlåtande beställs enligt priser och villkor.

**Hur förbereder jag mig?**

Välj kläder som gör axeln lätt att komma åt. Ta gärna med tidigare bildutlåtanden. Fundera över när smärtan började och vilka lyft, sovlägen eller vardagsrörelser som begränsar dig.

### När annan vård behövs först

Plötslig kraftig smärta efter skada, oförmåga att använda armen eller feber och sjukdomskänsla tillsammans med en varm eller svullen axel behöver skyndsam medicinsk bedömning. Välj då vård utifrån symtomen i stället för att invänta ett planerat ultraljudsbesök.

### Källor och bildmaterial

Undersökare och källa till de publicerade axelbilderna: Carl-Robert Kårell, legitimerad naprapat, Kansei. Textunderlag förberett 15 oktober 2026.

Bildkälla och villkor för återanvändning →

### Få dina besvär undersökta.

Besöket omfattar klinisk undersökning, riktat ultraljud, genomgång av fynden och rekommendation om nästa steg. Separat skriftligt utlåtande beställs enligt priser och villkor.

Läs om hela undersökningen av axeln →

## Källor

- [ESSR: tekniska riktlinjer för axelultraljud (PDF)](https://www.essr.org/content-essr/uploads/2016/10/shoulder.pdf)
- [AAOS/OrthoInfo: senor och slemsäck vid axelsmärta](https://www.orthoinfo.org/diseases--conditions/shoulder-impingementrotator-cuff-tendinitis/)
- [ACR/RSNA: muskuloskeletalt ultraljud](https://www.radiologyinfo.org/en/info/musculous)
- [NHS: axelsmärta och när medicinsk bedömning behövs](https://www.nhs.uk/symptoms/shoulder-pain/)
