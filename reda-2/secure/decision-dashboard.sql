-- Managed migration source. Clinician work queue; patient rollout flags are unchanged.
create table private.reda_followups (
 patient_id uuid primary key references public.reda_patients(id),
 clinician_id uuid not null references auth.users(id),
 due_date date not null,
 status text not null check(status in ('waiting','completed')),
 note text not null check(length(note) between 5 and 1000),
 completed_at timestamptz,
 updated_at timestamptz not null default now(),
 foreign key(patient_id,clinician_id) references public.reda_patients(id,clinician_id)
);
create index reda_followups_clinician on private.reda_followups(clinician_id);
create table private.reda_clinic_action_receipts (
 request_id uuid primary key,
 patient_id uuid not null references public.reda_patients(id),
 clinician_id uuid not null references auth.users(id),
 input jsonb not null,
 result jsonb not null,
 created_at timestamptz not null default now(),
 foreign key(patient_id,clinician_id) references public.reda_patients(id,clinician_id)
);
create index reda_clinic_receipts_patient_date on private.reda_clinic_action_receipts(patient_id,created_at desc,request_id);
create index reda_clinic_receipts_clinician on private.reda_clinic_action_receipts(clinician_id);
alter table private.reda_followups enable row level security;
alter table private.reda_clinic_action_receipts enable row level security;
revoke all on private.reda_followups,private.reda_clinic_action_receipts from public,anon,authenticated;
-- Explicit deny: only the checked definer RPCs below may access these tables.
create policy "rpc only" on private.reda_followups for all to authenticated using(false) with check(false);
create policy "rpc only" on private.reda_clinic_action_receipts for all to authenticated using(false) with check(false);
create index if not exists reda_dashboard_sessions on public.reda_sessions(patient_id,started_at desc,id);
create index if not exists reda_dashboard_responses on public.reda_training_responses(patient_id,created_at desc,id);
create index if not exists reda_dashboard_decisions on public.reda_engine_decisions(patient_id,created_at desc,id);
create index if not exists reda_dashboard_cases on public.reda_review_cases(patient_id,created_at,id) where status<>'resolved';

create function private.reda_safe_date(p text) returns date language plpgsql immutable set search_path='' as $$
begin if p !~ '^20[0-9]{2}-[0-9]{2}-[0-9]{2}$' then return null;end if;return p::date;exception when others then return null;end$$;

-- Indexed lateral reads keep patient rows bounded; names/evidence leave the database only for one page.
create function private.reda_dashboard_rows(p_actor uuid,p_org uuid,p_patient uuid default null)
returns table(patient_id uuid,display_name text,patient_status text,connected boolean,plan_id uuid,plan_version integer,
 last_session timestamptz,last_response timestamptz,open_count bigint,pending_count bigint,codes text[],first_case timestamptz,
 decision_id uuid,decision_code text,decision_action text,decision_applied boolean,decision_reviewed boolean,
 followup_date date,followup_status text,followup_note text,review_date date,missing_response boolean,quiet boolean)
language sql stable security invoker set search_path='' as $$
 select p.id,p.display_name,p.status,p.auth_user_id is not null,pl.id,pl.version,s.started_at,r.created_at,
 c.open_count,c.pending_count,c.codes,c.first_case,d.id,d.code,d.action,d.applied,dr.id is not null,
 f.due_date,f.status,f.note,
 (select min(private.reda_safe_date(cp->>'date')) from jsonb_array_elements(case when jsonb_typeof(pl.payload->'careJourney'->'checkpoints')='array' then pl.payload->'careJourney'->'checkpoints' else jsonb_build_array(jsonb_build_object('date',pl.payload->>'reviewDate')) end)cp where private.reda_safe_date(cp->>'date')>coalesce((f.completed_at at time zone 'Europe/Stockholm')::date,'1900-01-01'::date)),
 coalesce(s.status in ('completed','partial') and s.plan_id=pl.id and s.completed_at<(date_trunc('day',now() at time zone 'Europe/Stockholm') at time zone 'Europe/Stockholm') and s.completed_at>now()-interval '14 days' and s.completed_at>coalesce(f.completed_at,'1900-01-01'::timestamptz) and not exists(select 1 from public.reda_training_responses tr where tr.session_id=s.id),false),
 coalesce(pl.id is not null and greatest(s.started_at,pl.activated_at)<now()-interval '7 days' and greatest(s.started_at,pl.activated_at)>coalesce(f.completed_at,'1900-01-01'::timestamptz),false)
 from public.reda_patients p
 left join public.reda_plans pl on pl.patient_id=p.id and pl.status='active'
 left join lateral(select rs.* from public.reda_sessions rs where rs.patient_id=p.id order by rs.started_at desc,rs.id desc limit 1)s on true
 left join lateral(select tr.created_at from public.reda_training_responses tr where tr.patient_id=p.id order by tr.created_at desc,tr.id desc limit 1)r on true
 left join lateral(select count(*) filter(where rc.status='open') open_count,count(*) pending_count,array_agg(distinct rc.code) codes,min(rc.created_at) first_case from public.reda_review_cases rc where rc.patient_id=p.id and rc.status<>'resolved')c on true
 left join lateral(select ed.* from public.reda_engine_decisions ed where ed.patient_id=p.id order by ed.created_at desc,ed.id desc limit 1)d on true
 left join public.reda_decision_reviews dr on dr.decision_id=d.id
 left join private.reda_followups f on f.patient_id=p.id
 where p.organization_id=p_org and p.clinician_id=p_actor and (p_patient is null or p.id=p_patient)
