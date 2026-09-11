-- Server-owned Exercise Intelligence. Additive tables; automation and AI stay OFF.
-- Managed migration source, tested in an empty PostgreSQL database before deployment.
create table private.reda_engine_settings(
 singleton boolean primary key default true check(singleton),
 automatic_enabled boolean not null default false,
 ai_enabled boolean not null default false
);
insert into private.reda_engine_settings(singleton) values(true);
alter table private.reda_engine_settings enable row level security;
revoke all on private.reda_engine_settings from public,anon,authenticated;

create function private.reda_live_actor() returns uuid
language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=auth.uid();begin
 if actor is null or not exists(select 1 from auth.sessions s join auth.users u on u.id=s.user_id where s.id::text=auth.jwt()->>'session_id' and s.user_id=actor and u.deleted_at is null and (u.banned_until is null or u.banned_until<=now())) then
  raise exception using errcode='42501',message='Logga in igen.';
 end if;return actor;
end$$;
revoke all on function private.reda_live_actor() from public,anon,authenticated;

create function private.reda_plan_binding(p jsonb) returns jsonb
language sql immutable set search_path='' as $$
 select jsonb_build_object('schema',p->'schema','context',p->'context','goal',p->'goal','schedule',p->'schedule','exercises',p->'exercises');
$$;
create function private.reda_validate_frame(p jsonb) returns boolean
language plpgsql immutable set search_path='' as $$
declare st jsonb; x jsonb; k text; n numeric; baseline jsonb; previous jsonb;begin
 if p->>'schema' is distinct from '1' or p->>'mode' is distinct from 'simulation-only' or coalesce(length(p->>'id'),0)=0 or jsonb_typeof(p->'revision') is distinct from 'number' or (p->>'revision')::numeric<>trunc((p->>'revision')::numeric) or (p->>'revision')::int<1 or length(p::text)>300000 then return false;end if;
 if coalesce(p->>'validFrom','')!~'^20[0-9]{2}-[0-9]{2}-[0-9]{2}$' or coalesce(p->>'validUntil','')!~'^20[0-9]{2}-[0-9]{2}-[0-9]{2}$' or (p->>'validFrom')::date>(p->>'validUntil')::date then return false;end if;
 foreach k in array array['minSuccessfulDays','minDaysAtStep','maxEvidenceAgeDays'] loop
  n=(p->'rules'->>k)::numeric;if n is null or n<>trunc(n) or n<1 or n>(case when k='minSuccessfulDays' then 30 else 60 end) then return false;end if;
 end loop;
 if (p->'rules'->>'minSuccessfulDays')::int>(p->'rules'->>'maxEvidenceAgeDays')::int or jsonb_typeof(p->'rules'->'acceptedEffort') is distinct from 'array' or jsonb_array_length(p->'rules'->'acceptedEffort') not between 1 and 2 or exists(select 1 from jsonb_array_elements_text(p->'rules'->'acceptedEffort') e where e not in ('easy','okay')) then return false;end if;
 if jsonb_typeof(p->'steps') is distinct from 'array' or jsonb_array_length(p->'steps') not between 2 and 12 then return false;end if;
 if (select count(distinct e->>'id') from jsonb_array_elements(p->'steps') e)<>jsonb_array_length(p->'steps') then return false;end if;
 for st in select value from jsonb_array_elements(p->'steps') loop
  if coalesce(length(st->>'id'),0)=0 or coalesce(length(st->>'label'),0)=0 or st->'plan'->>'schema' is distinct from '6' or jsonb_typeof(st->'plan'->'exercises') is distinct from 'array' or jsonb_array_length(st->'plan'->'exercises') not between 1 and 12 then return false;end if;
  if baseline is null then baseline=st->'plan';end if;
  if (st->'plan'->'context') is distinct from baseline->'context' or (st->'plan'->'goal') is distinct from baseline->'goal' or (st->'plan'->'schedule') is distinct from baseline->'schedule' then return false;end if;
  if (select count(distinct e->>'id') from jsonb_array_elements(st->'plan'->'exercises') e)<>jsonb_array_length(st->'plan'->'exercises') then return false;end if;
  for x in select value from jsonb_array_elements(st->'plan'->'exercises') loop
   if coalesce(length(x->>'id'),0)=0 or coalesce(length(x->>'variantId'),0)=0 or x->>'side' not in ('left','right','both','simultaneous') or x->>'side' is null then return false;end if;
   foreach k in array array['sets','reps','hold','rest','tempo'] loop
    if jsonb_typeof(x->'dose'->k) is distinct from 'number' then return false;end if;n=(x->'dose'->>k)::numeric;
    if n<>trunc(n) or n<(case when k in ('hold','rest') then 0 else 1 end) or n>(case k when 'sets' then 8 when 'reps' then 100 when 'hold' then 180 when 'rest' then 600 else 60 end) then return false;end if;
   end loop;
  end loop;
  if previous is not null and (select jsonb_agg(jsonb_build_object('id',e->'id','variantId',e->'variantId','side',e->'side','dose',(e->'dose')-'label','load',e->'prescribedLoad')) from jsonb_array_elements(previous->'exercises') e)=(select jsonb_agg(jsonb_build_object('id',e->'id','variantId',e->'variantId','side',e->'side','dose',(e->'dose')-'label','load',e->'prescribedLoad')) from jsonb_array_elements(st->'plan'->'exercises') e) then return false;end if;
  previous=st->'plan';
 end loop;return true;
