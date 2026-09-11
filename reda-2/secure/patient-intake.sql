-- Reviewed patient intake. No invitations, bookings or external API calls.
create table private.reda_patient_profiles(
 patient_id uuid primary key references public.reda_patients(id),
 email text not null default '', phone text not null default '',
 focus text not null default '',goal text not null default '',handover text not null default '',
 next_contact date,source text not null default 'manual',external_id text not null default '',
 revision integer not null default 1,updated_at timestamptz not null default now()
);
create table private.reda_patient_intake_receipts(
 request_id uuid primary key,patient_id uuid not null references public.reda_patients(id),
 actor_id uuid not null references auth.users(id),input jsonb not null,result jsonb not null,
 created_at timestamptz not null default now()
);
create index reda_intake_receipt_patient on private.reda_patient_intake_receipts(patient_id);
create index reda_intake_receipt_actor on private.reda_patient_intake_receipts(actor_id);
alter table private.reda_patient_profiles enable row level security;
alter table private.reda_patient_intake_receipts enable row level security;
revoke all on private.reda_patient_profiles,private.reda_patient_intake_receipts from public,anon,authenticated;
create policy "rpc only" on private.reda_patient_profiles for all to authenticated using(false)with check(false);
create policy "rpc only" on private.reda_patient_intake_receipts for all to authenticated using(false)with check(false);

create function private.reda_contact_phone(p text)returns text language sql immutable set search_path='' as $$
 select regexp_replace(regexp_replace(regexp_replace(trim(p),'[^0-9+]','','g'),'^00','+'),'^0','+46')
$$;
create function private.reda_intake_validate(p jsonb)returns jsonb language plpgsql immutable set search_path='' as $$
declare k text;v text;r jsonb:='{}';maximum integer;begin
 if jsonb_typeof(p) is distinct from 'object' or exists(select 1 from jsonb_object_keys(p)x where x not in ('name','email','phone','focus','goal','handover','next_contact','source','external_id'))then raise exception using errcode='22023',message='Kontrollera patientuppgifterna.';end if;
 foreach k in array array['name','email','phone','focus','goal','handover','next_contact','source','external_id']loop
  if p?k and jsonb_typeof(p->k) not in ('string','null')then raise exception using errcode='22023',message='Patientuppgifter ska vara text.';end if;
  v:=trim(coalesce(p->>k,''));maximum:=case k when 'name'then 120 when 'email'then 254 when 'phone'then 40 when 'focus'then 120 when 'goal'then 240 when 'handover'then 240 when 'next_contact'then 10 when 'source'then 20 else 100 end;
  if length(v)>maximum then raise exception using errcode='22023',message='En patientuppgift är för lång.';end if;
  if k='email'then v:=lower(v);end if;if k='source'and v=''then v:='manual';end if;
  r:=r||jsonb_build_object(k,v);
 end loop;
 if length(r->>'name')<2 or (r->>'email'<>''and r->>'email'!~'^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$')or(r->>'phone'<>''and private.reda_contact_phone(r->>'phone')!~'^\+?[0-9]{7,15}$')or(r->>'next_contact'<>''and private.reda_safe_date(r->>'next_contact')is null)or r->>'source'not in ('manual','bokadirekt','easypractice','other')then raise exception using errcode='22023',message='Kontrollera namn, e-post, telefon och datum.';end if;
 if r->>'source'='manual'and r->>'external_id'<>''then raise exception using errcode='22023',message='Ange källsystem för ett externt kund-ID.';end if;
 return r;
end$$;

-- Only assigned patients are searched; another clinician's records never leak via duplicates.
create function private.reda_intake_matches(p jsonb,p_exclude uuid default null)returns jsonb language sql stable set search_path='' as $$
 select coalesce(jsonb_agg(to_jsonb(m) order by m.exact_source desc,m.display_name,m.patient_id),'[]'::jsonb)from(
 select pt.id patient_id,pt.display_name,pt.status patient_status,pt.auth_user_id is not null connected,
 pr.email,pr.phone,pt.updated_at,coalesce(pr.revision,0)revision,
 coalesce(p->>'external_id'<>''and pr.source=p->>'source'and pr.external_id=p->>'external_id',false)exact_source
 from public.reda_patients pt left join private.reda_patient_profiles pr on pr.patient_id=pt.id
 where pt.organization_id=private.reda_request_organization()and pt.clinician_id=private.reda_live_actor()and(p_exclude is null or pt.id<>p_exclude)
 and(lower(trim(pt.display_name))=lower(p->>'name')or(p->>'email'<>''and pr.email=p->>'email')or(p->>'phone'<>''and private.reda_contact_phone(pr.phone)=private.reda_contact_phone(p->>'phone'))or(p->>'external_id'<>''and pr.source=p->>'source'and pr.external_id=p->>'external_id'))
 order by exact_source desc,pt.display_name,pt.id limit 25)m
