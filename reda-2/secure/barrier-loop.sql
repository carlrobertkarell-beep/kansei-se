-- One practical barrier, one reviewed intervention, one attributable outcome.
-- No rollout flags or external messages. Existing clinical publication gate applies.
create table private.reda_barrier_loops(
 id uuid primary key default gen_random_uuid(),
 patient_id uuid not null references public.reda_patients,
 case_id uuid not null unique references public.reda_review_cases,
 source_plan_id uuid not null references public.reda_plans,
 barrier text not null check(barrier in ('time','equipment')),
 context jsonb, context_request uuid unique, context_at timestamptz,
 result_plan_id uuid references public.reda_plans,
 publish_request uuid unique, publish_input jsonb, publish_receipt jsonb,
 approved_by uuid references auth.users, approved_at timestamptz, due_date date,
 followup_stamp timestamptz,
 outcome text check(outcome in ('helped','partly','no','not_tried')),
 outcome_request uuid unique, outcome_session_id uuid references public.reda_sessions,
 outcome_at timestamptz, closed_at timestamptz,
 created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create index reda_barriers_patient on private.reda_barrier_loops(patient_id,created_at desc,id);
create index reda_barriers_source on private.reda_barrier_loops(source_plan_id);
create index reda_barriers_result on private.reda_barrier_loops(result_plan_id) where result_plan_id is not null;
create index reda_barriers_approver on private.reda_barrier_loops(approved_by) where approved_by is not null;
create index reda_barriers_session on private.reda_barrier_loops(outcome_session_id) where outcome_session_id is not null;
alter table private.reda_barrier_loops enable row level security;
revoke all on private.reda_barrier_loops from public,anon,authenticated;
create policy "checked RPC only" on private.reda_barrier_loops for all to authenticated using(false) with check(false);

create function private.reda_begin_barrier() returns trigger language plpgsql security definer set search_path='' as $$
declare a jsonb;b text;ctx jsonb;
begin
 if new.status<>'open' then return new;end if;
 if new.reflection_id is not null then
  select answers into a from public.reda_session_reflections where id=new.reflection_id;
  b=a->>'barrier';
 elsif new.checkin_id is not null and new.code in ('training_barrier','changed_environment') then
  select answers into a from public.reda_patient_checkins where id=new.checkin_id;
  b=case new.code when 'training_barrier' then 'time' else 'equipment' end;
  ctx=case b when 'time' then jsonb_build_object('minutes',a->'minutes') else jsonb_build_object('equipment',a->'equipment','band',a->'band','floorOK',a->'floorOK') end;
 end if;
 if b is null or b not in ('time','equipment') then return new;end if;
 perform private.reda_lock_patient_context(new.patient_id);
 perform 1 from public.reda_patients where id=new.patient_id and status='active' for update;
 if not found then return new;end if;
 -- Feedback for an old session remains a clinical signal, never a current-plan proposal.
 if not exists(select 1 from public.reda_plans where id=new.plan_id and patient_id=new.patient_id and status='active') then return new;end if;
 insert into private.reda_barrier_loops(patient_id,case_id,source_plan_id,barrier,context,context_at)
 values(new.patient_id,new.id,new.plan_id,b,ctx,case when ctx is not null then now() end);
 return new;
end$$;
revoke all on function private.reda_begin_barrier() from public,anon,authenticated;
create trigger reda_begin_barrier after insert on public.reda_review_cases for each row execute function private.reda_begin_barrier();

-- Safe projection shared by the patient and assigned clinician; no internal notes or receipts.
create function private.reda_barrier_state(p_id uuid) returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare l private.reda_barrier_loops%rowtype;sid uuid;phase text;blocked boolean;cstatus text;active_id uuid;
begin
 select * into l from private.reda_barrier_loops where id=p_id;
 if not found then return null;end if;
 select id into active_id from public.reda_plans where patient_id=l.patient_id and status='active';
 select status into cstatus from public.reda_review_cases where id=l.case_id;
 blocked=exists(select 1 from public.reda_review_cases where patient_id=l.patient_id and status<>'resolved' and code='changed_symptoms');
 select id into sid from public.reda_sessions where patient_id=l.patient_id and plan_id=l.result_plan_id
 and status in ('completed','partial') and completed_at is not null and completed_at<=now()
 and started_at>=l.approved_at and not coalesce(payload?'optionId',false)
 and exists(select 1 from jsonb_array_elements(payload->'exercises') x where coalesce((x->>'roundsDone')::int,0)>0)
 order by completed_at desc,id desc limit 1;
 phase=case when l.closed_at is not null then 'helped'
 when l.outcome is not null then 'needs_review'
 when cstatus='resolved' then 'handled'
 when coalesce(l.result_plan_id,l.source_plan_id) is distinct from active_id then 'superseded'
 when blocked then 'needs_review'
 when l.result_plan_id is not null and sid is not null then 'check_result'
 when l.result_plan_id is not null then 'trying'
 when l.context is null then 'needs_context' else 'ready' end;
 return jsonb_build_object('id',l.id,'case_id',l.case_id,'source_plan_id',l.source_plan_id,'barrier',l.barrier,
 'context',l.context,'context_at',l.context_at,'phase',phase,'blocked',blocked,'result_plan_id',l.result_plan_id,
 'result_version',(select version from public.reda_plans where id=l.result_plan_id),
 'session_id',sid,'approved_at',l.approved_at,'due_date',l.due_date,
 'overdue',coalesce(l.outcome is null and l.due_date<(now() at time zone 'Europe/Stockholm')::date,false),
 'outcome',l.outcome,'outcome_at',l.outcome_at,'closed_at',l.closed_at,'created_at',l.created_at);
end$$;
revoke all on function private.reda_barrier_state(uuid) from public,anon,authenticated;
create function private.reda_patient_barriers(p_patient_id uuid) returns jsonb language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();begin
 if not private.reda_is_own_patient(p_patient_id) then raise exception using errcode='42501',message='Uppföljningen är inte tillgänglig.';end if;
 return coalesce((select jsonb_agg(private.reda_barrier_state(id) order by created_at desc,id desc) from
 (select id,created_at from private.reda_barrier_loops where patient_id=p_patient_id order by created_at desc,id desc limit 20)l),'[]');
end$$;

create function private.reda_answer_barrier(p_loop_id uuid,p_request_id uuid,p_context jsonb) returns jsonb language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();l private.reda_barrier_loops%rowtype;begin
 select * into l from private.reda_barrier_loops where id=p_loop_id;
 perform private.reda_lock_patient_context(l.patient_id);
 perform 1 from public.reda_patients where id=l.patient_id and private.reda_is_own_patient(id) for update;
 if not found then raise exception using errcode='42501',message='Frågan är inte tillgänglig.';end if;
 select * into l from private.reda_barrier_loops where id=p_loop_id for update;
 if p_request_id is null or jsonb_typeof(p_context) is distinct from 'object' then raise exception using errcode='22023',message='Välj ett svar.';end if;
 if l.context_request=p_request_id and l.context=p_context then return private.reda_barrier_state(l.id);end if;
 if l.context is not null then raise exception using errcode='23505',message='Ditt svar är redan sparat. Hämta uppföljningen igen.';end if;
 if private.reda_barrier_state(l.id)->>'phase' is distinct from 'needs_context' then raise exception using errcode='40001',message='Förutsättningarna har ändrats. Hämta uppföljningen igen.';end if;
 if l.barrier='time' then
  if (select count(*)from jsonb_object_keys(p_context))<>1 or jsonb_typeof(p_context->'minutes') is distinct from 'number' or p_context->>'minutes' not in ('5','10','15','20','30','45','60') then raise exception using errcode='22023',message='Välj hur mycket tid du har.';end if;
 else
  if (select count(*)from jsonb_object_keys(p_context))<>3 or p_context->>'equipment' is null or p_context->>'equipment' not in ('home','gym') or jsonb_typeof(p_context->'band') is distinct from 'boolean' or jsonb_typeof(p_context->'floorOK') is distinct from 'boolean' then raise exception using errcode='22023',message='Välj plats, utrustning och möjlighet till golvövningar.';end if;
 end if;
 update private.reda_barrier_loops set context=p_context,context_request=p_request_id,context_at=now(),updated_at=clock_timestamp() where id=l.id;
 return private.reda_barrier_state(l.id);
end$$;

-- Reviewed publishing and follow-up are one transaction, including lost-receipt retries.
create function private.reda_publish_barrier(p_loop_id uuid,p_request_id uuid,p_token text,p_payload jsonb,p_note text,p_patient_message text,p_due_date date) returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();l private.reda_barrier_loops%rowtype;inp jsonb;r jsonb;stamp timestamptz;begin
 select * into l from private.reda_barrier_loops where id=p_loop_id;
 perform private.reda_lock_clinical_patient(l.patient_id);
 perform 1 from public.reda_patients where id=l.patient_id and status='active' and private.reda_owns_patient(id) for update;
 if not found then raise exception using errcode='42501',message='Patienten är inte tillgänglig.';end if;
 select * into l from private.reda_barrier_loops where id=p_loop_id for update;
 inp=jsonb_build_object('token',p_token,'payload',p_payload,'note',p_note,'message',p_patient_message,'due',p_due_date);
 if l.publish_request=p_request_id then
  if l.approved_by is distinct from actor or l.publish_input is distinct from inp then raise exception using errcode='23505',message='Begäran hör till en annan granskning.';end if;
  return l.publish_receipt;
 end if;
 if private.reda_barrier_state(l.id)->>'phase' is distinct from 'ready' then raise exception using errcode='40001',message='Hindret behöver nytt underlag. Öppna granskningen igen.';end if;
 if p_due_date is null or p_due_date<(now() at time zone 'Europe/Stockholm')::date or p_due_date>(now() at time zone 'Europe/Stockholm')::date+30 then raise exception using errcode='22023',message='Välj när uteblivet svar ska följas upp, inom 30 dagar.';end if;
 r=private.reda_publish_reviewed(l.patient_id,p_request_id,p_token,l.source_plan_id,p_payload,p_note,p_patient_message,null,null);
 update public.reda_review_cases set status='acknowledged',handled_by=actor,handling_note=trim(p_note),updated_at=now() where id=l.case_id and status='open';
 -- Only replace the untouched, system-created barrier task. Preserve independent clinical work.
 update private.reda_followups set due_date=p_due_date,completed_at=null,note='Följ upp om den godkända planändringen hjälpte med vardagshindret.',updated_at=clock_timestamp()
 where patient_id=l.patient_id and status='waiting'
 and note in ('Följ upp hindret som patienten har rapporterat i träningen.','Stäm av patientens ändrade träningsförutsättningar.')
 and not exists(select 1 from public.reda_review_cases where patient_id=l.patient_id and id<>l.case_id and status<>'resolved')
 and not exists(select 1 from private.reda_clinic_messages where patient_id=l.patient_id and handled_at is null)
 returning updated_at into stamp;
 update private.reda_barrier_loops set result_plan_id=(r->>'plan_id')::uuid,publish_request=p_request_id,publish_input=inp,publish_receipt=r,
 approved_by=actor,approved_at=now(),due_date=p_due_date,followup_stamp=stamp,updated_at=clock_timestamp() where id=l.id;
 return r;
end$$;

create function private.reda_barrier_outcome(p_loop_id uuid,p_request_id uuid,p_outcome text,p_session_id uuid default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();l private.reda_barrier_loops%rowtype;st jsonb;can_close boolean;begin
 select * into l from private.reda_barrier_loops where id=p_loop_id;
 perform private.reda_lock_patient_context(l.patient_id);
 perform 1 from public.reda_patients where id=l.patient_id and private.reda_is_own_patient(id) for update;
 if not found then raise exception using errcode='42501',message='Uppföljningen är inte tillgänglig.';end if;
 select * into l from private.reda_barrier_loops where id=p_loop_id for update;
 if p_request_id is null or p_outcome is null or p_outcome not in ('helped','partly','no','not_tried') then raise exception using errcode='22023',message='Välj hur ändringen fungerade.';end if;
 if l.outcome_request=p_request_id and l.outcome=p_outcome and l.outcome_session_id is not distinct from p_session_id then return private.reda_barrier_state(l.id);end if;
 if l.outcome is not null then raise exception using errcode='23505',message='Ett svar är redan sparat. Hämta uppföljningen igen.';end if;
 st=private.reda_barrier_state(l.id);
 if st->>'phase' not in ('trying','check_result') or l.result_plan_id is null then raise exception using errcode='40001',message='Planen eller uppföljningen har ändrats. Hämta den igen.';end if;
 if p_outcome='not_tried' then
  if p_session_id is not null then raise exception using errcode='22023',message='Ett oprövat upplägg ska inte kopplas till ett pass.';end if;
 else
  if p_session_id is null or not exists(select 1 from public.reda_sessions s where s.id=p_session_id and s.patient_id=l.patient_id and s.plan_id=l.result_plan_id and s.started_at>=l.approved_at and s.completed_at<=now() and s.status in ('completed','partial') and not coalesce(s.payload?'optionId',false) and exists(select 1 from jsonb_array_elements(s.payload->'exercises')x where coalesce((x->>'roundsDone')::int,0)>0)) then raise exception using errcode='22023',message='Svaret ska gälla ett avslutat pass med den nya planen.';end if;
 end if;
 can_close=p_outcome='helped'
 and not exists(select 1 from public.reda_review_cases where patient_id=l.patient_id and id<>l.case_id and status<>'resolved')
 and not exists(select 1 from private.reda_clinic_messages where patient_id=l.patient_id and handled_at is null)
 and not exists(select 1 from public.reda_review_cases c join public.reda_session_reflections r on r.id=c.reflection_id where c.id=l.case_id and r.answers->>'support'='yes');
 update private.reda_barrier_loops set outcome=p_outcome,outcome_request=p_request_id,outcome_session_id=p_session_id,outcome_at=now(),closed_at=case when can_close then now() end,updated_at=clock_timestamp() where id=l.id;
 if can_close then
  update public.reda_review_cases set status='resolved',handled_by=null,handling_note='EI: Patienten uppger att den granskade ändringen hjälpte med vardagshindret efter ett registrerat pass. Praktiskt hinder avslutat; ingen bedömning av tillfrisknande.',updated_at=now() where id=l.case_id;
  update private.reda_followups set status='completed',completed_at=now(),updated_at=clock_timestamp() where patient_id=l.patient_id and status='waiting' and updated_at=l.followup_stamp;
 else
  update public.reda_review_cases set status='open',updated_at=now() where id=l.case_id;
  -- Keep new signals visible even if the administrative scheduling mandate is off.
  insert into private.reda_followups(patient_id,clinician_id,due_date,status,note)
  select id,clinician_id,(now() at time zone 'Europe/Stockholm')::date,'waiting','Bedöm patientens svar på den godkända planändringen.' from public.reda_patients where id=l.patient_id and coalesce((select auto_followup from private.reda_ei_mandates where organization_id=reda_patients.organization_id),true)
  on conflict(patient_id)do update set due_date=case when reda_followups.status='waiting' then least(reda_followups.due_date,excluded.due_date) else excluded.due_date end,status='waiting',completed_at=null,updated_at=clock_timestamp();
 end if;
 return private.reda_barrier_state(l.id);
end$$;

-- Every reply changes the existing snapshot token, even when plan and clinical cases stay put.
alter function private.reda_dashboard_snapshot(uuid) rename to reda_dashboard_snapshot_before_barriers;
revoke all on function private.reda_dashboard_snapshot_before_barriers(uuid) from public,anon,authenticated;
create function private.reda_dashboard_snapshot(p_patient uuid) returns jsonb language sql stable security invoker set search_path='' as $$
 select private.reda_dashboard_snapshot_before_barriers(p_patient)||jsonb_build_object('barrier_revision',
 (select jsonb_build_object('count',count(*),'updated',max(updated_at))from private.reda_barrier_loops where patient_id=p_patient))
$$;
revoke all on function private.reda_dashboard_snapshot(uuid) from public,anon,authenticated;
alter function private.reda_dashboard_patient(uuid) rename to reda_dashboard_patient_before_barriers;
revoke all on function private.reda_dashboard_patient_before_barriers(uuid) from public,anon,authenticated;
create function private.reda_dashboard_patient(p_patient_id uuid) returns jsonb language plpgsql stable security definer set search_path='' as $$
declare r jsonb;begin
 r=private.reda_dashboard_patient_before_barriers(p_patient_id);
 return r||jsonb_build_object('barriers',coalesce((select jsonb_agg(private.reda_barrier_state(id)order by created_at desc,id desc)from(select id,created_at from private.reda_barrier_loops where patient_id=p_patient_id order by created_at desc,id desc limit 20)l),'[]'));
end$$;
create or replace function public.reda_dashboard_patient(p_patient_id uuid) returns jsonb language sql stable security invoker set search_path='' as $$select private.reda_dashboard_patient(p_patient_id)$$;
revoke all on function private.reda_dashboard_patient(uuid) from public,anon,authenticated;
grant execute on function private.reda_dashboard_patient(uuid) to authenticated;

create function public.reda_patient_barriers(p_patient_id uuid) returns jsonb language sql stable security invoker set search_path='' as $$select private.reda_patient_barriers(p_patient_id)$$;
create function public.reda_answer_barrier(p_loop_id uuid,p_request_id uuid,p_context jsonb) returns jsonb language sql security invoker set search_path='' as $$select private.reda_answer_barrier(p_loop_id,p_request_id,p_context)$$;
create function public.reda_publish_barrier(p_loop_id uuid,p_request_id uuid,p_token text,p_payload jsonb,p_note text,p_patient_message text,p_due_date date) returns jsonb language sql security invoker set search_path='' as $$select private.reda_publish_barrier(p_loop_id,p_request_id,p_token,p_payload,p_note,p_patient_message,p_due_date)$$;
create function public.reda_barrier_outcome(p_loop_id uuid,p_request_id uuid,p_outcome text,p_session_id uuid default null) returns jsonb language sql security invoker set search_path='' as $$select private.reda_barrier_outcome(p_loop_id,p_request_id,p_outcome,p_session_id)$$;
revoke all on function private.reda_patient_barriers(uuid),public.reda_patient_barriers(uuid),private.reda_answer_barrier(uuid,uuid,jsonb),public.reda_answer_barrier(uuid,uuid,jsonb),private.reda_publish_barrier(uuid,uuid,text,jsonb,text,text,date),public.reda_publish_barrier(uuid,uuid,text,jsonb,text,text,date),private.reda_barrier_outcome(uuid,uuid,text,uuid),public.reda_barrier_outcome(uuid,uuid,text,uuid) from public,anon,authenticated;
grant execute on function private.reda_patient_barriers(uuid),public.reda_patient_barriers(uuid),private.reda_answer_barrier(uuid,uuid,jsonb),public.reda_answer_barrier(uuid,uuid,jsonb),private.reda_publish_barrier(uuid,uuid,text,jsonb,text,text,date),public.reda_publish_barrier(uuid,uuid,text,jsonb,text,text,date),private.reda_barrier_outcome(uuid,uuid,text,uuid),public.reda_barrier_outcome(uuid,uuid,text,uuid) to authenticated;

-- Extend dated history without exposing internal clinical notes.
create or replace function private.reda_activity_log(p_patient_id uuid,p_category text default 'all',p_from date default null,p_to date default null,p_before_time timestamptz default null,p_before_key text default null)
returns jsonb language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();clinician boolean;timeline_result jsonb;
begin
 clinician=coalesce(private.reda_owns_patient(p_patient_id),false);
 if not clinician and not coalesce(private.reda_is_own_patient(p_patient_id),false) then raise exception using errcode='42501',message='Historiken är inte tillgänglig.';end if;
 if p_category is null or p_category not in ('all','plans','training','feedback','contact','finance','ei') or (p_from>p_to) or num_nonnulls(p_before_time,p_before_key)=1 then raise exception using errcode='22023',message='Kontrollera filter och datum.';end if;
 with events as (
 select 'patient:'||id as id,created_at as occurred_at,'contact'::text as category,'Patientprofil skapad'::text as title,''::text as detail,null::uuid as plan_id,null::integer as plan_version from public.reda_patients where id=p_patient_id
 union all select 'draft:'||id,created_at,'plans','Planversion skapad','Sparad version. Aktivering visas som en separat händelse',id,version from public.reda_plans where patient_id=p_patient_id and clinician
 union all select 'plan:'||id,activated_at,'plans','Plan aktiverad','Publicerad planversion',id,version from public.reda_plans where patient_id=p_patient_id and activated_at is not null
 union all select 'start:'||s.id,s.started_at,'training','Pass påbörjat',coalesce((select o->>'label' from jsonb_array_elements(p.payload->'planOptions'->'items') o where o->>'id'=s.payload->>'optionId'),'Ordinarie pass'),s.plan_id,s.plan_version from public.reda_sessions s join public.reda_plans p on p.id=s.plan_id where s.patient_id=p_patient_id and s.status<>'planned_rest'
 union all select 'end:'||s.id,s.completed_at,'training',case when s.status='completed' then 'Pass genomfört' else 'Pass delvis genomfört' end,coalesce((select o->>'label' from jsonb_array_elements(p.payload->'planOptions'->'items') o where o->>'id'=s.payload->>'optionId'),'Ordinarie pass'),s.plan_id,s.plan_version from public.reda_sessions s join public.reda_plans p on p.id=s.plan_id where s.patient_id=p_patient_id and s.completed_at is not null and s.status in ('completed','partial')
 union all select 'response:'||id,created_at,'feedback','Uppföljning efter träning sparad','Svar om kroppens reaktion',plan_id,plan_version from public.reda_training_responses where patient_id=p_patient_id
 union all select 'reflection:'||id,created_at,'feedback','Svar direkt efter passet sparade',case answers->>'barrier' when 'time' then 'Tiden räckte inte' when 'execution' then 'Svårt att förstå utförandet' when 'equipment' then 'Utrustning eller miljö' when 'symptoms' then 'Besvär under träningen' when 'energy' then 'Orken räckte inte' when 'other' then 'Annat hinder' else 'Inget hinder angivet' end||case when answers->>'support'='yes' then ' · Hjälp efterfrågad' else '' end,plan_id,plan_version from public.reda_session_reflections where patient_id=p_patient_id
 union all select 'message:'||id,created_at,'contact',case when kind='clinician' then 'Meddelande från kliniken' else 'Svar från patienten' end,'Sparat i Redas meddelanden',null,null from private.reda_clinic_messages where patient_id=p_patient_id
 union all select 'checkin:'||id,created_at,'feedback','Målskattning och vardagsförutsättningar sparade','Egen målskattning '||(answers->>'ability')||'/10 · '||(answers->>'minutes')||' minuter för träning',plan_id,plan_version from public.reda_patient_checkins where patient_id=p_patient_id
 union all select 'queue:'||id,created_at,'ei','EI lade till en uppföljningsuppgift','Tilldelad behandlaren · Datum '||(metadata->>'due_date'),(metadata->>'plan_id')::uuid,null from public.reda_audit_events where patient_id=p_patient_id and clinician and action='support_task_queued'
 union all select 'task:'||request_id,created_at,'ei',case result->>'action' when 'follow_up' then 'Uppföljning planerad' when 'complete_follow_up' then 'Uppföljning markerad genomförd' when 'resolve_cases' then 'Ärende markerat bedömt' else 'Klinikåtgärd sparad' end,'Sparat av behandlaren i arbetslistan',null,null from private.reda_clinic_action_receipts where patient_id=p_patient_id and clinician and result->>'action' in ('follow_up','complete_follow_up','resolve_cases')
 union all select 'review:'||id,created_at,'ei','EI-bedömning granskad',case verdict when 'agree' then 'Behandlaren instämmer' when 'disagree' then 'Behandlaren gör en annan bedömning' else 'Underlaget bedöms otillräckligt' end,null,null from public.reda_decision_reviews where patient_id=p_patient_id and clinician
 union all select 'ei:'||id,created_at,'ei',case when applied then 'EI-åtgärd genomförd' else 'EI-bedömning registrerad' end,case when applied then 'Utförd åtgärd: ' else 'Ingen automatisk planändring. Bedömning: ' end||action,plan_id,null from public.reda_engine_decisions where patient_id=p_patient_id and clinician

 union all select 'barrier-context:'||id,context_at,'feedback','Förutsättningar inför planändring sparade',case barrier when 'time' then (context->>'minutes')||' minuter tillgängligt' else 'Plats och utrustning angivna' end,source_plan_id,null from private.reda_barrier_loops where patient_id=p_patient_id
 union all select 'barrier-plan:'||id,approved_at,'plans','Ändring och riktad uppföljning godkända',case barrier when 'time' then 'Följ upp om passet blir lättare att hinna med' else 'Följ upp om plats och utrustning fungerar' end,result_plan_id,null from private.reda_barrier_loops where patient_id=p_patient_id
 union all select 'barrier-outcome:'||id,outcome_at,'feedback','Svar på planändring sparat',case outcome when 'helped' then 'Ändringen hjälpte med hindret' when 'partly' then 'Ändringen hjälpte delvis' when 'no' then 'Hindret kvarstår' else 'Har inte kunnat prova' end,result_plan_id,null from private.reda_barrier_loops where patient_id=p_patient_id
 union all select 'barrier-close:'||id,closed_at,'feedback','Praktiskt hinder avslutat','Avslutat efter patientens svar; gäller inte tillfrisknande',result_plan_id,null from private.reda_barrier_loops where patient_id=p_patient_id
 ), page as (
 select * from events where occurred_at is not null and (p_category='all' or category=p_category)
 and (p_from is null or occurred_at>=p_from::timestamp at time zone 'Europe/Stockholm')
 and (p_to is null or occurred_at<(p_to+1)::timestamp at time zone 'Europe/Stockholm')
 and (p_before_time is null or (occurred_at,id)<(p_before_time,p_before_key))
 order by occurred_at desc,id desc limit 51
 ), visible as(select * from page order by occurred_at desc,id desc limit 50)
 select jsonb_build_object('events',coalesce((select jsonb_agg(to_jsonb(v) order by occurred_at desc,id desc)from visible v),'[]'::jsonb),'next_cursor',case when (select count(*) from page)>50 then (select jsonb_build_object('time',occurred_at,'key',id)from visible order by occurred_at,id limit 1) else null end,'billing_connected',false,'audience',case when clinician then 'clinician' else 'patient' end)into timeline_result;
 return timeline_result;
end$$;
revoke all on function private.reda_activity_log(uuid,text,date,date,timestamptz,text) from public,anon,authenticated;
grant execute on function private.reda_activity_log(uuid,text,date,date,timestamptz,text) to authenticated;

-- The overview displays who acts next, with the same priority for new clinical signals.
alter function private.reda_support_state(uuid) rename to reda_support_state_before_barriers;
revoke all on function private.reda_support_state_before_barriers(uuid) from public,anon,authenticated;
create function private.reda_support_state(p_patient_id uuid) returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare r jsonb;l jsonb;begin
 r=private.reda_support_state_before_barriers(p_patient_id);
 select private.reda_barrier_state(b.id) into l from private.reda_barrier_loops b join public.reda_review_cases c on c.id=b.case_id
 where b.patient_id=p_patient_id and c.status<>'resolved' order by b.created_at desc,b.id desc limit 1;
 if l is not null and (r->>'pending_signals')::int=1 and not (l->>'blocked')::boolean
 and not exists(select 1 from private.reda_clinic_messages where patient_id=p_patient_id and handled_at is null) then
  r=r||jsonb_build_object('barrier',l);
  if l->>'phase'='needs_context' then r=r||jsonb_build_object('phase','barrier_question','responsibility','patient');
  elsif l->>'phase' in ('trying','check_result') and not (l->>'overdue')::boolean then r=r||jsonb_build_object('phase','barrier_trial','responsibility','patient');end if;
 end if;
 return r;
end$$;
revoke all on function private.reda_support_state(uuid) from public,anon,authenticated;
