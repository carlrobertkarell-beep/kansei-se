-- Clinician-owned reusable exercise recipes and favorite IDs. No patient records in templates.
create table private.reda_plan_templates(
 id uuid primary key,organization_id uuid not null references public.reda_organizations(id),
 clinician_id uuid not null references auth.users(id),title text not null check(length(trim(title))between 2 and 100),
 payload jsonb not null,revision integer not null default 1,archived boolean not null default false,
 updated_at timestamptz not null default now(),
 foreign key(organization_id,clinician_id)references public.reda_memberships(organization_id,user_id)
);
create index reda_templates_owner on private.reda_plan_templates(organization_id,clinician_id,archived,updated_at desc);
create index reda_templates_clinician on private.reda_plan_templates(clinician_id);
create table private.reda_authoring_preferences(
 organization_id uuid not null references public.reda_organizations(id),clinician_id uuid not null references auth.users(id),
 favorites jsonb not null default '[]',primary key(organization_id,clinician_id),
 foreign key(organization_id,clinician_id)references public.reda_memberships(organization_id,user_id)
);
create index reda_authoring_preferences_clinician on private.reda_authoring_preferences(clinician_id);
alter table private.reda_plan_templates enable row level security;
alter table private.reda_authoring_preferences enable row level security;
revoke all on private.reda_plan_templates,private.reda_authoring_preferences from public,anon,authenticated;
create policy "rpc only"on private.reda_plan_templates for all to authenticated using(false)with check(false);
create policy "rpc only"on private.reda_authoring_preferences for all to authenticated using(false)with check(false);

create function private.reda_template_valid(p jsonb)returns boolean language plpgsql immutable set search_path=''as $$
declare x jsonb;k text;v numeric;begin
 if jsonb_typeof(p)is distinct from'object'or p->>'schema'is distinct from'1'or exists(select 1 from jsonb_object_keys(p)as keys(key) where keys.key not in('schema','exercises'))or jsonb_typeof(p->'exercises')is distinct from'array'then return false;end if;
 if jsonb_array_length(p->'exercises')not between 1 and 12 or length(p::text)>20000 then return false;end if;
 if(select count(distinct e->>'id')from jsonb_array_elements(p->'exercises')e)<>jsonb_array_length(p->'exercises')then return false;end if;
 for x in select * from jsonb_array_elements(p->'exercises')loop
  if jsonb_typeof(x)is distinct from'object'or exists(select 1 from jsonb_object_keys(x)as keys(key) where keys.key not in('id','variantId','dose'))or coalesce(x->>'id','')!~'^[a-z0-9_]{1,80}$'or coalesce(x->>'variantId','')!~'^[a-z0-9_-]{1,80}$'or jsonb_typeof(x->'dose')is distinct from'object'then return false;end if;
  if exists(select 1 from jsonb_object_keys(x->'dose')as keys(key) where keys.key not in('sets','reps','hold','rest','tempo'))then return false;end if;
  foreach k in array array['sets','reps','hold','rest','tempo']loop
   if jsonb_typeof(x->'dose'->k)is distinct from'number'then return false;end if;v:=(x->'dose'->>k)::numeric;
   if v<>trunc(v)or v<(case when k in('hold','rest')then 0 else 1 end)or v>(case k when'sets'then 8 when'reps'then 100 when'hold'then 180 when'rest'then 600 else 60 end)then return false;end if;
  end loop;
 end loop;return true;
 exception when others then return false;
end$$;

