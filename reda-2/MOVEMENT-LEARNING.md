# Patient-paced exercise learning

The previous player combined a seven-second continuous loop with instructions. It also used visibly segmented limbs and an incorrect forward arm release in supported chair rises. Neither the passing geometry tests nor the previous release established acceptable teaching or illustration quality.

## Delivered

- Shared patient and fictional review guide: one saved instruction at a time, stationary illustration, optional local Swedish read-aloud, then a separate watch mode.
- No automatic transition from reading to movement. Each demonstrated part stops at its endpoint and waits. Chair rise separates forward lean (6 s), rise (10 s), and return (12 s). The next-part button explicitly starts the selected next part. These times are learning speeds, never a prescription.
- Pause/resume and speed changes retain the current point. Changing tab, closing the player, opening contextual help, saving a help response or hiding the page pauses playback. Reduced-motion mode offers stills and no playback.
- Read-aloud is user initiated and only offered for a Swedish voice marked `localService: true` by the browser. No remote voice fallback; the saved text remains available if speech fails. Speech stops before movement, navigation and exercise changes.
- Explicit “Jag är redo att träna” focuses existing prescribed rounds. Viewing, completing the visual guide and listening never mark a repetition, complete a clinical checklist, resolve a help case or change the plan.
- Continuous clothing silhouettes, a more detailed human profile, fingers and palm, visible front armrest and corrected supported-chair elbow/release trajectory replace the previous segmented presentation. This remains a two-dimensional illustration.

## Content and scaling

`movement-lesson-model.mjs` takes instruction strings from the session's actual exercise, preserving the wording. It includes saved support and range when available. It does not infer a patient-specific angle or assign arbitrary clinical text to a motion frame. Reading and reference movement are separate for that reason. Missing instructions lead to the existing help flow.

`lessonSegments` provides reusable temporal chapters. `createLessonPlayback` has no backend, dose or patient-completion callback. `createMovementLesson` is used in both `patient-live.mjs` and `exercise-guide.mjs`, with the real plan/session and fictional examples respectively. Existing source-bound exercise help remains unchanged.

## Required before accepting an exercise for clinical use

The current illustrations remain pending clinical review. Inspect support contacts, body proportions and continuous motion, required side, individual restrictions, camera angle and text alongside a clinician. A single side view cannot establish all execution requirements for a technical exercise. Such an exercise needs appropriate additional views or a reviewed human video/rigged motion asset before it is described as fully demonstrated. Do not treat the generic endpoint as the patient's prescribed range.

Usability must also be checked with representative older users, including ages 70–90+, on their own devices. Specifically observe reading/listening, finding pause and replay, comprehending a held endpoint, seeing hand support, and moving from learning to their prescribed rounds. Automated tests do not establish this.

## Verification

Model tests exercise stopping, explicit start, no looping, pause/resume, speed continuity, source wording, no mutation of the prescription, and local-only voice selection. Browser tests cover separate read/watch modes, endpoint waiting, no recorded rounds from learning, reduced motion, current side, mobile text/targets, and existing help receipts. Existing database and patient/clinician regression suites remain release gates.

Design references: [W3C cognitive accessibility guidance](https://www.w3.org/TR/coga-usable/) (separate instructions, break media into chunks, user control); [W3C pause and resume](https://www.w3.org/WAI/WCAG21/Techniques/general/G4.html); [MDN local speech services](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisVoice/localService).
