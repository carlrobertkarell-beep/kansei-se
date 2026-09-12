\ir ../../reda-2/secure/activity-log.sql
set role authenticated;select tests.login(1,'aal2',103);select tests.workspace('dashboard-test');
select tests.ok(jsonb_array_length(reda_activity_log(tests.id(700003))->'events')>0,'clinician gets real history');
select tests.ok((reda_activity_log(tests.id(700003))->>'audience')='clinician','clinical audience');
select tests.ok(jsonb_array_length(reda_activity_log(tests.id(700003),'finance')->'events')=0,'no fabricated billing');
select tests.denied('select reda_activity_log(tests.id(700003),''all'',''2026-09-12'',''2026-09-01'')','22023','invalid dates rejected');
select tests.denied('select reda_activity_log(tests.id(700003),''all'',null,null,now(),null)','22023','incomplete cursor rejected');
select tests.workspace('clinic-b');select tests.denied('select reda_activity_log(tests.id(700003))','42501','workspace isolation');
select tests.login(1,'aal1',103);select tests.workspace('dashboard-test');select tests.denied('select reda_activity_log(tests.id(700003))','42501','clinician MFA required');
select tests.login(9,'aal1',109);
select tests.ok((reda_activity_log(tests.id(700003))->>'audience')='patient','patient own history');
select tests.ok(not exists(select 1 from jsonb_array_elements(reda_activity_log(tests.id(700003))->'events')e where e->>'id' like 'draft:%' or e->>'category'='ei'),'patient never sees drafts or internal decisions');
select tests.ok(jsonb_array_length(reda_activity_log(tests.id(700003),'ei')->'events')=0,'explicit EI filter cannot disclose internal events');
select tests.login(2,'aal1',101);select tests.denied('select reda_activity_log(tests.id(700003))','42501','another patient denied');
reset role;
-- Many identical timestamps prove stable pagination without omissions.
insert into private.reda_clinic_messages(id,patient_id,author_id,kind,body,created_at)select tests.id(797000+i),tests.id(700003),tests.id(1),'clinician','Fictional message', '2026-06-01 10:00:00+00' from generate_series(1,75)i;
set role authenticated;select tests.login(9,'aal1',109);
select set_config('tests.log_page',reda_activity_log(tests.id(700003),'contact','2026-06-01','2026-06-01')::text,false);
select tests.ok(jsonb_array_length(current_setting('tests.log_page')::jsonb->'events')=50,'first page bounded');
select tests.ok(jsonb_array_length(reda_activity_log(tests.id(700003),'contact','2026-06-01','2026-06-01',(current_setting('tests.log_page')::jsonb#>>'{next_cursor,time}')::timestamptz,current_setting('tests.log_page')::jsonb#>>'{next_cursor,key}')->'events')=25,'tied timestamps paginate exactly');
reset role;
select tests.ok(not has_function_privilege('anon','public.reda_activity_log(uuid,text,date,date,timestamptz,text)','execute'),'anonymous access denied');
