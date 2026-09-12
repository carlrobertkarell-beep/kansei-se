-- Source-bound exercise explanations and patient-reported understanding.
-- No plan mutation, external message, clinical approval or rollout change.
create table public.reda_exercise_help(
 id uuid primary key default gen_random_uuid(),request_id uuid not null unique,
 patient_id uuid not null references public.reda_patients(id),
 session_id uuid not null references public.reda_sessions(id),
 plan_id uuid not null references public.reda_plans(id),plan_version integer not null,
 exercise_id text not null,exercise_name text not null,exercise jsonb not null,
 option_label text not null,topics jsonb not null,outcome text not null check(outcome in ('clear','needs_help')),
 note text not null,help_version integer not null,input jsonb not null,
 created_at timestamptz not null default now()
);
create index reda_exercise_help_patient_time on public.reda_exercise_help(patient_id,created_at desc,id);
create index reda_exercise_help_session on public.reda_exercise_help(session_id);
create index reda_exercise_help_plan on public.reda_exercise_help(plan_id);
alter table public.reda_exercise_help enable row level security;
revoke all on public.reda_exercise_help from public,anon,authenticated;
grant select on public.reda_exercise_help to authenticated;
create policy "own or assigned exercise help read" on public.reda_exercise_help for select to authenticated
 using(private.reda_is_own_patient(patient_id) or private.reda_owns_patient(patient_id));
alter table public.reda_review_cases add column exercise_help_id uuid references public.reda_exercise_help(id);
alter table public.reda_review_cases drop constraint reda_case_one_source;
alter table public.reda_review_cases add constraint reda_case_one_source check(num_nonnulls(response_id,reflection_id,checkin_id,exercise_help_id)=1);
create unique index reda_case_exercise_help on public.reda_review_cases(exercise_help_id);

create function private.reda_submit_exercise_help(p_client_session_id uuid,p_exercise_id text,p_request_id uuid,p_answers jsonb)returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();s public.reda_sessions%rowtype;p public.reda_plans%rowtype;
 saved public.reda_exercise_help%rowtype;old public.reda_exercise_help%rowtype;xs jsonb;x jsonb;o jsonb;label text:='Ordinarie pass';case_id uuid;
