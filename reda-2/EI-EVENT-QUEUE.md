# Eventdriven EI · durable kö

Första eventdrivna lagret är en beständig serverkö. Ett nytt nästa-dagssvar lägger en idempotent `response_saved`-händelse för patienten. Klienten behöver därmed inte vara öppen för att arbetet ska finnas kvar.

Kön är inte läs- eller skrivbar från patient- eller klinikerbrowsern. Den är avsedd för en betrodd worker som i nästa block claimar poster, kör samma serverägda `reda_evaluate_progression` och markerar resultatet. Unikt index på patient + orsak + source-ID gör retries idempotenta.

Statusarna `pending / processing / done / failed`, attempts och available_at finns från början för kontrollerade retries och backoff. Inga autonoma beslut körs direkt i triggern; patientens svarstransaktion hålls därför kort och en motorbugg kan inte blockera att patientens svar sparas.
