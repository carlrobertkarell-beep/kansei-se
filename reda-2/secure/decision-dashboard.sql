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

-- Clinician-reviewed communication stays inside Reda. No email/SMS delivery.
create table private.reda_clinic_messages(
 id uuid primary key,
 patient_id uuid not null references public.reda_patients(id),
 author_id uuid not null references auth.users(id),
 kind text not null check(kind in ('clinician','patient')),
 body text not null check(length(trim(body)) between 5 and 1000),
 reply_to uuid,
 created_at timestamptz not null default now(),
 handled_at timestamptz,
 handling_note text,
 unique(id,patient_id),
 foreign key(reply_to,patient_id) references private.reda_clinic_messages(id,patient_id),
 check((kind='patient' and reply_to is not null)or(kind='clinician' and reply_to is null))
);
create unique index reda_message_one_reply on private.reda_clinic_messages(reply_to)where kind='patient';
create index reda_messages_patient_created on private.reda_clinic_messages(patient_id,created_at desc,id);
create index reda_messages_author on private.reda_clinic_messages(author_id);
alter table private.reda_clinic_messages enable row level security;
revoke all on private.reda_clinic_messages from public,anon,authenticated;
create policy "rpc only" on private.reda_clinic_messages for all to authenticated using(false)with check(false);

-- Indexed lateral reads keep patient rows bounded; names/evidence leave the database only for one page.
create function private.reda_dashboard_rows(p_actor uuid,p_org uuid,p_patient uuid default null)
returns table(patient_id uuid,display_name text,patient_status text,connected boolean,plan_id uuid,plan_version integer,
 last_session timestamptz,last_response timestamptz,open_count bigint,pending_count bigint,codes text[],first_case timestamptz,
 decision_id uuid,decision_code text,decision_action text,decision_applied boolean,decision_reviewed boolean,
 followup_date date,followup_status text,followup_note text,review_date date,missing_response boolean,quiet boolean,pending_messages bigint,new_reply boolean)
language sql stable security invoker set search_path='' as $$
 select p.id,p.display_name,p.status,p.auth_user_id is not null,pl.id,pl.version,s.started_at,r.created_at,
 c.open_count,c.pending_count,c.codes,c.first_case,d.id,d.code,d.action,d.applied,dr.id is not null,
 f.due_date,f.status,f.note,
 (select min(private.reda_safe_date(cp->>'date')) from jsonb_array_elements(case when jsonb_typeof(pl.payload->'careJourney'->'checkpoints')='array' then pl.payload->'careJourney'->'checkpoints' else jsonb_build_array(jsonb_build_object('date',pl.payload->>'reviewDate')) end)cp where private.reda_safe_date(cp->>'date')>coalesce((f.completed_at at time zone 'Europe/Stockholm')::date,'1900-01-01'::date)),
 coalesce(s.status in ('completed','partial') and s.plan_id=pl.id and s.completed_at<(date_trunc('day',now() at time zone 'Europe/Stockholm') at time zone 'Europe/Stockholm') and s.completed_at>now()-interval '14 days' and s.completed_at>coalesce(f.completed_at,'1900-01-01'::timestamptz) and not exists(select 1 from public.reda_training_responses tr where tr.session_id=s.id),false),
 coalesce(pl.id is not null and greatest(s.started_at,pl.activated_at)<now()-interval '7 days' and greatest(s.started_at,pl.activated_at)>coalesce(f.completed_at,'1900-01-01'::timestamptz),false),
 (select count(*) from private.reda_clinic_messages cm where cm.patient_id=p.id and cm.handled_at is null),
 exists(select 1 from private.reda_clinic_messages cm where cm.patient_id=p.id and cm.kind='patient' and cm.handled_at is null and cm.created_at>coalesce(f.updated_at,'1900-01-01'::timestamptz))
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
  (open_count>0 or new_reply or (followup_status='waiting' and followup_date<=today) or
   (coalesce(followup_status,'')<>'waiting' and (pending_count>0 or pending_messages>0 or (patient_status='active' and (review_date<=today or missing_response or quiet or (decision_action in ('advance','complete','review') and not decision_applied and not decision_reviewed)))))) is true needs_review
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
 'messages',coalesce((select jsonb_agg(jsonb_build_object('id',cm.id,'handled_at',cm.handled_at) order by cm.created_at,cm.id)from private.reda_clinic_messages cm where cm.patient_id=p.id),'[]'::jsonb),
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
 'messages',coalesce((select jsonb_agg(jsonb_build_object('id',cm.id,'kind',cm.kind,'body',cm.body,'reply_to',cm.reply_to,'created_at',cm.created_at,'handled_at',cm.handled_at)order by cm.created_at,cm.id)from private.reda_clinic_messages cm where cm.patient_id=p_patient_id and (cm.handled_at is null or cm.id in (select x.id from private.reda_clinic_messages x where x.patient_id=p_patient_id order by x.created_at desc,x.id desc limit 20))),'[]'::jsonb),
 'history',coalesce((select jsonb_agg(h.result||jsonb_build_object('created_at',h.created_at) order by h.created_at desc,h.request_id)from(select cr.result,cr.created_at,cr.request_id from private.reda_clinic_action_receipts cr where cr.patient_id=p_patient_id order by cr.created_at desc,cr.request_id limit 10)h),'[]'::jsonb))into result
 from private.reda_dashboard_rows(actor,private.reda_request_organization(),p_patient_id)r;
 return result;
