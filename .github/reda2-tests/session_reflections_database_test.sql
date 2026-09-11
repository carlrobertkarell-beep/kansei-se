-- Fictional services only. Run after fast_workflows_database_test.sql.
\ir ../../reda-2/secure/session-reflections.sql
insert into reda_sessions(id,client_session_id,patient_id,plan_id,plan_version,status,started_at,completed_at,payload)
select tests.id(795000+n),tests.id(795100+n),tests.id(700003),tests.id(710003),1,
case when n=3 then 'started' else 'completed' end,now()-interval '1 hour',
case when n=3 then null when n=4 then now()-interval '2 days' else now() end,'{}' from generate_series(1,5)n;
set role authenticated;select tests.login(1,'aal2',103);select tests.workspace('dashboard-test');
select set_config('tests.reflection_before',reda_dashboard_patient(tests.id(700003))->>'token',false);
select tests.login(9,'aal1',109);
select set_config('tests.reflection_input','{"barrier":"time","support":"no","exerciseId":"extension"}',false);
select set_config('tests.reflection_saved',reda_submit_session_reflection(tests.id(795001),tests.id(795201),current_setting('tests.reflection_input')::jsonb)::text,false);
select tests.ok(current_setting('tests.reflection_saved')::jsonb->>'plan_id'=tests.id(710003)::text,'reflection retains original session plan');
select tests.ok(current_setting('tests.reflection_saved')::jsonb->>'exercise_name'='Fictional knee extension','exercise name is derived by server');
select tests.ok(reda_submit_session_reflection(tests.id(795001),tests.id(795201),current_setting('tests.reflection_input')::jsonb)=current_setting('tests.reflection_saved')::jsonb,'lost response retry returns same receipt');
select tests.ok(reda_submit_session_reflection(tests.id(795001),tests.id(795202),current_setting('tests.reflection_input')::jsonb)=current_setting('tests.reflection_saved')::jsonb,'new request with same answer does not duplicate evidence');
select tests.denied('select reda_submit_session_reflection(tests.id(795001),tests.id(795201),current_setting(''tests.reflection_input'')::jsonb||''{"barrier":"none"}''::jsonb)','23505','changed retry cannot overwrite reflection');
select tests.denied('select reda_submit_session_reflection(tests.id(795002),tests.id(795201),current_setting(''tests.reflection_input'')::jsonb)','23505','request cannot move to another session');
select tests.denied('select reda_submit_session_reflection(tests.id(795002),tests.id(795202),current_setting(''tests.reflection_input'')::jsonb||''{"exerciseId":"foreign"}''::jsonb)','22023','exercise must belong to original session');
select tests.denied('select reda_submit_session_reflection(tests.id(795002),tests.id(795202),current_setting(''tests.reflection_input'')::jsonb||''{"nextDay":"settled"}''::jsonb)','22023','immediate answer cannot forge next-day evidence');
select tests.denied('select reda_submit_session_reflection(tests.id(795003),tests.id(795203),current_setting(''tests.reflection_input'')::jsonb)','22023','unfinished session cannot be reflected on');
select tests.denied('select reda_submit_session_reflection(tests.id(795004),tests.id(795204),current_setting(''tests.reflection_input'')::jsonb)','22023','past-day sessions use separate follow-up');
select tests.denied('select reda_submit_training_response(tests.id(795001),tests.id(795205),tests.answer())','22023','next-day timing remains in force');
select tests.denied('update reda_session_reflections set answers=''{}''','42501','browser cannot rewrite history');
select tests.denied('delete from reda_session_reflections','42501','browser cannot delete history');
select tests.denied('insert into reda_session_reflections default values','42501','browser cannot bypass submit ownership checks');
select tests.login(2,'aal1',101);
select tests.ok((select count(*)=0 from reda_session_reflections),'another patient cannot read reflection');
select tests.denied('select reda_submit_session_reflection(tests.id(795002),tests.id(795202),current_setting(''tests.reflection_input'')::jsonb)','42501','another patient cannot submit reflection');
select tests.login(9,'aal1',999);
select tests.denied('select reda_submit_session_reflection(tests.id(795002),tests.id(795202),current_setting(''tests.reflection_input'')::jsonb)','42501','revoked session cannot submit');
select tests.login(1,'aal1',103);
select tests.ok((select count(*)=0 from reda_session_reflections),'clinician reflection read requires MFA');
select tests.login(1,'aal2',103);select tests.workspace('clinic-b');
select tests.ok((select count(*)=0 from reda_session_reflections),'another workspace cannot read reflection');
select tests.workspace('dashboard-test');
select tests.ok((select count(*)=1 from reda_session_reflections),'assigned clinician reads confirmed reflection');
select tests.ok(reda_dashboard_patient(tests.id(700003))->'cases'->0->'reflection'->'answers'->>'barrier'='time','dashboard includes original immediate evidence');
select tests.ok(exists(select 1 from jsonb_array_elements(reda_dashboard('','priority')->'patients')x where x->>'patient_id'=tests.id(700003)::text),'immediate barrier enters grouped work queue');
select tests.ok(reda_clinic_inbox('unresolved','training_barrier')->>'total'='1','inbox count matches immediate case source');
select tests.denied('select reda_dashboard_act(tests.id(700003),current_setting(''tests.reflection_before''),tests.id(795301),''resolve_cases'',''Stale review cannot resolve a new report.'')','40001','new reflection invalidates an old clinician decision');
select tests.ok(reda_evaluate_progression(tests.id(700003),tests.id(795302))->>'code'='pending_review','unresolved reflection stops progression');
select reda_dashboard_act(tests.id(700003),reda_dashboard_patient(tests.id(700003))->>'token',tests.id(795303),'resolve_cases','Fiktiv granskning av hinder, bedömningen är dokumenterad.');
select tests.ok(reda_clinic_inbox('unresolved','training_barrier')->>'total'='0','clinician can explicitly finish reflected case');
select tests.login(9,'aal1',109);
select reda_submit_session_reflection(tests.id(795002),tests.id(795202),'{"barrier":"none","support":"no","exerciseId":null}');
reset role;
select tests.ok((select count(*)=1 from reda_review_cases where reflection_id is not null),'neutral reflection does not create a clinician task');
select tests.ok((select count(*)=0 from reda_training_responses where session_id=tests.id(795001)),'immediate reflection never enters next-day evidence');
select tests.ok((select count(*)=2 from reda_audit_events where action='session_reflection_submitted'),'retry produces exactly one audit event per reflection');
select tests.ok((select not automatic_enabled and not ai_enabled from private.reda_engine_settings),'automation and external AI remain closed');
set role anon;
select tests.denied('select * from reda_session_reflections','42501','anonymous reflection reads denied');
select tests.denied('select reda_submit_session_reflection(tests.id(795002),tests.id(795202),''{}'')','42501','anonymous reflection submits denied');
reset role;
