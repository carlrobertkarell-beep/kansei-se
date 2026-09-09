create index if not exists reda_patients_clinician_idx on public.reda_patients(clinician_id);
create index if not exists reda_plans_clinician_idx on public.reda_plans(clinician_id);
create index if not exists reda_plans_patient_created_idx on public.reda_plans(patient_id,created_at desc);
create index if not exists reda_sessions_patient_idx on public.reda_sessions(patient_id);
create index if not exists reda_sessions_plan_idx on public.reda_sessions(plan_id);
create index if not exists reda_sessions_patient_started_idx on public.reda_sessions(patient_id,started_at desc);
create index if not exists reda_audit_actor_idx on public.reda_audit_events(actor_id);
create index if not exists reda_audit_patient_idx on public.reda_audit_events(patient_id);
