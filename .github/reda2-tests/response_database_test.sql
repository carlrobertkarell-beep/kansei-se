-- Runs only in an empty, ephemeral CI database with fictional identities.
\set ON_ERROR_STOP on
create role anon;
create role authenticated;
create schema auth;
create table auth.users(id uuid primary key,deleted_at timestamptz,banned_until timestamptz);
create table auth.sessions(id uuid primary key,user_id uuid references auth.users);
create function auth.jwt() returns jsonb language sql stable as $$select coalesce(nullif(current_setting('request.jwt.claims',true),''),'{}')::jsonb$$;
create function auth.uid() returns uuid language sql stable as $$select (auth.jwt()->>'sub')::uuid$$;
grant usage on schema auth to authenticated,anon;
\ir ../../reda-2/supabase/migrations/20260909_001_secure_reda.sql
\ir ../../reda-2/secure/training-responses.sql
create schema tests;
grant usage on schema tests to authenticated,anon;
create function tests.id(n integer) returns uuid language sql immutable as $$select ('00000000-0000-4000-8000-'||lpad(n::text,12,'0'))::uuid$$;
create function tests.login(n integer,level text default 'aal1',sid integer default 101) returns void language sql as $$select set_config('request.jwt.claims',jsonb_build_object('sub',tests.id(n),'aal',level,'session_id',tests.id(sid))::text,false)$$;
create function tests.ok(condition boolean,label text) returns void language plpgsql as $$begin if condition is distinct from true then raise exception 'FAILED: %',label;end if;raise notice 'PASS: %',label;end$$;
create function tests.denied(command text,expected text,label text) returns void language plpgsql security invoker as $$
declare caught boolean:=false;begin
 begin execute command;exception when others then if sqlstate<>expected then raise exception 'FAILED %: expected %, got %: %',label,expected,sqlstate,sqlerrm;end if;caught:=true;end;
 perform tests.ok(caught,label);
end$$;
create function tests.answer() returns jsonb language sql immutable as $$select '{"nextDay":"settled","function":"stable","recovery":"ready","otherTraining":"usual","quality":"controlled","contact":"no"}'::jsonb$$;
insert into auth.users(id) select tests.id(n) from generate_series(1,4)n;
insert into auth.sessions values(tests.id(101),tests.id(2)),(tests.id(102),tests.id(3));
insert into reda_profiles(user_id,role) values(tests.id(1),'clinician'),(tests.id(4),'clinician');
insert into reda_patients(id,clinician_id,auth_user_id,display_name) values(tests.id(11),tests.id(1),tests.id(2),'Fictional A'),(tests.id(12),tests.id(4),tests.id(3),'Fictional B');
insert into reda_plans(id,patient_id,clinician_id,version,status,payload) values(tests.id(21),tests.id(11),tests.id(1),1,'superseded','{}'),(tests.id(22),tests.id(11),tests.id(1),2,'active','{}'),(tests.id(23),tests.id(12),tests.id(4),1,'active','{}');
insert into reda_sessions(id,client_session_id,patient_id,plan_id,plan_version,status,started_at,completed_at)
 select tests.id(30+n),tests.id(200+n),tests.id(11),tests.id(case when n=1 then 21 else 22 end),case when n=1 then 1 else 2 end,
 case when n=5 then 'started' when n=2 then 'partial' else 'completed' end,now()-interval '3 days',
 case when n=3 then now() when n=4 then now()-interval '16 days' when n=5 then null else now()-interval '2 days' end
 from generate_series(1,7)n;
