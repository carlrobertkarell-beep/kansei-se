-- Immediate session experience. Distinct from next-day responses and progression evidence.
-- Additive migration; no rollout, invitation, payment or automation flag is changed.
create table public.reda_session_reflections(
 id uuid primary key default gen_random_uuid(),
 request_id uuid not null unique,
 session_id uuid not null unique references public.reda_sessions(id),
 patient_id uuid not null references public.reda_patients(id),
 plan_id uuid not null references public.reda_plans(id),
 plan_version integer not null,
 reported_by uuid not null references auth.users(id),
 answers jsonb not null,
 exercise_name text,
 created_at timestamptz not null default now()
);
create index reda_reflections_patient_created on public.reda_session_reflections(patient_id,created_at desc,id);
create index reda_reflections_plan on public.reda_session_reflections(plan_id);
create index reda_reflections_reporter on public.reda_session_reflections(reported_by);
alter table public.reda_session_reflections enable row level security;
revoke all on public.reda_session_reflections from public,anon,authenticated;
grant select on public.reda_session_reflections to authenticated;
create policy "own session reflection read" on public.reda_session_reflections for select to authenticated
 using(private.reda_is_own_patient(patient_id));
create policy "assigned clinician reflection read" on public.reda_session_reflections for select to authenticated
 using((select private.reda_is_clinician_aal2()) and private.reda_owns_patient(patient_id));

alter table public.reda_review_cases alter column response_id drop not null;
alter table public.reda_review_cases add column reflection_id uuid references public.reda_session_reflections(id);
alter table public.reda_review_cases add constraint reda_case_one_source check(num_nonnulls(response_id,reflection_id)=1);
create unique index reda_case_reflection on public.reda_review_cases(reflection_id) where reflection_id is not null;

create function private.reda_submit_session_reflection(p_session_id uuid,p_request_id uuid,p_answers jsonb)
returns jsonb language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();s public.reda_sessions%rowtype;existing public.reda_session_reflections%rowtype;
 saved public.reda_session_reflections%rowtype;reason text;exercise_label text;exercise_id text;
begin
 if p_session_id is null or p_request_id is null or p_answers is null or jsonb_typeof(p_answers)<>'object'
 then raise exception using errcode='22023',message='Kontrollera dina svar.';end if;
 perform private.reda_lock_patient_context((select patient_id from public.reda_sessions where id=p_session_id));
 select rs.* into s from public.reda_sessions rs
 join public.reda_plans p on p.id=rs.plan_id and p.patient_id=rs.patient_id and p.version=rs.plan_version
 where rs.id=p_session_id and private.reda_is_own_patient(rs.patient_id) for update of rs;
 if s.id is null then raise exception using errcode='42501',message='Passet är inte tillgängligt.';end if;
 if (select count(*) from jsonb_object_keys(p_answers))<>3 or p_answers->>'barrier' is null or p_answers->>'support' is null
 or p_answers->>'barrier' not in ('none','time','execution','equipment','symptoms','energy','other')
 or p_answers->>'support' not in ('no','yes') or not p_answers?'exerciseId'
 or jsonb_typeof(p_answers->'exerciseId') not in ('string','null')
 then raise exception using errcode='22023',message='Välj vad som fungerade och om du vill ha hjälp.';end if;
 exercise_id=p_answers->>'exerciseId';
 if exercise_id is not null then
  select x->>'name' into exercise_label from public.reda_plans p cross join lateral jsonb_array_elements(p.payload->'exercises') x where p.id=s.plan_id and x->>'id'=exercise_id;
  if exercise_label is null then raise exception using errcode='22023',message='Övningen hör inte till passets plan.';end if;
 end if;
 select * into existing from public.reda_session_reflections where request_id=p_request_id;
 if existing.id is not null then
  if existing.reported_by=actor and existing.session_id=s.id and existing.answers=p_answers then return to_jsonb(existing);end if;
  raise exception using errcode='23505',message='Begäran hör till ett annat svar.';
 end if;
 select * into existing from public.reda_session_reflections where session_id=s.id;
 if existing.id is not null then
  if existing.reported_by=actor and existing.answers=p_answers then return to_jsonb(existing);end if;
  raise exception using errcode='23505',message='Ett annat svar är redan sparat. Ladda om sidan för att läsa det.';
 end if;
 if s.status not in ('completed','partial') or s.completed_at is null or s.completed_at>now()
 or (s.completed_at at time zone 'Europe/Stockholm')::date<>(now() at time zone 'Europe/Stockholm')::date
 then raise exception using errcode='22023',message='De här frågorna gäller ett avslutat pass idag. Från nästa dag använder du uppföljningen.';end if;
 insert into public.reda_session_reflections(request_id,session_id,patient_id,plan_id,plan_version,reported_by,answers,exercise_name)
 values(p_request_id,s.id,s.patient_id,s.plan_id,s.plan_version,actor,p_answers,exercise_label) returning * into saved;
 reason=case p_answers->>'barrier' when 'symptoms' then 'changed_symptoms' when 'equipment' then 'changed_environment' when 'execution' then 'execution_help' when 'time' then 'training_barrier' when 'energy' then 'training_barrier' when 'other' then 'training_barrier' else case when p_answers->>'support'='yes' then 'requested_contact' end end;
 if reason is not null then insert into public.reda_review_cases(patient_id,plan_id,reflection_id,code) values(s.patient_id,s.plan_id,saved.id,reason);end if;
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata) values(actor,s.patient_id,'session_reflection_submitted',jsonb_build_object('reflection_id',saved.id,'session_id',s.id,'plan_id',s.plan_id,'plan_version',s.plan_version));
 return to_jsonb(saved);
