# Exercise Intelligence · svar efter passet

`training-responses.sql` är källan för en hanterad Supabase-migrering. Den lägger till en tom tabell, RLS och en avgränsad RPC. Befintliga planer, träningspass och konton ändras inte. Migreringens faktiska fjärrversion dokumenteras efter tillämpning.

Publik RPC `reda_submit_training_response(p_session_id, p_request_id, p_answers)` kör som anroparen och delegerar till en privat skrivfunktion. Inloggad användare måste ha en levande Auth-session, vara varken raderad eller avstängd och vara kopplad till passets aktiva patient. Servern härleder planversion och alla ägarfält. Browserrollen saknar direkt INSERT, UPDATE och DELETE. Patienten kan läsa egna svar, behandlaren egna patienters svar med AAL2.

Sex fasta fält med kategoriska svar; ingen fritext. CHECK begränsar typer, nycklar och värden. Samma request-ID och samma svar returnerar befintlig post. Samma pass och identiska svar är också idempotent vid ny begäran. Motstridiga svar skriver inte över varandra. Audit innehåller ID och version, inte svarets innehåll.

UI kräver avslutat eller stängt delvis genomfört pass, tidigast följande kalenderdag i Stockholm och högst 14 kalenderdagar bakåt. Detta är rapporteringsfönstret, inte en medicinsk progressionsregel. Svar kan höra till en äldre planversion och flyttas aldrig till den nu aktiva. Återkopplingen ändrar inte ordinationen och skapar inte bokning eller bevakat ärende. Den kopplas inte automatiskt till progressionsmotorn ännu.

Den nya API-hämtningen är isolerad från plan/pass: ett fel visar återkopplingsfel, men stoppar inte träningen. Upp till 100 svar hämtas och gränsen framgår i kliniken. Inmatning ligger i minnet under formulärflödet. Misslyckad sparning kan försökas igen med samma begäran medan sidan är öppen; ingen offlinegaranti. Senare rättelser och arkivexport återstår.

## Verifiering
`node --test .github/reda2-tests/intelligence-system.test.cjs`

GitHub Actions kör `response_database_test.sql` i en helt separat, tom PostgreSQL-databas med fiktiva Auth-identiteter. Tester prövar RLS, AAL2, främmande pass, indragen session, avstängd/raderad användare, rapporteringsfönster, validering, dubletter, konflikter och revisionsspår. Detta är databasverifiering, inte ett prov av riktig mejlleverans eller patientinloggning.

`intelligence_browser_test.py` använder en fiktiv tjänst i minnet för patient-, klinik- och publikflöden samt skärmbilder i mobil och desktop. Ingen mejlsändning eller patientaktivering ingår.