exception when others then return false;end$$;
revoke all on function private.reda_plan_binding(jsonb),private.reda_validate_frame(jsonb) from public,anon,authenticated;

create table public.reda_progression_frames(
 id uuid primary key default gen_random_uuid(),patient_id uuid not null references public.reda_patients(id),clinician_id uuid not null references auth.users(id),
 source_plan_id uuid not null references public.reda_plans(id),current_plan_id uuid not null references public.reda_plans(id),
 policy jsonb not null check(private.reda_validate_frame(policy)),execution text not null check(execution in ('shadow','automatic')),
 status text not null default 'approved' check(status in ('approved','revoked','completed')),
 current_step integer not null default 0 check(current_step between 0 and 11),started_at timestamptz not null default now(),
 approved_by uuid not null references auth.users(id),approved_at timestamptz not null default now(),revoked_at timestamptz
);
create unique index reda_one_approved_frame on public.reda_progression_frames(patient_id) where status='approved';
create index reda_frames_clinician on public.reda_progression_frames(clinician_id);
create index reda_frames_source on public.reda_progression_frames(source_plan_id);
create index reda_frames_current on public.reda_progression_frames(current_plan_id);
create index reda_frames_approver on public.reda_progression_frames(approved_by);
create table public.reda_engine_decisions(
 id uuid primary key default gen_random_uuid(),request_id uuid not null unique,patient_id uuid not null references public.reda_patients(id),
 frame_id uuid not null references public.reda_progression_frames(id),plan_id uuid not null references public.reda_plans(id),step integer not null,
 actor_id uuid not null references auth.users(id),action text not null check(action in ('wait','hold','review','advance','complete','blocked')),
 code text not null,metrics jsonb not null default '{}',evidence_ids uuid[] not null default '{}',
 applied boolean not null default false,result_plan_id uuid references public.reda_plans(id),created_at timestamptz not null default now()
);
create index reda_decisions_patient_created on public.reda_engine_decisions(patient_id,created_at desc);
create index reda_decisions_frame on public.reda_engine_decisions(frame_id);
create index reda_decisions_plan on public.reda_engine_decisions(plan_id);
create index reda_decisions_result on public.reda_engine_decisions(result_plan_id);
create index reda_decisions_actor on public.reda_engine_decisions(actor_id);
create table public.reda_review_cases(
 id uuid primary key default gen_random_uuid(),patient_id uuid not null references public.reda_patients(id),plan_id uuid not null references public.reda_plans(id),
 response_id uuid not null references public.reda_training_responses(id),code text not null,
 status text not null default 'open' check(status in ('open','acknowledged','resolved')),
 handled_by uuid references auth.users(id),handling_note text not null default '',created_at timestamptz not null default now(),updated_at timestamptz not null default now(),
 unique(response_id,code)
);
create index reda_cases_patient_status on public.reda_review_cases(patient_id,status);
create index reda_cases_plan on public.reda_review_cases(plan_id);
create index reda_cases_handler on public.reda_review_cases(handled_by);
alter table public.reda_progression_frames enable row level security;
alter table public.reda_engine_decisions enable row level security;
alter table public.reda_review_cases enable row level security;
revoke all on public.reda_progression_frames,public.reda_engine_decisions,public.reda_review_cases from public,anon,authenticated;
grant select on public.reda_progression_frames,public.reda_engine_decisions,public.reda_review_cases to authenticated;
create policy "clinician frame read" on public.reda_progression_frames for select to authenticated using((select private.reda_is_clinician_aal2()) and private.reda_owns_patient(patient_id));
create policy "own decision read" on public.reda_engine_decisions for select to authenticated using(((select private.reda_is_clinician_aal2()) and private.reda_owns_patient(patient_id)) or exists(select 1 from public.reda_patients p where p.id=patient_id and p.auth_user_id=(select auth.uid()) and p.status='active'));
create policy "clinician case read" on public.reda_review_cases for select to authenticated using((select private.reda_is_clinician_aal2()) and private.reda_owns_patient(patient_id));

