-- Managed migration source: organizations + organization-runtime.sql apply atomically.
-- Legacy bootstrap deliberately requires one independently allowlisted owner.
create table public.reda_organizations (
 id uuid primary key default gen_random_uuid(), slug text not null unique,
 name text not null check(length(trim(name)) between 1 and 100),
 kind text not null check(kind in ('clinic','direct')),
 status text not null default 'active' check(status in ('active','disabled')),
 created_at timestamptz not null default now()
);
create table public.reda_memberships (
 organization_id uuid not null references public.reda_organizations,
 user_id uuid not null references auth.users,
 display_name text not null default '' check(length(display_name)<=100),
 role text not null check(role in ('owner','admin','finance','member')),
 clinical_access boolean not null default false,
 status text not null default 'active' check(status in ('active','revoked')),
 revision integer not null default 1 check(revision>0),
 updated_at timestamptz not null default now(),
 primary key(organization_id,user_id)
);
create index reda_memberships_user on public.reda_memberships(user_id,organization_id);
create table private.reda_membership_events (
 id bigint generated always as identity primary key,
 organization_id uuid not null references public.reda_organizations,
 actor_id uuid not null references auth.users,
 member_id uuid not null references auth.users,
 before_state jsonb not null, after_state jsonb not null,
 created_at timestamptz not null default now()
);
create index reda_membership_events_org on private.reda_membership_events(organization_id,created_at desc);
create index reda_membership_events_actor on private.reda_membership_events(actor_id);
create index reda_membership_events_member on private.reda_membership_events(member_id);
alter table public.reda_organizations enable row level security;
alter table public.reda_memberships enable row level security;
alter table private.reda_membership_events enable row level security;
revoke all on public.reda_organizations,public.reda_memberships,private.reda_membership_events from public,anon,authenticated;
create policy "workspace RPC only" on public.reda_organizations for all to authenticated using(false) with check(false);
create policy "membership RPC only" on public.reda_memberships for all to authenticated using(false) with check(false);
create policy "membership event RPC only" on private.reda_membership_events for all to authenticated using(false) with check(false);
grant select,insert,update on public.reda_organizations,public.reda_memberships to service_role;
alter table public.reda_patients add column organization_id uuid references public.reda_organizations;
do $$
declare owner_id uuid;clinic_id uuid;direct_id uuid;begin
 if (select count(*) from public.reda_profiles p join auth.users u on u.id=p.user_id join public.reda_clinician_allowlist a on a.email=lower(u.email) where p.role='clinician' and u.deleted_at is null and (u.banned_until is null or u.banned_until<=now()))<>1 then
  raise exception 'Bootstrap requires exactly one verified owner; no data migrated';
 end if;
 select p.user_id into owner_id from public.reda_profiles p join auth.users u on u.id=p.user_id join public.reda_clinician_allowlist a on a.email=lower(u.email) where p.role='clinician' and u.deleted_at is null and (u.banned_until is null or u.banned_until<=now());
 if exists(select 1 from public.reda_patients where clinician_id<>owner_id) then raise exception 'Unmapped legacy clinician; no data migrated';end if;
 insert into public.reda_organizations(slug,name,kind) values('kansei','Kansei','clinic') returning id into clinic_id;
 insert into public.reda_organizations(slug,name,kind) values('reda-direct','Reda · direktverksamhet','direct') returning id into direct_id;
 insert into public.reda_memberships(organization_id,user_id,display_name,role,clinical_access) select clinic_id,owner_id,display_name,'owner',true from public.reda_profiles where user_id=owner_id;
 insert into public.reda_memberships(organization_id,user_id,display_name,role,clinical_access) select direct_id,owner_id,display_name,'owner',false from public.reda_profiles where user_id=owner_id;
 update public.reda_patients set organization_id=clinic_id;
end$$;
alter table public.reda_patients alter column organization_id set not null;
create index reda_patients_org_clinician on public.reda_patients(organization_id,clinician_id,status,updated_at desc);
alter table public.reda_patients add constraint reda_patient_member foreign key(organization_id,clinician_id) references public.reda_memberships(organization_id,user_id);

