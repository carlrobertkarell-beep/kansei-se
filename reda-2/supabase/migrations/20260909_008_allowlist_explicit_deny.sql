drop policy if exists "no browser access" on public.reda_clinician_allowlist;
create policy "no browser access" on public.reda_clinician_allowlist for select to authenticated using (false);
