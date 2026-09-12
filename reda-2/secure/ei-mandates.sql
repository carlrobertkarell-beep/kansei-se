-- Organization-scoped operational mandate; clinical and external actions stay separately gated.
create table private.reda_ei_mandates(organization_id uuid primary key references public.reda_organizations(id),auto_followup boolean not null default true,revision integer not null default 1,updated_by uuid not null references auth.users(id),updated_at timestamptz not null default now());
create table private.reda_ei_mandate_receipts(request_id uuid primary key,organization_id uuid not null references public.reda_organizations(id),actor_id uuid not null references auth.users(id),input jsonb not null,result jsonb not null,created_at timestamptz not null default now());
create index reda_ei_mandate_actor on private.reda_ei_mandates(updated_by);
create index reda_ei_mandate_receipt_org on private.reda_ei_mandate_receipts(organization_id,created_at desc);
create index reda_ei_mandate_receipt_actor on private.reda_ei_mandate_receipts(actor_id);
alter table private.reda_ei_mandates enable row level security;alter table private.reda_ei_mandate_receipts enable row level security;
revoke all on private.reda_ei_mandates,private.reda_ei_mandate_receipts from public,anon,authenticated;
create policy "rpc only" on private.reda_ei_mandates for all to authenticated using(false)with check(false);
create policy "rpc only" on private.reda_ei_mandate_receipts for all to authenticated using(false)with check(false);
create function private.reda_ei_settings()returns jsonb language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();org uuid:=private.reda_request_organization();begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='Behandlarbehörighet och MFA krävs.';end if;
 return jsonb_build_object('revision',coalesce((select revision from private.reda_ei_mandates where organization_id=org),0),'auto_followup',coalesce((select auto_followup from private.reda_ei_mandates where organization_id=org),true),
 'can_manage',exists(select 1 from public.reda_memberships where organization_id=org and user_id=actor and role='owner' and status='active'),
 'clinical_progression_enabled',(select automatic_enabled from private.reda_engine_settings limit 1),'external_ai_enabled',(select ai_enabled from private.reda_engine_settings limit 1),
 'connections',jsonb_build_array(jsonb_build_object('id','booking','name','Bokning','connected',false),jsonb_build_object('id','journal','name','Journal','connected',false),jsonb_build_object('id','billing','name','Betalning och abonnemang','connected',false)),
 'imports',coalesce((select jsonb_agg(to_jsonb(s))from(select pr.source,count(*) as patients,max(pr.updated_at)as last_saved from private.reda_patient_profiles pr join public.reda_patients p on p.id=pr.patient_id where p.organization_id=org and p.clinician_id=actor and pr.source<>'manual'group by pr.source)s),'[]'::jsonb));
end$$;
create function private.reda_save_ei_mandate(p_request_id uuid,p_revision integer,p_auto_followup boolean)returns jsonb language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();org uuid:=private.reda_request_organization();old private.reda_ei_mandate_receipts%rowtype;submitted jsonb;result jsonb;begin
 perform 1 from public.reda_organizations where id=org and status='active'for update;
 if not found or not private.reda_is_clinician_aal2() or not exists(select 1 from public.reda_memberships where organization_id=org and user_id=actor and role='owner'and status='active')then raise exception using errcode='42501',message='En aktiv ägare med behandlarbehörighet och MFA krävs.';end if;
 if p_request_id is null or p_revision is null or p_revision<0 or p_auto_followup is null then raise exception using errcode='22023',message='Kontrollera inställningen.';end if;
 submitted=jsonb_build_object('revision',p_revision,'auto_followup',p_auto_followup);
 select * into old from private.reda_ei_mandate_receipts where request_id=p_request_id;
 if found then if old.actor_id=actor and old.organization_id=org and old.input=submitted then return old.result;end if;raise exception using errcode='23505',message='Begäran hör till en annan ändring.';end if;
 if p_revision<>coalesce((select revision from private.reda_ei_mandates where organization_id=org),0)then raise exception using errcode='40001',message='Mandatet har ändrats. Uppdatera innan du sparar.';end if;
 insert into private.reda_ei_mandates(organization_id,auto_followup,updated_by)values(org,p_auto_followup,actor)on conflict(organization_id)do update set auto_followup=excluded.auto_followup,revision=reda_ei_mandates.revision+1,updated_by=actor,updated_at=now();
 result=private.reda_ei_settings();
 insert into private.reda_ei_mandate_receipts(request_id,organization_id,actor_id,input,result)values(p_request_id,org,actor,submitted,result);
 return result;
end$$;
create function public.reda_ei_settings()returns jsonb language sql stable security invoker set search_path='' as $$select private.reda_ei_settings()$$;
create function public.reda_save_ei_mandate(p_request_id uuid,p_revision integer,p_auto_followup boolean)returns jsonb language sql security invoker set search_path='' as $$select private.reda_save_ei_mandate(p_request_id,p_revision,p_auto_followup)$$;
revoke all on function private.reda_ei_settings(),public.reda_ei_settings(),private.reda_save_ei_mandate(uuid,integer,boolean),public.reda_save_ei_mandate(uuid,integer,boolean) from public,anon,authenticated;
grant execute on function private.reda_ei_settings(),public.reda_ei_settings(),private.reda_save_ei_mandate(uuid,integer,boolean),public.reda_save_ei_mandate(uuid,integer,boolean) to authenticated;

create or replace function private.reda_queue_support_signal() returns trigger
language plpgsql security definer set search_path='' as $$
declare owner_id uuid;today date:=(now() at time zone 'Europe/Stockholm')::date;due date;task_note text;
begin
 if new.status<>'open' then return new;end if;
 perform private.reda_lock_patient_context(new.patient_id);
 select p.clinician_id into owner_id from public.reda_patients p where p.id=new.patient_id and p.status='active' for update;
 if owner_id is null then return new;end if;
 if not coalesce((select m.auto_followup from private.reda_ei_mandates m join public.reda_patients p on p.organization_id=m.organization_id where p.id=new.patient_id),true) then return new;end if;
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