$$;

create function private.reda_dashboard(p_search text default '',p_filter text default 'priority',p_offset integer default 0) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();org uuid:=private.reda_request_organization();result jsonb;today date:=(now() at time zone 'Europe/Stockholm')::date;begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='Behandlarinloggning med MFA krävs.';end if;
 if p_search is null or length(p_search)>100 or p_filter is null or p_filter not in ('priority','waiting','active','all','archived','no_plan') or p_offset is null or p_offset<0 or p_offset>100000 then raise exception using errcode='22023',message='Kontrollera sökning och filter.';end if;
 with base as materialized(select r.*,
  (open_count>0 or (followup_status='waiting' and followup_date<=today) or
   (coalesce(followup_status,'')<>'waiting' and (pending_count>0 or (patient_status='active' and (review_date<=today or missing_response or quiet or (decision_action in ('advance','complete','review') and not decision_applied and not decision_reviewed)))))) is true needs_review
  from private.reda_dashboard_rows(actor,org)r),
 filtered as materialized(select * from base where strpos(lower(display_name),lower(trim(p_search)))>0 and case p_filter
  when 'priority' then needs_review when 'waiting' then followup_status='waiting' and not needs_review
  when 'active' then patient_status='active' and plan_id is not null when 'archived' then patient_status='archived'
  when 'no_plan' then patient_status='active' and plan_id is null else true end),
 page as(select * from filtered order by needs_review desc,
  case when open_count>0 and codes&&array['changed_symptoms','changed_environment'] then 0 when open_count>0 then 1 when followup_date<=today then 2 else 3 end,
  coalesce(first_case,followup_date::timestamptz,review_date::timestamptz,'infinity'::timestamptz),lower(display_name),patient_id limit 25 offset p_offset)
 select jsonb_build_object('today',today,'total',(select count(*) from filtered),'offset',p_offset,'limit',25,
  'counts',(select jsonb_build_object('all',count(*),'active',count(*) filter(where patient_status='active' and plan_id is not null),'priority',count(*) filter(where needs_review),'waiting',count(*) filter(where followup_status='waiting' and not needs_review),'no_plan',count(*) filter(where patient_status='active' and plan_id is null),'archived',count(*) filter(where patient_status='archived'))from base),
  'patients',coalesce((select jsonb_agg(to_jsonb(page)) from page),'[]'::jsonb)) into result;
 return result;
end$$;

-- A snapshot binds the review to exact evidence, including case status and follow-up changes.
-- All writers of sessions/responses/decisions/cases already lock this patient first.
create function private.reda_dashboard_snapshot(p_patient uuid) returns jsonb
language plpgsql stable security invoker set search_path='' as $$
declare result jsonb;begin
 select jsonb_build_object('patient',jsonb_build_object('id',p.id,'status',p.status,'updated_at',p.updated_at),
 'plan',(select to_jsonb(pl) from public.reda_plans pl where pl.patient_id=p.id and pl.status='active'),
 'session_count',(select count(*) from public.reda_sessions s where s.patient_id=p.id),
 'session_updated',(select max(s.updated_at) from public.reda_sessions s where s.patient_id=p.id),
 'response_count',(select count(*) from public.reda_training_responses r where r.patient_id=p.id),
 'response_latest',(select r.id from public.reda_training_responses r where r.patient_id=p.id order by r.created_at desc,r.id desc limit 1),
 'cases',coalesce((select jsonb_agg(jsonb_build_object('id',c.id,'code',c.code,'status',c.status,'updated_at',c.updated_at,'plan_id',c.plan_id,'response_id',c.response_id) order by c.created_at,c.id) from public.reda_review_cases c where c.patient_id=p.id and c.status<>'resolved'),'[]'::jsonb),
 'decision',(select to_jsonb(d) from public.reda_engine_decisions d where d.patient_id=p.id order by d.created_at desc,d.id desc limit 1),
 'review_count',(select count(*) from public.reda_decision_reviews r where r.patient_id=p.id),
 'frame',(select to_jsonb(f) from public.reda_progression_frames f where f.patient_id=p.id and f.status='approved'),
 'followup',(select to_jsonb(f) from private.reda_followups f where f.patient_id=p.id)) into result from public.reda_patients p where p.id=p_patient;
 return result;
