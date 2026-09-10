-- Exercise Intelligence: append-only responses after a completed/closed training session.
-- Source for the managed Supabase migration. No patient records or credentials in this file.
create table public.reda_training_responses (
 id uuid primary key default gen_random_uuid(),
 request_id uuid not null unique,
 session_id uuid not null unique references public.reda_sessions(id),
 patient_id uuid not null references public.reda_patients(id) on delete cascade,
 plan_id uuid not null references public.reda_plans(id),
 plan_version integer not null,
 reported_by uuid not null references auth.users(id),
 created_at timestamptz not null default now(),
 answers jsonb not null,
 constraint reda_response_shape check (
  jsonb_typeof(answers)='object'
  and answers ?& array['nextDay','function','recovery','otherTraining','quality','contact']
  and answers - array['nextDay','function','recovery','otherTraining','quality','contact'] = '{}'::jsonb
  and jsonb_typeof(answers->'nextDay')='string' and answers->>'nextDay' in ('settled','worse','unknown')
  and jsonb_typeof(answers->'function')='string' and answers->>'function' in ('stable','better','worse','unknown')
  and jsonb_typeof(answers->'recovery')='string' and answers->>'recovery' in ('ready','low','unknown')
  and jsonb_typeof(answers->'otherTraining')='string' and answers->>'otherTraining' in ('usual','high','unknown')
  and jsonb_typeof(answers->'quality')='string' and answers->>'quality' in ('controlled','difficult','unknown')
  and jsonb_typeof(answers->'contact')='string' and answers->>'contact' in ('no','yes')
 )
);
create index reda_responses_patient_created on public.reda_training_responses(patient_id,created_at desc);
create index reda_responses_plan on public.reda_training_responses(plan_id);
create index reda_responses_reporter on public.reda_training_responses(reported_by);
alter table public.reda_training_responses enable row level security;
revoke all on public.reda_training_responses from public,anon,authenticated;
grant select on public.reda_training_responses to authenticated;

create policy "patient reads own responses" on public.reda_training_responses for select to authenticated using (
 reported_by=(select auth.uid()) and exists(select 1 from public.reda_patients p where p.id=patient_id and p.auth_user_id=(select auth.uid()) and p.status='active')
);
create policy "own clinician reads responses at aal2" on public.reda_training_responses for select to authenticated using (
 (select private.reda_is_clinician_aal2()) and private.reda_owns_patient(patient_id)
);

-- The narrowly scoped writer derives identity, plan version and time on the server.
-- Browser roles have no table INSERT/UPDATE/DELETE privilege.
create function private.reda_submit_training_response(p_session_id uuid,p_request_id uuid,p_answers jsonb)
returns jsonb language plpgsql security definer set search_path='' as $$
declare
 actor uuid:=auth.uid();
 s public.reda_sessions%rowtype;
 existing public.reda_training_responses%rowtype;
 saved public.reda_training_responses%rowtype;
begin
 if actor is null or not exists(
  select 1 from auth.sessions a join auth.users u on u.id=a.user_id
  where a.id::text=auth.jwt()->>'session_id' and a.user_id=actor and u.deleted_at is null and (u.banned_until is null or u.banned_until<=now())
 ) then raise exception using errcode='42501',message='Logga in igen för att lämna återkoppling.'; end if;
 if p_request_id is null or p_session_id is null or p_answers is null then raise exception using errcode='22023',message='Återkopplingen är ofullständig.'; end if;
 select rs.* into s from public.reda_sessions rs
 join public.reda_patients p on p.id=rs.patient_id
 join public.reda_plans rp on rp.id=rs.plan_id and rp.patient_id=rs.patient_id and rp.version=rs.plan_version
 where rs.id=p_session_id and p.auth_user_id=actor and p.status='active'
 for update of rs;
 if s.id is null then raise exception using errcode='42501',message='Passet är inte tillgängligt.'; end if;
 -- Resolve retries before the submission window so a successful old request remains idempotent.
 select * into existing from public.reda_training_responses where request_id=p_request_id;
 if existing.id is not null then
  if existing.reported_by=actor and existing.session_id=s.id and existing.answers=p_answers then return to_jsonb(existing); end if;
  raise exception using errcode='23505',message='Den här begäran hör till ett annat svar.';
 end if;
 select * into existing from public.reda_training_responses where session_id=s.id;
 if existing.id is not null then
  if existing.reported_by=actor and existing.answers=p_answers then return to_jsonb(existing); end if;
  raise exception using errcode='23505',message='Ett annat svar är redan sparat för passet. Uppdatera sidan för att läsa det.';
 end if;
 if s.status not in ('completed','partial') or s.completed_at is null
  or (s.completed_at at time zone 'Europe/Stockholm')::date >= (now() at time zone 'Europe/Stockholm')::date
  or (now() at time zone 'Europe/Stockholm')::date-(s.completed_at at time zone 'Europe/Stockholm')::date>14
 then raise exception using errcode='22023',message='Återkopplingen gäller ett avslutat pass från de senaste 14 dagarna, tidigast dagen efter.'; end if;
 insert into public.reda_training_responses(request_id,session_id,patient_id,plan_id,plan_version,reported_by,answers)
 values(p_request_id,s.id,s.patient_id,s.plan_id,s.plan_version,actor,p_answers) returning * into saved;
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata)
 values(actor,s.patient_id,'training_response_submitted',jsonb_build_object('response_id',saved.id,'session_id',s.id,'plan_id',s.plan_id,'plan_version',s.plan_version));
 return to_jsonb(saved);
end $$;
revoke all on function private.reda_submit_training_response(uuid,uuid,jsonb) from public,anon,authenticated;
grant usage on schema private to authenticated;
grant execute on function private.reda_submit_training_response(uuid,uuid,jsonb) to authenticated;

-- Public RPC wrapper runs as the caller. The privileged implementation stays in private.
create function public.reda_submit_training_response(p_session_id uuid,p_request_id uuid,p_answers jsonb)
returns jsonb language sql security invoker set search_path='' as $$
 select private.reda_submit_training_response(p_session_id,p_request_id,p_answers);
$$;
revoke all on function public.reda_submit_training_response(uuid,uuid,jsonb) from public,anon,authenticated;
grant execute on function public.reda_submit_training_response(uuid,uuid,jsonb) to authenticated;
