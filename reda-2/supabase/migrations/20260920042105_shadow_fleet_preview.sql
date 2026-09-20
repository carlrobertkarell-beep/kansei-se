-- Install only on the engine version reviewed for this feature.
set local lock_timeout='5s';
set local statement_timeout='30s';
do $$begin
 if (select md5(prosrc)from pg_proc where oid='private.reda_evaluate_progression(uuid,uuid)'::regprocedure) is distinct from 'ab6e1bffaf97b3a29b1b7723d6262baf' then raise exception 'Engine changed; review preview migration again.';end if;
end$$;
create function private.reda_progression_decision(p_patient_id uuid,p_request_id uuid,p_preview boolean) returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();patient public.reda_patients%rowtype;f public.reda_progression_frames%rowtype;p public.reda_plans%rowtype;d public.reda_engine_decisions%rowtype;
 a text:='wait';code text:='evidence';today date:=(now() at time zone 'Europe/Stockholm')::date;r record;ex jsonb;mark jsonb;latest jsonb;days date[]:='{}';ids uuid[]:='{}';next_id uuid;next_version int;min_days int;can_apply boolean:=false;cutoff timestamptz;m private.reda_clinical_ei_mandates%rowtype;engine_open boolean;
begin
 if p_preview is null then raise exception using errcode='22023',message='Körläge saknas.';end if;
 perform private.reda_lock_patient_context(p_patient_id);
 select * into patient from public.reda_patients where id=p_patient_id and status='active' and (private.reda_is_own_patient(id) or private.reda_owns_patient(id)) for update;
 if patient.id is null or (not p_preview and p_request_id is null) then raise exception using errcode='42501',message='Patienten är inte tillgänglig.';end if;
 if not p_preview then
 select * into d from public.reda_engine_decisions where request_id=p_request_id;
 if d.id is not null then if d.patient_id<>patient.id or d.actor_id<>actor then raise exception using errcode='42501',message='Begäran är inte tillgänglig.';end if;return to_jsonb(d);end if;
 end if;
 select * into f from public.reda_progression_frames where patient_id=patient.id and status='approved' for update;
 if f.id is null then return jsonb_build_object('action','none','code','no_frame','applied',false);end if;
 select * into p from public.reda_plans where id=f.current_plan_id for update;
 min_days=(f.policy->'rules'->>'minSuccessfulDays')::int;
 cutoff=greatest(f.started_at,((today-(f.policy->'rules'->>'maxEvidenceAgeDays')::int)::timestamp at time zone 'Europe/Stockholm'));
 select * into m from private.reda_clinical_ei_mandates where organization_id=patient.organization_id;
 select automatic_enabled into engine_open from private.reda_engine_settings for share;
 <<decision>> begin
  if f.execution='automatic' then
   if not p_preview and not coalesce(engine_open,false) then a='blocked';code='execution_closed';exit decision;end if;
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
 -- Preview returns before every INSERT/UPDATE: no decisions, audit entries or plans are written.
 if p_preview then return jsonb_build_object('action',a,'code',code,'applied',false,
 'frame_id',f.id,'plan_id',p.id,'step',f.current_step,'steps',jsonb_array_length(f.policy->'steps'),
 'execution',f.execution,'execution_open',coalesce(engine_open,false),'mandate_enabled',coalesce(m.enabled,false),
 'metrics',jsonb_build_object('successfulDays',(select count(distinct unnest)from unnest(days)),'requiredDays',min_days,'daysAtStep',today-(f.started_at at time zone 'Europe/Stockholm')::date),
 'next_step',case when a='advance' then f.policy->'steps'->(f.current_step+1)->>'label' else null end);end if;
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

revoke all on function private.reda_progression_decision(uuid,uuid,boolean)from public,anon,authenticated;
-- Existing saved evaluations retain their semantics, idempotence, locks and grants.
create or replace function private.reda_evaluate_progression(p_patient_id uuid,p_request_id uuid)returns jsonb
language sql security definer set search_path='' as $$select private.reda_progression_decision(p_patient_id,p_request_id,false)$$;

create function private.reda_preview_progression_batch(p_after uuid default null)returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();org uuid:=private.reda_request_organization();r record;items jsonb:='[]';decision jsonb;cursor_id uuid;has_more boolean:=false;n integer:=0;
begin
 perform 1 from public.reda_organizations where id=org and status='active'for share;
 if not found or not private.reda_is_clinician_aal2()then raise exception using errcode='42501',message='En aktiv klinikarbetsyta, behandlarbehörighet och MFA krävs.';end if;
 -- Keyset pagination is bounded independently of clinic size; only assigned active plans.
 for r in select p.id,p.display_name from public.reda_patients p
 where p.organization_id=org and p.clinician_id=actor and p.status='active'and(p_after is null or p.id>p_after)
 and exists(select 1 from public.reda_plans pl where pl.patient_id=p.id and pl.status='active')
 order by p.id limit 26 loop
  if n=25 then has_more=true;exit;end if;
  decision=private.reda_progression_decision(r.id,null,true);
  items=items||jsonb_build_array(jsonb_build_object('patient_id',r.id,'display_name',r.display_name,'evaluated_at',clock_timestamp(),'decision',decision));
  cursor_id=r.id;n=n+1;
 end loop;
 return jsonb_build_object('items',items,'next_cursor',case when has_more then cursor_id else null end,'preview',true);
end$$;
create function public.reda_preview_progression_batch(p_after uuid default null)returns jsonb
language sql security invoker set search_path='' as $$select private.reda_preview_progression_batch(p_after)$$;
revoke all on function private.reda_preview_progression_batch(uuid),public.reda_preview_progression_batch(uuid)from public,anon,authenticated;
grant execute on function private.reda_preview_progression_batch(uuid),public.reda_preview_progression_batch(uuid)to authenticated;