end$$;
revoke all on function private.reda_submit_session_reflection(uuid,uuid,jsonb) from public,anon,authenticated;
grant execute on function private.reda_submit_session_reflection(uuid,uuid,jsonb) to authenticated;
create function public.reda_submit_session_reflection(p_session_id uuid,p_request_id uuid,p_answers jsonb)
returns jsonb language sql security invoker set search_path='' as $$select private.reda_submit_session_reflection(p_session_id,p_request_id,p_answers)$$;
revoke all on function public.reda_submit_session_reflection(uuid,uuid,jsonb) from public,anon,authenticated;
grant execute on function public.reda_submit_session_reflection(uuid,uuid,jsonb) to authenticated;

create or replace function private.reda_dashboard_patient(p_patient_id uuid) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();snap jsonb;result jsonb;begin
 if not private.reda_owns_patient(p_patient_id) then raise exception using errcode='42501',message='Patienten är inte tillgänglig i arbetsytan.';end if;
 snap=private.reda_dashboard_snapshot(p_patient_id);
 select jsonb_build_object('patient',to_jsonb(r)||private.reda_patient_brief(r.patient_id),'contact',(select jsonb_build_object('email',pr.email,'phone',pr.phone)from private.reda_patient_profiles pr where pr.patient_id=r.patient_id),'token',md5(snap::text),'today',(now() at time zone 'Europe/Stockholm')::date,
 'plan',case when snap->'plan'='null'::jsonb then null else jsonb_build_object('id',snap->'plan'->'id','version',snap->'plan'->'version','goal',snap->'plan'->'payload'->'goal','exercises',snap->'plan'->'payload'->'exercises') end,
 'cases',coalesce((select jsonb_agg(jsonb_build_object('id',c.id,'code',c.code,'status',c.status,'created_at',c.created_at,'plan_id',c.plan_id,'plan_version',coalesce(tr.plan_version,sr.plan_version),'answers',tr.answers,'reflection',case when sr.id is null then null else to_jsonb(sr) end) order by c.created_at,c.id) from public.reda_review_cases c left join public.reda_training_responses tr on tr.id=c.response_id left join public.reda_session_reflections sr on sr.id=c.reflection_id where c.patient_id=p_patient_id and c.status<>'resolved'),'[]'::jsonb),
 'prepared_frame',snap->'plan'->'payload'->'progressionDraft',
 'decision',snap->'decision','frame',case when snap->'frame'='null'::jsonb then null else jsonb_build_object('execution',snap->'frame'->'execution','current_step',snap->'frame'->'current_step','policy',snap->'frame'->'policy') end,
 'messages',coalesce((select jsonb_agg(jsonb_build_object('id',cm.id,'kind',cm.kind,'body',cm.body,'reply_to',cm.reply_to,'created_at',cm.created_at,'handled_at',cm.handled_at)order by cm.created_at,cm.id)from private.reda_clinic_messages cm where cm.patient_id=p_patient_id and (cm.handled_at is null or cm.id in (select x.id from private.reda_clinic_messages x where x.patient_id=p_patient_id order by x.created_at desc,x.id desc limit 20))),'[]'::jsonb),
 'history',coalesce((select jsonb_agg(h.result||jsonb_build_object('created_at',h.created_at) order by h.created_at desc,h.request_id)from(select cr.result,cr.created_at,cr.request_id from private.reda_clinic_action_receipts cr where cr.patient_id=p_patient_id order by cr.created_at desc,cr.request_id limit 10)h),'[]'::jsonb))into result
 from private.reda_dashboard_rows(actor,private.reda_request_organization(),p_patient_id)r;
 return result;
end$$;


