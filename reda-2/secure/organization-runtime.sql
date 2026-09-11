-- Organization-aware replacements. Apply in the SAME migration as organizations.sql.

create or replace function private.reda_approve_frame(p_plan_id uuid,p_policy jsonb,p_execution text default 'shadow') returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor(); p public.reda_plans%rowtype; f public.reda_progression_frames%rowtype;pid uuid;begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='Behandlarinloggning med MFA krävs.';end if;
 select patient_id into pid from public.reda_plans where id=p_plan_id and clinician_id=actor;
 perform private.reda_lock_clinical_patient(pid);
 perform 1 from public.reda_patients where id=pid and private.reda_owns_patient(id) and status='active' for update;
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

create or replace function private.reda_revoke_frame(p_frame_id uuid) returns void language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor(); pid uuid;begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='MFA krävs.';end if;
 select patient_id into pid from public.reda_progression_frames where id=p_frame_id and clinician_id=actor;
 perform private.reda_lock_clinical_patient(pid);
 perform 1 from public.reda_patients where id=pid and private.reda_owns_patient(id) for update;if not found then raise exception using errcode='42501',message='Ramen är inte tillgänglig.';end if;
 update public.reda_progression_frames set status='revoked',revoked_at=now() where id=p_frame_id and status='approved';
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata) values(actor,pid,'progression_frame_revoked',jsonb_build_object('frame_id',p_frame_id));
end$$;

create or replace function private.reda_handle_case(p_case_id uuid,p_status text,p_note text) returns jsonb language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();c public.reda_review_cases%rowtype;begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='MFA krävs.';end if;
 select * into c from public.reda_review_cases where id=p_case_id;
 perform private.reda_lock_clinical_patient(c.patient_id);
 perform 1 from public.reda_patients where id=c.patient_id and private.reda_owns_patient(id) for update;
 if not found then raise exception using errcode='42501',message='Ärendet är inte tillgängligt.';end if;
 if p_status not in ('acknowledged','resolved') or p_status is null or length(coalesce(p_note,''))>1000 or (p_status='resolved' and length(trim(coalesce(p_note,'')))<5) then raise exception using errcode='22023',message='Ange status och vad som bedömts eller gjorts.';end if;
 update public.reda_review_cases set status=p_status,handled_by=actor,handling_note=coalesce(p_note,''),updated_at=now() where id=p_case_id returning * into c;
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata) values(actor,c.patient_id,'review_case_handled',jsonb_build_object('case_id',c.id,'status',p_status));return to_jsonb(c);
end$$;