end$$;

create function private.reda_dashboard_patient(p_patient_id uuid) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();snap jsonb;result jsonb;begin
 if not private.reda_owns_patient(p_patient_id) then raise exception using errcode='42501',message='Patienten är inte tillgänglig i arbetsytan.';end if;
 snap=private.reda_dashboard_snapshot(p_patient_id);
 select jsonb_build_object('patient',to_jsonb(r),'token',md5(snap::text),'today',(now() at time zone 'Europe/Stockholm')::date,
 'plan',case when snap->'plan'='null'::jsonb then null else jsonb_build_object('id',snap->'plan'->'id','version',snap->'plan'->'version','goal',snap->'plan'->'payload'->'goal','exercises',snap->'plan'->'payload'->'exercises') end,
 'cases',coalesce((select jsonb_agg(jsonb_build_object('id',c.id,'code',c.code,'status',c.status,'created_at',c.created_at,'plan_version',tr.plan_version,'answers',tr.answers) order by c.created_at,c.id) from public.reda_review_cases c join public.reda_training_responses tr on tr.id=c.response_id where c.patient_id=p_patient_id and c.status<>'resolved'),'[]'::jsonb),
 'prepared_frame',snap->'plan'->'payload'->'progressionDraft',
 'decision',snap->'decision','frame',case when snap->'frame'='null'::jsonb then null else jsonb_build_object('execution',snap->'frame'->'execution','current_step',snap->'frame'->'current_step','policy',snap->'frame'->'policy') end,
 'history',coalesce((select jsonb_agg(h.result||jsonb_build_object('created_at',h.created_at) order by h.created_at desc,h.request_id)from(select cr.result,cr.created_at,cr.request_id from private.reda_clinic_action_receipts cr where cr.patient_id=p_patient_id order by cr.created_at desc,cr.request_id limit 10)h),'[]'::jsonb))into result
 from private.reda_dashboard_rows(actor,private.reda_request_organization(),p_patient_id)r;
 return result;
end$$;

