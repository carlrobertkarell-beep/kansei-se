-- EI work policy v1: create internal follow-up tasks from new saved patient signals.
-- Clinical decisions, communication, invitation and progression gates are unchanged.
create function private.reda_queue_support_signal() returns trigger
language plpgsql security definer set search_path='' as $$
declare owner_id uuid;today date:=(now() at time zone 'Europe/Stockholm')::date;due date;task_note text;
begin
 if new.status<>'open' then return new;end if;
 perform private.reda_lock_patient_context(new.patient_id);
 select p.clinician_id into owner_id from public.reda_patients p where p.id=new.patient_id and p.status='active' for update;
 if owner_id is null then return new;end if;
 task_note=case new.code when 'changed_symptoms' then 'Bedöm patientens rapport om förändrade besvär eller funktion.' when 'changed_environment' then 'Stäm av patientens ändrade träningsförutsättningar.' when 'execution_help' then 'Gå igenom det utförande som patienten behöver hjälp med.' when 'training_barrier' then 'Följ upp hindret som patienten har rapporterat i träningen.' else 'Följ upp patientens önskemål om hjälp.' end;
 insert into private.reda_followups(patient_id,clinician_id,due_date,status,note)
 values(new.patient_id,owner_id,today,'waiting',task_note)
 on conflict(patient_id)do update set due_date=case when reda_followups.status='waiting' then least(reda_followups.due_date,excluded.due_date) else excluded.due_date end,
 status='waiting',note=case when reda_followups.status='waiting' then reda_followups.note else excluded.note end,updated_at=now()
 returning due_date into due;
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata)
 values(auth.uid(),new.patient_id,'support_task_queued',jsonb_build_object('case_id',new.id,'plan_id',new.plan_id,'policy_version',1,'due_date',due,'assigned_to',owner_id,'message_sent',false,'plan_changed',false));
 return new;
end$$;
revoke all on function private.reda_queue_support_signal() from public,anon,authenticated;
create trigger reda_queue_support_signal after insert on public.reda_review_cases for each row execute function private.reda_queue_support_signal();

-- Internal, bounded per-patient state projection. No clinical notes are returned.
create function private.reda_support_state(p_patient_id uuid) returns jsonb
language plpgsql stable security invoker set search_path='' as $$
declare pending integer;fresh integer;resolved integer;messages integer;reply boolean;question uuid;phase text;f private.reda_followups%rowtype;signal_at timestamptz;today date:=(now() at time zone 'Europe/Stockholm')::date;
begin
 select count(*)filter(where status<>'resolved'),count(*)filter(where status='open'),count(*)filter(where status='resolved'),max(created_at) into pending,fresh,resolved,signal_at from public.reda_review_cases where patient_id=p_patient_id;
 select * into f from private.reda_followups where patient_id=p_patient_id;
 select count(*),coalesce(bool_or(kind='patient' and created_at>coalesce(f.updated_at,'1900-01-01'::timestamptz)),false) into messages,reply from private.reda_clinic_messages where patient_id=p_patient_id and handled_at is null;
 select cm.id into question from private.reda_clinic_messages cm where cm.patient_id=p_patient_id and cm.kind='clinician' and cm.handled_at is null
 and not exists(select 1 from private.reda_clinic_messages r where r.reply_to=cm.id)
 and not exists(select 1 from private.reda_clinic_messages x where x.patient_id=p_patient_id and x.kind='clinician' and (x.created_at,x.id)>(cm.created_at,cm.id)) order by cm.created_at desc,cm.id desc limit 1;
 phase=case when fresh>0 or reply then 'needs_review'
 when question is not null then 'awaiting_patient'
 when f.status='waiting' then 'scheduled'
 when pending>0 or messages>0 then 'needs_resolution'
 when resolved>0 then 'handled' else 'none' end;
 return jsonb_build_object('phase',phase,'pending_signals',pending,'new_signals',fresh,'new_reply',reply,'reply_to',question,
 'due_date',case when f.status='waiting' then f.due_date end,'overdue',coalesce(f.status='waiting' and f.due_date<today,false),
 'last_signal_at',signal_at,'policy_version',1,'responsibility',case when question is not null and fresh=0 and not reply then 'patient' else 'clinician' end);
end$$;
revoke all on function private.reda_support_state(uuid) from public,anon,authenticated;

create function private.reda_patient_support(p_patient_id uuid) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();s jsonb;
begin
 if not private.reda_is_own_patient(p_patient_id) then raise exception using errcode='42501',message='Hjälpstatusen är inte tillgänglig.';end if;
 s=private.reda_support_state(p_patient_id);
 -- Internal deadlines, counts, handling notes and decision material stay with the clinician.
 return jsonb_build_object('phase',s->'phase','reply_to',s->'reply_to','last_signal_at',s->'last_signal_at');
end$$;
create function public.reda_patient_support(p_patient_id uuid) returns jsonb
language sql stable security invoker set search_path='' as $$select private.reda_patient_support(p_patient_id)$$;
revoke all on function private.reda_patient_support(uuid),public.reda_patient_support(uuid) from public,anon,authenticated;
grant execute on function private.reda_patient_support(uuid),public.reda_patient_support(uuid) to authenticated;

-- Enrich the existing dashboard page only. Existing search, counts and authorization are retained.
alter function private.reda_dashboard(text,text,integer) rename to reda_dashboard_before_support;
revoke all on function private.reda_dashboard_before_support(text,text,integer) from public,anon,authenticated;
create function private.reda_dashboard(p_search text default '',p_filter text default 'priority',p_offset integer default 0) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare result jsonb;begin
 result=private.reda_dashboard_before_support(p_search,p_filter,p_offset);
 return jsonb_set(result,'{patients}',coalesce((select jsonb_agg(p||jsonb_build_object('workflow',private.reda_support_state((p->>'patient_id')::uuid)) order by n)from jsonb_array_elements(result->'patients')with ordinality as rows(p,n)),'[]'::jsonb));
end$$;
revoke all on function private.reda_dashboard(text,text,integer) from public,anon,authenticated;
grant execute on function private.reda_dashboard(text,text,integer) to authenticated;
alter function private.reda_dashboard_patient(uuid) rename to reda_dashboard_patient_before_support;
revoke all on function private.reda_dashboard_patient_before_support(uuid) from public,anon,authenticated;
create function private.reda_dashboard_patient(p_patient_id uuid) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare result jsonb;begin
 result=private.reda_dashboard_patient_before_support(p_patient_id);
 return result||jsonb_build_object('workflow',private.reda_support_state(p_patient_id));
end$$;
revoke all on function private.reda_dashboard_patient(uuid) from public,anon,authenticated;
grant execute on function private.reda_dashboard_patient(uuid) to authenticated;
-- Rebind public wrappers after renaming their original private implementations.
create or replace function public.reda_dashboard(p_search text default '',p_filter text default 'priority',p_offset integer default 0) returns jsonb language sql stable security invoker set search_path='' as $$select private.reda_dashboard(p_search,p_filter,p_offset)$$;
create or replace function public.reda_dashboard_patient(p_patient_id uuid) returns jsonb language sql stable security invoker set search_path='' as $$select private.reda_dashboard_patient(p_patient_id)$$;