-- Preserve six-field historical replies; new replies may explicitly report changed circumstances.
alter table public.reda_training_responses drop constraint reda_response_shape;
alter table public.reda_training_responses add constraint reda_response_shape check(
 jsonb_typeof(answers)='object' and answers ?& array['nextDay','function','recovery','otherTraining','quality','contact']
 and answers-array['nextDay','function','recovery','otherTraining','quality','contact','environment']='{}'::jsonb
 and answers->>'nextDay' in ('settled','worse','unknown') and jsonb_typeof(answers->'nextDay')='string'
 and answers->>'function' in ('stable','better','worse','unknown') and jsonb_typeof(answers->'function')='string'
 and answers->>'recovery' in ('ready','low','unknown') and jsonb_typeof(answers->'recovery')='string'
 and answers->>'otherTraining' in ('usual','high','unknown') and jsonb_typeof(answers->'otherTraining')='string'
 and answers->>'quality' in ('controlled','difficult','unknown') and jsonb_typeof(answers->'quality')='string'
 and answers->>'contact' in ('no','yes') and jsonb_typeof(answers->'contact')='string'
 and (not answers?'environment' or (answers->>'environment' in ('same','changed','unknown') and jsonb_typeof(answers->'environment')='string'))
);
create function private.reda_capture_response_case() returns trigger language plpgsql security definer set search_path='' as $$
declare reason text;begin
 reason=case when new.answers->>'nextDay'='worse' or new.answers->>'function'='worse' then 'changed_symptoms' when new.answers->>'environment'='changed' then 'changed_environment' when new.answers->>'contact'='yes' then 'requested_contact' when new.answers->>'quality'='difficult' then 'execution_help' else null end;
 if reason is not null then insert into public.reda_review_cases(patient_id,plan_id,response_id,code) values(new.patient_id,new.plan_id,new.id,reason) on conflict do nothing;end if;return new;
end$$;
revoke all on function private.reda_capture_response_case() from public,anon,authenticated;
create trigger reda_response_review after insert on public.reda_training_responses for each row execute function private.reda_capture_response_case();