create function private.reda_dashboard_act(p_patient_id uuid,p_token text,p_request_id uuid,p_action text,p_note text,p_due_date date default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();snap jsonb;submitted jsonb;receipt private.reda_clinic_action_receipts%rowtype;result jsonb;case_count integer:=0;today date:=(now() at time zone 'Europe/Stockholm')::date;engine_result jsonb;begin
 perform private.reda_lock_clinical_patient(p_patient_id);
 perform 1 from public.reda_patients where id=p_patient_id and private.reda_owns_patient(id) for update;
 if not found then raise exception using errcode='42501',message='Patienten är inte tillgänglig.';end if;
 if p_request_id is null or p_token is null or p_action is null or p_action not in ('follow_up','complete_follow_up','resolve_cases','review_agree','review_disagree','review_uncertain','approve_frame','evaluate') or coalesce(length(trim(p_note)),0) not between 5 and 1000 then raise exception using errcode='22023',message='Kontrollera åtgärd och bedömning (5–1 000 tecken).';end if;
 submitted=jsonb_build_object('token',p_token,'action',p_action,'note',trim(p_note),'due_date',p_due_date);
 select * into receipt from private.reda_clinic_action_receipts where request_id=p_request_id;
 if receipt.request_id is not null then
  if receipt.patient_id=p_patient_id and receipt.clinician_id=actor and receipt.input=submitted then return receipt.result;end if;
  raise exception using errcode='23505',message='Förfrågan har redan använts för en annan åtgärd.';
 end if;
 if (p_action='follow_up' and (p_due_date is null or p_due_date<today or p_due_date>today+90)) or (p_action<>'follow_up' and p_due_date is not null) then raise exception using errcode='22023',message='Uppföljningsdatum ska vara idag eller inom 90 dagar.';end if;
 snap=private.reda_dashboard_snapshot(p_patient_id);
 if md5(snap::text)<>p_token then raise exception using errcode='40001',message='Underlaget har ändrats. Läs det nya förslaget innan du godkänner.';end if;
 if p_action='follow_up' then
  insert into private.reda_followups(patient_id,clinician_id,due_date,status,note)values(p_patient_id,actor,p_due_date,'waiting',trim(p_note))
  on conflict(patient_id)do update set due_date=excluded.due_date,status='waiting',note=excluded.note,updated_at=now();
  update public.reda_review_cases set status='acknowledged',handled_by=actor,handling_note=trim(p_note),updated_at=now() where patient_id=p_patient_id and status='open';
  get diagnostics case_count=row_count;
 elsif p_action='approve_frame' then
  if snap->'frame'<>'null'::jsonb then raise exception using errcode='22023',message='Det finns redan en godkänd ram. Granska den under Ordination.';end if;
  engine_result=private.reda_approve_frame((snap->'plan'->>'id')::uuid,snap->'plan'->'payload'->'progressionDraft','shadow');
 elsif p_action='evaluate' then
  engine_result=private.reda_evaluate_progression(p_patient_id,p_request_id);
 elsif p_action='complete_follow_up' then
  update private.reda_followups set status='completed',note=trim(p_note),completed_at=now(),updated_at=now() where patient_id=p_patient_id and status='waiting';
  if not found then raise exception using errcode='22023',message='Det finns ingen pågående uppföljning att avsluta.';end if;
 elsif p_action='resolve_cases' then
  update public.reda_review_cases set status='resolved',handled_by=actor,handling_note=trim(p_note),updated_at=now() where patient_id=p_patient_id and status<>'resolved';
  get diagnostics case_count=row_count;
  if case_count=0 then raise exception using errcode='22023',message='Det finns inga öppna signaler att avsluta.';end if;
  update private.reda_followups set status='completed',note=trim(p_note),completed_at=now(),updated_at=now() where patient_id=p_patient_id and status='waiting';
 else
  if snap->'decision'='null'::jsonb then raise exception using errcode='22023',message='Det finns ingen EI-prövning att bedöma.';end if;
  perform private.reda_review_decision((snap->'decision'->>'id')::uuid,substring(p_action from 8),trim(p_note));
 end if;
 result=jsonb_build_object('request_id',p_request_id,'action',p_action,'note',trim(p_note),'due_date',p_due_date,'case_count',case_count,'plan_changed',coalesce((engine_result->>'applied')::boolean,false),'message_sent',false,'engine_result',engine_result);
 insert into private.reda_clinic_action_receipts(request_id,patient_id,clinician_id,input,result)values(p_request_id,p_patient_id,actor,submitted,result);
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata)values(actor,p_patient_id,'clinic_action_approved',jsonb_build_object('request_id',p_request_id,'action',p_action,'evidence_token',p_token,'case_count',case_count));
 return result;
end$$;

create function public.reda_dashboard(p_search text default '',p_filter text default 'priority',p_offset integer default 0) returns jsonb language sql security invoker set search_path='' as $$select private.reda_dashboard(p_search,p_filter,p_offset)$$;
create function public.reda_dashboard_patient(p_patient_id uuid) returns jsonb language sql security invoker set search_path='' as $$select private.reda_dashboard_patient(p_patient_id)$$;
create function public.reda_dashboard_act(p_patient_id uuid,p_token text,p_request_id uuid,p_action text,p_note text,p_due_date date default null) returns jsonb language sql security invoker set search_path='' as $$select private.reda_dashboard_act(p_patient_id,p_token,p_request_id,p_action,p_note,p_due_date)$$;
revoke all on function private.reda_safe_date(text),private.reda_dashboard_rows(uuid,uuid,uuid),private.reda_dashboard_snapshot(uuid) from public,anon,authenticated;
revoke all on function private.reda_dashboard(text,text,integer),public.reda_dashboard(text,text,integer),private.reda_dashboard_patient(uuid),public.reda_dashboard_patient(uuid),private.reda_dashboard_act(uuid,text,uuid,text,text,date),public.reda_dashboard_act(uuid,text,uuid,text,text,date) from public,anon,authenticated;
grant execute on function private.reda_dashboard(text,text,integer),public.reda_dashboard(text,text,integer),private.reda_dashboard_patient(uuid),public.reda_dashboard_patient(uuid),private.reda_dashboard_act(uuid,text,uuid,text,text,date),public.reda_dashboard_act(uuid,text,uuid,text,text,date) to authenticated;
