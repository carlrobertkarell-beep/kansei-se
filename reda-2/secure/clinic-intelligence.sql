-- Managed migration source. No change to activation or AI feature flags.
create or replace function private.reda_validate_frame(p jsonb) returns boolean
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
  if st?'rationale' and (jsonb_typeof(st->'rationale') is distinct from 'string' or length(st->>'rationale')>500) then return false;end if;
  for x in select value from jsonb_array_elements(st->'plan'->'exercises') loop
   if coalesce(length(x->>'id'),0)=0 or coalesce(length(x->>'variantId'),0)=0 or x->>'side' not in ('left','right','both','simultaneous') or x->>'side' is null then return false;end if;
   if x?'prescribedRange' and (jsonb_typeof(x->'prescribedRange') is distinct from 'string' or length(x->>'prescribedRange')>160) then return false;end if;
   foreach k in array array['sets','reps','hold','rest','tempo'] loop
    if jsonb_typeof(x->'dose'->k) is distinct from 'number' then return false;end if;n=(x->'dose'->>k)::numeric;
    if n<>trunc(n) or n<(case when k in ('hold','rest') then 0 else 1 end) or n>(case k when 'sets' then 8 when 'reps' then 100 when 'hold' then 180 when 'rest' then 600 else 60 end) then return false;end if;
   end loop;
  end loop;
  if previous is not null and (select jsonb_agg(jsonb_build_object('id',e->'id','variantId',e->'variantId','side',e->'side','dose',(e->'dose')-'label','load',e->'prescribedLoad','range',e->'prescribedRange')) from jsonb_array_elements(previous->'exercises') e)=(select jsonb_agg(jsonb_build_object('id',e->'id','variantId',e->'variantId','side',e->'side','dose',(e->'dose')-'label','load',e->'prescribedLoad','range',e->'prescribedRange')) from jsonb_array_elements(st->'plan'->'exercises') e) then return false;end if;
  previous=st->'plan';
 end loop;return true;
exception when others then return false;end$$;

create or replace function private.reda_dialogue_context(p_plan_id uuid,p_consume boolean default false) returns jsonb language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();p public.reda_plans%rowtype;enabled boolean;bucket_name text;n int;slim jsonb;begin
 select rp.* into p from public.reda_plans rp join public.reda_patients pt on pt.id=rp.patient_id where rp.id=p_plan_id and rp.status='active' and pt.status='active' and pt.auth_user_id=actor;
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

-- Immutable clinician judgments, separate from motor authority and case resolution.
create table public.reda_decision_reviews(
 id uuid primary key default gen_random_uuid(),
 decision_id uuid not null unique references public.reda_engine_decisions(id),
 patient_id uuid not null references public.reda_patients(id),
 clinician_id uuid not null references auth.users(id),
 verdict text not null check(verdict in ('agree','disagree','uncertain')),
 note text not null check(length(trim(note)) between 5 and 1000),
 created_at timestamptz not null default now()
);
create index reda_decision_reviews_patient on public.reda_decision_reviews(patient_id);
create index reda_decision_reviews_clinician on public.reda_decision_reviews(clinician_id);
alter table public.reda_decision_reviews enable row level security;
revoke all on public.reda_decision_reviews from public,anon,authenticated;
grant select on public.reda_decision_reviews to authenticated;
create function private.reda_review_reader() returns boolean language plpgsql stable security definer set search_path='' as $$begin
 perform private.reda_live_actor();return private.reda_is_clinician_aal2();exception when insufficient_privilege then return false;end$$;
revoke all on function private.reda_review_reader() from public,anon,authenticated;
grant execute on function private.reda_review_reader() to authenticated;
create policy "clinician review read" on public.reda_decision_reviews for select to authenticated
 using((select private.reda_review_reader()) and private.reda_owns_patient(patient_id));