-- Organization is inherited from the immutable patient relation, never copied from a model.
-- Composite FKs prohibit a child record from binding to another patient's plan or evidence.
alter table public.reda_patients add constraint reda_patient_clinician_pair unique(id,clinician_id);
alter table public.reda_plans add constraint reda_plan_patient_pair unique(id,patient_id);
alter table public.reda_plans add constraint reda_plan_version_pair unique(id,patient_id,version);
alter table public.reda_plans add constraint reda_plan_clinician_binding foreign key(patient_id,clinician_id) references public.reda_patients(id,clinician_id);
alter table public.reda_sessions add constraint reda_session_plan_binding foreign key(plan_id,patient_id,plan_version) references public.reda_plans(id,patient_id,version);
alter table public.reda_sessions add constraint reda_session_binding unique(id,patient_id,plan_id,plan_version);
alter table public.reda_training_responses add constraint reda_response_session_binding foreign key(session_id,patient_id,plan_id,plan_version) references public.reda_sessions(id,patient_id,plan_id,plan_version);
alter table public.reda_training_responses add constraint reda_response_patient_plan unique(id,patient_id,plan_id);
alter table public.reda_progression_frames add constraint reda_frame_clinician_binding foreign key(patient_id,clinician_id) references public.reda_patients(id,clinician_id);
alter table public.reda_progression_frames add constraint reda_frame_source_binding foreign key(source_plan_id,patient_id) references public.reda_plans(id,patient_id);
alter table public.reda_progression_frames add constraint reda_frame_current_binding foreign key(current_plan_id,patient_id) references public.reda_plans(id,patient_id);
alter table public.reda_progression_frames add constraint reda_frame_patient_pair unique(id,patient_id);
alter table public.reda_engine_decisions add constraint reda_decision_plan_binding foreign key(plan_id,patient_id) references public.reda_plans(id,patient_id);
alter table public.reda_engine_decisions add constraint reda_decision_result_binding foreign key(result_plan_id,patient_id) references public.reda_plans(id,patient_id);
alter table public.reda_engine_decisions add constraint reda_decision_frame_binding foreign key(frame_id,patient_id) references public.reda_progression_frames(id,patient_id);
alter table public.reda_engine_decisions add constraint reda_decision_patient_pair unique(id,patient_id);
alter table public.reda_review_cases add constraint reda_case_response_binding foreign key(response_id,patient_id,plan_id) references public.reda_training_responses(id,patient_id,plan_id);
alter table public.reda_decision_reviews add constraint reda_review_decision_binding foreign key(decision_id,patient_id) references public.reda_engine_decisions(id,patient_id);
alter table public.reda_decision_reviews add constraint reda_review_clinician_binding foreign key(patient_id,clinician_id) references public.reda_patients(id,clinician_id);

create function private.reda_request_organization() returns uuid language plpgsql stable set search_path='' as $$
begin return (nullif(current_setting('request.headers',true),'')::jsonb->>'x-reda-organization')::uuid;
exception when invalid_text_representation then return null;end$$;
create function private.reda_session_valid() returns boolean language plpgsql stable security definer set search_path='' as $$
begin perform private.reda_live_actor();return true;exception when insufficient_privilege then return false;end$$;
create function private.reda_clinical_member(org uuid,actor uuid) returns boolean language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.reda_memberships m join public.reda_organizations o on o.id=m.organization_id
 join public.reda_profiles p on p.user_id=m.user_id join auth.users u on u.id=m.user_id
 where m.organization_id=org and m.user_id=actor and m.status='active' and m.clinical_access
 and o.status='active' and o.kind='clinic' and p.role='clinician' and u.deleted_at is null and (u.banned_until is null or u.banned_until<=now()))
$$;
create or replace function private.reda_is_clinician_aal2() returns boolean language sql stable security definer set search_path='' as $$
 select private.reda_session_valid() and auth.jwt()->>'aal'='aal2' and private.reda_clinical_member(private.reda_request_organization(),auth.uid())
