# Adaptive plan process

`plan-readiness.mjs` provides shared rules for clinician plans, worksheets and an internal self-service preview. Requirements are derived from current evidence. Optional information is separate from completion; the count is not a measure of clinical safety or AI confidence.

Clinician preparation covers goal/context, digital contact when needed, exercise checks, follow-up, explicit review and the exact saved payload. Distances and longer periods retain the existing care-journey validation. Worksheets need exercise checks and review only. Print opening does not prove that a patient received the plan. Digital delivery requires an actual matching active plan; training and response completion require that same plan ID and current payload.

Review confirmation is deliberately session-local and tied to a canonical content fingerprint. Changes invalidate it. Returning to a saved draft starts a fresh review. Existing active plans retain their established activation evidence. Save status is derived from a matching saved record; unsaved changes cannot retain the saved checkmark. Draft saving remains possible before preparation is complete, while clinician activation and printing use the readiness check as well as their existing guards.

The internal self-plan preview is reached from the worksheet. It uses the same process rules and existing library, in memory only. It has no patient, account, payment, delivery or external AI API. Choosing rehab for symptoms pauses automatic preparation for clinician assessment. This is not a public self-service launch or clinical triage. Existing rollout and organization gates remain unchanged.

No schema migration is required. Tests cover stale reviews, exact-plan evidence, conditional steps, closed activation, explicit print review, draft reload, self-service input changes, and responsive screenshots using fictional services.