begin
 select * into s from public.reda_sessions where client_session_id=p_client_session_id and private.reda_is_own_patient(patient_id);
 if s.id is null then raise exception using errcode='42501',message='Passet är inte tillgängligt. Synka passet och försök igen.';end if;
 perform private.reda_lock_patient_context(s.patient_id);
 perform 1 from public.reda_patients where id=s.patient_id and private.reda_is_own_patient(id)for update;
 if not found then raise exception using errcode='42501',message='Patientkontot är inte tillgängligt.';end if;
 select * into s from public.reda_sessions where id=s.id for update;
 if p_request_id is null or coalesce(length(p_exercise_id),0)not between 1 and 100 or jsonb_typeof(p_answers)is distinct from 'object' then raise exception using errcode='22023',message='Kontrollera din fråga.';end if;
 if not p_answers?&array['topics','outcome','note','version'] or (select count(*)from jsonb_object_keys(p_answers))<>4
 or p_answers->'version' is distinct from '1'::jsonb or jsonb_typeof(p_answers->'topics')is distinct from 'array'
 or jsonb_typeof(p_answers->'note')is distinct from 'string' or length(p_answers->>'note')>500
 or p_answers->>'outcome' is null or p_answers->>'outcome' not in ('clear','needs_help')
 then raise exception using errcode='22023',message='Välj vilken hjälp du behöver och om förklaringen blev tydlig.';end if;
 if jsonb_array_length(p_answers->'topics')not between 1 and 5
 or exists(select 1 from jsonb_array_elements(p_answers->'topics')t where jsonb_typeof(t)is distinct from 'string' or t#>>'{}'not in ('setup','execution','side','range','dose'))
 or (select count(distinct t)from jsonb_array_elements(p_answers->'topics')t)<>jsonb_array_length(p_answers->'topics')
 or (p_answers->>'outcome'='clear' and p_answers->>'note'<>'') then raise exception using errcode='22023',message='Kontrollera frågorna som förklaringen gäller.';end if;
 select * into old from public.reda_exercise_help where request_id=p_request_id;
 if found then
  if old.patient_id=s.patient_id and old.session_id=s.id and old.exercise_id=p_exercise_id and old.input=p_answers then return jsonb_build_object('id',old.id,'outcome',old.outcome,'created_at',old.created_at);end if;
  raise exception using errcode='23505',message='Begäran hör till en tidigare återkoppling.';
 end if;
 if s.completed_at is not null or s.status not in ('started','partial') then raise exception using errcode='40001',message='Passet är avslutat. Din tidigare återkoppling finns kvar i historiken.';end if;
 select * into p from public.reda_plans where id=s.plan_id and patient_id=s.patient_id and version=s.plan_version and status<>'draft';
 if p.id is null then raise exception using errcode='40001',message='Passets planversion kunde inte bekräftas.';end if;
 xs=p.payload->'exercises';
 if s.payload->>'optionId' is not null then
  if not private.reda_options_valid(p.payload) then raise exception using errcode='40001',message='Passets alternativ kunde inte bekräftas.';end if;
  select value into o from jsonb_array_elements(p.payload->'planOptions'->'items')where value->>'id'=s.payload->>'optionId';
  if o is null then raise exception using errcode='40001',message='Passets alternativ kunde inte hittas.';end if;
  xs=o->'exercises';label=o->>'label';
 end if;
 if (select count(*)from jsonb_array_elements(xs)e where e->>'id'=p_exercise_id)<>1
 or not exists(select 1 from jsonb_array_elements(s.payload->'exercises')e where e->>'exerciseId'=p_exercise_id)
 then raise exception using errcode='22023',message='Övningen ingår inte i det här passet.';end if;
 select value into x from jsonb_array_elements(xs)where value->>'id'=p_exercise_id;
 if (select count(*)from public.reda_exercise_help where patient_id=s.patient_id and created_at>now()-interval '24 hours')>=30 then raise exception using errcode='54000',message='Dina tidigare frågor är sparade. Använd klinikens kontaktuppgifter om du behöver mer hjälp idag.';end if;
 insert into public.reda_exercise_help(request_id,patient_id,session_id,plan_id,plan_version,exercise_id,exercise_name,exercise,option_label,topics,outcome,note,help_version,input)
 values(p_request_id,s.patient_id,s.id,p.id,p.version,p_exercise_id,coalesce(x->>'name',p_exercise_id),x,label,p_answers->'topics',p_answers->>'outcome',trim(p_answers->>'note'),1,p_answers)returning * into saved;
 if saved.outcome='needs_help' then
  insert into public.reda_review_cases(patient_id,plan_id,exercise_help_id,code)values(s.patient_id,p.id,saved.id,'execution_help')returning id into case_id;
 end if;
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata)values(actor,s.patient_id,'exercise_help_saved',jsonb_build_object('help_id',saved.id,'plan_id',p.id,'case_id',case_id,'outcome',saved.outcome,'help_version',1,'plan_changed',false));
 return jsonb_build_object('id',saved.id,'outcome',saved.outcome,'created_at',saved.created_at);
end$$;
create function public.reda_submit_exercise_help(p_client_session_id uuid,p_exercise_id text,p_request_id uuid,p_answers jsonb)returns jsonb language sql security invoker set search_path='' as $$select private.reda_submit_exercise_help(p_client_session_id,p_exercise_id,p_request_id,p_answers)$$;
revoke all on function private.reda_submit_exercise_help(uuid,text,uuid,jsonb),public.reda_submit_exercise_help(uuid,text,uuid,jsonb)from public,anon,authenticated;
grant execute on function private.reda_submit_exercise_help(uuid,text,uuid,jsonb),public.reda_submit_exercise_help(uuid,text,uuid,jsonb)to authenticated;

