# Kansei UX 2.0

## Produktprincip
Kansei.se ska inte primärt organiseras efter klinikens tjänster. Den ska hjälpa patienten från problem till rätt nästa steg.

**Kärnflöde:** Problem → förstå → undersök → behandla → bygg upp → följ upp.

## Primära patientresor
1. **Jag har ont och vet inte vad det är** → problemnavigator → rekommenderad bedömning → bokning.
2. **Jag vet vad jag söker** → ultraljud / naprapati / injektion / rehab → tjänstesida → bokning.
3. **Jag har en känd diagnos eller frågeställning** → kunskapsbank → relevanta behandlingsalternativ → bokning.
4. **Jag är befintlig patient** → Reda / återbesök / progression.
5. **Jag är vårdgivare** → professionellt remiss- och samarbetsflöde.

## Startsida 2.0
1. Hero: `Först förstå. Sedan behandla.`
2. Primärt val: `Vad behöver du hjälp med?`
3. Smart problemnavigator: kroppsdel → symtommönster → rätt vårdväg.
4. Kansei-metoden: `Undersök → Förstå → Behandla → Bygg upp`.
5. Visuell diagnostik: riktiga klinik- och ultraljudsbilder.
6. Rätt behandling, inte flest behandlingar: naprapati, MSK-ultraljud, injektioner, rehab.
7. Reda: vården fortsätter mellan besöken.
8. Kliniken och teamet.
9. Kunskap / vanliga problem.
10. Omdömen och förtroende.
11. Enkel slut-CTA.

## UX-regler
- Patienten ska aldrig behöva förstå tjänstekatalogen för att boka rätt.
- En primär CTA per vy.
- Progressive disclosure: enkelt först, medicinskt djup vid behov.
- Ingen generisk AI-chatbot. Intelligens ska byggas in i navigation, rekommendation och bokningslogik.
- Medicinsk trygghet före säljspråk.
- Kampanjer presenteras som `Aktuellt på Kansei`, inte som rabattbutik.
- Mobile-first. Stora tryckytor, kort läsavstånd, minimalt antal beslut per steg.
- Motion ska förklara hierarki och respons, aldrig vara dekorativt brus.
- Reda är steg fyra i vårdkedjan, inte en separat appannons.

## Problemnavigator v1
### Kroppsdel
Axel · Armbåge · Hand/handled · Rygg · Höft/ljumske · Knä · Fot/fotled

### Exempel: knä
**Var känns det?** Framsida · Insida · Utsida · Baksida · Diffust/svullet

**När märks det mest?** Trappor · Löpning/belastning · Efter vila · Vridning · Svullnad · Annat

### Resultat
Resultatet ska inte ställa diagnos. Det ska säga:
- vad symtommönstret kan motivera att vi undersöker,
- om MSK-ultraljud kan vara relevant,
- vilken typ av besök som är rimligast,
- när annan vård bör sökas först.

## Smart bokning v1
Ingångar:
- Jag har ont och vet inte vad jag ska boka
- Jag vill undersöka med ultraljud
- Jag har axelbesvär
- Jag har artros / funderar på injektion
- Jag vill boka naprapati
- Jag är redan patient och ska på återbesök

Systemet rekommenderar tjänst innan extern Bokadirekt-länk öppnas.

## Bildplan
Riktiga bilder prioriteras framför stock:
- undersökning i behandlingsrum
- MSK-ultraljud med patient + skärm
- närbild prob/hand/struktur
- ultraljudsskärm med kliniskt fynd
- injektionsmiljö utan onödigt dramatisk nålbild
- rehab/rörelse
- klinikens entré/interiör
- team i arbete, inte poserande porträtt

## Nästa implementation
1. QA och inventering av befintlig startsida.
2. Bygg navigator som återanvändbar komponent i statisk HTML/CSS/JS.
3. Bygg smart bokningslager före Bokadirekt.
4. Omstrukturera startsidan kring Kansei-metoden.
5. Integrera riktiga klinikbilder när de levereras.
6. Därefter kunskapsbankens symptom-/diagnosarkitektur och internlänkning.
