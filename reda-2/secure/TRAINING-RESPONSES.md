# Exercise Intelligence · svar efter passet

`training-responses.sql` är källan för en hanterad Supabase-migrering. Den lägger till en tom tabell, RLS och en avgränsad RPC. Befintliga planer, träningspass och konton ändras inte. Tillämpad i det separata Reda-projektet 2026-09-10: fjärrversion `20260910192327`, namn `exercise_intelligence_training_responses`. Efterkontroll: RLS aktiverad, anonym RPC avstängd, publik funktion kör som anropare, privilegierad funktion ligger i `private`. Inga svar skapades i projektet under verifieringen.

Publik RPC `reda_submit_training_response(p_session_id, p_request_id, p_answers)` kör som anroparen och delegerar till en privat skrivfunktion. Inloggad användare måste ha en levande Auth-session, vara varken raderad eller avstängd och vara kopplad till passets aktiva patient. Servern härleder planversion och alla ägarfält. Browserrollen saknar direkt INSERT, UPDATE och DELETE. Patienten kan läsa egna svar, behandlaren egna patienters svar med AAL2.

Sex fasta fält med kategoriska svar; ingen fritext. CHECK begränsar typer, nycklar och värden. Samma request-ID och samma svar returnerar befintlig post. Samma pass och identiska svar är också idempotent vid ny begäran. Motstridiga svar skriver inte över varandra. Audit innehåller ID och version, inte svarets innehåll.

UI kräver avslutat eller stängt delvis genomfört pass, tidigast följande kalenderdag i Stockholm och högst 14 kalenderdagar bakåt. Detta är rapporteringsfönstret, inte en medicinsk progressionsregel. Svar kan höra till en äldre planversion och flyttas aldrig till den nu aktiva. Återkopplingen ändrar inte ordinationen och skapar inte bokning eller bevakat ärende. Den kopplas inte automatiskt till progressionsmotorn ännu.

Den nya API-hämtningen är isolerad från plan/pass: ett fel visar återkopplingsfel, men stoppar inte träningen. Upp till 100 svar hämtas och gränsen framgår i kliniken. Inmatning ligger i minnet under formulärflödet. Misslyckad sparning kan försökas igen med samma begäran medan sidan är öppen; ingen offlinegaranti. Senare rättelser och arkivexport återstår.

## Verifiering
`node --test .github/reda2-tests/intelligence-system.test.cjs`

GitHub Actions kör `response_database_test.sql` i en helt separat, tom PostgreSQL-databas med fiktiva Auth-identiteter. Tester prövar RLS, AAL2, främmande pass, indragen session, avstängd/raderad användare, rapporteringsfönster, validering, dubletter, konflikter och revisionsspår. Detta är databasverifiering, inte ett prov av riktig mejlleverans eller patientinloggning.

`intelligence_browser_test.py` använder en fiktiv tjänst i minnet för patient-, klinik- och publikflöden samt skärmbilder i mobil och desktop. Ingen mejlsändning eller patientaktivering ingår.

## Efterkontroll av rådgivare
Ingen ny säkerhetsanmärkning för svarstabellen eller RPC:n. Den befintliga Auth-inställningen för [kontroll av läckta lösenord](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection) är avstängd och kvarstår inför pilot. Rådgivaren visar också äldre RLS-optimeringar och [två läspolicyer](https://supabase.com/docs/guides/database/database-linter?lint=0006_multiple_permissive_policies) för olika behörighetsvägar; svarstabellen följer samma uppdelning mellan patient och MFA-behandlare. Oanvända index är väntat innan användardrift och tas inte bort av den anledningen.