$$;

create function private.reda_patient_profile(p_patient_id uuid)returns jsonb language plpgsql stable security definer set search_path='' as $$
declare r jsonb;begin
 if not private.reda_owns_patient(p_patient_id)then raise exception using errcode='42501',message='Patienten är inte tillgänglig.';end if;
 select coalesce(to_jsonb(pr)-'patient_id','{}')||jsonb_build_object('patient_id',p.id,'name',p.display_name,'revision',coalesce(pr.revision,0))into r from public.reda_patients p left join private.reda_patient_profiles pr on pr.patient_id=p.id where p.id=p_patient_id;return r;
end$$;

create function private.reda_save_patient_profile(p_patient_id uuid,p_request_id uuid,p_profile jsonb,p_revision integer default 0,p_duplicate_token text default null)returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();org uuid:=private.reda_request_organization();p jsonb;matches jsonb;input jsonb;receipt private.reda_patient_intake_receipts%rowtype;pid uuid:=p_patient_id;result jsonb;rev integer;begin
 if not private.reda_is_clinician_aal2()then raise exception using errcode='42501',message='Behandlarinloggning med MFA krävs.';end if;
 perform 1 from public.reda_organizations where id=org for share;
 if not private.reda_is_clinician_aal2()then raise exception using errcode='42501',message='Arbetsytan är inte tillgänglig.';end if;
 -- Serialize intake writes per clinician and organization, before taking a patient lock.
 perform pg_advisory_xact_lock(hashtextextended(org::text||actor::text,17));
 if p_request_id is null or p_revision is null or p_revision<0 then raise exception using errcode='22023',message='Uppdatera formuläret och försök igen.';end if;
 p:=private.reda_intake_validate(p_profile);
 input:=jsonb_build_object('patient_id',p_patient_id,'profile',p,'revision',p_revision,'duplicate_token',p_duplicate_token);
 select * into receipt from private.reda_patient_intake_receipts where request_id=p_request_id;
 if found then
  if receipt.actor_id<>actor or not private.reda_owns_patient(receipt.patient_id)or receipt.input<>input then raise exception using errcode='23505',message='Begäran har redan använts.';end if;
  return receipt.result;
 end if;
 if pid is not null then
  perform private.reda_lock_clinical_patient(pid);perform 1 from public.reda_patients where id=pid and private.reda_owns_patient(id)for update;
  if not found then raise exception using errcode='42501',message='Patienten är inte tillgänglig.';end if;
  select revision into rev from private.reda_patient_profiles where patient_id=pid;
  if coalesce(rev,0)<>p_revision then raise exception using errcode='40001',message='Patientuppgifterna har ändrats. Öppna formuläret på nytt.';end if;
 end if;
 matches:=private.reda_intake_matches(p,pid);
 if jsonb_array_length(matches)>0 and(p_duplicate_token is distinct from md5((p||jsonb_build_object('matches',matches))::text)or exists(select 1 from jsonb_array_elements(matches)m where(m->>'exact_source')::boolean))then
  return jsonb_build_object('status','duplicates','matches',matches,'duplicate_token',md5((p||jsonb_build_object('matches',matches))::text));
 end if;
 if pid is null then
  insert into public.reda_patients(organization_id,clinician_id,display_name)values(org,actor,p->>'name')returning id into pid;
 else update public.reda_patients set display_name=p->>'name',updated_at=clock_timestamp()where id=pid;end if;
 insert into private.reda_patient_profiles(patient_id,email,phone,focus,goal,handover,next_contact,source,external_id)
 values(pid,p->>'email',p->>'phone',p->>'focus',p->>'goal',p->>'handover',private.reda_safe_date(p->>'next_contact'),p->>'source',p->>'external_id')
 on conflict(patient_id)do update set email=excluded.email,phone=excluded.phone,focus=excluded.focus,goal=excluded.goal,handover=excluded.handover,next_contact=excluded.next_contact,source=excluded.source,external_id=excluded.external_id,revision=reda_patient_profiles.revision+1,updated_at=clock_timestamp();
 select jsonb_build_object('status','saved','patient',jsonb_build_object('id',pt.id,'display_name',pt.display_name,'status',pt.status,'auth_user_id',case when pt.auth_user_id is not null then 'connected'else null end),'profile',private.reda_patient_profile(pid))into result from public.reda_patients pt where pt.id=pid;
 insert into private.reda_patient_intake_receipts(request_id,patient_id,actor_id,input,result)values(p_request_id,pid,actor,input,result);
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata)values(actor,pid,case when p_patient_id is null then 'patient_intake_created'else 'patient_profile_updated'end,jsonb_build_object('request_id',p_request_id,'source',p->>'source'));
 return result;
