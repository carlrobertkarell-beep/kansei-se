-- Abort if production engine definitions changed since review. Never overwrite unseen logic.
set local lock_timeout='5s';
set local statement_timeout='30s';
do $$begin
 if (select md5(prosrc)from pg_proc where oid='private.reda_approve_frame(uuid,jsonb,text)'::regprocedure) is distinct from '4f83366174edbd4614440c6c2e585bbf'
 or (select md5(prosrc)from pg_proc where oid='private.reda_evaluate_progression(uuid,uuid)'::regprocedure) is distinct from 'd1c7a1d74ca34010814927f10633709f' then
 raise exception 'Engine changed since mandate review; rebase this migration.';end if;
 if exists(select 1 from private.reda_engine_settings where automatic_enabled or ai_enabled)then raise exception 'This installation requires closed rollout flags.';end if;
end$$;
-- Clinical authority is separate from administrative follow-up. Installation enables nothing.
-- Lock order: organization, patient/frame/plan, global engine settings.
create table private.reda_clinical_ei_mandates(
 organization_id uuid primary key references public.reda_organizations(id),
 enabled boolean not null default false,
 max_steps integer not null default 3 check(max_steps between 1 and 11),
 revision integer not null check(revision>0),
 updated_by uuid not null references auth.users(id), updated_at timestamptz not null default now());
create index reda_clinical_mandate_actor on private.reda_clinical_ei_mandates(updated_by);
create table private.reda_clinical_mandate_receipts(
 request_id uuid primary key,organization_id uuid not null references public.reda_organizations(id),
 actor_id uuid not null references auth.users(id),input jsonb not null,before_state jsonb not null,
 result jsonb not null,created_at timestamptz not null default now());
create index reda_clinical_receipt_org on private.reda_clinical_mandate_receipts(organization_id,created_at desc);
create index reda_clinical_receipt_actor on private.reda_clinical_mandate_receipts(actor_id);
alter table private.reda_clinical_ei_mandates enable row level security;
alter table private.reda_clinical_mandate_receipts enable row level security;
revoke all on private.reda_clinical_ei_mandates,private.reda_clinical_mandate_receipts from public,anon,authenticated;
create policy "rpc only" on private.reda_clinical_ei_mandates for all to authenticated using(false)with check(false);
create policy "rpc only" on private.reda_clinical_mandate_receipts for all to authenticated using(false)with check(false);
-- Old approvals deliberately remain unbound and fail closed. No patient plan is changed.
alter table public.reda_progression_frames add column mandate_organization_id uuid references public.reda_organizations(id),add column mandate_revision integer check(mandate_revision>0);
alter table public.reda_progression_frames add constraint reda_frame_mandate_pair check((mandate_organization_id is null)=(mandate_revision is null));
create index reda_frame_mandate_org on public.reda_progression_frames(mandate_organization_id);
create function private.reda_clinical_ei_settings() returns jsonb language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();org uuid:=private.reda_request_organization();m private.reda_clinical_ei_mandates%rowtype;
begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='Behandlarbehörighet och MFA krävs.';end if;
 select * into m from private.reda_clinical_ei_mandates where organization_id=org;
 return jsonb_build_object('revision',coalesce(m.revision,0),'enabled',coalesce(m.enabled,false),'max_steps',coalesce(m.max_steps,3),'updated_at',m.updated_at,
 'execution_open',coalesce((select automatic_enabled from private.reda_engine_settings),false),
 'can_manage',exists(select 1 from public.reda_memberships where organization_id=org and user_id=actor and role='owner' and status='active'));
end$$;
create function private.reda_save_clinical_ei_mandate(p_request_id uuid,p_revision integer,p_enabled boolean,p_max_steps integer) returns jsonb language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();org uuid:=private.reda_request_organization();old private.reda_clinical_mandate_receipts%rowtype;submitted jsonb;result jsonb;before_state jsonb;
begin
 perform 1 from public.reda_organizations where id=org and status='active' for update;
 if not found or not private.reda_is_clinician_aal2() or not exists(select 1 from public.reda_memberships where organization_id=org and user_id=actor and role='owner' and status='active')then raise exception using errcode='42501',message='En aktiv ägare med behandlarbehörighet och MFA krävs.';end if;
 if p_request_id is null or p_revision is null or p_revision<0 or p_enabled is null or p_max_steps is null or p_max_steps not between 1 and 11 then raise exception using errcode='22023',message='Ange ett mandat och en gräns på 1–11 steg.';end if;
 submitted=jsonb_build_object('revision',p_revision,'enabled',p_enabled,'max_steps',p_max_steps);
 select * into old from private.reda_clinical_mandate_receipts where request_id=p_request_id;
 if found then
  if old.actor_id=actor and old.organization_id=org and old.input=submitted then return old.result;end if;
  raise exception using errcode='23505',message='Begäran hör till en annan ändring.';
 end if;
 before_state=private.reda_clinical_ei_settings();
 if p_revision<>(before_state->>'revision')::integer then raise exception using errcode='40001',message='Mandatet har ändrats. Läs in det igen före sparning.';end if;
 insert into private.reda_clinical_ei_mandates(organization_id,enabled,max_steps,revision,updated_by)
 values(org,p_enabled,p_max_steps,1,actor) on conflict(organization_id)do update
 set enabled=excluded.enabled,max_steps=excluded.max_steps,revision=reda_clinical_ei_mandates.revision+1,updated_by=actor,updated_at=now();
 result=private.reda_clinical_ei_settings();
 insert into private.reda_clinical_mandate_receipts(request_id,organization_id,actor_id,input,before_state,result)values(p_request_id,org,actor,submitted,before_state,result);
 return result;