-- A new answer makes a previous clinical approval snapshot stale.
alter function private.reda_dashboard_snapshot(uuid)rename to reda_dashboard_snapshot_before_exercise_help;
revoke all on function private.reda_dashboard_snapshot_before_exercise_help(uuid)from public,anon,authenticated;
create function private.reda_dashboard_snapshot(p_patient uuid)returns jsonb language sql stable security invoker set search_path='' as $$
 select private.reda_dashboard_snapshot_before_exercise_help(p_patient)||jsonb_build_object('exercise_help',(select jsonb_build_object('id',id,'created_at',created_at)from public.reda_exercise_help where patient_id=p_patient order by created_at desc,id desc limit 1))
$$;
revoke all on function private.reda_dashboard_snapshot(uuid)from public,anon,authenticated;

-- Bounded enrichment after the existing authorization and pagination have run.
create function private.reda_with_exercise_help(cases jsonb)returns jsonb language sql stable security invoker set search_path='' as $$
 select coalesce(jsonb_agg(c||case when h.id is null then '{}'::jsonb else jsonb_build_object('exercise_help',to_jsonb(h)-'input'-'request_id','plan_version',h.plan_version)end order by n),'[]'::jsonb)
 from jsonb_array_elements(cases)with ordinality as rows(c,n)
 left join public.reda_review_cases rc on rc.id=(c->>'id')::uuid left join public.reda_exercise_help h on h.id=rc.exercise_help_id
$$;
revoke all on function private.reda_with_exercise_help(jsonb)from public,anon,authenticated;
alter function private.reda_dashboard_patient(uuid)rename to reda_dashboard_patient_before_exercise_help;
revoke all on function private.reda_dashboard_patient_before_exercise_help(uuid)from public,anon,authenticated;
create function private.reda_dashboard_patient(p_patient_id uuid)returns jsonb language plpgsql stable security definer set search_path='' as $$
declare r jsonb;begin
 r=private.reda_dashboard_patient_before_exercise_help(p_patient_id);
 return jsonb_set(r,'{cases}',private.reda_with_exercise_help(r->'cases'));
end$$;
revoke all on function private.reda_dashboard_patient(uuid)from public,anon,authenticated;
grant execute on function private.reda_dashboard_patient(uuid)to authenticated;
create or replace function public.reda_dashboard_patient(p_patient_id uuid)returns jsonb language sql stable security invoker set search_path='' as $$select private.reda_dashboard_patient(p_patient_id)$$;
alter function private.reda_clinic_inbox(text,text,integer)rename to reda_clinic_inbox_before_exercise_help;
revoke all on function private.reda_clinic_inbox_before_exercise_help(text,text,integer)from public,anon,authenticated;
create function private.reda_clinic_inbox(p_status text default 'unresolved',p_code text default 'all',p_offset integer default 0)returns jsonb language plpgsql stable security definer set search_path='' as $$
declare r jsonb;begin
 r=private.reda_clinic_inbox_before_exercise_help(p_status,p_code,p_offset);
 return jsonb_set(r,'{cases}',private.reda_with_exercise_help(r->'cases'));
end$$;
revoke all on function private.reda_clinic_inbox(text,text,integer)from public,anon,authenticated;
grant execute on function private.reda_clinic_inbox(text,text,integer)to authenticated;
create or replace function public.reda_clinic_inbox(p_status text default 'unresolved',p_code text default 'all',p_offset integer default 0)returns jsonb language sql stable security invoker set search_path='' as $$select private.reda_clinic_inbox(p_status,p_code,p_offset)$$;

-- Same date filters, cursor ordering and audience boundaries as the existing timeline.
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
 union all select 'exercise-help:'||id,created_at,'feedback',case outcome when 'clear' then 'Övningsinstruktionen upplevs tydlig' else 'Hjälp med övning efterfrågad' end,exercise_name||' · '||case outcome when 'clear' then 'Patientens egen återkoppling efter förklaringen' else 'Övning och öppnade förklaringar följer med till kliniken' end,plan_id,plan_version from public.reda_exercise_help where patient_id=p_patient_id
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
