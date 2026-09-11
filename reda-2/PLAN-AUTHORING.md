# Two entry points, one prescription

The live clinic editor now starts with an empty manual prescription for a patient without a plan. Intake goal, contact details and next contact carry forward. No clinical direction, tolerance or training history is inferred from a patient's name or free text.

- **Sätt ihop själv:** search the complete existing exercise library, filter by its actual regions, add exercises, select variants and individual doses, reorder, remove and undo. A side selector changes only exercises supporting that side. Days are edited directly. Exercise instructions and the existing motion renderer are available beside the prescription.
- **Få ett EI-förslag:** choose a transparent starting profile and clinician-confirmed direction, or enter context manually. Matching directions use body-region words, not a diagnosis. The existing deterministic planner proposes exercises. The current prescription remains intact until the clinician applies the visible proposal.
- Switching entry points retains the same prescription. Constraint assistance preserves compatible exercise choices and doses. An incompatible exercise with no library variant remains flagged for clinician replacement; the plan cannot be saved or activated with that unresolved warning.
- Own templates contain only exercise and variant identifiers plus numeric doses. Library instructions are reconstructed on reuse. A different patient's identity, goals, advice, side, prescribed load/range and progression never enter the reusable payload. Previous plans are available only for the selected patient. Reuse is reviewed before replacing the current plan.
- Favorites and templates persist per clinician and clinic through MFA-protected RPCs. Raw private tables have no client access. Template writes use version checks, retries preserve identity, and archiving a template never changes patient plans.
- “Rehabplanen ingår i besöket” is explicitly selected for applicable package patients; it defaults off. Both entry points save through the existing draft version path. Reopening resumes the newest draft or active version. There is no hidden autosave creating extra versions.

Patient activation/invitations, sales and automatic progression retain their existing rollout gates. This change introduces no external model calls, diagnoses or patient messages. New authoring tables do not modify existing patients or prescriptions.

Verification: existing unit/regression suite plus authoring model, isolated PostgreSQL permissions/retry tests, and fictional browser flows covering manual creation, EI review, reuse, side/dose/day persistence, constraints, undo, motion preview and responsive layout.