end$$;
create function public.reda_clinical_ei_settings()returns jsonb language sql stable security invoker set search_path='' as $$select private.reda_clinical_ei_settings()$$;
create function public.reda_save_clinical_ei_mandate(p_request_id uuid,p_revision integer,p_enabled boolean,p_max_steps integer)returns jsonb language sql security invoker set search_path='' as $$select private.reda_save_clinical_ei_mandate(p_request_id,p_revision,p_enabled,p_max_steps)$$;
revoke all on function private.reda_clinical_ei_settings(),public.reda_clinical_ei_settings(),private.reda_save_clinical_ei_mandate(uuid,integer,boolean,integer),public.reda_save_clinical_ei_mandate(uuid,integer,boolean,integer) from public,anon,authenticated;
grant execute on function private.reda_clinical_ei_settings(),public.reda_clinical_ei_settings(),private.reda_save_clinical_ei_mandate(uuid,integer,boolean,integer),public.reda_save_clinical_ei_mandate(uuid,integer,boolean,integer) to authenticated;

create or replace function private.reda_approve_frame(p_plan_id uuid,p_policy jsonb,p_execution text default 'shadow') returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor(); p public.reda_plans%rowtype; f public.reda_progression_frames%rowtype;pid uuid;org uuid;m private.reda_clinical_ei_mandates%rowtype;engine_open boolean;begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='Behandlarinloggning med MFA krävs.';end if;
 select patient_id into pid from public.reda_plans where id=p_plan_id and clinician_id=actor;
 perform private.reda_lock_clinical_patient(pid);
 perform 1 from public.reda_patients where id=pid and private.reda_owns_patient(id) and status='active' for update;
 if not found then raise exception using errcode='42501',message='Planen är inte tillgänglig.';end if;
 select * into p from public.reda_plans where id=p_plan_id and status='active' for update;
 if p.id is null or not private.reda_validate_frame(p_policy) or private.reda_plan_binding(p.payload) is distinct from private.reda_plan_binding(p_policy->'steps'->0->'plan') then raise exception using errcode='22023',message='Ramen måste utgå från den aktuella publicerade ordinationen.';end if;
 if p_execution not in ('shadow','automatic') or p_execution is null then raise exception using errcode='22023',message='Ogiltigt körläge.';end if;
 if p_execution='automatic' then
  select organization_id into org from public.reda_patients where id=pid;
  select * into m from private.reda_clinical_ei_mandates where organization_id=org;
  select automatic_enabled into engine_open from private.reda_engine_settings for share;
  if not coalesce(engine_open,false) or not coalesce(m.enabled,false) then raise exception using errcode='42501',message='Automatisk progression kräver både öppnad körning och klinikens mandat.';end if;
 end if;
 if (p_policy->>'validUntil')::date<(now() at time zone 'Europe/Stockholm')::date then raise exception using errcode='22023',message='Ramens slutdatum har passerat.';end if;
 update public.reda_progression_frames set status='revoked',revoked_at=now() where patient_id=pid and status='approved';
 insert into public.reda_progression_frames(patient_id,clinician_id,source_plan_id,current_plan_id,policy,execution,approved_by,mandate_organization_id,mandate_revision) values(pid,actor,p.id,p.id,p_policy,p_execution,actor,org,m.revision) returning * into f;
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata) values(actor,pid,'progression_frame_approved',jsonb_build_object('frame_id',f.id,'plan_id',p.id,'execution',p_execution,'mandate_revision',m.revision,'mandate_organization_id',org));
 return to_jsonb(f);
end$$;

