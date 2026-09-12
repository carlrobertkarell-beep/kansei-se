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