end$$;

-- Context and reported outcomes are fetched for the visible page only.
create function private.reda_patient_brief(pid uuid)returns jsonb language sql stable set search_path='' as $$
 select jsonb_build_object('profile',jsonb_build_object('focus',pr.focus,'goal',pr.goal,'handover',pr.handover,'next_contact',pr.next_contact,'has_contact',coalesce(pr.email<>''or pr.phone<>'',false),'source',pr.source),
 'care_goal',coalesce(nullif(pr.goal,''),pl.payload->>'goal'),'care_focus',coalesce(nullif(pr.focus,''),pl.payload->>'blueprintName'),
 'stage',pl.payload->'context'->>'stage','sessions_14d',(select count(*)from public.reda_sessions s where s.patient_id=pid and s.status in ('completed','partial')and s.started_at>=now()-interval '14 days'),
 'latest_report',(select jsonb_build_object('function',r.answers->'function','nextDay',r.answers->'nextDay','created_at',r.created_at,'plan_version',r.plan_version)from public.reda_training_responses r where r.patient_id=pid order by r.created_at desc,r.id desc limit 1),
 'draft_version',(select max(dp.version)from public.reda_plans dp where dp.patient_id=pid and dp.status='draft'))
 from public.reda_patients pt left join private.reda_patient_profiles pr on pr.patient_id=pt.id left join public.reda_plans pl on pl.patient_id=pt.id and pl.status='active'where pt.id=pid
$$;

create function public.reda_patient_profile(p_patient_id uuid)returns jsonb language sql security invoker set search_path=''as $$select private.reda_patient_profile(p_patient_id)$$;
create function public.reda_save_patient_profile(p_patient_id uuid,p_request_id uuid,p_profile jsonb,p_revision integer default 0,p_duplicate_token text default null)returns jsonb language sql security invoker set search_path=''as $$select private.reda_save_patient_profile(p_patient_id,p_request_id,p_profile,p_revision,p_duplicate_token)$$;
revoke all on function private.reda_contact_phone(text),private.reda_intake_validate(jsonb),private.reda_intake_matches(jsonb,uuid),private.reda_patient_brief(uuid)from public,anon,authenticated;
revoke all on function private.reda_patient_profile(uuid),public.reda_patient_profile(uuid),private.reda_save_patient_profile(uuid,uuid,jsonb,integer,text),public.reda_save_patient_profile(uuid,uuid,jsonb,integer,text)from public,anon,authenticated;
grant execute on function private.reda_patient_profile(uuid),public.reda_patient_profile(uuid),private.reda_save_patient_profile(uuid,uuid,jsonb,integer,text),public.reda_save_patient_profile(uuid,uuid,jsonb,integer,text)to authenticated;

create or replace function private.reda_dashboard_rows(p_actor uuid,p_org uuid,p_patient uuid default null)
returns table(patient_id uuid,display_name text,patient_status text,connected boolean,plan_id uuid,plan_version integer,
 last_session timestamptz,last_response timestamptz,open_count bigint,pending_count bigint,codes text[],first_case timestamptz,
 decision_id uuid,decision_code text,decision_action text,decision_applied boolean,decision_reviewed boolean,
 followup_date date,followup_status text,followup_note text,review_date date,missing_response boolean,quiet boolean,pending_messages bigint,new_reply boolean)
language sql stable security invoker set search_path='' as $$
 select p.id,p.display_name,p.status,p.auth_user_id is not null,pl.id,pl.version,s.started_at,r.created_at,
 c.open_count,c.pending_count,c.codes,c.first_case,d.id,d.code,d.action,d.applied,dr.id is not null,
 f.due_date,f.status,f.note,
 least((select min(private.reda_safe_date(cp->>'date')) from jsonb_array_elements(case when jsonb_typeof(pl.payload->'careJourney'->'checkpoints')='array' then pl.payload->'careJourney'->'checkpoints' else jsonb_build_array(jsonb_build_object('date',pl.payload->>'reviewDate')) end)cp where private.reda_safe_date(cp->>'date')>coalesce((f.completed_at at time zone 'Europe/Stockholm')::date,'1900-01-01'::date)),(select pr.next_contact from private.reda_patient_profiles pr where pr.patient_id=p.id and pr.next_contact>coalesce((f.completed_at at time zone 'Europe/Stockholm')::date,'1900-01-01'::date))),
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