create or replace function private.reda_evaluate_progression(p_patient_id uuid,p_request_id uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();patient public.reda_patients%rowtype;f public.reda_progression_frames%rowtype;p public.reda_plans%rowtype;d public.reda_engine_decisions%rowtype;
 a text:='wait';code text:='evidence';today date:=(now() at time zone 'Europe/Stockholm')::date;r record;ex jsonb;mark jsonb;latest jsonb;days date[]:='{}';ids uuid[]:='{}';next_id uuid;next_version int;min_days int;can_apply boolean:=false;cutoff timestamptz;m private.reda_clinical_ei_mandates%rowtype;engine_open boolean;
begin
 perform private.reda_lock_patient_context(p_patient_id);
 select * into patient from public.reda_patients where id=p_patient_id and status='active' and (private.reda_is_own_patient(id) or private.reda_owns_patient(id)) for update;
 if patient.id is null or p_request_id is null then raise exception using errcode='42501',message='Patienten är inte tillgänglig.';end if;
 select * into d from public.reda_engine_decisions where request_id=p_request_id;
 if d.id is not null then if d.patient_id<>patient.id or d.actor_id<>actor then raise exception using errcode='42501',message='Begäran är inte tillgänglig.';end if;return to_jsonb(d);end if;
 select * into f from public.reda_progression_frames where patient_id=patient.id and status='approved' for update;
 if f.id is null then return jsonb_build_object('action','none','code','no_frame','applied',false);end if;
 select * into p from public.reda_plans where id=f.current_plan_id for update;
 min_days=(f.policy->'rules'->>'minSuccessfulDays')::int;
 cutoff=greatest(f.started_at,((today-(f.policy->'rules'->>'maxEvidenceAgeDays')::int)::timestamp at time zone 'Europe/Stockholm'));
 select * into m from private.reda_clinical_ei_mandates where organization_id=patient.organization_id;
 select automatic_enabled into engine_open from private.reda_engine_settings for share;
 <<decision>> begin
  if f.execution='automatic' then
   if not coalesce(engine_open,false) then a='blocked';code='execution_closed';exit decision;end if;
   if not coalesce(m.enabled,false) then a='blocked';code='mandate_disabled';exit decision;end if;
   if f.mandate_organization_id is distinct from patient.organization_id or f.mandate_revision is distinct from m.revision then a='blocked';code='mandate_changed';exit decision;end if;
  end if;
  if patient.clinician_id<>f.clinician_id or not private.reda_clinical_member(patient.organization_id,f.clinician_id) or not exists(select 1 from public.reda_profiles pr join auth.users u on u.id=pr.user_id where pr.user_id=f.clinician_id and pr.role='clinician' and u.deleted_at is null and (u.banned_until is null or u.banned_until<=now())) then a='blocked';code='clinician_authority';exit decision;end if;
  if p.status<>'active' or private.reda_plan_binding(p.payload) is distinct from private.reda_plan_binding(f.policy->'steps'->f.current_step->'plan') then a='blocked';code='version';exit decision;end if;
  if exists(select 1 from public.reda_review_cases where patient_id=patient.id and status<>'resolved') or exists(select 1 from private.reda_clinic_messages where patient_id=patient.id and handled_at is null) then a='review';code='pending_review';exit decision;end if;
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
  if f.execution='automatic' and f.current_step>=m.max_steps then a='review';code='mandate_limit';exit decision;end if;
  a='advance';code='ready';
 end decision;
 can_apply=f.execution='automatic' and coalesce(engine_open,false) and coalesce(m.enabled,false) and f.mandate_organization_id=patient.organization_id and f.mandate_revision=m.revision;
 if a='advance' and can_apply then
  select coalesce(max(version),0)+1 into next_version from public.reda_plans where patient_id=patient.id;
  update public.reda_plans set status='superseded',superseded_at=now() where id=p.id;
  insert into public.reda_plans(patient_id,clinician_id,version,status,payload,activated_at) values(patient.id,f.clinician_id,next_version,'active',(f.policy->'steps'->(f.current_step+1)->'plan')-'progressionDraft',now()) returning id into next_id;
  update public.reda_progression_frames set current_step=current_step+1,current_plan_id=next_id,started_at=now() where id=f.id;
 elsif a='complete' and can_apply then update public.reda_progression_frames set status='completed' where id=f.id;
 end if;
 insert into public.reda_engine_decisions(request_id,patient_id,frame_id,plan_id,step,actor_id,action,code,metrics,evidence_ids,applied,result_plan_id) values(p_request_id,patient.id,f.id,p.id,f.current_step,actor,a,code,jsonb_build_object('mandateRevision',m.revision,'mandateMaxSteps',m.max_steps,'successfulDays',(select count(distinct unnest) from unnest(days)),'requiredDays',min_days,'daysAtStep',today-(f.started_at at time zone 'Europe/Stockholm')::date),ids,can_apply and a in ('advance','complete'),next_id) returning * into d;
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata) values(actor,patient.id,'progression_evaluated',jsonb_build_object('decision_id',d.id,'frame_id',f.id,'code',code,'applied',d.applied,'mandate_revision',m.revision,'mandate_organization_id',patient.organization_id));return to_jsonb(d);
end$$;