create function private.reda_approve_frame(p_plan_id uuid,p_policy jsonb,p_execution text default 'shadow') returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor(); p public.reda_plans%rowtype; f public.reda_progression_frames%rowtype;pid uuid;begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='Behandlarinloggning med MFA krävs.';end if;
 select patient_id into pid from public.reda_plans where id=p_plan_id and clinician_id=actor;
 perform 1 from public.reda_patients where id=pid and clinician_id=actor and status='active' for update;
 if not found then raise exception using errcode='42501',message='Planen är inte tillgänglig.';end if;
 select * into p from public.reda_plans where id=p_plan_id and status='active' for update;
 if p.id is null or not private.reda_validate_frame(p_policy) or private.reda_plan_binding(p.payload) is distinct from private.reda_plan_binding(p_policy->'steps'->0->'plan') then raise exception using errcode='22023',message='Ramen måste utgå från den aktuella publicerade ordinationen.';end if;
 if p_execution not in ('shadow','automatic') or p_execution is null then raise exception using errcode='22023',message='Ogiltigt körläge.';end if;
 if p_execution='automatic' and not (select automatic_enabled from private.reda_engine_settings) then raise exception using errcode='42501',message='Automatisk tillämpning är inte öppnad.';end if;
 if (p_policy->>'validUntil')::date<(now() at time zone 'Europe/Stockholm')::date then raise exception using errcode='22023',message='Ramens slutdatum har passerat.';end if;
 update public.reda_progression_frames set status='revoked',revoked_at=now() where patient_id=pid and status='approved';
 insert into public.reda_progression_frames(patient_id,clinician_id,source_plan_id,current_plan_id,policy,execution,approved_by) values(pid,actor,p.id,p.id,p_policy,p_execution,actor) returning * into f;
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata) values(actor,pid,'progression_frame_approved',jsonb_build_object('frame_id',f.id,'plan_id',p.id,'execution',p_execution));
 return to_jsonb(f);
end$$;
create function private.reda_revoke_frame(p_frame_id uuid) returns void language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor(); pid uuid;begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='MFA krävs.';end if;
 select patient_id into pid from public.reda_progression_frames where id=p_frame_id and clinician_id=actor;
 perform 1 from public.reda_patients where id=pid and clinician_id=actor for update;if not found then raise exception using errcode='42501',message='Ramen är inte tillgänglig.';end if;
 update public.reda_progression_frames set status='revoked',revoked_at=now() where id=p_frame_id and status='approved';
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata) values(actor,pid,'progression_frame_revoked',jsonb_build_object('frame_id',p_frame_id));
end$$;
create function private.reda_handle_case(p_case_id uuid,p_status text,p_note text) returns jsonb language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();c public.reda_review_cases%rowtype;begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='MFA krävs.';end if;
 select * into c from public.reda_review_cases where id=p_case_id;
 perform 1 from public.reda_patients where id=c.patient_id and clinician_id=actor for update;
 if not found then raise exception using errcode='42501',message='Ärendet är inte tillgängligt.';end if;
 if p_status not in ('acknowledged','resolved') or p_status is null or length(coalesce(p_note,''))>1000 or (p_status='resolved' and length(trim(coalesce(p_note,'')))<5) then raise exception using errcode='22023',message='Ange status och vad som bedömts eller gjorts.';end if;
 update public.reda_review_cases set status=p_status,handled_by=actor,handling_note=coalesce(p_note,''),updated_at=now() where id=p_case_id returning * into c;
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata) values(actor,c.patient_id,'review_case_handled',jsonb_build_object('case_id',c.id,'status',p_status));return to_jsonb(c);
end$$;

