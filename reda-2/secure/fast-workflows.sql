-- Persist confirmed intake choices and expose bounded clinical work queues.
alter table private.reda_patient_profiles add column clinical_context jsonb not null default '{}',add column delivery_mode text not null default 'unspecified' check(delivery_mode in('unspecified','digital','clinic'));
create function private.reda_start_context_valid(p jsonb)returns boolean language plpgsql immutable set search_path=''as $$
begin
 if jsonb_typeof(p)is distinct from'object'or length(p::text)>2000 or exists(select 1 from jsonb_object_keys(p)as keys(key)where keys.key not in('stage','capacity','trainingHistory','goalProfile','equipment','floorOK','band','guidance','side','includedInVisit'))then return false;end if;
 if coalesce(p->>'stage','')not in('protected','build','higher')or coalesce(p->>'capacity','')not in('supported','standard','high')or coalesce(p->>'trainingHistory','')not in('new','regular','rehab_experienced')or coalesce(p->>'goalProfile','')not in('daily','strength','run','sport')or coalesce(p->>'equipment','')not in('home','gym','both')or coalesce(p->>'guidance','')not in('guided','trained')or coalesce(p->>'side','')not in('left','right','both','unspecified')then return false;end if;
 if jsonb_typeof(p->'floorOK')is distinct from'boolean'or jsonb_typeof(p->'band')is distinct from'boolean'or jsonb_typeof(p->'includedInVisit')is distinct from'boolean'then return false;end if;
 return true;exception when others then return false;
end$$;
revoke all on function private.reda_start_context_valid(jsonb)from public,anon,authenticated;


create or replace function private.reda_intake_validate(p jsonb)returns jsonb language plpgsql immutable set search_path='' as $$
declare k text;v text;r jsonb:='{}';maximum integer;begin
 if jsonb_typeof(p) is distinct from 'object' or exists(select 1 from jsonb_object_keys(p)x where x not in ('name','email','phone','focus','goal','handover','next_contact','source','external_id','clinical_context','delivery_mode'))then raise exception using errcode='22023',message='Kontrollera patientuppgifterna.';end if;
 foreach k in array array['name','email','phone','focus','goal','handover','next_contact','source','external_id']loop
  if p?k and jsonb_typeof(p->k) not in ('string','null')then raise exception using errcode='22023',message='Patientuppgifter ska vara text.';end if;
  v:=trim(coalesce(p->>k,''));maximum:=case k when 'name'then 120 when 'email'then 254 when 'phone'then 40 when 'focus'then 120 when 'goal'then 240 when 'handover'then 240 when 'next_contact'then 10 when 'source'then 20 else 100 end;
  if length(v)>maximum then raise exception using errcode='22023',message='En patientuppgift är för lång.';end if;
  if k='email'then v:=lower(v);end if;if k='source'and v=''then v:='manual';end if;
  r:=r||jsonb_build_object(k,v);
 end loop;
 if length(r->>'name')<2 or (r->>'email'<>''and r->>'email'!~'^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$')or(r->>'phone'<>''and private.reda_contact_phone(r->>'phone')!~'^\+?[0-9]{7,15}$')or(r->>'next_contact'<>''and private.reda_safe_date(r->>'next_contact')is null)or r->>'source'not in ('manual','bokadirekt','easypractice','other')then raise exception using errcode='22023',message='Kontrollera namn, e-post, telefon och datum.';end if;
 if r->>'source'='manual'and r->>'external_id'<>''then raise exception using errcode='22023',message='Ange källsystem för ett externt kund-ID.';end if;
 if p?'clinical_context' then
  if not private.reda_start_context_valid(p->'clinical_context')then raise exception using errcode='22023',message='Kontrollera startläget för rehab.';end if;
  r:=r||jsonb_build_object('clinical_context',p->'clinical_context');
 end if;
 if p?'delivery_mode' then
  if jsonb_typeof(p->'delivery_mode')is distinct from'string'or p->>'delivery_mode'not in('digital','clinic')then raise exception using errcode='22023',message='Välj hur planen ska överlämnas.';end if;
  if length(r->>'focus')<2 or length(r->>'goal')<2 or not(p?'clinical_context')then raise exception using errcode='22023',message='Välj behandlingsområde, mål och startläge.';end if;
  if p->>'delivery_mode'='digital'and r->>'email'=''and r->>'phone'=''then raise exception using errcode='22023',message='Ange e-post eller telefon, eller välj överlämning på kliniken.';end if;
  r:=r||jsonb_build_object('delivery_mode',p->>'delivery_mode');
 end if;
 return r;
end$$;