create or replace function private.reda_dashboard(p_search text default '',p_filter text default 'priority',p_offset integer default 0) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();org uuid:=private.reda_request_organization();result jsonb;today date:=(now() at time zone 'Europe/Stockholm')::date;begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='Behandlarinloggning med MFA krävs.';end if;
 if p_search is null or length(p_search)>100 or p_filter is null or p_filter not in ('priority','waiting','active','all','archived','no_plan','upcoming') or p_offset is null or p_offset<0 or p_offset>100000 then raise exception using errcode='22023',message='Kontrollera sökning och filter.';end if;
 with base as materialized(select r.*,
  (open_count>0 or new_reply or (followup_status='waiting' and followup_date<=today) or
   (coalesce(followup_status,'')<>'waiting' and (pending_count>0 or pending_messages>0 or (patient_status='active' and (review_date<=today or missing_response or quiet or (decision_action in ('advance','complete','review') and not decision_applied and not decision_reviewed)))))) is true needs_review
  from private.reda_dashboard_rows(actor,org)r),
 filtered as materialized(select * from base where (strpos(lower(display_name),lower(trim(p_search)))>0 or exists(select 1 from public.reda_plans sp where sp.id=base.plan_id and strpos(lower(coalesce(sp.payload->>'blueprintName','')||' '||coalesce(sp.payload->>'goal','')),lower(trim(p_search)))>0) or exists(select 1 from private.reda_patient_profiles pr where pr.patient_id=base.patient_id and (strpos(lower(pr.email||' '||pr.phone||' '||pr.focus||' '||pr.goal||' '||pr.external_id),lower(trim(p_search)))>0 or (length(regexp_replace(p_search,'[^0-9]','','g'))>=4 and strpos(private.reda_contact_phone(pr.phone),regexp_replace(p_search,'[^0-9]','','g'))>0)))) and case p_filter
  when 'priority' then needs_review when 'waiting' then followup_status='waiting' and not needs_review
  when 'active' then patient_status='active' and plan_id is not null when 'archived' then patient_status='archived'
  when 'upcoming' then patient_status='active' and review_date>today when 'no_plan' then patient_status='active' and plan_id is null else true end),
 page as(select * from filtered order by needs_review desc,
  case when open_count>0 and codes&&array['changed_symptoms','changed_environment'] then 0 when open_count>0 then 1 when followup_date<=today then 2 else 3 end,
  coalesce(first_case,followup_date::timestamptz,review_date::timestamptz,'infinity'::timestamptz),lower(display_name),patient_id limit 25 offset p_offset)
 select jsonb_build_object('today',today,'total',(select count(*) from filtered),'offset',p_offset,'limit',25,
  'counts',(select jsonb_build_object('all',count(*),'active',count(*) filter(where patient_status='active' and plan_id is not null),'priority',count(*) filter(where needs_review),'waiting',count(*) filter(where followup_status='waiting' and not needs_review),'no_plan',count(*) filter(where patient_status='active' and plan_id is null),'upcoming',count(*) filter(where patient_status='active' and review_date>today),'archived',count(*) filter(where patient_status='archived'))from base),
  'patients',coalesce((select jsonb_agg(to_jsonb(page)||private.reda_patient_brief(page.patient_id)) from page),'[]'::jsonb)) into result;
 return result;
end$$;


create or replace function private.reda_dashboard_patient(p_patient_id uuid) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();snap jsonb;result jsonb;begin
 if not private.reda_owns_patient(p_patient_id) then raise exception using errcode='42501',message='Patienten är inte tillgänglig i arbetsytan.';end if;
 snap=private.reda_dashboard_snapshot(p_patient_id);
 select jsonb_build_object('patient',to_jsonb(r)||private.reda_patient_brief(r.patient_id),'contact',(select jsonb_build_object('email',pr.email,'phone',pr.phone)from private.reda_patient_profiles pr where pr.patient_id=r.patient_id),'token',md5(snap::text),'today',(now() at time zone 'Europe/Stockholm')::date,
 'plan',case when snap->'plan'='null'::jsonb then null else jsonb_build_object('id',snap->'plan'->'id','version',snap->'plan'->'version','goal',snap->'plan'->'payload'->'goal','exercises',snap->'plan'->'payload'->'exercises') end,
 'cases',coalesce((select jsonb_agg(jsonb_build_object('id',c.id,'code',c.code,'status',c.status,'created_at',c.created_at,'plan_version',tr.plan_version,'answers',tr.answers) order by c.created_at,c.id) from public.reda_review_cases c join public.reda_training_responses tr on tr.id=c.response_id where c.patient_id=p_patient_id and c.status<>'resolved'),'[]'::jsonb),
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
