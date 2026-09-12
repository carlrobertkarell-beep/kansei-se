# Kansei UX 2.0 QA

## Funktion
- [ ] Startsidan laddar UX2-sektionerna utan console errors.
- [ ] `/hjalp-mig-boka/` fungerar för samtliga valvägar.
- [ ] Externa Bokadirekt-länkar öppnas korrekt.
- [ ] Kunskapsbankens sök och filter fungerar.
- [ ] Nya kunskapssidor har fungerande interna länkar.

## Mobil
- [ ] iPhone Safari 375–430 px.
- [ ] Android Chrome 360–430 px.
- [ ] Inga horisontella overflow-problem.
- [ ] Tryckytor minst cirka 44 px.
- [ ] Rubriker bryts naturligt.

## Desktop
- [ ] 1280, 1440 och 1728 px.
- [ ] Bildplatshållare ersätts med riktiga klinikbilder.
- [ ] Ingen sektion känns överdrivet hög eller glest satt.

## Medicinsk kvalitet
- [ ] Ingen problemnavigator uttrycker en definitiv diagnos.
- [ ] Röda flaggor leder vidare till annan vård.
- [ ] Injektionsvägar kräver bedömning före behandling.
- [ ] Ultraljud beskrivs som komplement till klinisk undersökning.

## SEO
- [ ] Lägg nya URL:er i sitemap.xml före merge.
- [ ] Kontrollera canonical på samtliga nya sidor.
- [ ] Lägg Article/MedicalWebPage-schema på kunskapssidor i nästa SEO-pass.
- [ ] Kontrollera interna länkar från startsida och relevanta tjänstesidor.

## Bilder
När klinikbilder kommer:
1. huvudbild behandlingsrum/arbete,
2. patient + ultraljudsskärm,
3. detaljbild prob/skärm,
4. injektionsmiljö,
5. rehab/rörelse,
6. entré/interiör.

Bildfiler konverteras till WebP/AVIF, får fasta dimensioner och beskrivande alt-text innan produktion.
