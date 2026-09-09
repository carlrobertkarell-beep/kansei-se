# Reda secure distribution & sync

Status: **built as deployable backend design, not activated**. Do not use real patient data until every production gate below is completed.

## Architecture

- Static Reda UI contains no secret key.
- Dedicated Supabase project stores patient/program/session data.
- Browser receives only a Supabase **publishable** key. A secret/service key never ships to the browser.
- Supabase Auth identifies users. PostgreSQL grants + Row Level Security (RLS) restrict every exposed row.
- Clinician data access requires role `clinician` **and AAL2/MFA** in database policies.
- Patient can read only their linked patient row and active plan, and can write training sessions only through the idempotent `reda_save_session` RPC.
- Plan activation is atomic: old active plan becomes superseded, new draft becomes active, audit event is written.
- Patient invitations are created by authenticated `invite-patient` Edge Function. The privileged key remains server-side.
- No public Storage bucket is part of v1.

## Production gates

1. Create a **dedicated** Supabase project in exact region `eu-north-1` (Stockholm) if available for the selected plan. Do not use a generic Europe region when a specific EU/Swedish residency decision is required.
2. Complete Kansei's controller/processor assessment and sign/accept the applicable Supabase DPA before health-related personal data is introduced. Confirm Swedish healthcare/privacy requirements with the clinic's privacy/legal adviser.
3. Enable MFA for all clinician/admin accounts. Clinician database policies require AAL2.
4. Enable SSL enforcement, appropriate network restrictions, database connection logging and backup/PITR settings required by the clinic's risk assessment.
5. Apply migrations in order. Then test **allow and deny** cases for anonymous, patient A, patient B and clinician. No production launch before RLS tests pass.
6. Deploy `invite-patient` as an authenticated function. Set `REDA_PATIENT_REDIRECT` to the final patient app URL. Never put a secret key in GitHub or `config.js`.
7. Configure Auth redirect allow-list, email templates, rate limits and session/JWT lifetime. Patient invitation links must identify the intended account; no public share links containing a plan are permitted in production.
8. Replace prototype hash-plan links with authenticated plan loading. Remove all demo patients and local-only patient identifiers from production clinician UI.
9. Add retention/deletion routines, audit review, incident procedure and tested backup/restore.
10. Perform a production security review before first real patient. GitHub Pages alone is not the security boundary; Supabase Auth + RLS + server functions are.

## Sync semantics

- Every plan is versioned. A patient session records both `plan_id` and `plan_version`.
- Activating a new plan never rewrites historical sessions.
- An in-progress session stays attached to the version it started with. The UI may offer the newly active plan only after the current session is closed.
- `client_session_id` makes session writes idempotent so retrying after a network loss does not duplicate a session.
- Patient UI must explicitly show `Sparat på enheten`, `Synkar…`, `Synkat` or `Kunde inte synka`.
- Clinician dashboard reads completion/partial/feedback data as decision support only. It never auto-progresses the patient.

## Files

- `supabase/migrations/20260909_001_secure_reda.sql` – schema, least-privilege grants, RLS, atomic plan activation.
- `supabase/migrations/20260909_002_session_rpc.sql` – hardened idempotent patient session write.
- `supabase/functions/invite-patient/index.ts` – authenticated AAL2 clinician invitation flow.
- `klinik-2.html` – new clinician workspace. Demo-only until this deployment gate is complete.
