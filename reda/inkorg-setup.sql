-- Kansei: inkorg för patientloggar. Kör i Supabase > SQL Editor. Välj EU-region (Frankfurt eller Stockholm) för projektet.
create table if not exists public.loggar (
  id uuid primary key default gen_random_uuid(),
  kod text not null,
  namn text,
  program text,
  text text not null,
  payload jsonb,
  skickad timestamptz not null default now(),
  last boolean not null default false,
  constraint loggar_kod_form check (kod ~ '^[A-Z2-9]{5,17}(-[A-Z2-9]{2})?$'),
  constraint loggar_text_storlek check (length(text) < 40000),
  constraint loggar_namn_storlek check (namn is null or length(namn) <= 40)
);
create index if not exists loggar_kod_idx on public.loggar (kod, skickad desc);
alter table public.loggar enable row level security;
-- Patienten (anonym) får bara lägga in, aldrig läsa.
create policy "patient skickar" on public.loggar for insert to anon with check (true);
-- Kliniken (inloggad via e-postlänk) får läsa och markera läst.
create policy "klinik laser" on public.loggar for select to authenticated using (true);
create policy "klinik markerar" on public.loggar for update to authenticated using (true) with check (true);
-- Tillåt bara din egen e-post att logga in: Authentication > Providers > Email, stäng av "Enable sign ups" och lägg till dig som användare manuellt.

-- Checklista i Supabase innan drift:
-- 1. Project Settings > General: regionen ska vara EU (Frankfurt eller Stockholm).
-- 2. Authentication > Providers > Email: slå på, stäng av "Enable sign ups". Lägg till din e-post under Users > Add user.
-- 3. Authentication > URL Configuration: Site URL https://www.kansei.se, Redirect URLs: https://www.kansei.se/ovningar/
-- 4. Project Settings > API: kopiera Project URL och anon public till config.js under inkorg.
-- 5. Organization > Legal: godkänn personuppgiftsbiträdesavtalet (DPA), det som skickas är hälsouppgifter med namn.

-- Dina egna noter per patient. Bara inloggad klinik läser och skriver.
create table if not exists public.patientnoter (
  kod text primary key,
  note text,
  uppdaterad timestamptz not null default now()
);
alter table public.patientnoter enable row level security;
create policy "klinik noter" on public.patientnoter for all to authenticated using (true) with check (true);
