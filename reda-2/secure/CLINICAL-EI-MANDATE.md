# Clinical EI mandate

This gate is scoped to the existing clinic organization/workspace. It does not create a separate unit model. Administrative `auto_followup` remains independent.

Installation leaves global automatic execution and external AI off. New clinic mandates default off. Owners with active clinical access and MFA may prepare a mandate and a limit of 1–11 automatic advances per approved patient frame. Saving it never changes the global engine settings or a patient plan.

Automatic approval requires both open global execution and an enabled clinic mandate. The server binds the approval to the exact organization and mandate revision. Evaluation rechecks those bindings, current clinical authority, existing evidence and review gates, and the advance limit. Shadow evaluation remains available without automatic authority.

Every mandate change increments its revision. Disabling and re-enabling cannot revive prior automatic approvals. Existing automatic approvals without a mandate binding fail closed and require fresh review. Existing shadow approvals continue normally. Reapproval begins a new frame and therefore a new advance budget; that remains an explicit clinical action against the current published prescription.

The organization lock serializes mandate changes with frame approval/evaluation. The global settings row is share-locked during approval/evaluation so a committed kill-switch change cannot be missed by a waiting execution. An execution already holding the lock may finish before revocation commits; revocation takes effect at its transaction's commit. Retry receipts are scoped to actor, organization and complete input, with live permission revalidation before replay. They retain the previous and resulting mandate states.

Apply `supabase/migrations/20260919165540_clinical_ei_mandates.sql` after the existing production migrations. It verifies the reviewed function hashes and closed rollout flags before replacing any engine function. The migration is additive; it changes no patient plan and enables no execution. `secure/clinical-ei-mandates.sql` is the readable implementation included verbatim after that preflight. CI runs the actual migration in an ephemeral database, including permission, retry, old approval, revision, limit and runtime tests, followed by independent-connection concurrency tests.

The UI lives under **EI och mandat**. It deliberately offers no switch for global rollout and no new automatic patient approval button. Current patient frame review stays in shadow mode until a separate controlled rollout is ready.