create or replace function private.reda_save_patient_profile(p_patient_id uuid,p_request_id uuid,p_profile jsonb,p_revision integer default 0,p_duplicate_token text default null)returns jsonb
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
 insert into private.reda_patient_profiles(patient_id,email,phone,focus,goal,handover,next_contact,source,external_id,clinical_context,delivery_mode)
 values(pid,p->>'email',p->>'phone',p->>'focus',p->>'goal',p->>'handover',private.reda_safe_date(p->>'next_contact'),p->>'source',p->>'external_id',coalesce(p->'clinical_context','{}'),coalesce(p->>'delivery_mode','unspecified'))
 on conflict(patient_id)do update set email=excluded.email,phone=excluded.phone,focus=excluded.focus,goal=excluded.goal,handover=excluded.handover,next_contact=excluded.next_contact,source=excluded.source,external_id=excluded.external_id,clinical_context=case when p?'clinical_context'then excluded.clinical_context else reda_patient_profiles.clinical_context end,delivery_mode=case when p?'delivery_mode'then excluded.delivery_mode else reda_patient_profiles.delivery_mode end,revision=reda_patient_profiles.revision+1,updated_at=clock_timestamp();
 select jsonb_build_object('status','saved','patient',jsonb_build_object('id',pt.id,'display_name',pt.display_name,'status',pt.status,'auth_user_id',case when pt.auth_user_id is not null then 'connected'else null end),'profile',private.reda_patient_profile(pid))into result from public.reda_patients pt where pt.id=pid;
 insert into private.reda_patient_intake_receipts(request_id,patient_id,actor_id,input,result)values(p_request_id,pid,actor,input,result);
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata)values(actor,pid,case when p_patient_id is null then 'patient_intake_created'else 'patient_profile_updated'end,jsonb_build_object('request_id',p_request_id,'source',p->>'source'));
 return result;
end$$;

create or replace function private.reda_dashboard(p_search text default '',p_filter text default 'priority',p_offset integer default 0) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();org uuid:=private.reda_request_organization();result jsonb;today date:=(now() at time zone 'Europe/Stockholm')::date;begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='Behandlarinloggning med MFA krävs.';end if;
 if p_search is null or length(p_search)>100 or p_filter is null or p_filter not in ('priority','waiting','active','all','archived','no_plan','upcoming','ei','symptoms','replies','reviews') or p_offset is null or p_offset<0 or p_offset>100000 then raise exception using errcode='22023',message='Kontrollera sökning och filter.';end if;
 with base as materialized(select r.*,
  (open_count>0 or new_reply or (followup_status='waiting' and followup_date<=today) or
   (coalesce(followup_status,'')<>'waiting' and (pending_count>0 or pending_messages>0 or (patient_status='active' and (review_date<=today or missing_response or quiet or (decision_action in ('advance','complete','review') and not decision_applied and not decision_reviewed)))))) is true needs_review
  from private.reda_dashboard_rows(actor,org)r),
 filtered as materialized(select * from base where (strpos(lower(display_name),lower(trim(p_search)))>0 or exists(select 1 from public.reda_plans sp where sp.id=base.plan_id and strpos(lower(coalesce(sp.payload->>'blueprintName','')||' '||coalesce(sp.payload->>'goal','')),lower(trim(p_search)))>0) or exists(select 1 from private.reda_patient_profiles pr where pr.patient_id=base.patient_id and (strpos(lower(pr.email||' '||pr.phone||' '||pr.focus||' '||pr.goal||' '||pr.external_id),lower(trim(p_search)))>0 or (length(regexp_replace(p_search,'[^0-9]','','g'))>=4 and strpos(private.reda_contact_phone(pr.phone),regexp_replace(p_search,'[^0-9]','','g'))>0)))) and case p_filter
  when 'ei' then patient_status='active'and needs_review and(pending_count>0 or pending_messages>0 or (decision_action in('advance','complete','review')and not decision_applied and not decision_reviewed)) when 'symptoms' then open_count>0 and codes&&array['changed_symptoms'] when 'replies' then new_reply when 'reviews' then needs_review and(followup_date<=today or review_date<=today) when 'priority' then needs_review when 'waiting' then followup_status='waiting' and not needs_review
  when 'active' then patient_status='active' and plan_id is not null when 'archived' then patient_status='archived'
  when 'upcoming' then patient_status='active' and review_date>today when 'no_plan' then patient_status='active' and plan_id is null else true end),
 page as(select * from filtered order by needs_review desc,
  case when open_count>0 and codes&&array['changed_symptoms','changed_environment'] then 0 when open_count>0 then 1 when followup_date<=today then 2 else 3 end,
  coalesce(first_case,followup_date::timestamptz,review_date::timestamptz,'infinity'::timestamptz),lower(display_name),patient_id limit 25 offset p_offset)
 select jsonb_build_object('today',today,'total',(select count(*) from filtered),'offset',p_offset,'limit',25,
  'counts',(select jsonb_build_object('ei',count(*) filter(where patient_status='active'and needs_review and(pending_count>0 or pending_messages>0 or (decision_action in('advance','complete','review')and not decision_applied and not decision_reviewed))),'symptoms',count(*) filter(where open_count>0 and codes&&array['changed_symptoms']),'replies',count(*) filter(where new_reply),'reviews',count(*) filter(where needs_review and(followup_date<=today or review_date<=today)),'all',count(*),'active',count(*) filter(where patient_status='active' and plan_id is not null),'priority',count(*) filter(where needs_review),'waiting',count(*) filter(where followup_status='waiting' and not needs_review),'no_plan',count(*) filter(where patient_status='active' and plan_id is null),'upcoming',count(*) filter(where patient_status='active' and review_date>today),'archived',count(*) filter(where patient_status='archived'))from base),
  'patients',coalesce((select jsonb_agg(to_jsonb(page)||private.reda_patient_brief(page.patient_id)) from page),'[]'::jsonb)) into result;
 return result;
end$$;
