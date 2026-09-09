-- Reda secure sync schema. Apply only to a dedicated Supabase project after privacy/compliance review.
-- Health-related data must never be placed in the public GitHub repository.
create extension if not exists pgcrypto;
create schema if not exists private;

create table if not exists public.reda_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  role text not null check (role in ('clinician','patient')),
  display_name text not null default '',
  created_at timestamptz not null default now()
);

create table if not exists public.reda_patients (
  id uuid primary key default gen_random_uuid(),
  clinician_id uuid not null references auth.users(id),
  auth_user_id uuid unique references auth.users(id),
  display_name text not null,
  status text not null default 'active' check (status in ('active','archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.reda_plans (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid not null references public.reda_patients(id) on delete cascade,
  clinician_id uuid not null references auth.users(id),
  version integer not null,
  status text not null default 'draft' check (status in ('draft','active','superseded','archived')),
  payload jsonb not null,
  created_at timestamptz not null default now(),
  activated_at timestamptz,
  superseded_at timestamptz,
  unique(patient_id,version)
);
create unique index if not exists reda_one_active_plan on public.reda_plans(patient_id) where status='active';

create table if not exists public.reda_sessions (
  id uuid primary key default gen_random_uuid(),
  client_session_id uuid not null unique,
  patient_id uuid not null references public.reda_patients(id) on delete cascade,
  plan_id uuid not null references public.reda_plans(id),
  plan_version integer not null,
  status text not null check (status in ('started','partial','completed','planned_rest')),
  started_at timestamptz not null,
  completed_at timestamptz,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.reda_audit_events (
  id bigint generated always as identity primary key,
  actor_id uuid references auth.users(id),
  patient_id uuid references public.reda_patients(id) on delete set null,
  action text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create or replace function private.reda_is_clinician_aal2()
returns boolean language sql stable security definer set search_path='' as $$
  select coalesce((auth.jwt()->>'aal')='aal2',false)
    and exists(select 1 from public.reda_profiles p where p.user_id=auth.uid() and p.role='clinician');
$$;
create or replace function private.reda_owns_patient(pid uuid)
returns boolean language sql stable security definer set search_path='' as $$
  select exists(select 1 from public.reda_patients p where p.id=pid and p.clinician_id=auth.uid());
$$;
revoke all on function private.reda_is_clinician_aal2() from public;
revoke all on function private.reda_owns_patient(uuid) from public;
grant execute on function private.reda_is_clinician_aal2() to authenticated;
grant execute on function private.reda_owns_patient(uuid) to authenticated;

alter table public.reda_profiles enable row level security;
alter table public.reda_patients enable row level security;
alter table public.reda_plans enable row level security;
alter table public.reda_sessions enable row level security;
alter table public.reda_audit_events enable row level security;

revoke all on public.reda_profiles,public.reda_patients,public.reda_plans,public.reda_sessions,public.reda_audit_events from anon,authenticated;
grant select on public.reda_profiles to authenticated;
grant select,insert,update on public.reda_patients to authenticated;
grant select,insert,update on public.reda_plans to authenticated;
grant select,insert,update on public.reda_sessions to authenticated;

create policy "profile self read" on public.reda_profiles for select to authenticated using(user_id=auth.uid());

create policy "clinician patient read" on public.reda_patients for select to authenticated
 using(clinician_id=auth.uid() and private.reda_is_clinician_aal2());
create policy "patient self read" on public.reda_patients for select to authenticated using(auth_user_id=auth.uid());
create policy "clinician patient create" on public.reda_patients for insert to authenticated
 with check(clinician_id=auth.uid() and private.reda_is_clinician_aal2() and auth_user_id is null);
create policy "clinician patient update" on public.reda_patients for update to authenticated
 using(clinician_id=auth.uid() and private.reda_is_clinician_aal2())
 with check(clinician_id=auth.uid() and private.reda_is_clinician_aal2());

create policy "clinician plan read" on public.reda_plans for select to authenticated
 using(clinician_id=auth.uid() and private.reda_is_clinician_aal2() and private.reda_owns_patient(patient_id));
create policy "patient active plan read" on public.reda_plans for select to authenticated
 using(status='active' and exists(select 1 from public.reda_patients p where p.id=patient_id and p.auth_user_id=auth.uid()));
create policy "clinician plan create" on public.reda_plans for insert to authenticated
 with check(clinician_id=auth.uid() and status='draft' and private.reda_is_clinician_aal2() and private.reda_owns_patient(patient_id));
create policy "clinician draft update" on public.reda_plans for update to authenticated
 using(clinician_id=auth.uid() and status='draft' and private.reda_is_clinician_aal2())
 with check(clinician_id=auth.uid() and status='draft' and private.reda_is_clinician_aal2());

create policy "patient session read" on public.reda_sessions for select to authenticated
 using(exists(select 1 from public.reda_patients p where p.id=patient_id and p.auth_user_id=auth.uid()));
create policy "patient session create" on public.reda_sessions for insert to authenticated
 with check(exists(select 1 from public.reda_patients p where p.id=patient_id and p.auth_user_id=auth.uid())
   and exists(select 1 from public.reda_plans rp where rp.id=plan_id and rp.patient_id=patient_id and rp.status='active'));
create policy "patient session update" on public.reda_sessions for update to authenticated
 using(exists(select 1 from public.reda_patients p where p.id=patient_id and p.auth_user_id=auth.uid()))
 with check(exists(select 1 from public.reda_patients p where p.id=patient_id and p.auth_user_id=auth.uid()));
create policy "clinician session read" on public.reda_sessions for select to authenticated
 using(private.reda_is_clinician_aal2() and private.reda_owns_patient(patient_id));

create or replace function public.reda_activate_plan(p_plan_id uuid)
returns void language plpgsql security definer set search_path='' as $$
declare v_plan public.reda_plans%rowtype;
begin
  if not private.reda_is_clinician_aal2() then raise exception 'AAL2 clinician required'; end if;
  select * into v_plan from public.reda_plans where id=p_plan_id for update;
  if v_plan.id is null or v_plan.clinician_id<>auth.uid() or not private.reda_owns_patient(v_plan.patient_id) then raise exception 'Not allowed'; end if;
  if v_plan.status<>'draft' then raise exception 'Only draft plans can be activated'; end if;
  update public.reda_plans set status='superseded',superseded_at=now() where patient_id=v_plan.patient_id and status='active';
  update public.reda_plans set status='active',activated_at=now() where id=p_plan_id;
  insert into public.reda_audit_events(actor_id,patient_id,action,metadata) values(auth.uid(),v_plan.patient_id,'plan_activated',jsonb_build_object('plan_id',p_plan_id,'version',v_plan.version));
end $$;
revoke all on function public.reda_activate_plan(uuid) from public;
grant execute on function public.reda_activate_plan(uuid) to authenticated;

-- Audit table intentionally has no browser grants. Privileged Edge Functions and activation RPC write audit events.