$$;
create or replace function private.reda_owns_patient(pid uuid) returns boolean language sql stable security definer set search_path='' as $$
 select private.reda_is_clinician_aal2() and exists(select 1 from public.reda_patients p where p.id=pid and p.clinician_id=auth.uid() and p.organization_id=private.reda_request_organization())
$$;
create function private.reda_is_own_patient(pid uuid) returns boolean language sql stable security definer set search_path='' as $$
 select private.reda_session_valid() and exists(select 1 from public.reda_patients p join public.reda_organizations o on o.id=p.organization_id where p.id=pid and p.auth_user_id=auth.uid() and p.status='active' and o.status='active' and o.kind='clinic')
$$;
create function private.reda_lock_clinical_patient(pid uuid) returns void language plpgsql security definer set search_path='' as $$
begin
 perform 1 from public.reda_organizations o join public.reda_patients p on p.organization_id=o.id where p.id=pid for share of o;
 if not private.reda_owns_patient(pid) then raise exception using errcode='42501',message='Patienten är inte tillgänglig i den här arbetsytan.';end if;
end$$;
create function private.reda_patient_binding_guard() returns trigger language plpgsql security definer set search_path='' as $$
begin
 if tg_op='UPDATE' and (new.id,new.organization_id,new.clinician_id) is distinct from (old.id,old.organization_id,old.clinician_id) then raise exception using errcode='23514',message='Patientrelationen kan inte flyttas eller byta ansvarig i detta flöde.';end if;
 perform 1 from public.reda_organizations where id=new.organization_id for share;
 if tg_op='INSERT' and not private.reda_clinical_member(new.organization_id,new.clinician_id) then raise exception using errcode='42501',message='En aktiv klinik och behörig ansvarig behandlare krävs.';end if;
 if current_setting('role',true)='authenticated' and (not private.reda_is_clinician_aal2() or new.organization_id is distinct from private.reda_request_organization() or new.clinician_id is distinct from auth.uid() or (tg_op='UPDATE' and new.auth_user_id is distinct from old.auth_user_id)) then raise exception using errcode='42501',message='Patientändringen saknar behörighet.';end if;
 return new;
end$$;
create trigger reda_patient_binding before insert or update on public.reda_patients for each row execute function private.reda_patient_binding_guard();
create function private.reda_draft_guard() returns trigger language plpgsql security invoker set search_path='' as $$
begin
 if tg_op='UPDATE' and (new.id,new.patient_id,new.clinician_id,new.version) is distinct from (old.id,old.patient_id,old.clinician_id,old.version) then raise exception using errcode='23514',message='Planens relation och version är oföränderliga.';end if;
 if current_user='authenticated' then
  perform private.reda_lock_clinical_patient(new.patient_id);
  if new.status<>'draft' or (tg_op='UPDATE' and old.status<>'draft') then raise exception using errcode='42501',message='Endast utkast får ändras här.';end if;
 end if;return new;
end$$;
create trigger reda_draft_binding before insert or update on public.reda_plans for each row execute function private.reda_draft_guard();

-- Replace every permissive legacy policy (policies otherwise combine with OR).
do $$declare r record;begin
 for r in select tablename,policyname from pg_policies where schemaname='public' and tablename=any(array['reda_profiles','reda_patients','reda_plans','reda_sessions','reda_training_responses','reda_progression_frames','reda_engine_decisions','reda_review_cases','reda_decision_reviews']) loop
  execute format('drop policy %I on public.%I',r.policyname,r.tablename);
 end loop;