create function private.reda_evaluate_progression(p_patient_id uuid,p_request_id uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();patient public.reda_patients%rowtype;f public.reda_progression_frames%rowtype;p public.reda_plans%rowtype;d public.reda_engine_decisions%rowtype;
 a text:='wait';code text:='evidence';today date:=(now() at time zone 'Europe/Stockholm')::date;r record;ex jsonb;mark jsonb;latest jsonb;days date[]:='{}';ids uuid[]:='{}';next_id uuid;next_version int;min_days int;can_apply boolean:=false;cutoff timestamptz;
begin
 select * into patient from public.reda_patients where id=p_patient_id and status='active' and (auth_user_id=actor or (clinician_id=actor and private.reda_is_clinician_aal2())) for update;
 if patient.id is null or p_request_id is null then raise exception using errcode='42501',message='Patienten är inte tillgänglig.';end if;
 select * into d from public.reda_engine_decisions where request_id=p_request_id;
 if d.id is not null then if d.patient_id<>patient.id or d.actor_id<>actor then raise exception using errcode='42501',message='Begäran är inte tillgänglig.';end if;return to_jsonb(d);end if;
 select * into f from public.reda_progression_frames where patient_id=patient.id and status='approved' for update;
 if f.id is null then return jsonb_build_object('action','none','code','no_frame','applied',false);end if;
 select * into p from public.reda_plans where id=f.current_plan_id for update;
 min_days=(f.policy->'rules'->>'minSuccessfulDays')::int;
 cutoff=greatest(f.started_at,((today-(f.policy->'rules'->>'maxEvidenceAgeDays')::int)::timestamp at time zone 'Europe/Stockholm'));
 <<decision>> begin
  if patient.clinician_id<>f.clinician_id or not exists(select 1 from public.reda_profiles pr join auth.users u on u.id=pr.user_id where pr.user_id=f.clinician_id and pr.role='clinician' and u.deleted_at is null and (u.banned_until is null or u.banned_until<=now())) then a='blocked';code='clinician_authority';exit decision;end if;
  if p.status<>'active' or private.reda_plan_binding(p.payload) is distinct from private.reda_plan_binding(f.policy->'steps'->f.current_step->'plan') then a='blocked';code='version';exit decision;end if;
  if exists(select 1 from public.reda_review_cases where patient_id=patient.id and status<>'resolved') then a='review';code='pending_review';exit decision;end if;
  if today>(f.policy->>'validUntil')::date then a='review';code='expired';exit decision;end if;
  if today<(f.policy->>'validFrom')::date then code='not_started';exit decision;end if;
  if exists(select 1 from public.reda_sessions where patient_id=patient.id and completed_at is null and status in ('started','partial')) then code='open_session';exit decision;end if;
  select tr.answers into latest from public.reda_training_responses tr join public.reda_sessions s on s.id=tr.session_id where tr.plan_id=p.id and s.created_at>=f.started_at and tr.created_at>=cutoff order by tr.created_at desc limit 1;
  if latest is null or latest->>'environment' is distinct from 'same' or latest->>'recovery' is null or latest->>'otherTraining' is null then code='context';exit decision;end if;
  if latest->>'recovery'='low' or latest->>'otherTraining'='high' then a='hold';code='load';exit decision;end if;
  if latest->>'recovery'<>'ready' or latest->>'otherTraining'<>'usual' then code='context';exit decision;end if;
  for r in select s.*,tr.id response_id,tr.answers,tr.created_at responded_at from public.reda_sessions s left join public.reda_training_responses tr on tr.session_id=s.id where s.patient_id=patient.id and s.plan_id=p.id and s.created_at>=f.started_at and s.completed_at>=cutoff and s.status<>'planned_rest' order by s.completed_at loop
   if r.response_id is not null and exists(select 1 from public.reda_review_cases c where c.response_id=r.response_id and c.status='resolved') then continue;end if;
   if r.status<>'completed' then a='hold';code='partial';exit decision;end if;
   if r.response_id is null or (r.responded_at at time zone 'Europe/Stockholm')::date<=(r.completed_at at time zone 'Europe/Stockholm')::date then code='response';exit decision;end if;
   if r.answers->>'nextDay'<>'settled' or r.answers->>'quality'<>'controlled' or r.answers->>'function' not in ('stable','better') or r.answers->>'environment' is distinct from 'same' then code='response';exit decision;end if;
   if jsonb_typeof(r.payload->'exercises') is distinct from 'array' or jsonb_array_length(r.payload->'exercises')<>jsonb_array_length(p.payload->'exercises') then a='blocked';code='invalid_session';exit decision;end if;
   for ex in select value from jsonb_array_elements(p.payload->'exercises') loop
    select value into mark from jsonb_array_elements(r.payload->'exercises') where value->>'exerciseId'=ex->>'id';
    if mark is null or (select count(*) from jsonb_array_elements(r.payload->'exercises') where value->>'exerciseId'=ex->>'id')<>1 or mark->>'status' is distinct from 'completed' or jsonb_typeof(mark->'roundsDone') is distinct from 'number' or (mark->>'roundsDone')::numeric<>((ex->'dose'->>'sets')::int*case when ex->>'side'='both' then 2 else 1 end) then a='blocked';code='invalid_session';exit decision;end if;
    if not (f.policy->'rules'->'acceptedEffort') ? (case when mark->>'feedback'='light' then 'easy' else coalesce(mark->>'feedback','') end) then a='hold';code='effort';exit decision;end if;
   end loop;
   days=array_append(days,(r.completed_at at time zone 'Europe/Stockholm')::date);ids=array_append(ids,r.response_id);
  end loop;
  if (select count(distinct unnest) from unnest(days))<min_days then code='evidence';exit decision;end if;
  if today-(f.started_at at time zone 'Europe/Stockholm')::date<(f.policy->'rules'->>'minDaysAtStep')::int then code='time';exit decision;end if;
  if f.current_step+1>=jsonb_array_length(f.policy->'steps') then a='complete';code='complete';exit decision;end if;
  a='advance';code='ready';
 end decision;
 can_apply=f.execution='automatic' and (select automatic_enabled from private.reda_engine_settings);
 if a='advance' and can_apply then
  select coalesce(max(version),0)+1 into next_version from public.reda_plans where patient_id=patient.id;
  update public.reda_plans set status='superseded',superseded_at=now() where id=p.id;
  insert into public.reda_plans(patient_id,clinician_id,version,status,payload,activated_at) values(patient.id,f.clinician_id,next_version,'active',(f.policy->'steps'->(f.current_step+1)->'plan')-'progressionDraft',now()) returning id into next_id;
  update public.reda_progression_frames set current_step=current_step+1,current_plan_id=next_id,started_at=now() where id=f.id;
 elsif a='complete' and can_apply then update public.reda_progression_frames set status='completed' where id=f.id;
 end if;
 insert into public.reda_engine_decisions(request_id,patient_id,frame_id,plan_id,step,actor_id,action,code,metrics,evidence_ids,applied,result_plan_id) values(p_request_id,patient.id,f.id,p.id,f.current_step,actor,a,code,jsonb_build_object('successfulDays',(select count(distinct unnest) from unnest(days)),'requiredDays',min_days,'daysAtStep',today-(f.started_at at time zone 'Europe/Stockholm')::date),ids,can_apply and a in ('advance','complete'),next_id) returning * into d;
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata) values(actor,patient.id,'progression_evaluated',jsonb_build_object('decision_id',d.id,'frame_id',f.id,'code',code,'applied',d.applied));return to_jsonb(d);
end$$;

