-- Managed migration. Release readiness is operator-owned, never enabled by this migration.
alter table public.reda_organizations add column patient_delivery_enabled boolean not null default false;
create table private.reda_handovers(
 id uuid primary key default gen_random_uuid(), request_id uuid not null unique,
 patient_id uuid not null references public.reda_patients, plan_id uuid not null references public.reda_plans,
 actor_id uuid not null references auth.users, input jsonb not null, patient_message text not null,
 email text, expires_at timestamptz not null default now()+interval '7 days',
 delivery_state text not null default 'not_requested' check(delivery_state in ('not_requested','pending','sending','accepted','failed')),
 frame_continued boolean not null default false, lease uuid, attempted_at timestamptz, opened_at timestamptz, created_at timestamptz not null default now()
);
create index reda_handovers_patient on private.reda_handovers(patient_id,created_at desc);
create index reda_handovers_plan on private.reda_handovers(plan_id);
create index reda_handovers_actor on private.reda_handovers(actor_id);
create index reda_handovers_email on private.reda_handovers(email,expires_at);
alter table private.reda_handovers enable row level security;
revoke all on private.reda_handovers from public,anon,authenticated;
create policy "rpc only" on private.reda_handovers for all to authenticated using(false) with check(false);

-- Rebind public wrappers after renaming so old callers do not keep an obsolete OID.
alter function private.reda_my_workspaces() rename to reda_my_workspaces_before_delivery;
revoke all on function private.reda_my_workspaces_before_delivery() from public,anon,authenticated;
create function private.reda_my_workspaces() returns jsonb language plpgsql stable security definer set search_path='' as $$
declare r jsonb;begin
 r:=private.reda_my_workspaces_before_delivery();
 return coalesce((select jsonb_agg(x||jsonb_build_object('activation_enabled',o.patient_delivery_enabled) order by ord) from jsonb_array_elements(r) with ordinality a(x,ord) join public.reda_organizations o on o.id=(x->>'id')::uuid),'[]');
end$$;
create or replace function public.reda_my_workspaces() returns jsonb language sql security invoker set search_path='' as $$select private.reda_my_workspaces()$$;

create function private.reda_publishable(p jsonb) returns boolean language plpgsql immutable set search_path='' as $$
declare x jsonb;begin
 if length(p::text)>300000 or p->>'schema' is distinct from '6' or coalesce(length(trim(p->>'goal')),0)<2 or jsonb_typeof(p->'exercises') is distinct from 'array' or not private.reda_options_valid(p) then return false;end if;
 if coalesce(jsonb_array_length(p->'warnings'),0)>0 then return false;end if;
 if jsonb_typeof(p->'schedule'->'days') is distinct from 'array' or jsonb_array_length(p->'schedule'->'days') not between 1 and 7 then return false;end if;
 if not private.reda_template_valid(jsonb_build_object('schema',1,'exercises',(select jsonb_agg(jsonb_build_object('id',e->'id','variantId',e->'variantId','dose',(e->'dose')-'label')) from jsonb_array_elements(p->'exercises') e))) then return false;end if;
 for x in select * from jsonb_array_elements(p->'exercises') loop
  if x->>'side' is null or x->>'side' not in ('left','right','both','simultaneous') or coalesce(length(x->>'name'),0)<2 or jsonb_typeof(x->'instructions') is distinct from 'array' or jsonb_array_length(x->'instructions')<1 then return false;end if;
 end loop;
 return true;
exception when others then return false;end$$;
revoke all on function private.reda_publishable(jsonb) from public,anon,authenticated;