create or replace function private.reda_dashboard_snapshot(p_patient uuid) returns jsonb
language plpgsql stable security invoker set search_path='' as $$
declare result jsonb;begin
 select jsonb_build_object('patient',jsonb_build_object('id',p.id,'status',p.status,'updated_at',p.updated_at),
 'profile',(select to_jsonb(pr)from private.reda_patient_profiles pr where pr.patient_id=p.id),
 'plan',(select to_jsonb(pl) from public.reda_plans pl where pl.patient_id=p.id and pl.status='active'),
 'session_count',(select count(*) from public.reda_sessions s where s.patient_id=p.id),
 'session_updated',(select max(s.updated_at) from public.reda_sessions s where s.patient_id=p.id),
 'reflection_count',(select count(*) from public.reda_session_reflections sr where sr.patient_id=p.id),
 'reflection_latest',(select sr.id from public.reda_session_reflections sr where sr.patient_id=p.id order by sr.created_at desc,sr.id desc limit 1),
 'response_count',(select count(*) from public.reda_training_responses r where r.patient_id=p.id),
 'response_latest',(select r.id from public.reda_training_responses r where r.patient_id=p.id order by r.created_at desc,r.id desc limit 1),
 'cases',coalesce((select jsonb_agg(jsonb_build_object('id',c.id,'code',c.code,'status',c.status,'updated_at',c.updated_at,'plan_id',c.plan_id,'response_id',c.response_id,'reflection_id',c.reflection_id) order by c.created_at,c.id) from public.reda_review_cases c where c.patient_id=p.id and c.status<>'resolved'),'[]'::jsonb),
 'decision',(select to_jsonb(d) from public.reda_engine_decisions d where d.patient_id=p.id order by d.created_at desc,d.id desc limit 1),
 'review_count',(select count(*) from public.reda_decision_reviews r where r.patient_id=p.id),
 'frame',(select to_jsonb(f) from public.reda_progression_frames f where f.patient_id=p.id and f.status='approved'),
 'messages',coalesce((select jsonb_agg(jsonb_build_object('id',cm.id,'handled_at',cm.handled_at) order by cm.created_at,cm.id)from private.reda_clinic_messages cm where cm.patient_id=p.id),'[]'::jsonb),
 'followup',(select to_jsonb(f) from private.reda_followups f where f.patient_id=p.id)) into result from public.reda_patients p where p.id=p_patient;
 return result;
end$$;

create or replace function private.reda_clinic_inbox(p_status text default 'unresolved',p_code text default 'all',p_offset integer default 0) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();result jsonb;begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='Behandlarinloggning med MFA krävs.';end if;
 if p_status is null or p_status not in ('unresolved','open','acknowledged','resolved') or p_code is null or p_code not in ('all','changed_symptoms','changed_environment','requested_contact','execution_help','training_barrier') or p_offset is null or p_offset<0 or p_offset>100000 then raise exception using errcode='22023',message='Ogiltigt filter eller sidnummer.';end if;
 with owned as materialized (
  select c.*,p.display_name,p.status patient_status from public.reda_review_cases c join public.reda_patients p on p.id=c.patient_id where private.reda_owns_patient(p.id)
 ), filtered as materialized (
  select * from owned where (case when p_status='unresolved' then status<>'resolved' else status=p_status end) and (p_code='all' or code=p_code)
 ), page as (
  select * from filtered order by case code when 'changed_symptoms' then 0 when 'changed_environment' then 1 when 'requested_contact' then 2 else 3 end,created_at,id limit 25 offset p_offset
 )
 select jsonb_build_object('total',(select count(*) from filtered),'offset',p_offset,'limit',25,
 'counts',(select jsonb_build_object('open',count(*) filter(where status='open'),'acknowledged',count(*) filter(where status='acknowledged'),'resolved',count(*) filter(where status='resolved')) from owned),
 'cases',coalesce((select jsonb_agg(jsonb_build_object('id',pg.id,'patient_id',pg.patient_id,'display_name',pg.display_name,'patient_status',pg.patient_status,'code',pg.code,'status',pg.status,'created_at',pg.created_at,'handling_note',pg.handling_note,'plan_id',pg.plan_id,'response',jsonb_build_object('plan_version',r.plan_version,'answers',r.answers),'reflection',case when sr.id is null then null else to_jsonb(sr) end) order by case pg.code when 'changed_symptoms' then 0 when 'changed_environment' then 1 when 'requested_contact' then 2 else 3 end,pg.created_at,pg.id) from page pg left join public.reda_training_responses r on r.id=pg.response_id left join public.reda_session_reflections sr on sr.id=pg.reflection_id),'[]'::jsonb),
 'reviews',(select jsonb_build_object('agree',count(*) filter(where r.verdict='agree'),'disagree',count(*) filter(where r.verdict='disagree'),'uncertain',count(*) filter(where r.verdict='uncertain')) from public.reda_decision_reviews r join public.reda_patients p on p.id=r.patient_id where private.reda_owns_patient(p.id))
 ) into result;
 return result;
end$$;

