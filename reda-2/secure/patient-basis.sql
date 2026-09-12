-- Patient-reported circumstances and goal ability. Immutable, source-bound reports.
create table public.reda_patient_checkins(
 id uuid primary key default gen_random_uuid(),request_id uuid not null unique,
 patient_id uuid not null references public.reda_patients(id),plan_id uuid not null references public.reda_plans(id),
 plan_version integer not null,goal text not null,focus text not null,goal_key text not null,
 answers jsonb not null,created_at timestamptz not null default now()
);
create index reda_checkins_patient_created on public.reda_patient_checkins(patient_id,created_at desc,id);
create index reda_checkins_goal on public.reda_patient_checkins(patient_id,goal_key,created_at desc,id);
create index reda_checkins_plan on public.reda_patient_checkins(plan_id);
alter table public.reda_patient_checkins enable row level security;
revoke all on public.reda_patient_checkins from public,anon,authenticated;
grant select on public.reda_patient_checkins to authenticated;
create policy "own or assigned checkin read" on public.reda_patient_checkins for select to authenticated using(private.reda_is_own_patient(patient_id) or private.reda_owns_patient(patient_id));
alter table public.reda_review_cases add column checkin_id uuid references public.reda_patient_checkins(id);
alter table public.reda_review_cases drop constraint reda_case_one_source;
alter table public.reda_review_cases add constraint reda_case_one_source check(num_nonnulls(response_id,reflection_id,checkin_id)=1);
create unique index reda_case_checkin on public.reda_review_cases(checkin_id);

create function private.reda_submit_checkin(p_plan_id uuid,p_request_id uuid,p_answers jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();p public.reda_plans%rowtype;old public.reda_patient_checkins%rowtype;saved public.reda_patient_checkins%rowtype;previous public.reda_patient_checkins%rowtype;f text;g text;reason text;baseline jsonb;
begin
 select * into p from public.reda_plans where id=p_plan_id;
 perform private.reda_lock_patient_context(p.patient_id);
 perform 1 from public.reda_patients where id=p.patient_id and private.reda_is_own_patient(id)for update;
 if not found then raise exception using errcode='42501',message='Planen är inte tillgänglig.';end if;
 -- Re-read after the patient lock: an activation may have committed while waiting.
 select * into p from public.reda_plans where id=p_plan_id;
 if p_request_id is null or jsonb_typeof(p_answers) is distinct from 'object' then raise exception using errcode='22023',message='Kontrollera dina svar.';end if;
 if (select count(*)from jsonb_object_keys(p_answers))<>5 or not p_answers?&array['ability','minutes','equipment','band','floorOK']
 or jsonb_typeof(p_answers->'ability') is distinct from 'number' or (p_answers->>'ability')::numeric not between 0 and 10 or (p_answers->>'ability')::numeric<>trunc((p_answers->>'ability')::numeric)
 or jsonb_typeof(p_answers->'minutes') is distinct from 'number' or p_answers->>'minutes' not in ('5','10','15','20','30','45','60')
 or p_answers->>'equipment' is null or p_answers->>'equipment' not in ('home','gym')
 or jsonb_typeof(p_answers->'band') is distinct from 'boolean' or jsonb_typeof(p_answers->'floorOK') is distinct from 'boolean'
 then raise exception using errcode='22023',message='Välj målskattning, tid och träningsförutsättningar.';end if;
 select * into old from public.reda_patient_checkins where request_id=p_request_id;
 if found then
  if old.patient_id=p.patient_id and old.plan_id=p.id and old.answers=p_answers then return to_jsonb(old);end if;
  raise exception using errcode='23505',message='Begäran hör till ett annat svar.';
 end if;
 if p.status<>'active' or coalesce(length(trim(p.payload->>'goal')),0)<2 then raise exception using errcode='40001',message='Ladda om den aktuella planen och kontrollera målet innan du svarar.';end if;
 if (select count(*)from public.reda_patient_checkins where patient_id=p.patient_id and created_at>now()-interval '24 hours')>=10 then raise exception using errcode='54000',message='Dina senaste svar är sparade. Vänta till nästa dag innan du lämnar fler.';end if;
 select coalesce(pr.focus,'')into f from private.reda_patient_profiles pr where pr.patient_id=p.patient_id;f=coalesce(f,'');
 g=md5(jsonb_build_object('goal',trim(p.payload->>'goal'),'focus',f,'blueprint',p.payload->'context'->'blueprintId','side',p.payload->'context'->'side')::text);
 select * into previous from public.reda_patient_checkins where patient_id=p.patient_id and goal_key=g order by created_at desc,id desc limit 1;
 baseline=coalesce(previous.answers,p.payload->'context','{}');
 insert into public.reda_patient_checkins(request_id,patient_id,plan_id,plan_version,goal,focus,goal_key,answers)
 values(p_request_id,p.patient_id,p.id,p.version,trim(p.payload->>'goal'),f,g,p_answers)returning * into saved;
 if previous.id is not null and (p_answers->>'ability')::int<(previous.answers->>'ability')::int then reason='changed_symptoms';
 elsif (baseline?'equipment' and baseline->>'equipment' is distinct from p_answers->>'equipment') or (baseline?'band' and baseline->'band' is distinct from p_answers->'band') or (baseline?'floorOK' and baseline->'floorOK' is distinct from p_answers->'floorOK') then reason='changed_environment';
 elsif previous.id is not null and (p_answers->>'minutes')::int<(previous.answers->>'minutes')::int then reason='training_barrier';end if;
 if reason is not null then insert into public.reda_review_cases(patient_id,plan_id,checkin_id,code)values(p.patient_id,p.id,saved.id,reason);end if;
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata)values(actor,p.patient_id,'patient_checkin_saved',jsonb_build_object('checkin_id',saved.id,'plan_id',p.id));
 return to_jsonb(saved);