create or replace function private.reda_evaluate_progression(p_patient_id uuid,p_request_id uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();patient public.reda_patients%rowtype;f public.reda_progression_frames%rowtype;p public.reda_plans%rowtype;d public.reda_engine_decisions%rowtype;
 a text:='wait';code text:='evidence';today date:=(now() at time zone 'Europe/Stockholm')::date;r record;ex jsonb;mark jsonb;latest jsonb;days date[]:='{}';ids uuid[]:='{}';next_id uuid;next_version int;min_days int;can_apply boolean:=false;cutoff timestamptz;
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
 <<decision>> begin
  if patient.clinician_id<>f.clinician_id or not private.reda_clinical_member(patient.organization_id,f.clinician_id) or not exists(select 1 from public.reda_profiles pr join auth.users u on u.id=pr.user_id where pr.user_id=f.clinician_id and pr.role='clinician' and u.deleted_at is null and (u.banned_until is null or u.banned_until<=now())) then a='blocked';code='clinician_authority';exit decision;end if;
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
 perform private.reda_lock_patient_context((select patient_id from public.reda_sessions where id=p_session_id));
 -- Organization, then patient, then evidence lock order.
 perform 1 from public.reda_patients p join public.reda_sessions rs on rs.patient_id=p.id where rs.id=p_session_id and private.reda_is_own_patient(p.id) for update of p;
 select rs.* into s from public.reda_sessions rs
 join public.reda_patients p on p.id=rs.patient_id
 join public.reda_plans rp on rp.id=rs.plan_id and rp.patient_id=rs.patient_id and rp.version=rs.plan_version
 where rs.id=p_session_id and private.reda_is_own_patient(p.id)
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

create or replace function private.reda_save_session_internal(p_user_id uuid,p_client_session_id uuid,p_plan_id uuid,p_status text,p_started_at timestamptz,p_completed_at timestamptz,p_payload jsonb) returns uuid language plpgsql security invoker set search_path='' as $$
declare patient public.reda_patients%rowtype;p public.reda_plans%rowtype;s public.reda_sessions%rowtype;new_id uuid;begin
 if p_status not in ('started','partial','completed','planned_rest') or (p_status='completed' and p_completed_at is null) then raise exception 'Invalid session status';end if;
 select * into patient from public.reda_patients where auth_user_id=p_user_id and status='active' and exists(select 1 from public.reda_organizations o where o.id=organization_id and o.status='active' and o.kind='clinic') and exists(select 1 from auth.users u where u.id=p_user_id and u.deleted_at is null and (u.banned_until is null or u.banned_until<=now())) for update;if patient.id is null then raise exception 'Patient unavailable';end if;
 select * into s from public.reda_sessions where client_session_id=p_client_session_id for update;
 if s.id is not null then
  if s.patient_id<>patient.id or s.plan_id<>p_plan_id then raise exception 'Session mismatch';end if;
  if s.completed_at is not null then if s.status=p_status and (s.payload-'clientUpdatedAt')=(coalesce(p_payload,'{}'::jsonb)-'clientUpdatedAt') and p_completed_at is not null then return s.id;end if;raise exception 'Closed session is immutable';end if;
  update public.reda_sessions set status=p_status,completed_at=case when p_completed_at is not null then now() else null end,payload=coalesce(p_payload,'{}'::jsonb),updated_at=now() where id=s.id;return s.id;
 end if;
 select * into p from public.reda_plans where id=p_plan_id and patient_id=patient.id and status='active';if p.id is null then raise exception 'Active plan required';end if;
 insert into public.reda_sessions(client_session_id,patient_id,plan_id,plan_version,status,started_at,completed_at,payload) values(p_client_session_id,patient.id,p.id,p.version,p_status,now(),case when p_completed_at is not null then now() else null end,coalesce(p_payload,'{}'::jsonb)) returning id into new_id;return new_id;
end$$;

create or replace function private.reda_dialogue_context(p_plan_id uuid,p_consume boolean default false) returns jsonb language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();p public.reda_plans%rowtype;enabled boolean;bucket_name text;n int;slim jsonb;begin
 select rp.* into p from public.reda_plans rp join public.reda_patients pt on pt.id=rp.patient_id where rp.id=p_plan_id and rp.status='active' and private.reda_is_own_patient(pt.id);
 if p.id is null then raise exception using errcode='42501',message='Den aktuella planen krävs.';end if;
 select ai_enabled into enabled from private.reda_engine_settings;
 if enabled and p_consume then
  delete from private.reda_dialogue_quota where user_id=actor and substring(bucket from position(':' in bucket)+1 for 10)<to_char((now() at time zone 'UTC')-interval '7 days','YYYY-MM-DD');
  foreach bucket_name in array array['day:'||to_char(now() at time zone 'UTC','YYYY-MM-DD'),'hour:'||to_char(now() at time zone 'UTC','YYYY-MM-DD-HH24')] loop
   insert into private.reda_dialogue_quota(user_id,bucket,calls) values(actor,bucket_name,1) on conflict(user_id,bucket) do update set calls=private.reda_dialogue_quota.calls+1 returning calls into n;
   if n>(case when bucket_name like 'day:%' then 100 else 20 end) then raise exception using errcode='54000',message='Gränsen för AI-frågor är nådd. Använd planens instruktioner och återkopplingsfrågor.';end if;
  end loop;
 end if;
 select jsonb_build_object('goal',p.payload->'goal','exercises',jsonb_agg(jsonb_build_object('name',x->'name','variantLabel',x->'variantLabel','why',x->'why','instructions',x->'instructions','instruction',x->'instruction','side',x->'side','dose',x->'dose','prescribedLoad',x->'prescribedLoad','prescribedRange',x->'prescribedRange','equipment',x->'equipment','support',x->'support','focus',x->'focus') order by ord)) into slim from jsonb_array_elements(p.payload->'exercises') with ordinality as e(x,ord);
 return jsonb_build_object('enabled',enabled,'plan',slim);
end$$;

create or replace function private.reda_review_decision(p_decision_id uuid,p_verdict text,p_note text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor(); d public.reda_engine_decisions%rowtype;r public.reda_decision_reviews%rowtype;begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='Behandlarinloggning med MFA krävs.';end if;
 select * into d from public.reda_engine_decisions where id=p_decision_id;
 perform private.reda_lock_clinical_patient(d.patient_id);
 perform 1 from public.reda_patients where id=d.patient_id and private.reda_owns_patient(id) for update;
 if not found then raise exception using errcode='42501',message='Beslutet är inte tillgängligt.';end if;
 if p_verdict is null or p_verdict not in ('agree','disagree','uncertain') or coalesce(length(trim(p_note)),0) not between 5 and 1000 then raise exception using errcode='22023',message='Välj ett ställningstagande och beskriv din bedömning (5–1 000 tecken).';end if;
 select * into r from public.reda_decision_reviews where decision_id=d.id;
 if r.id is not null then
  if r.clinician_id=actor and r.verdict=p_verdict and r.note=trim(p_note) then return to_jsonb(r);end if;
  raise exception using errcode='23505',message='Beslutet har redan en sparad bedömning. Gör en ny prövning om underlaget ändrats.';
 end if;
 insert into public.reda_decision_reviews(decision_id,patient_id,clinician_id,verdict,note) values(d.id,d.patient_id,actor,p_verdict,trim(p_note)) returning * into r;
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata) values(actor,d.patient_id,'engine_decision_reviewed',jsonb_build_object('decision_id',d.id,'review_id',r.id,'verdict',p_verdict));
 return to_jsonb(r);
end$$;

create or replace function private.reda_clinic_inbox(p_status text default 'unresolved',p_code text default 'all',p_offset integer default 0) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();result jsonb;begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='Behandlarinloggning med MFA krävs.';end if;
 if p_status is null or p_status not in ('unresolved','open','acknowledged','resolved') or p_code is null or p_code not in ('all','changed_symptoms','changed_environment','requested_contact','execution_help') or p_offset is null or p_offset<0 or p_offset>100000 then raise exception using errcode='22023',message='Ogiltigt filter eller sidnummer.';end if;
 with owned as materialized (
  select c.*,p.display_name,p.status patient_status from public.reda_review_cases c join public.reda_patients p on p.id=c.patient_id where private.reda_owns_patient(p.id)
 ), filtered as materialized (
  select * from owned where (case when p_status='unresolved' then status<>'resolved' else status=p_status end) and (p_code='all' or code=p_code)
 ), page as (
  select * from filtered order by case code when 'changed_symptoms' then 0 when 'changed_environment' then 1 when 'requested_contact' then 2 else 3 end,created_at,id limit 25 offset p_offset
 )
 select jsonb_build_object('total',(select count(*) from filtered),'offset',p_offset,'limit',25,
 'counts',(select jsonb_build_object('open',count(*) filter(where status='open'),'acknowledged',count(*) filter(where status='acknowledged'),'resolved',count(*) filter(where status='resolved')) from owned),
 'cases',coalesce((select jsonb_agg(jsonb_build_object('id',pg.id,'patient_id',pg.patient_id,'display_name',pg.display_name,'patient_status',pg.patient_status,'code',pg.code,'status',pg.status,'created_at',pg.created_at,'handling_note',pg.handling_note,'plan_id',pg.plan_id,'response',jsonb_build_object('plan_version',r.plan_version,'answers',r.answers)) order by case pg.code when 'changed_symptoms' then 0 when 'changed_environment' then 1 when 'requested_contact' then 2 else 3 end,pg.created_at,pg.id) from page pg join public.reda_training_responses r on r.id=pg.response_id),'[]'::jsonb),
 'reviews',(select jsonb_build_object('agree',count(*) filter(where r.verdict='agree'),'disagree',count(*) filter(where r.verdict='disagree'),'uncertain',count(*) filter(where r.verdict='uncertain')) from public.reda_decision_reviews r join public.reda_patients p on p.id=r.patient_id where private.reda_owns_patient(p.id))
 ) into result;
 return result;
end$$;

-- Activation remains closed at the server, including the legacy service endpoint.
create or replace function public.reda_activate_plan_internal(p_plan_id uuid,p_actor_id uuid) returns void language plpgsql security invoker set search_path='' as $$
begin raise exception using errcode='42501',message='Patientaktivering är inte öppnad.';end$$;
-- Edge passes the original authenticated user through this narrow RPC. A live
-- session is checked inside the same transaction, before the service-only writer.
create function private.reda_sync_session(p_client_session_id uuid,p_plan_id uuid,p_status text,p_started_at timestamptz,p_completed_at timestamptz,p_payload jsonb) returns uuid language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();pid uuid;begin
 select patient_id into pid from public.reda_plans where id=p_plan_id;
 perform private.reda_lock_patient_context(pid);
 if not private.reda_is_own_patient(pid) then raise exception using errcode='42501',message='Planen är inte tillgänglig.';end if;
 return private.reda_save_session_internal(actor,p_client_session_id,p_plan_id,p_status,p_started_at,p_completed_at,p_payload);
end$$;
create function public.reda_sync_session(p_client_session_id uuid,p_plan_id uuid,p_status text,p_started_at timestamptz,p_completed_at timestamptz,p_payload jsonb) returns uuid language sql security invoker set search_path='' as $$select private.reda_sync_session(p_client_session_id,p_plan_id,p_status,p_started_at,p_completed_at,p_payload)$$;
revoke all on function private.reda_sync_session(uuid,uuid,text,timestamptz,timestamptz,jsonb),public.reda_sync_session(uuid,uuid,text,timestamptz,timestamptz,jsonb) from public,anon,authenticated;
grant execute on function private.reda_sync_session(uuid,uuid,text,timestamptz,timestamptz,jsonb),public.reda_sync_session(uuid,uuid,text,timestamptz,timestamptz,jsonb) to authenticated;

