-- Version-bound clinician-approved alternatives. No activation or rollout flags change.
create function private.reda_options_binding(p jsonb) returns jsonb language sql immutable set search_path='' as $$
 select jsonb_build_object('schema',p->'schema','context',p->'context','goal',p->'goal','schedule',p->'schedule','exercises',p->'exercises','clinicianNote',p->'clinicianNote','reviewDate',p->'reviewDate','presentation',p->'presentation','careJourney',p->'careJourney');
$$;
create function private.reda_options_valid(p jsonb) returns boolean language plpgsql immutable set search_path='' as $$
declare o jsonb:=p->'planOptions';item jsonb;x jsonb;k text;n numeric;begin
 if o is null then return true;end if;
 if jsonb_typeof(o) is distinct from 'object' or o->>'schema' is distinct from '1' or o->'approved' is distinct from 'true'::jsonb or o->'source' is distinct from private.reda_options_binding(p) or length(o::text)>250000 or p?'progressionDraft' or p?'progressionFrame' then return false;end if;
 if jsonb_typeof(o->'items') is distinct from 'array' or jsonb_array_length(o->'items') not between 1 and 3 then return false;end if;
 if (select count(distinct value->>'id') from jsonb_array_elements(o->'items'))<>jsonb_array_length(o->'items') then return false;end if;
 for item in select * from jsonb_array_elements(o->'items') loop
  if item->>'id' is null or item->>'id' not in ('less-rounds','band','floor','home') or item->>'reason' is distinct from (case when item->>'id'='less-rounds' then 'time' else 'equipment' end) or coalesce(length(trim(item->>'label')),0) not between 2 and 80 or jsonb_typeof(item->'context') is distinct from 'object' or jsonb_typeof(item->'exercises') is distinct from 'array' then return false;end if;
  if jsonb_array_length(item->'exercises') not between 1 and 12 or (select jsonb_agg(e->>'id' order by ord) from jsonb_array_elements(item->'exercises') with ordinality as xs(e,ord)) is distinct from (select jsonb_agg(e->>'id' order by ord) from jsonb_array_elements(p->'exercises') with ordinality as xs(e,ord)) then return false;end if;
  for x in select * from jsonb_array_elements(item->'exercises') loop
   if coalesce(length(x->>'variantId'),0)=0 or x->>'side' is null or x->>'side' not in ('left','right','both','simultaneous') or jsonb_typeof(x->'instructions') is distinct from 'array' or jsonb_array_length(x->'instructions') not between 1 and 30 then return false;end if;
   foreach k in array array['sets','reps','hold','rest','tempo'] loop
    if jsonb_typeof(x->'dose'->k) is distinct from 'number' then return false;end if;n:=(x->'dose'->>k)::numeric;
    if n<>trunc(n) or n<(case when k in ('hold','rest')then 0 else 1 end) or n>(case k when 'sets'then 8 when 'reps'then 100 when 'hold'then 180 when 'rest'then 600 else 60 end)then return false;end if;
   end loop;
  end loop;
 end loop;return true;
exception when others then return false;end$$;
create function private.reda_options_plan_guard() returns trigger language plpgsql set search_path='' as $$
begin
 if not private.reda_options_valid(new.payload) then raise exception using errcode='22023',message='Alternativen måste vara granskade för exakt den här ordinationen.';end if;
 if tg_op='UPDATE' and old.status<>'draft' and (old.payload?'planOptions' or new.payload?'planOptions') and new.payload is distinct from old.payload then raise exception using errcode='22023',message='Aktiva och tidigare planalternativ kan inte skrivas om.';end if;
 return new;
end$$;
create trigger reda_options_plan_guard before insert or update on public.reda_plans for each row execute function private.reda_options_plan_guard();

create function private.reda_options_session_guard() returns trigger language plpgsql set search_path='' as $$
declare option_id text:=new.payload->>'optionId';p jsonb;o jsonb;x jsonb;mark jsonb;n numeric;expected integer;begin
 if tg_op='UPDATE' and option_id is distinct from old.payload->>'optionId' then raise exception using errcode='22023',message='Ett påbörjat pass behåller sitt valda alternativ.';end if;
 if option_id is null then return new;end if;
 select payload into p from public.reda_plans where id=new.plan_id and patient_id=new.patient_id and version=new.plan_version;
 if p is null or not private.reda_options_valid(p) then raise exception using errcode='22023',message='Planens alternativ är inte tillgängliga.';end if;
 select value into o from jsonb_array_elements(p->'planOptions'->'items') where value->>'id'=option_id;
 if o is null or jsonb_typeof(new.payload->'exercises') is distinct from 'array' or jsonb_array_length(new.payload->'exercises')<>jsonb_array_length(o->'exercises') or new.status='planned_rest' then raise exception using errcode='22023',message='Passet måste följa ett godkänt alternativ.';end if;
 for x in select * from jsonb_array_elements(o->'exercises') loop
  if(select count(*) from jsonb_array_elements(new.payload->'exercises') where value->>'exerciseId'=x->>'id')<>1 then raise exception using errcode='22023',message='Övningarna stämmer inte med alternativet.';end if;
  select value into mark from jsonb_array_elements(new.payload->'exercises') where value->>'exerciseId'=x->>'id';
  expected:=(x->'dose'->>'sets')::int*case when x->>'side'='both' then 2 else 1 end;
  if jsonb_typeof(mark->'roundsDone') is distinct from 'number' or mark->>'status' is null or mark->>'status' not in ('pending','partial','completed','skipped') then raise exception using errcode='22023',message='Omgångarna kunde inte valideras.';end if;
  n:=(mark->>'roundsDone')::numeric;
  if n<>trunc(n) or n<0 or n>expected or (mark->>'status'='completed' and n<>expected) or (new.status='completed' and (mark->>'status'<>'completed' or n<>expected)) then raise exception using errcode='22023',message='Registreringen stämmer inte med den valda dosen.';end if;
 end loop;return new;