end$$;

create function private.reda_dashboard_act(p_patient_id uuid,p_token text,p_request_id uuid,p_action text,p_note text,p_due_date date default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();snap jsonb;submitted jsonb;receipt private.reda_clinic_action_receipts%rowtype;result jsonb;case_count integer:=0;message_count integer:=0;today date:=(now() at time zone 'Europe/Stockholm')::date;engine_result jsonb;begin
 perform private.reda_lock_clinical_patient(p_patient_id);
 perform 1 from public.reda_patients where id=p_patient_id and private.reda_owns_patient(id) for update;
 if not found then raise exception using errcode='42501',message='Patienten är inte tillgänglig.';end if;
 if p_request_id is null or p_token is null or p_action is null or p_action not in ('follow_up','complete_follow_up','resolve_cases','review_agree','review_disagree','review_uncertain','approve_frame','evaluate','send_message') or coalesce(length(trim(p_note)),0) not between 5 and 1000 then raise exception using errcode='22023',message='Kontrollera åtgärd och bedömning (5–1 000 tecken).';end if;
 submitted=jsonb_build_object('token',p_token,'action',p_action,'note',trim(p_note),'due_date',p_due_date);
 select * into receipt from private.reda_clinic_action_receipts where request_id=p_request_id;
 if receipt.request_id is not null then
  if receipt.patient_id=p_patient_id and receipt.clinician_id=actor and receipt.input=submitted then return receipt.result;end if;
  raise exception using errcode='23505',message='Förfrågan har redan använts för en annan åtgärd.';
 end if;
 if (p_action in ('follow_up','send_message') and (p_due_date is null or p_due_date<today or p_due_date>today+90)) or (p_action not in ('follow_up','send_message') and p_due_date is not null) then raise exception using errcode='22023',message='Uppföljningsdatum ska vara idag eller inom 90 dagar.';end if;
 snap=private.reda_dashboard_snapshot(p_patient_id);
 if md5(snap::text)<>p_token then raise exception using errcode='40001',message='Underlaget har ändrats. Läs det nya förslaget innan du godkänner.';end if;
 if p_action in ('follow_up','send_message') then
  if p_action='send_message' then
   if not exists(select 1 from public.reda_patients pt where pt.id=p_patient_id and pt.status='active' and pt.auth_user_id is not null)then raise exception using errcode='42501',message='Meddelanden kan bara skickas till en redan ansluten aktiv patient.';end if;
   insert into private.reda_clinic_messages(id,patient_id,author_id,kind,body)values(p_request_id,p_patient_id,actor,'clinician',trim(p_note));
  end if;
  insert into private.reda_followups(patient_id,clinician_id,due_date,status,note)values(p_patient_id,actor,p_due_date,'waiting',case when p_action='send_message' then 'Följ upp svaret på meddelandet i Reda.' else trim(p_note) end)
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
  update private.reda_clinic_messages set handled_at=now(),handling_note=trim(p_note)where patient_id=p_patient_id and handled_at is null;
  get diagnostics message_count=row_count;
  if case_count=0 and message_count=0 then raise exception using errcode='22023',message='Det finns inga öppna signaler eller meddelanden att avsluta.';end if;
  update private.reda_followups set status='completed',note=trim(p_note),completed_at=now(),updated_at=now() where patient_id=p_patient_id and status='waiting';
 else
  if snap->'decision'='null'::jsonb then raise exception using errcode='22023',message='Det finns ingen EI-prövning att bedöma.';end if;
  perform private.reda_review_decision((snap->'decision'->>'id')::uuid,substring(p_action from 8),trim(p_note));
 end if;
 result=jsonb_build_object('request_id',p_request_id,'action',p_action,'note',trim(p_note),'due_date',p_due_date,'case_count',case_count,'plan_changed',coalesce((engine_result->>'applied')::boolean,false),'message_sent',p_action='send_message','message_count',message_count,'engine_result',engine_result);
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

create function private.reda_patient_messages() returns jsonb language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();pid uuid;result jsonb;begin
 select p.id into pid from public.reda_patients p where private.reda_is_own_patient(p.id);
 if pid is null then raise exception using errcode='42501',message='Logga in med ditt patientkonto.';end if;
 select jsonb_build_object('patient_id',pid,'messages',coalesce((select jsonb_agg(to_jsonb(m)order by m.created_at,m.id)from(select cm.id,cm.kind,cm.body,cm.reply_to,cm.created_at,cm.handled_at from private.reda_clinic_messages cm where cm.patient_id=pid order by cm.created_at desc,cm.id desc limit 20)m),'[]'::jsonb),
 'reply_to',(select cm.id from private.reda_clinic_messages cm where cm.patient_id=pid and cm.kind='clinician' and cm.handled_at is null and not exists(select 1 from private.reda_clinic_messages r where r.reply_to=cm.id) and not exists(select 1 from private.reda_clinic_messages x where x.patient_id=pid and x.kind='clinician' and (x.created_at,x.id)>(cm.created_at,cm.id))order by cm.created_at desc,cm.id desc limit 1))into result;
 return result;
end$$;
create function private.reda_patient_reply(p_message_id uuid,p_request_id uuid,p_body text)returns jsonb language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();m private.reda_clinic_messages%rowtype;existing private.reda_clinic_messages%rowtype;begin
 select * into m from private.reda_clinic_messages where id=p_message_id and kind='clinician';
 perform private.reda_lock_patient_context(m.patient_id);
 perform 1 from public.reda_patients where id=m.patient_id and private.reda_is_own_patient(id)for update;
 if not found then raise exception using errcode='42501',message='Meddelandet är inte tillgängligt.';end if;
 if p_request_id is null or coalesce(length(trim(p_body)),0)not between 5 and 1000 then raise exception using errcode='22023',message='Skriv ett svar på 5–1 000 tecken.';end if;
 select * into existing from private.reda_clinic_messages where id=p_request_id;
 if existing.id is not null then
  if existing.author_id=actor and existing.reply_to=p_message_id and existing.body=trim(p_body)then return jsonb_build_object('id',existing.id,'sent',true);end if;
  raise exception using errcode='23505',message='Förfrågan har redan använts. Uppdatera meddelandena.';
 end if;
 select * into m from private.reda_clinic_messages where id=p_message_id;
 if m.handled_at is not null or exists(select 1 from private.reda_clinic_messages cm where cm.reply_to=m.id)or exists(select 1 from private.reda_clinic_messages cm where cm.patient_id=m.patient_id and cm.kind='clinician' and (cm.created_at,cm.id)>(m.created_at,m.id))then raise exception using errcode='40001',message='Meddelandena har ändrats. Uppdatera och läs det senaste innan du svarar.';end if;
 insert into private.reda_clinic_messages(id,patient_id,author_id,kind,body,reply_to)values(p_request_id,m.patient_id,actor,'patient',trim(p_body),m.id);
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata)values(actor,m.patient_id,'patient_message_replied',jsonb_build_object('message_id',p_request_id,'reply_to',m.id));
 return jsonb_build_object('id',p_request_id,'sent',true);
end$$;
create function public.reda_patient_messages()returns jsonb language sql security invoker set search_path='' as $$select private.reda_patient_messages()$$;
create function public.reda_patient_reply(p_message_id uuid,p_request_id uuid,p_body text)returns jsonb language sql security invoker set search_path='' as $$select private.reda_patient_reply(p_message_id,p_request_id,p_body)$$;
revoke all on function private.reda_patient_messages(),public.reda_patient_messages(),private.reda_patient_reply(uuid,uuid,text),public.reda_patient_reply(uuid,uuid,text)from public,anon,authenticated;
grant execute on function private.reda_patient_messages(),public.reda_patient_messages(),private.reda_patient_reply(uuid,uuid,text),public.reda_patient_reply(uuid,uuid,text)to authenticated;

-- Same engine and locks; an unresolved conversation also blocks progression.
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