create function private.reda_review_decision(p_decision_id uuid,p_verdict text,p_note text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor(); d public.reda_engine_decisions%rowtype;r public.reda_decision_reviews%rowtype;begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='Behandlarinloggning med MFA krävs.';end if;
 select * into d from public.reda_engine_decisions where id=p_decision_id;
 perform 1 from public.reda_patients where id=d.patient_id and clinician_id=actor for update;
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
create function public.reda_review_decision(p_decision_id uuid,p_verdict text,p_note text) returns jsonb language sql security invoker set search_path='' as $$select private.reda_review_decision(p_decision_id,p_verdict,p_note)$$;
revoke all on function private.reda_review_decision(uuid,text,text),public.reda_review_decision(uuid,text,text) from public,anon,authenticated;
grant execute on function private.reda_review_decision(uuid,text,text),public.reda_review_decision(uuid,text,text) to authenticated;

-- The inbox spans this clinician's patients, including archived patients with unresolved cases.
-- Only the visible page contains names and answer data; counts cover the full owned set.
create function private.reda_clinic_inbox(p_status text default 'unresolved',p_code text default 'all',p_offset integer default 0) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();result jsonb;begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='Behandlarinloggning med MFA krävs.';end if;
 if p_status is null or p_status not in ('unresolved','open','acknowledged','resolved') or p_code is null or p_code not in ('all','changed_symptoms','changed_environment','requested_contact','execution_help') or p_offset is null or p_offset<0 or p_offset>100000 then raise exception using errcode='22023',message='Ogiltigt filter eller sidnummer.';end if;
 with owned as materialized (
  select c.*,p.display_name,p.status patient_status from public.reda_review_cases c join public.reda_patients p on p.id=c.patient_id where p.clinician_id=actor
 ), filtered as materialized (
  select * from owned where (case when p_status='unresolved' then status<>'resolved' else status=p_status end) and (p_code='all' or code=p_code)
 ), page as (
  select * from filtered order by case code when 'changed_symptoms' then 0 when 'changed_environment' then 1 when 'requested_contact' then 2 else 3 end,created_at,id limit 25 offset p_offset
 )
 select jsonb_build_object('total',(select count(*) from filtered),'offset',p_offset,'limit',25,
 'counts',(select jsonb_build_object('open',count(*) filter(where status='open'),'acknowledged',count(*) filter(where status='acknowledged'),'resolved',count(*) filter(where status='resolved')) from owned),
 'cases',coalesce((select jsonb_agg(jsonb_build_object('id',pg.id,'patient_id',pg.patient_id,'display_name',pg.display_name,'patient_status',pg.patient_status,'code',pg.code,'status',pg.status,'created_at',pg.created_at,'handling_note',pg.handling_note,'plan_id',pg.plan_id,'response',jsonb_build_object('plan_version',r.plan_version,'answers',r.answers)) order by case pg.code when 'changed_symptoms' then 0 when 'changed_environment' then 1 when 'requested_contact' then 2 else 3 end,pg.created_at,pg.id) from page pg join public.reda_training_responses r on r.id=pg.response_id),'[]'::jsonb),
 'reviews',(select jsonb_build_object('agree',count(*) filter(where r.verdict='agree'),'disagree',count(*) filter(where r.verdict='disagree'),'uncertain',count(*) filter(where r.verdict='uncertain')) from public.reda_decision_reviews r join public.reda_patients p on p.id=r.patient_id where p.clinician_id=actor)
 ) into result;
 return result;
end$$;
create function public.reda_clinic_inbox(p_status text default 'unresolved',p_code text default 'all',p_offset integer default 0) returns jsonb language sql security invoker set search_path='' as $$select private.reda_clinic_inbox(p_status,p_code,p_offset)$$;
revoke all on function private.reda_clinic_inbox(text,text,integer),public.reda_clinic_inbox(text,text,integer) from public,anon,authenticated;
grant execute on function private.reda_clinic_inbox(text,text,integer),public.reda_clinic_inbox(text,text,integer) to authenticated;
