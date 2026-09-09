-- Browser-facing roles must not execute privileged write RPCs directly.
-- Edge Functions authenticate/authorize the user, then call these as service_role.

drop function if exists public.reda_activate_plan(uuid);
drop function if exists public.reda_save_session(uuid,uuid,text,timestamptz,timestamptz,jsonb);

revoke insert,update on public.reda_sessions from authenticated;
drop policy if exists "patient session create" on public.reda_sessions;
drop policy if exists "patient session update" on public.reda_sessions;

create function public.reda_activate_plan_internal(p_plan_id uuid,p_actor_id uuid)
returns void language plpgsql security invoker set search_path='' as $$
declare v_plan public.reda_plans%rowtype;
begin
  select * into v_plan from public.reda_plans where id=p_plan_id and clinician_id=p_actor_id for update;
  if v_plan.id is null then raise exception 'Plan not available'; end if;
  if v_plan.status<>'draft' then raise exception 'Only draft plans can be activated'; end if;
  update public.reda_plans set status='superseded',superseded_at=now() where patient_id=v_plan.patient_id and status='active';
  update public.reda_plans set status='active',activated_at=now() where id=p_plan_id;
  insert into public.reda_audit_events(actor_id,patient_id,action,metadata)
    values(p_actor_id,v_plan.patient_id,'plan_activated',jsonb_build_object('plan_id',p_plan_id,'version',v_plan.version));
end $$;
revoke execute on function public.reda_activate_plan_internal(uuid,uuid) from public,anon,authenticated;
grant execute on function public.reda_activate_plan_internal(uuid,uuid) to service_role;

create function public.reda_save_session_internal(p_user_id uuid,p_client_session_id uuid,p_plan_id uuid,p_status text,p_started_at timestamptz,p_completed_at timestamptz,p_payload jsonb)
returns uuid language plpgsql security invoker set search_path='' as $$
declare v_patient public.reda_patients%rowtype; v_plan public.reda_plans%rowtype; v_id uuid;
begin
  if p_status not in ('started','partial','completed','planned_rest') then raise exception 'Invalid session status'; end if;
  select * into v_patient from public.reda_patients where auth_user_id=p_user_id and status='active';
  if v_patient.id is null then raise exception 'Patient account not linked'; end if;
  select * into v_plan from public.reda_plans where id=p_plan_id and patient_id=v_patient.id and status='active';
  if v_plan.id is null then raise exception 'Active plan not available'; end if;
  insert into public.reda_sessions(client_session_id,patient_id,plan_id,plan_version,status,started_at,completed_at,payload)
  values(p_client_session_id,v_patient.id,v_plan.id,v_plan.version,p_status,p_started_at,p_completed_at,coalesce(p_payload,'{}'::jsonb))
  on conflict(client_session_id) do update set status=excluded.status,completed_at=excluded.completed_at,payload=excluded.payload,updated_at=now()
  where public.reda_sessions.patient_id=v_patient.id and public.reda_sessions.plan_id=v_plan.id
  returning id into v_id;
  return v_id;
end $$;
revoke execute on function public.reda_save_session_internal(uuid,uuid,uuid,text,timestamptz,timestamptz,jsonb) from public,anon,authenticated;
grant execute on function public.reda_save_session_internal(uuid,uuid,uuid,text,timestamptz,timestamptz,jsonb) to service_role;

-- Audit remains server-side only; an explicit false policy keeps browser access denied and visible to linters.
drop policy if exists "audit browser deny" on public.reda_audit_events;
create policy "audit browser deny" on public.reda_audit_events for select to authenticated using(false);

-- New public-schema functions are opt-in.
alter default privileges for role postgres in schema public revoke execute on functions from public;
alter default privileges for role postgres in schema public revoke execute on functions from anon,authenticated;