end$$;
create trigger reda_options_session_guard before insert or update on public.reda_sessions for each row execute function private.reda_options_session_guard();

-- Progression policies cannot quietly treat a shorter/alternate session as the base dose.
-- Adding the option package to the existing binding makes omission fail closed.
create or replace function private.reda_plan_binding(p jsonb) returns jsonb language sql immutable set search_path='' as $$
 select jsonb_build_object('schema',p->'schema','context',p->'context','goal',p->'goal','schedule',p->'schedule','exercises',p->'exercises','planOptions',p->'planOptions');
$$;
alter function private.reda_validate_frame(jsonb) rename to reda_validate_frame_without_options;
create function private.reda_validate_frame(p jsonb) returns boolean language plpgsql immutable set search_path='' as $$
begin
 if jsonb_typeof(p->'steps') is distinct from 'array' then return false;end if;
 if exists(select 1 from jsonb_array_elements(p->'steps') s where s->'plan'?'planOptions')then return false;end if;
 return private.reda_validate_frame_without_options(p);
end$$;
revoke all on function private.reda_options_binding(jsonb),private.reda_options_valid(jsonb),private.reda_options_plan_guard(),private.reda_options_session_guard(),private.reda_validate_frame(jsonb) from public,anon,authenticated;
grant execute on function private.reda_options_binding(jsonb),private.reda_options_valid(jsonb) to authenticated;

create or replace function private.reda_dashboard_patient(p_patient_id uuid) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();snap jsonb;result jsonb;begin
 if not private.reda_owns_patient(p_patient_id) then raise exception using errcode='42501',message='Patienten är inte tillgänglig i arbetsytan.';end if;
 snap=private.reda_dashboard_snapshot(p_patient_id);
 select jsonb_build_object('patient',to_jsonb(r)||private.reda_patient_brief(r.patient_id),'contact',(select jsonb_build_object('email',pr.email,'phone',pr.phone)from private.reda_patient_profiles pr where pr.patient_id=r.patient_id),'token',md5(snap::text),'today',(now() at time zone 'Europe/Stockholm')::date,
 'plan',case when snap->'plan'='null'::jsonb then null else (snap->'plan'->'payload')||jsonb_build_object('id',snap->'plan'->'id','version',snap->'plan'->'version') end,
 'cases',coalesce((select jsonb_agg(jsonb_build_object('id',c.id,'code',c.code,'status',c.status,'created_at',c.created_at,'plan_id',c.plan_id,'plan_version',coalesce(tr.plan_version,sr.plan_version),'answers',tr.answers,'reflection',case when sr.id is null then null else to_jsonb(sr)||jsonb_build_object('optionLabel',case when rs.payload->>'optionId' is null then 'Ordinarie pass' else (select v->>'label' from jsonb_array_elements(rp.payload->'planOptions'->'items')v where v->>'id'=rs.payload->>'optionId')end) end) order by c.created_at,c.id) from public.reda_review_cases c left join public.reda_training_responses tr on tr.id=c.response_id left join public.reda_session_reflections sr on sr.id=c.reflection_id left join public.reda_sessions rs on rs.id=sr.session_id left join public.reda_plans rp on rp.id=sr.plan_id where c.patient_id=p_patient_id and c.status<>'resolved'),'[]'::jsonb),
 'option_sessions',coalesce((select jsonb_agg(to_jsonb(recent)) from (select ss.id,ss.plan_id,ss.status,ss.completed_at,ss.payload from public.reda_sessions ss where ss.patient_id=p_patient_id and ss.plan_id=(snap->'plan'->>'id')::uuid order by ss.started_at desc,ss.id desc limit 30)recent),'[]'::jsonb),
 'prepared_frame',snap->'plan'->'payload'->'progressionDraft',
 'decision',snap->'decision','frame',case when snap->'frame'='null'::jsonb then null else jsonb_build_object('execution',snap->'frame'->'execution','current_step',snap->'frame'->'current_step','policy',snap->'frame'->'policy') end,
 'messages',coalesce((select jsonb_agg(jsonb_build_object('id',cm.id,'kind',cm.kind,'body',cm.body,'reply_to',cm.reply_to,'created_at',cm.created_at,'handled_at',cm.handled_at)order by cm.created_at,cm.id)from private.reda_clinic_messages cm where cm.patient_id=p_patient_id and (cm.handled_at is null or cm.id in (select x.id from private.reda_clinic_messages x where x.patient_id=p_patient_id order by x.created_at desc,x.id desc limit 20))),'[]'::jsonb),
 'history',coalesce((select jsonb_agg(h.result||jsonb_build_object('created_at',h.created_at) order by h.created_at desc,h.request_id)from(select cr.result,cr.created_at,cr.request_id from private.reda_clinic_action_receipts cr where cr.patient_id=p_patient_id order by cr.created_at desc,cr.request_id limit 10)h),'[]'::jsonb))into result
 from private.reda_dashboard_rows(actor,private.reda_request_organization(),p_patient_id)r;
 return result;
end$$;