insert into reda_sessions(id,client_session_id,patient_id,plan_id,plan_version,status,started_at,completed_at) values(tests.id(38),tests.id(208),tests.id(12),tests.id(23),1,'completed',now()-interval '3 days',now()-interval '2 days');
set role authenticated;
select tests.login(2);
select tests.ok((reda_submit_training_response(tests.id(31),tests.id(301),tests.answer())->>'plan_id')::uuid=tests.id(21),'response stays with superseded plan');
select tests.ok((select plan_version=1 and patient_id=tests.id(11) and reported_by=tests.id(2) from reda_training_responses where session_id=tests.id(31)),'server-bound ownership and version');
select tests.ok(reda_submit_training_response(tests.id(31),tests.id(301),tests.answer())=reda_submit_training_response(tests.id(31),tests.id(302),tests.answer()),'same and new request retries are idempotent');
select tests.ok((select count(*)=1 from reda_training_responses),'no duplicate reply');
select tests.denied('select reda_submit_training_response(tests.id(31),tests.id(303),tests.answer()||''{"contact":"yes"}''::jsonb)','23505','saved answers cannot be silently overwritten');
select tests.denied('select reda_submit_training_response(tests.id(32),tests.id(301),tests.answer())','23505','request cannot move between sessions');
select tests.denied('select reda_submit_training_response(tests.id(38),tests.id(304),tests.answer())','42501','cross-patient session refused');
select tests.denied('select reda_submit_training_response(tests.id(33),tests.id(305),tests.answer())','22023','same-day response refused');
select tests.denied('select reda_submit_training_response(tests.id(34),tests.id(306),tests.answer())','22023','stale response refused');
select tests.denied('select reda_submit_training_response(tests.id(35),tests.id(307),tests.answer())','22023','unfinished session refused');
select tests.denied('select reda_submit_training_response(tests.id(36),tests.id(308),tests.answer()||''{"contact":null}''::jsonb)','23514','JSON null rejected');
select tests.denied('select reda_submit_training_response(tests.id(36),tests.id(308),tests.answer()||''{"dose":100}''::jsonb)','23514','extra fields rejected');
select tests.denied('select reda_submit_training_response(tests.id(36),tests.id(308),tests.answer()-''quality'')','23514','missing field rejected');
select tests.denied('select reda_submit_training_response(tests.id(36),tests.id(308),tests.answer()||''{"nextDay":"fine"}''::jsonb)','23514','unknown enum rejected');
select tests.denied('select reda_submit_training_response(tests.id(36),tests.id(308),null)','22023','SQL null rejected');
select tests.ok((reda_submit_training_response(tests.id(32),tests.id(309),tests.answer()||'{"quality":"unknown"}'::jsonb)->'answers'->>'quality')='unknown','closed partial session and explicit uncertainty accepted');
select tests.denied('delete from reda_training_responses','42501','browser delete forbidden');
select tests.denied('update reda_training_responses set answers=tests.answer()','42501','browser update forbidden');
select tests.denied('insert into reda_training_responses default values','42501','direct browser insert forbidden');
select tests.login(2,'aal1',999);
select tests.denied('select reda_submit_training_response(tests.id(36),tests.id(310),tests.answer())','42501','revoked session refused');
select tests.login(2,'aal1',102);
select tests.denied('select reda_submit_training_response(tests.id(36),tests.id(310),tests.answer())','42501','foreign auth session refused');
reset role;
update auth.users set banned_until=now()+interval '1 day' where id=tests.id(2);
set role authenticated;
select tests.login(2);
select tests.denied('select reda_submit_training_response(tests.id(36),tests.id(310),tests.answer())','42501','banned user refused');
reset role;
update auth.users set banned_until=null,deleted_at=now() where id=tests.id(2);
set role authenticated;
select tests.denied('select reda_submit_training_response(tests.id(36),tests.id(310),tests.answer())','42501','deleted user refused');
reset role;
update auth.users set deleted_at=null where id=tests.id(2);
update reda_patients set status='archived' where id=tests.id(11);
set role authenticated;
select tests.denied('select reda_submit_training_response(tests.id(36),tests.id(310),tests.answer())','42501','archived patient refused');
select tests.ok((select count(*)=0 from reda_training_responses),'archived patient cannot read replies');
reset role;
update reda_patients set status='active' where id=tests.id(11);
set role authenticated;
select tests.login(3,'aal1',102);
select tests.ok((select count(*)=0 from reda_training_responses),'patient B cannot read patient A');
select tests.ok((reda_submit_training_response(tests.id(38),tests.id(311),tests.answer())->>'patient_id')::uuid=tests.id(12),'patient B gets own binding');
select tests.login(1);
select tests.ok((select count(*)=0 from reda_training_responses),'clinician requires MFA');
select tests.login(1,'aal2');
select tests.ok((select count(*)=2 and bool_and(patient_id=tests.id(11)) from reda_training_responses),'MFA clinician reads only own patients');
select tests.login(4,'aal2');
select tests.ok((select count(*)=1 and bool_and(patient_id=tests.id(12)) from reda_training_responses),'second clinician isolated');
reset role;
select tests.ok((select count(*)=3 and bool_and(not metadata?'answers') from reda_audit_events where action='training_response_submitted'),'exactly one audit per response without answer content');
set role anon;
select tests.denied('select * from reda_training_responses','42501','anonymous read forbidden');
select tests.denied('select reda_submit_training_response(tests.id(31),tests.id(312),tests.answer())','42501','anonymous RPC forbidden');
reset role;