end$$;
create policy "live profile self" on public.reda_profiles for select to authenticated using(user_id=(select auth.uid()) and (select private.reda_session_valid()));
create policy "scoped patient read" on public.reda_patients for select to authenticated using(private.reda_owns_patient(id) or private.reda_is_own_patient(id));
create policy "scoped patient create" on public.reda_patients for insert to authenticated with check((select private.reda_is_clinician_aal2()) and organization_id=(select private.reda_request_organization()) and clinician_id=(select auth.uid()) and auth_user_id is null);
create policy "scoped patient edit" on public.reda_patients for update to authenticated using(private.reda_owns_patient(id)) with check(private.reda_owns_patient(id));
create policy "scoped plan read" on public.reda_plans for select to authenticated using(private.reda_owns_patient(patient_id) or (status='active' and private.reda_is_own_patient(patient_id)));
create policy "scoped draft create" on public.reda_plans for insert to authenticated with check(status='draft' and clinician_id=(select auth.uid()) and private.reda_owns_patient(patient_id));
create policy "scoped draft edit" on public.reda_plans for update to authenticated using(status='draft' and private.reda_owns_patient(patient_id)) with check(status='draft' and private.reda_owns_patient(patient_id));
create policy "scoped session read" on public.reda_sessions for select to authenticated using(private.reda_owns_patient(patient_id) or private.reda_is_own_patient(patient_id));
create policy "scoped response read" on public.reda_training_responses for select to authenticated using(private.reda_owns_patient(patient_id) or private.reda_is_own_patient(patient_id));
create policy "scoped frame read" on public.reda_progression_frames for select to authenticated using(private.reda_owns_patient(patient_id));
create policy "scoped decision read" on public.reda_engine_decisions for select to authenticated using(private.reda_owns_patient(patient_id) or private.reda_is_own_patient(patient_id));
create policy "scoped case read" on public.reda_review_cases for select to authenticated using(private.reda_owns_patient(patient_id));
create policy "scoped review read" on public.reda_decision_reviews for select to authenticated using(private.reda_owns_patient(patient_id));
revoke all on function private.reda_request_organization(),private.reda_session_valid(),private.reda_clinical_member(uuid,uuid),private.reda_is_own_patient(uuid),private.reda_lock_clinical_patient(uuid),private.reda_patient_binding_guard(),private.reda_draft_guard() from public,anon,authenticated;
grant execute on function private.reda_request_organization(),private.reda_session_valid(),private.reda_is_own_patient(uuid),private.reda_lock_clinical_patient(uuid) to authenticated;

create function private.reda_my_workspaces() returns jsonb language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();result jsonb;begin
 if auth.jwt()->>'aal' is distinct from 'aal2' then raise exception using errcode='42501',message='Logga in med tvåstegsverifiering.';end if;
 select coalesce(jsonb_agg(jsonb_build_object('id',o.id,'name',o.name,'kind',o.kind,'role',m.role,'clinical_access',private.reda_clinical_member(o.id,actor),'revision',m.revision,'activation_enabled',false) order by o.kind,o.name),'[]') into result
 from public.reda_memberships m join public.reda_organizations o on o.id=m.organization_id where m.user_id=actor and m.status='active' and o.status='active';return result;
end$$;
create function private.reda_workspace_team() returns jsonb language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();org uuid:=private.reda_request_organization();own boolean;result jsonb;begin
 if auth.jwt()->>'aal' is distinct from 'aal2' then raise exception using errcode='42501',message='Tvåstegsverifiering krävs.';end if;
 select m.role='owner' into own from public.reda_memberships m join public.reda_organizations o on o.id=m.organization_id where m.organization_id=org and m.user_id=actor and m.status='active' and o.status='active';
 if own is null then raise exception using errcode='42501',message='Arbetsytan är inte tillgänglig.';end if;
 select jsonb_build_object('can_manage',own,'members',coalesce(jsonb_agg(jsonb_build_object('user_id',m.user_id,'display_name',case when m.display_name='' then 'Teammedlem' else m.display_name end,'role',m.role,'clinical_access',m.clinical_access,'clinical_eligible',exists(select 1 from public.reda_profiles p join auth.users u on u.id=p.user_id where p.user_id=m.user_id and p.role='clinician' and u.deleted_at is null and (u.banned_until is null or u.banned_until<=now())),'status',m.status,'revision',m.revision,'is_self',m.user_id=actor) order by m.status,m.display_name,m.user_id),'[]')) into result from public.reda_memberships m where m.organization_id=org and (own or m.status='active');
 return result || jsonb_build_object('events',case when own then coalesce((select jsonb_agg(to_jsonb(e)) from (select id,member_id,before_state,after_state,created_at from private.reda_membership_events where organization_id=org order by id desc limit 20)e),'[]'::jsonb) else '[]'::jsonb end);
