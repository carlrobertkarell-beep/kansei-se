create table if not exists public.reda_clinician_allowlist (
  email text primary key check (email = lower(email)),
  created_at timestamptz not null default now()
);
alter table public.reda_clinician_allowlist enable row level security;
revoke all on public.reda_clinician_allowlist from anon, authenticated;
grant select,insert,update,delete on public.reda_clinician_allowlist to service_role;
create index if not exists reda_clinician_allowlist_email_idx on public.reda_clinician_allowlist(email);