end$$;
create function public.reda_submit_checkin(p_plan_id uuid,p_request_id uuid,p_answers jsonb)returns jsonb language sql security invoker set search_path='' as $$select private.reda_submit_checkin(p_plan_id,p_request_id,p_answers)$$;
revoke all on function private.reda_submit_checkin(uuid,uuid,jsonb),public.reda_submit_checkin(uuid,uuid,jsonb) from public,anon,authenticated;
grant execute on function private.reda_submit_checkin(uuid,uuid,jsonb),public.reda_submit_checkin(uuid,uuid,jsonb) to authenticated;

create function private.reda_patient_basis(p_patient_id uuid) returns jsonb
language plpgsql stable security invoker set search_path='' as $$
declare profile jsonb;p public.reda_plans%rowtype;latest public.reda_patient_checkins%rowtype;baseline public.reda_patient_checkins%rowtype;g text;f text;
begin
 select to_jsonb(pr)-'patient_id' into profile from private.reda_patient_profiles pr where patient_id=p_patient_id;
 select * into p from public.reda_plans where patient_id=p_patient_id and status='active';
 f=coalesce(profile->>'focus','');g=md5(jsonb_build_object('goal',trim(p.payload->>'goal'),'focus',f,'blueprint',p.payload->'context'->'blueprintId','side',p.payload->'context'->'side')::text);
 select * into latest from public.reda_patient_checkins where patient_id=p_patient_id and goal_key=g order by created_at desc,id desc limit 1;
 select * into baseline from public.reda_patient_checkins where patient_id=p_patient_id and goal_key=g order by created_at,id limit 1;
 return jsonb_build_object('profile',profile,'plan',case when p.id is null then null else jsonb_build_object('id',p.id,'version',p.version,'goal',p.payload->'goal','context',p.payload->'context','activated_at',p.activated_at)end,
 'latest',case when latest.id is null then null else to_jsonb(latest)end,'baseline',case when baseline.id is null then null else to_jsonb(baseline)end,
 'history',coalesce((select jsonb_agg(to_jsonb(h)order by created_at,id)from(select id,created_at,plan_version,answers from public.reda_patient_checkins where patient_id=p_patient_id and goal_key=g order by created_at desc,id desc limit 12)h),'[]'::jsonb));
end$$;
revoke all on function private.reda_patient_basis(uuid) from public,anon,authenticated;
create function private.reda_my_checkins(p_patient_id uuid)returns jsonb language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();b jsonb;begin
 if not private.reda_is_own_patient(p_patient_id) then raise exception using errcode='42501',message='Uppföljningen är inte tillgänglig.';end if;
 b=private.reda_patient_basis(p_patient_id);return b-'profile';
end$$;
create function public.reda_my_checkins(p_patient_id uuid)returns jsonb language sql stable security invoker set search_path='' as $$select private.reda_my_checkins(p_patient_id)$$;
revoke all on function private.reda_my_checkins(uuid),public.reda_my_checkins(uuid) from public,anon,authenticated;
grant execute on function private.reda_my_checkins(uuid),public.reda_my_checkins(uuid) to authenticated;

