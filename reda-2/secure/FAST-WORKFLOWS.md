# Patient overview and fast plan workflows

The registry starts with all patients, server-paged in batches of 25. Counts describe the clinician's selected workspace. EI, symptom, reply and review queues overlap; they are not additive totals. Opening a patient keeps the registry visible. Full authoring is an explicit next step.

Normal registration requires a name, clinical focus, goal and a reviewed start profile. Digital handover also requires email or phone. Explicit clinic handover can omit electronic contact. Quick choices populate the same validated fields used by import and duplicate review. The separate worksheet stays in memory and can be printed without creating a patient or plan record.

EI keeps a separate proposal context until the clinician applies a reviewed candidate. Empty legacy fields receive visible defaults; patient intake choices and existing plan context take precedence. A clinical direction is always selected by the clinician. The complete, focused and lower-volume choices use the existing exercise library and rules, with no inferred diagnosis or external patient AI call.

Apply `fast-workflows.sql` after the patient-intake and plan-authoring migrations. It adds private profile metadata and replaces the existing checked functions. Older clients remain compatible and do not erase the new metadata. Existing session/MFA, organization, clinician ownership, receipt, duplicate and revision checks remain in force. No patient record or plan is changed by the migration. Activation, invitations, external patient AI and automatic progression gates retain their existing settings.

The CI suite verifies a 1,000-patient workspace, quick registration through saved draft, multiple EI candidates, direction persistence, worksheet print isolation and database authorization/idempotency. Browser screenshots are included in the test artifact.