create function private.reda_authoring_library(p_favorites jsonb default null)returns jsonb language plpgsql security definer set search_path=''as $$
declare actor uuid:=private.reda_live_actor();org uuid:=private.reda_request_organization();result jsonb;begin
 if not private.reda_is_clinician_aal2()then raise exception using errcode='42501',message='Behandlarinloggning med MFA krävs.';end if;
 if p_favorites is not null then
  perform 1 from public.reda_organizations where id=org for share;
  if not private.reda_is_clinician_aal2()then raise exception using errcode='42501',message='Arbetsytan är inte tillgänglig.';end if;
  if jsonb_typeof(p_favorites)is distinct from'array'then raise exception using errcode='22023',message='Kontrollera favoriterna.';end if;
  if jsonb_array_length(p_favorites)>100 or exists(select 1 from jsonb_array_elements(p_favorites)x where jsonb_typeof(x)<>'string'or(x#>>'{}')!~'^[a-z0-9_]{1,80}$')then raise exception using errcode='22023',message='Favoriter får bara innehålla övnings-ID.';end if;
  insert into private.reda_authoring_preferences(organization_id,clinician_id,favorites)values(org,actor,p_favorites)on conflict(organization_id,clinician_id)do update set favorites=excluded.favorites;
 end if;
 select jsonb_build_object('favorites',coalesce((select favorites from private.reda_authoring_preferences where organization_id=org and clinician_id=actor),'[]'),
 'templates',coalesce((select jsonb_agg(to_jsonb(t)order by t.updated_at desc,t.id)from(select id,title,payload,revision,updated_at from private.reda_plan_templates where organization_id=org and clinician_id=actor and not archived order by updated_at desc,id limit 50)t),'[]'))into result;return result;
end$$;

create function private.reda_save_plan_template(p_id uuid,p_revision integer,p_title text,p_payload jsonb,p_archived boolean default false)returns jsonb language plpgsql security definer set search_path=''as $$
declare actor uuid:=private.reda_live_actor();org uuid:=private.reda_request_organization();previous private.reda_plan_templates%rowtype;result jsonb;begin
 if not private.reda_is_clinician_aal2()then raise exception using errcode='42501',message='Behandlarinloggning med MFA krävs.';end if;
 perform 1 from public.reda_organizations where id=org for share;
 if not private.reda_is_clinician_aal2()then raise exception using errcode='42501',message='Arbetsytan är inte tillgänglig.';end if;
 perform pg_advisory_xact_lock(hashtextextended(org::text||actor::text,21));
 if p_id is null or p_revision is null or p_revision<0 or coalesce(length(trim(p_title)),0)not between 2 and 100 or p_archived is null or not private.reda_template_valid(p_payload)then raise exception using errcode='22023',message='Kontrollera mallens namn, övningar och doser.';end if;
 select * into previous from private.reda_plan_templates where id=p_id for update;
 if found then
  if previous.organization_id<>org or previous.clinician_id<>actor then raise exception using errcode='42501',message='Mallen är inte tillgänglig.';end if;
  if previous.revision=p_revision+1 and previous.title=trim(p_title)and previous.payload=p_payload and previous.archived=p_archived then return to_jsonb(previous)-'organization_id'-'clinician_id';end if;
  if previous.revision<>p_revision then raise exception using errcode='40001',message='Mallen har ändrats. Öppna patienten igen för aktuella mallar.';end if;
  update private.reda_plan_templates set title=trim(p_title),payload=p_payload,archived=p_archived,revision=revision+1,updated_at=clock_timestamp()where id=p_id returning to_jsonb(reda_plan_templates)-'organization_id'-'clinician_id'into result;
 else
  if p_revision<>0 or p_archived then raise exception using errcode='40001',message='Mallen finns inte längre.';end if;
  if(select count(*)from private.reda_plan_templates where organization_id=org and clinician_id=actor and not archived)>=50 then raise exception using errcode='22023',message='Du har 50 mallar. Ta bort en mall innan du sparar en ny.';end if;
  insert into private.reda_plan_templates(id,organization_id,clinician_id,title,payload)values(p_id,org,actor,trim(p_title),p_payload)returning to_jsonb(reda_plan_templates)-'organization_id'-'clinician_id'into result;
 end if;return result;
end$$;
create function public.reda_authoring_library(p_favorites jsonb default null)returns jsonb language sql security invoker set search_path=''as $$select private.reda_authoring_library(p_favorites)$$;
create function public.reda_save_plan_template(p_id uuid,p_revision integer,p_title text,p_payload jsonb,p_archived boolean default false)returns jsonb language sql security invoker set search_path=''as $$select private.reda_save_plan_template(p_id,p_revision,p_title,p_payload,p_archived)$$;
revoke all on function private.reda_template_valid(jsonb)from public,anon,authenticated;
revoke all on function private.reda_authoring_library(jsonb),public.reda_authoring_library(jsonb),private.reda_save_plan_template(uuid,integer,text,jsonb,boolean),public.reda_save_plan_template(uuid,integer,text,jsonb,boolean)from public,anon,authenticated;
grant execute on function private.reda_authoring_library(jsonb),public.reda_authoring_library(jsonb),private.reda_save_plan_template(uuid,integer,text,jsonb,boolean),public.reda_save_plan_template(uuid,integer,text,jsonb,boolean)to authenticated;
