# EI Fleet · serveraggregering

Flottstatus beräknas nu i dashboard-RPC:n över hela behandlarens patientpopulation innan paginering. Den är därför oberoende av om kliniken har 50, 500 eller många tusen aktiva planer; klienten räknar aldrig totalsiffror från de 25 synliga raderna.

Varje dashboardrad får `frame_status`, `frame_execution` och en serverberäknad `fleet_state`. Servern returnerar dessutom `fleet` med totaler för `autonomous`, `evidence`, `held`, `review`, `shadow` och `unmanaged`.

Filtren `autonomous`, `evidence`, `held` och `shadow` körs server-side före `limit 25 offset`, så arbetslistorna kan pagineras utan att tappa patienter. `review` fortsätter använda den befintliga prioriteringskön eftersom den inkluderar kliniska signaler, meddelanden och förfallna uppföljningar utöver motorstatus.

Databasen använder redan indexerade laterala läsningar för senaste session, svar, motorbeslut och öppna ärenden. Den godkända progressionsramen hämtas via det partiella unika indexet `reda_one_approved_frame(patient_id)`. Nästa skalningssteg är cursor-baserad paginering när volymerna motiverar att lämna offset-modellen.