end$$;
create function private.reda_update_membership(p_user_id uuid,p_role text,p_clinical_access boolean,p_status text,p_revision integer) returns jsonb language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();org uuid:=private.reda_request_organization();m public.reda_memberships%rowtype;old_state jsonb;new_state jsonb;begin
 if auth.jwt()->>'aal' is distinct from 'aal2' then raise exception using errcode='42501',message='Tvåstegsverifiering krävs.';end if;
 -- One lock order for concurrent role changes and clinical writes.
 perform 1 from public.reda_organizations where id=org and status='active' for update;
 if not found or not exists(select 1 from public.reda_memberships where organization_id=org and user_id=actor and status='active' and role='owner') then raise exception using errcode='42501',message='Endast en aktiv ägare får ändra teamet.';end if;
 select * into m from public.reda_memberships where organization_id=org and user_id=p_user_id for update;
 if m.user_id is null then raise exception using errcode='42501',message='Medlemskapet är inte tillgängligt.';end if;
 if p_revision is distinct from m.revision then raise exception using errcode='40001',message='Teamet har ändrats. Uppdatera innan du försöker igen.';end if;
 if p_role is null or p_role not in ('owner','admin','finance','member') or p_status is null or p_status not in ('active','revoked') or p_clinical_access is null then raise exception using errcode='22023',message='Ogiltig roll eller status.';end if;
 if p_clinical_access and (not exists(select 1 from public.reda_organizations where id=org and kind='clinic') or not exists(select 1 from public.reda_profiles p join auth.users u on u.id=p.user_id where p.user_id=p_user_id and p.role='clinician' and u.deleted_at is null and (u.banned_until is null or u.banned_until<=now()))) then raise exception using errcode='42501',message='Kontot måste först vara godkänt som behandlare.';end if;
 if m.role='owner' and m.status='active' and (p_role<>'owner' or p_status<>'active') and not exists(select 1 from public.reda_memberships where organization_id=org and role='owner' and status='active' and user_id<>p_user_id) then raise exception using errcode='23514',message='Arbetsytan måste ha minst en aktiv ägare.';end if;
 old_state=jsonb_build_object('role',m.role,'clinical_access',m.clinical_access,'status',m.status,'revision',m.revision);
 if (m.role,m.clinical_access,m.status)=(p_role,p_clinical_access,p_status) then return old_state;end if;
 update public.reda_memberships set role=p_role,clinical_access=p_clinical_access,status=p_status,revision=revision+1,updated_at=now() where organization_id=org and user_id=p_user_id returning jsonb_build_object('role',role,'clinical_access',clinical_access,'status',status,'revision',revision) into new_state;
 insert into private.reda_membership_events(organization_id,actor_id,member_id,before_state,after_state) values(org,actor,p_user_id,old_state,new_state);return new_state;
end$$;
create function public.reda_my_workspaces() returns jsonb language sql security invoker set search_path='' as $$select private.reda_my_workspaces()$$;
create function public.reda_workspace_team() returns jsonb language sql security invoker set search_path='' as $$select private.reda_workspace_team()$$;
create function public.reda_update_membership(p_user_id uuid,p_role text,p_clinical_access boolean,p_status text,p_revision integer) returns jsonb language sql security invoker set search_path='' as $$select private.reda_update_membership(p_user_id,p_role,p_clinical_access,p_status,p_revision)$$;
revoke all on function public.reda_my_workspaces(),private.reda_my_workspaces(),public.reda_workspace_team(),private.reda_workspace_team(),public.reda_update_membership(uuid,text,boolean,text,integer),private.reda_update_membership(uuid,text,boolean,text,integer) from public,anon,authenticated;
grant execute on function public.reda_my_workspaces(),private.reda_my_workspaces(),public.reda_workspace_team(),private.reda_workspace_team(),public.reda_update_membership(uuid,text,boolean,text,integer),private.reda_update_membership(uuid,text,boolean,text,integer) to authenticated;
