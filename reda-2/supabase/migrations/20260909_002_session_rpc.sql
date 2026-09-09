-- Patient session writes go through one idempotent RPC so identity fields cannot be rewritten from the browser.
revoke update on public.reda_sessions from authenticated;
drop policy if exists "patient session update" on public.reda_sessions;

create or replace function public.reda_save_session(
  p_client_session_id uuid,
  p_plan_id uuid,
  p_status text,
  p_started_at timestamptz,
  p_completed_at timestamptz,
  p_payload jsonb
) returns uuid
language plpgsql security definer set search_path='' as $$
declare v_patient public.reda_patients%rowtype; v_plan public.reda_plans%rowtype; v_id uuid;
begin
  if p_status not in ('started','partial','completed','planned_rest') then raise exception 'Invalid session status'; end if;
  select * into v_patient from public.reda_patients where auth_user_id=auth.uid() and status='active';
  if v_patient.id is null then raise exception 'Patient account not linked'; end if;
  select * into v_plan from public.reda_plans where id=p_plan_id and patient_id=v_patient.id and status='active';
  if v_plan.id is null then raise exception 'Active plan not available'; end if;
  insert into public.reda_sessions(client_session_id,patient_id,plan_id,plan_version,status,started_at,completed_at,payload)
  values(p_client_session_id,v_patient.id,v_plan.id,v_plan.version,p_status,p_started_at,p_completed_at,coalesce(p_payload,'{}'::jsonb))
  on conflict(client_session_id) do update set
    status=excluded.status,
    completed_at=excluded.completed_at,
    payload=excluded.payload,
    updated_at=now()
  where public.reda_sessions.patient_id=v_patient.id and public.reda_sessions.plan_id=v_plan.id
  returning id into v_id;
  return v_id;
end $$;
revoke all on function public.reda_save_session(uuid,uuid,text,timestamptz,timestamptz,jsonb) from public;
grant execute on function public.reda_save_session(uuid,uuid,text,timestamptz,timestamptz,jsonb) to authenticated;