create function private.reda_publish_reviewed(p_patient_id uuid,p_request_id uuid,p_token text,p_base_plan_id uuid,p_payload jsonb,p_note text,p_patient_message text,p_email text default null,p_decision_id uuid default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();pt public.reda_patients%rowtype;oldplan public.reda_plans%rowtype;np public.reda_plans%rowtype;h private.reda_handovers%rowtype;inp jsonb;mail text:=nullif(lower(trim(p_email)),'');d jsonb;f public.reda_progression_frames%rowtype;keep_frame boolean:=false;begin
 perform private.reda_lock_clinical_patient(p_patient_id);
 select * into pt from public.reda_patients where id=p_patient_id and private.reda_owns_patient(id) and status='active' for update;
 if pt.id is null then raise exception using errcode='42501',message='Patienten är inte tillgänglig.';end if;
 inp:=jsonb_build_object('token',p_token,'base',p_base_plan_id,'payload',p_payload,'note',p_note,'message',p_patient_message,'email',mail,'decision',p_decision_id);
 select * into h from private.reda_handovers where request_id=p_request_id;
 if h.id is not null then
  if h.patient_id<>pt.id or h.actor_id<>actor or h.input is distinct from inp then raise exception using errcode='23505',message='Begäran hör till en annan överlämning.';end if;
  select * into np from public.reda_plans where id=h.plan_id;
  return jsonb_build_object('id',h.id,'plan_id',np.id,'version',np.version,'delivery_state',h.delivery_state,'frame_continued',h.frame_continued);
 end if;
 if not (select patient_delivery_enabled from public.reda_organizations where id=pt.organization_id) then raise exception using errcode='42501',message='Patientdistribution är inte öppnad för arbetsytan. Klinisk granskning och e-postprov behöver slutföras före pilot.';end if;
 if p_request_id is null or coalesce(length(trim(p_note)),0) not between 5 and 1000 or coalesce(length(trim(p_patient_message)),0) not between 5 and 500 or not private.reda_publishable(p_payload) then raise exception using errcode='22023',message='Granska övningar, instruktioner, sida, dos, träningsdagar och överlämningstext.';end if;
 if p_token is distinct from md5(private.reda_dashboard_snapshot(pt.id)::text) then raise exception using errcode='40001',message='Underlaget har ändrats. Hämta och granska den nya versionen.';end if;
 if not exists(select 1 from private.reda_patient_profiles where patient_id=pt.id and length(trim(focus))>=2) then raise exception using errcode='22023',message='Komplettera patientens behandlingsfokus före överlämningen.';end if;
 select * into oldplan from public.reda_plans where patient_id=pt.id and status='active';
 if oldplan.id is distinct from p_base_plan_id then raise exception using errcode='40001',message='En annan plan är aktuell. Granska ändringen på nytt.';end if;
 if p_decision_id is not null then
  if p_decision_id is distinct from (select id from public.reda_engine_decisions where patient_id=pt.id order by created_at desc,id desc limit 1) or not exists(select 1 from public.reda_engine_decisions where id=p_decision_id and patient_id=pt.id and action='advance' and not applied) then raise exception using errcode='40001',message='EI-förslaget är inte längre tillgängligt.';end if;
  d:=private.reda_evaluate_progression(pt.id,gen_random_uuid());
  if d->>'action' is distinct from 'advance' or coalesce((d->>'applied')::boolean,false) then raise exception using errcode='40001',message='Underlaget tillåter inte längre nästa steg. Granska patienten igen.';end if;
  select * into f from public.reda_progression_frames where patient_id=pt.id and status='approved';
  keep_frame:=private.reda_plan_binding(p_payload)=private.reda_plan_binding(f.policy->'steps'->(f.current_step+1)->'plan');
 end if;
 if pt.auth_user_id is null then
  if mail is null or mail!~'^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$' or length(mail)>254 then raise exception using errcode='22023',message='Kontrollera patientens e-postadress.';end if;
  perform pg_advisory_xact_lock(hashtextextended(mail,0));
  if exists(select 1 from private.reda_handovers where email=mail and patient_id<>pt.id and expires_at>now()) or exists(select 1 from auth.users u where lower(u.email)=mail and (exists(select 1 from public.reda_patients p where p.auth_user_id=u.id and p.id<>pt.id) or exists(select 1 from public.reda_profiles pr where pr.user_id=u.id and pr.role='clinician'))) then raise exception using errcode='23505',message='Adressen används redan för ett annat konto. Kontrollera mottagaren.';end if;
 else mail:=null;end if;
 update private.reda_handovers set expires_at=now() where patient_id=pt.id and opened_at is null;
 update public.reda_progression_frames set status='revoked',revoked_at=now() where patient_id=pt.id and status='approved' and not keep_frame;
 update public.reda_plans set status='superseded',superseded_at=now() where patient_id=pt.id and status='active';
 insert into public.reda_plans(patient_id,clinician_id,version,status,payload,activated_at)
 values(pt.id,actor,(select coalesce(max(version),0)+1 from public.reda_plans where patient_id=pt.id),'active',p_payload,now()) returning * into np;
 if keep_frame then update public.reda_progression_frames set current_step=current_step+1,current_plan_id=np.id,started_at=now() where id=f.id;end if;
 if d is not null then update public.reda_engine_decisions set applied=true,result_plan_id=np.id where id=(d->>'id')::uuid;end if;
 insert into private.reda_handovers(request_id,patient_id,plan_id,actor_id,input,patient_message,email,delivery_state,frame_continued)
 values(p_request_id,pt.id,np.id,actor,inp,p_patient_message,mail,case when mail is null then 'not_requested' else 'pending' end,keep_frame) returning * into h;
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata) values(actor,pt.id,'plan_activated',jsonb_build_object('plan_id',np.id,'version',np.version,'previous_plan_id',oldplan.id,'handover_id',h.id,'decision_id',p_decision_id,'manual_approval',true));
 return jsonb_build_object('id',h.id,'plan_id',np.id,'version',np.version,'delivery_state',h.delivery_state,'frame_continued',h.frame_continued);