-- Public invoker wrappers: all privilege stays in private, with ownership checked there.
create function public.reda_approve_frame(p_plan_id uuid,p_policy jsonb,p_execution text default 'shadow') returns jsonb language sql security invoker set search_path='' as $$select private.reda_approve_frame(p_plan_id,p_policy,p_execution)$$;
create function public.reda_revoke_frame(p_frame_id uuid) returns void language sql security invoker set search_path='' as $$select private.reda_revoke_frame(p_frame_id)$$;
create function public.reda_handle_case(p_case_id uuid,p_status text,p_note text) returns jsonb language sql security invoker set search_path='' as $$select private.reda_handle_case(p_case_id,p_status,p_note)$$;
create function public.reda_evaluate_progression(p_patient_id uuid,p_request_id uuid) returns jsonb language sql security invoker set search_path='' as $$select private.reda_evaluate_progression(p_patient_id,p_request_id)$$;
do $$declare r record;begin for r in select p.oid::regprocedure sig from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname in ('public','private') and p.proname in ('reda_approve_frame','reda_revoke_frame','reda_handle_case','reda_evaluate_progression') loop execute format('revoke all on function %s from public,anon,authenticated',r.sig);execute format('grant execute on function %s to authenticated',r.sig);end loop;end$$;

-- Serialize every plan activation with engine evaluation and stop an obsolete frame.
create or replace function public.reda_activate_plan_internal(p_plan_id uuid,p_actor_id uuid) returns void language plpgsql security invoker set search_path='' as $$
declare p public.reda_plans%rowtype;pid uuid;begin
 select patient_id into pid from public.reda_plans where id=p_plan_id and clinician_id=p_actor_id;
 perform 1 from public.reda_patients where id=pid and clinician_id=p_actor_id and status='active' for update;if not found then raise exception 'Plan not available';end if;
 select * into p from public.reda_plans where id=p_plan_id and status='draft' for update;if p.id is null then raise exception 'Draft required';end if;
 update public.reda_progression_frames set status='revoked',revoked_at=now() where patient_id=pid and status='approved';
 update public.reda_plans set status='superseded',superseded_at=now() where patient_id=pid and status='active';
 update public.reda_plans set status='active',activated_at=now() where id=p.id;
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata) values(p_actor_id,pid,'plan_activated',jsonb_build_object('plan_id',p.id,'version',p.version));
end$$;
revoke all on function public.reda_activate_plan_internal(uuid,uuid) from public,anon,authenticated;
grant execute on function public.reda_activate_plan_internal(uuid,uuid) to service_role;

