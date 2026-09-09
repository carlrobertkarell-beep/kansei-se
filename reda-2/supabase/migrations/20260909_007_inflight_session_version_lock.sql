create or replace function private.reda_save_session_internal(
  p_user_id uuid,p_client_session_id uuid,p_plan_id uuid,p_status text,p_started_at timestamptz,p_completed_at timestamptz,p_payload jsonb
) returns uuid language plpgsql security invoker set search_path='' as $$
declare v_patient public.reda_patients%rowtype; v_plan public.reda_plans%rowtype; v_existing public.reda_sessions%rowtype; v_id uuid;
begin
  if p_status not in ('started','partial','completed','planned_rest') then raise exception 'Invalid session status'; end if;
  select * into v_patient from public.reda_patients where auth_user_id=p_user_id and status='active';
  if v_patient.id is null then raise exception 'Patient account not linked'; end if;
  select * into v_existing from public.reda_sessions where client_session_id=p_client_session_id and patient_id=v_patient.id for update;
  if v_existing.id is not null then
    if v_existing.plan_id<>p_plan_id then raise exception 'Session plan mismatch'; end if;
    update public.reda_sessions set status=p_status,completed_at=p_completed_at,payload=coalesce(p_payload,'{}'::jsonb),updated_at=now() where id=v_existing.id returning id into v_id;
    return v_id;
  end if;
  select * into v_plan from public.reda_plans where id=p_plan_id and patient_id=v_patient.id and status='active';
  if v_plan.id is null then raise exception 'Active plan not available'; end if;
  insert into public.reda_sessions(client_session_id,patient_id,plan_id,plan_version,status,started_at,completed_at,payload)
  values(p_client_session_id,v_patient.id,v_plan.id,v_plan.version,p_status,p_started_at,p_completed_at,coalesce(p_payload,'{}'::jsonb)) returning id into v_id;
  return v_id;
end $$;
revoke all on function private.reda_save_session_internal(uuid,uuid,uuid,text,timestamptz,timestamptz,jsonb) from public,anon,authenticated;
grant execute on function private.reda_save_session_internal(uuid,uuid,uuid,text,timestamptz,timestamptz,jsonb) to service_role;
