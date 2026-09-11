-- No external AI traffic is enabled by this migration.
create table private.reda_dialogue_quota(user_id uuid not null references auth.users(id),bucket text not null,calls integer not null,primary key(user_id,bucket));
alter table private.reda_dialogue_quota enable row level security;
revoke all on private.reda_dialogue_quota from public,anon,authenticated;
create function private.reda_dialogue_context(p_plan_id uuid,p_consume boolean default false) returns jsonb language plpgsql security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();p public.reda_plans%rowtype;enabled boolean;bucket_name text;n int;slim jsonb;begin
 select rp.* into p from public.reda_plans rp join public.reda_patients pt on pt.id=rp.patient_id where rp.id=p_plan_id and rp.status='active' and pt.status='active' and pt.auth_user_id=actor;
 if p.id is null then raise exception using errcode='42501',message='Den aktuella planen krävs.';end if;
 select ai_enabled into enabled from private.reda_engine_settings;
 if enabled and p_consume then
  foreach bucket_name in array array['day:'||to_char(now() at time zone 'UTC','YYYY-MM-DD'),'hour:'||to_char(now() at time zone 'UTC','YYYY-MM-DD-HH24')] loop
   insert into private.reda_dialogue_quota(user_id,bucket,calls) values(actor,bucket_name,1) on conflict(user_id,bucket) do update set calls=private.reda_dialogue_quota.calls+1 returning calls into n;
   if n>case when bucket_name like 'day:%' then 100 else 20 end then raise exception using errcode='54000',message='Gränsen för AI-frågor är nådd. Använd planens instruktioner och återkopplingsfrågor.';end if;
  end loop;
 end if;
 select jsonb_build_object('goal',p.payload->'goal','exercises',jsonb_agg(jsonb_build_object('name',x->'name','variantLabel',x->'variantLabel','why',x->'why','instructions',x->'instructions','instruction',x->'instruction','side',x->'side','dose',x->'dose','prescribedLoad',x->'prescribedLoad','focus',x->'focus') order by ord)) into slim from jsonb_array_elements(p.payload->'exercises') with ordinality as e(x,ord);
 return jsonb_build_object('enabled',enabled,'plan',slim);
end$$;
create function public.reda_dialogue_context(p_plan_id uuid,p_consume boolean default false) returns jsonb language sql security invoker set search_path='' as $$select private.reda_dialogue_context(p_plan_id,p_consume)$$;
revoke all on function private.reda_dialogue_context(uuid,boolean),public.reda_dialogue_context(uuid,boolean) from public,anon,authenticated;
grant execute on function private.reda_dialogue_context(uuid,boolean),public.reda_dialogue_context(uuid,boolean) to authenticated;