-- A server clock and immutable closed sessions make evidence resistant to backdating.
-- Unfinished sessions retain their original plan and can still be closed after a manual update.
create or replace function private.reda_save_session_internal(p_user_id uuid,p_client_session_id uuid,p_plan_id uuid,p_status text,p_started_at timestamptz,p_completed_at timestamptz,p_payload jsonb) returns uuid language plpgsql security invoker set search_path='' as $$
declare patient public.reda_patients%rowtype;p public.reda_plans%rowtype;s public.reda_sessions%rowtype;new_id uuid;begin
 if p_status not in ('started','partial','completed','planned_rest') or (p_status='completed' and p_completed_at is null) then raise exception 'Invalid session status';end if;
 select * into patient from public.reda_patients where auth_user_id=p_user_id and status='active' for update;if patient.id is null then raise exception 'Patient unavailable';end if;
 select * into s from public.reda_sessions where client_session_id=p_client_session_id for update;
 if s.id is not null then
  if s.patient_id<>patient.id or s.plan_id<>p_plan_id then raise exception 'Session mismatch';end if;
  if s.completed_at is not null then if s.status=p_status and (s.payload-'clientUpdatedAt')=(coalesce(p_payload,'{}'::jsonb)-'clientUpdatedAt') and p_completed_at is not null then return s.id;end if;raise exception 'Closed session is immutable';end if;
  update public.reda_sessions set status=p_status,completed_at=case when p_completed_at is not null then now() else null end,payload=coalesce(p_payload,'{}'::jsonb),updated_at=now() where id=s.id;return s.id;
 end if;
 select * into p from public.reda_plans where id=p_plan_id and patient_id=patient.id and status='active';if p.id is null then raise exception 'Active plan required';end if;
 insert into public.reda_sessions(client_session_id,patient_id,plan_id,plan_version,status,started_at,completed_at,payload) values(p_client_session_id,patient.id,p.id,p.version,p_status,now(),case when p_completed_at is not null then now() else null end,coalesce(p_payload,'{}'::jsonb)) returning id into new_id;return new_id;
end$$;
create or replace function public.reda_save_session_internal(p_user_id uuid,p_client_session_id uuid,p_plan_id uuid,p_status text,p_started_at timestamptz,p_completed_at timestamptz,p_payload jsonb) returns uuid language sql security invoker set search_path='' as $$select private.reda_save_session_internal(p_user_id,p_client_session_id,p_plan_id,p_status,p_started_at,p_completed_at,p_payload)$$;
revoke all on function public.reda_save_session_internal(uuid,uuid,uuid,text,timestamptz,timestamptz,jsonb),private.reda_save_session_internal(uuid,uuid,uuid,text,timestamptz,timestamptz,jsonb) from public,anon,authenticated;
grant execute on function public.reda_save_session_internal(uuid,uuid,uuid,text,timestamptz,timestamptz,jsonb),private.reda_save_session_internal(uuid,uuid,uuid,text,timestamptz,timestamptz,jsonb) to service_role;
revoke insert,update,delete on public.reda_sessions from authenticated;

create or replace function private.reda_submit_training_response(p_session_id uuid,p_request_id uuid,p_answers jsonb)
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
 -- Same patient-first lock order as session saving and engine evaluation.
 perform 1 from public.reda_patients p join public.reda_sessions rs on rs.patient_id=p.id where rs.id=p_session_id and p.auth_user_id=actor and p.status='active' for update of p;
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

grant usage on schema private to service_role;
grant select,update on public.reda_progression_frames to service_role;
grant execute on function private.reda_validate_frame(jsonb) to service_role;