-- Every report, including neutral reports, invalidates an old clinical approval snapshot.
alter function private.reda_dashboard_snapshot(uuid) rename to reda_dashboard_snapshot_before_basis;
revoke all on function private.reda_dashboard_snapshot_before_basis(uuid) from public,anon,authenticated;
create function private.reda_dashboard_snapshot(p_patient uuid)returns jsonb language sql stable security invoker set search_path='' as $$
 select private.reda_dashboard_snapshot_before_basis(p_patient)||jsonb_build_object('checkin',(select jsonb_build_object('id',id,'created_at',created_at)from public.reda_patient_checkins where patient_id=p_patient order by created_at desc,id desc limit 1))
$$;
revoke all on function private.reda_dashboard_snapshot(uuid) from public,anon,authenticated;
alter function private.reda_dashboard_patient(uuid) rename to reda_dashboard_patient_before_basis;
revoke all on function private.reda_dashboard_patient_before_basis(uuid) from public,anon,authenticated;
create function private.reda_dashboard_patient(p_patient_id uuid)returns jsonb language plpgsql stable security definer set search_path='' as $$
declare r jsonb;begin
 r=private.reda_dashboard_patient_before_basis(p_patient_id);
 r=jsonb_set(r,'{cases}',coalesce((select jsonb_agg(c||case when k.id is null then '{}'::jsonb else jsonb_build_object('checkin',to_jsonb(k),'plan_version',k.plan_version)end order by n)
 from jsonb_array_elements(r->'cases')with ordinality as item(c,n)left join public.reda_review_cases rc on rc.id=(c->>'id')::uuid left join public.reda_patient_checkins k on k.id=rc.checkin_id),'[]'::jsonb));
 return r||jsonb_build_object('basis',private.reda_patient_basis(p_patient_id));
end$$;
revoke all on function private.reda_dashboard_patient(uuid) from public,anon,authenticated;
grant execute on function private.reda_dashboard_patient(uuid) to authenticated;
create or replace function public.reda_dashboard_patient(p_patient_id uuid)returns jsonb language sql stable security invoker set search_path='' as $$select private.reda_dashboard_patient(p_patient_id)$$;

-- Read-only timeline. No rollout flags or patient records are changed.
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
create or replace function public.reda_activity_log(p_patient_id uuid,p_category text default 'all',p_from date default null,p_to date default null,p_before_time timestamptz default null,p_before_key text default null)
returns jsonb language sql stable security invoker set search_path='' as $$select private.reda_activity_log(p_patient_id,p_category,p_from,p_to,p_before_time,p_before_key)$$;
revoke all on function public.reda_activity_log(uuid,text,date,date,timestamptz,text) from public,anon,authenticated;
grant execute on function public.reda_activity_log(uuid,text,date,date,timestamptz,text) to authenticated;

alter function private.reda_clinic_inbox(text,text,integer) rename to reda_clinic_inbox_before_basis;
revoke all on function private.reda_clinic_inbox_before_basis(text,text,integer) from public,anon,authenticated;
create function private.reda_clinic_inbox(p_status text default 'unresolved',p_code text default 'all',p_offset integer default 0)returns jsonb language plpgsql stable security definer set search_path='' as $$
declare r jsonb;begin
 r=private.reda_clinic_inbox_before_basis(p_status,p_code,p_offset);
 return jsonb_set(r,'{cases}',coalesce((select jsonb_agg(c||case when k.id is null then '{}'::jsonb else jsonb_build_object('checkin',to_jsonb(k))end order by n)from jsonb_array_elements(r->'cases')with ordinality as item(c,n)left join public.reda_review_cases rc on rc.id=(c->>'id')::uuid left join public.reda_patient_checkins k on k.id=rc.checkin_id),'[]'::jsonb));
end$$;
revoke all on function private.reda_clinic_inbox(text,text,integer) from public,anon,authenticated;
grant execute on function private.reda_clinic_inbox(text,text,integer) to authenticated;
create or replace function public.reda_clinic_inbox(p_status text default 'unresolved',p_code text default 'all',p_offset integer default 0)returns jsonb language sql stable security invoker set search_path='' as $$select private.reda_clinic_inbox(p_status,p_code,p_offset)$$;