end$$;

-- Clinician reserves an email attempt; only the server can record provider acceptance.
create function private.reda_reserve_invitation(p_handover_id uuid) returns jsonb language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();h private.reda_handovers%rowtype;begin
 select * into h from private.reda_handovers where id=p_handover_id;
 perform private.reda_lock_clinical_patient(h.patient_id);
 perform 1 from public.reda_patients where id=h.patient_id and private.reda_owns_patient(id) and status='active' for update;
 if not found then raise exception using errcode='42501',message='Överlämningen är inte tillgänglig.';end if;
 select * into h from private.reda_handovers where id=p_handover_id for update;
 if h.email is null or h.expires_at<=now() or not exists(select 1 from public.reda_plans p join public.reda_patients pt on pt.id=p.patient_id join public.reda_organizations o on o.id=pt.organization_id where p.id=h.plan_id and p.status='active' and o.patient_delivery_enabled) then raise exception using errcode='40001',message='Inbjudan är inte aktuell. Granska en ny överlämning.';end if;
 if h.delivery_state='accepted' then return jsonb_build_object('accepted',true);end if;
 if h.attempted_at>now()-interval '60 seconds' then raise exception using errcode='54000',message='Ett utskick pågår eller gjordes nyligen. Vänta en minut och försök igen.';end if;
 update private.reda_handovers set delivery_state='sending',lease=gen_random_uuid(),attempted_at=now() where id=h.id returning * into h;
 return jsonb_build_object('id',h.id,'lease',h.lease,'email',h.email,'accepted',false);
end$$;
create function public.reda_finish_invitation(p_id uuid,p_lease uuid,p_accepted boolean) returns void language plpgsql security invoker set search_path='' as $$
begin
 update private.reda_handovers set delivery_state=case when p_accepted then 'accepted' else 'failed' end,lease=null where id=p_id and lease=p_lease;
end$$;
revoke all on function public.reda_finish_invitation(uuid,uuid,boolean) from public,anon,authenticated;
grant select,update on private.reda_handovers to service_role;
grant execute on function public.reda_finish_invitation(uuid,uuid,boolean) to service_role;

-- A verified email signs in first; only then can its current invitation claim a patient.
create function private.reda_claim_patient_access() returns jsonb language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();mail text;h private.reda_handovers%rowtype;pt public.reda_patients%rowtype;begin
 select lower(email) into mail from auth.users where id=actor and email_confirmed_at is not null;
 if mail is null or exists(select 1 from public.reda_profiles where user_id=actor and role='clinician') then return jsonb_build_object('status','unavailable');end if;
 if exists(select 1 from public.reda_patients where auth_user_id=actor) then return jsonb_build_object('status','linked');end if;
 perform pg_advisory_xact_lock(hashtextextended('claim:'||actor::text,0));
 select * into h from private.reda_handovers where email=mail and expires_at>now() order by created_at desc,id desc limit 1;
 if h.id is null then return jsonb_build_object('status','unavailable');end if;
 perform 1 from public.reda_organizations o join public.reda_patients p on p.organization_id=o.id where p.id=h.patient_id for share of o;
 select * into pt from public.reda_patients where id=h.patient_id and status='active' for update;
 select * into h from private.reda_handovers where id=h.id;
 if pt.id is null or not private.reda_can_claim(pt.id,actor) or pt.auth_user_id is not null then return jsonb_build_object('status','unavailable');end if;
 update public.reda_patients set auth_user_id=actor,updated_at=now() where id=pt.id;
 insert into public.reda_audit_events(actor_id,patient_id,action,metadata) values(actor,pt.id,'patient_access_claimed',jsonb_build_object('handover_id',h.id));
 return jsonb_build_object('status','linked');
end$$;

create function private.reda_can_claim(pid uuid,uid uuid) returns boolean language sql stable security definer set search_path='' as $$
 select uid=auth.uid() and not exists(select 1 from public.reda_profiles where user_id=uid and role='clinician') and exists(
 select 1 from private.reda_handovers h join auth.users u on lower(u.email)=h.email
 join public.reda_patients pt on pt.id=h.patient_id join public.reda_plans p on p.id=h.plan_id
 join public.reda_organizations o on o.id=pt.organization_id
 where h.patient_id=pid and u.id=uid and u.email_confirmed_at is not null and u.deleted_at is null and (u.banned_until is null or u.banned_until<=now())
 and h.expires_at>now() and pt.status='active' and p.status='active' and o.status='active' and o.patient_delivery_enabled);
$$;
revoke all on function private.reda_can_claim(uuid,uuid) from public,anon,authenticated;
create or replace function private.reda_patient_binding_guard() returns trigger language plpgsql security definer set search_path='' as $$
begin
 if tg_op='UPDATE' and (new.id,new.organization_id,new.clinician_id) is distinct from (old.id,old.organization_id,old.clinician_id) then raise exception using errcode='23514',message='Patientrelationen kan inte flyttas eller byta ansvarig i detta flöde.';end if;
 perform 1 from public.reda_organizations where id=new.organization_id for share;
 if tg_op='INSERT' and not private.reda_clinical_member(new.organization_id,new.clinician_id) then raise exception using errcode='42501',message='En aktiv klinik och behörig ansvarig behandlare krävs.';end if;
 if current_setting('role',true)='authenticated' then
  if tg_op='UPDATE' and old.auth_user_id is null and new.auth_user_id=auth.uid() and private.reda_can_claim(old.id,new.auth_user_id) and (to_jsonb(new)-'auth_user_id'-'updated_at')=(to_jsonb(old)-'auth_user_id'-'updated_at') then return new;end if;
  if not private.reda_is_clinician_aal2() or new.organization_id is distinct from private.reda_request_organization() or new.clinician_id is distinct from auth.uid() or (tg_op='UPDATE' and new.auth_user_id is distinct from old.auth_user_id) then raise exception using errcode='42501',message='Patientändringen saknar behörighet.';end if;
 end if;return new;
end$$;

create function private.reda_open_patient_plan(p_plan_id uuid) returns jsonb language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();pid uuid;h private.reda_handovers%rowtype;begin
 select patient_id into pid from public.reda_plans where id=p_plan_id;
 perform private.reda_lock_patient_context(pid);
 perform 1 from public.reda_patients where id=pid and private.reda_is_own_patient(id) for update;
 if not found then raise exception using errcode='42501',message='Planen är inte tillgänglig.';end if;
 if not exists(select 1 from public.reda_plans where id=p_plan_id and status='active') then raise exception using errcode='40001',message='En ny plan finns. Uppdatera sidan.';end if;
 update private.reda_handovers set opened_at=coalesce(opened_at,now()) where plan_id=p_plan_id returning * into h;
 return jsonb_build_object('message',h.patient_message,'opened_at',h.opened_at);
end$$;

alter function private.reda_dashboard_patient(uuid) rename to reda_dashboard_patient_before_handover;
revoke all on function private.reda_dashboard_patient_before_handover(uuid) from public,anon,authenticated;
create function private.reda_dashboard_patient(p_patient_id uuid) returns jsonb language plpgsql stable security definer set search_path='' as $$
declare r jsonb;begin
 r:=private.reda_dashboard_patient_before_handover(p_patient_id);
 return r||jsonb_build_object('handover',(select jsonb_build_object('id',h.id,'plan_id',h.plan_id,'delivery_state',h.delivery_state,'expires_at',h.expires_at,'opened_at',h.opened_at,'created_at',h.created_at,'first_session_at',(select min(started_at) from public.reda_sessions where plan_id=h.plan_id)) from private.reda_handovers h where patient_id=p_patient_id order by created_at desc,id desc limit 1),'delivery_enabled',(select o.patient_delivery_enabled from public.reda_patients p join public.reda_organizations o on o.id=p.organization_id where p.id=p_patient_id));
end$$;
create or replace function public.reda_dashboard_patient(p_patient_id uuid) returns jsonb language sql security invoker set search_path='' as $$select private.reda_dashboard_patient(p_patient_id)$$;
create function public.reda_publish_reviewed(p_patient_id uuid,p_request_id uuid,p_token text,p_base_plan_id uuid,p_payload jsonb,p_note text,p_patient_message text,p_email text default null,p_decision_id uuid default null) returns jsonb language sql security invoker set search_path='' as $$select private.reda_publish_reviewed(p_patient_id,p_request_id,p_token,p_base_plan_id,p_payload,p_note,p_patient_message,p_email,p_decision_id)$$;
create function public.reda_reserve_invitation(p_handover_id uuid) returns jsonb language sql security invoker set search_path='' as $$select private.reda_reserve_invitation(p_handover_id)$$;
create function public.reda_claim_patient_access() returns jsonb language sql security invoker set search_path='' as $$select private.reda_claim_patient_access()$$;
create function public.reda_open_patient_plan(p_plan_id uuid) returns jsonb language sql security invoker set search_path='' as $$select private.reda_open_patient_plan(p_plan_id)$$;
do $$declare r record;begin for r in select p.oid::regprocedure sig from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname in ('private','public') and p.proname in ('reda_publish_reviewed','reda_reserve_invitation','reda_claim_patient_access','reda_open_patient_plan','reda_my_workspaces','reda_dashboard_patient') loop execute format('revoke all on function %s from public,anon,authenticated',r.sig);execute format('grant execute on function %s to authenticated',r.sig);end loop;end$$;
