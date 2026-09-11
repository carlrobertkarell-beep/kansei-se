-- Fictional 1,000-patient clinic. Never run these fixtures against production.
\ir ../../reda-2/secure/decision-dashboard.sql
insert into reda_organizations(slug,name,kind)values('dashboard-test','Fictional dashboard clinic','clinic');
insert into reda_memberships(organization_id,user_id,role,clinical_access)values(tests.org('dashboard-test'),tests.id(1),'owner',true),(tests.org('dashboard-test'),tests.id(4),'member',true);
insert into reda_patients(id,organization_id,clinician_id,display_name,status)
select tests.id(700000+n),tests.org('dashboard-test'),tests.id(1),'Överblickpatient '||lpad(n::text,4,'0'),case when n<=400 then 'active' else 'archived' end from generate_series(1,1000)n;
insert into reda_patients(id,organization_id,clinician_id,display_name)values(tests.id(799999),tests.org('dashboard-test'),tests.id(4),'Other clinician patient');
insert into reda_plans(id,patient_id,clinician_id,version,status,payload,activated_at)
select tests.id(710000+n),tests.id(700000+n),tests.id(1),1,'active',tests.plan(8),now()from generate_series(1,400)n;
set role authenticated;
select tests.login(1,'aal2',103);select tests.workspace('dashboard-test');
select tests.ok(reda_dashboard()->'counts'->>'all'='1000','counts cover all 1,000 owned patients');
select tests.ok(reda_dashboard()->'counts'->>'active'='400','active means 400 current plans, separate from registry');
select tests.ok(reda_dashboard()->'counts'->>'archived'='600','archived patients remain searchable');
select tests.ok(reda_dashboard()->>'total'='0','a new plan alone does not create an exception');
select tests.ok(jsonb_array_length(reda_dashboard('','all')->'patients')=25,'bounded page of 25');
select tests.ok(not exists(select 1 from jsonb_array_elements(reda_dashboard('','all',0)->'patients')a join jsonb_array_elements(reda_dashboard('','all',25)->'patients')b on a->>'patient_id'=b->>'patient_id'),'adjacent pages never duplicate tied rows');
select tests.ok(reda_dashboard('ÖVERBLICKPATIENT 0999','all')->>'total'='1','case-insensitive literal Swedish search finds archive');
select tests.ok(reda_dashboard('%','all')->>'total'='0','wildcards are literal search characters');
select tests.denied('select reda_dashboard(null)','22023','invalid search rejected');
select tests.denied('select reda_dashboard_patient(tests.id(799999))','42501','same organization other assignment cannot be read');
select tests.denied('select reda_dashboard_patient(tests.id(9111))','42501','same clinician other organization cannot be read');
select tests.denied('select * from private.reda_followups','42501','raw work queue cannot bypass ownership');
select tests.denied('select private.reda_dashboard_snapshot(tests.id(9111))','42501','internal snapshot inaccessible');
select set_config('tests.dash_token',reda_dashboard_patient(tests.id(700001))->>'token',false);
select set_config('tests.dash_result',reda_dashboard_act(tests.id(700001),current_setting('tests.dash_token'),tests.id(720001),'follow_up','Fictional follow-up to complete tomorrow.',current_date+1)::text,false);
select tests.ok(reda_dashboard()->'counts'->>'waiting'='1','approved follow-up enters waiting work queue');
select tests.ok(reda_dashboard_act(tests.id(700001),current_setting('tests.dash_token'),tests.id(720001),'follow_up','Fictional follow-up to complete tomorrow.',current_date+1)=current_setting('tests.dash_result')::jsonb,'identical retry returns exact receipt');
select tests.denied('select reda_dashboard_act(tests.id(700001),current_setting(''tests.dash_token''),tests.id(720001),''follow_up'',''Different note'',current_date+1)','23505','changed retry cannot overwrite receipt');
select tests.denied('select reda_dashboard_act(tests.id(700001),current_setting(''tests.dash_token''),tests.id(720002),''follow_up'',''Stale competing action'',current_date+1)','40001','stale proposal rejected after another action');
select tests.denied('select reda_dashboard_act(tests.id(700001),reda_dashboard_patient(tests.id(700001))->>''token'',tests.id(720002),''follow_up'',''Invalid due date'',current_date-1)','22023','new follow-up cannot be scheduled in the past');
reset role;
insert into reda_sessions(id,client_session_id,patient_id,plan_id,plan_version,status,started_at,completed_at)
values(tests.id(730001),tests.id(730101),tests.id(700001),tests.id(710001),1,'completed',now()-interval '2 days',now()-interval '2 days');
insert into reda_training_responses(id,request_id,session_id,patient_id,plan_id,plan_version,reported_by,answers)
values(tests.id(740001),tests.id(740101),tests.id(730001),tests.id(700001),tests.id(710001),1,tests.id(2),tests.answer()||'{"environment":"same","nextDay":"worse"}');
-- Two signals for the same evidence are still one patient in the work queue.
insert into reda_review_cases(patient_id,plan_id,response_id,code)values(tests.id(700001),tests.id(710001),tests.id(740001),'requested_contact');
set role authenticated;
select tests.ok(reda_dashboard()->'counts'->>'priority'='1','new signal interrupts future follow-up, grouped by person');
select tests.ok(reda_dashboard()->'counts'->>'waiting'='0','patient is not counted in both queues');
select tests.ok(jsonb_array_length(reda_dashboard_patient(tests.id(700001))->'cases')=2,'proposal includes every signal affected by approval');
select tests.denied('select reda_dashboard_act(tests.id(700001),current_setting(''tests.dash_token''),tests.id(720003),''resolve_cases'',''Old evidence cannot authorize this.'')','40001','new patient feedback invalidates old approval');
select reda_dashboard_act(tests.id(700001),reda_dashboard_patient(tests.id(700001))->>'token',tests.id(720004),'follow_up','Follow up the newly changed report tomorrow.',current_date+1);
select tests.ok(reda_dashboard()->'counts'->>'waiting'='1','one click acknowledges all reviewed signals and creates one follow-up');
select reda_dashboard_act(tests.id(700001),reda_dashboard_patient(tests.id(700001))->>'token',tests.id(720005),'complete_follow_up','Fictional follow-up has been completed.');
select tests.ok(reda_dashboard()->'counts'->>'priority'='1','completing a task never silently resolves clinical signals');
select reda_dashboard_act(tests.id(700001),reda_dashboard_patient(tests.id(700001))->>'token',tests.id(720006),'resolve_cases','All displayed signals assessed in this fictional review.');
select tests.ok(reda_dashboard()->'counts'->>'priority'='0','explicit case assessment closes the grouped work item');
select tests.ok(jsonb_array_length(reda_dashboard_patient(tests.id(700001))->'history')=4,'one immutable history receipt per actual action');
select set_config('tests.plan_token',reda_dashboard_patient(tests.id(700002))->>'token',false);
reset role;
update reda_plans set status='superseded' where id=tests.id(710002);
insert into reda_plans(id,patient_id,clinician_id,version,status,payload,activated_at)values(tests.id(719002),tests.id(700002),tests.id(1),2,'active',tests.plan(10),now());
set role authenticated;
select tests.denied('select reda_dashboard_act(tests.id(700002),current_setting(''tests.plan_token''),tests.id(720007),''follow_up'',''Based on superseded plan'',current_date+1)','40001','plan replacement invalidates pending proposal');
select tests.login(1,'aal1',103);
select tests.denied('select reda_dashboard()','42501','dashboard requires MFA');
select tests.login(1,'aal2',999);
select tests.denied('select reda_dashboard()','42501','revoked session cannot read dashboard');
select tests.login(1,'aal2',103);select tests.workspace('clinic-b');
select tests.denied('select reda_dashboard_act(tests.id(700001),current_setting(''tests.dash_token''),tests.id(720001),''follow_up'',''Fictional follow-up to complete tomorrow.'',current_date+1)','42501','successful receipt cannot be replayed across workspaces');
reset role;
update reda_memberships set status='revoked' where organization_id=tests.org('dashboard-test') and user_id=tests.id(1);
set role authenticated;select tests.workspace('dashboard-test');
select tests.denied('select reda_dashboard()','42501','live membership revocation blocks queue');
select tests.denied('select reda_dashboard_act(tests.id(700001),current_setting(''tests.dash_token''),tests.id(720001),''follow_up'',''Fictional follow-up to complete tomorrow.'',current_date+1)','42501','membership revocation also blocks receipt retry');
reset role;
update reda_memberships set status='active' where organization_id=tests.org('dashboard-test') and user_id=tests.id(1);
-- One-click approval takes the prepared frame from the saved plan, never client/model input.
update reda_plans set payload=payload||jsonb_build_object('progressionDraft',tests.policy())where id=tests.id(710003);
set role authenticated;
select tests.ok(reda_dashboard_act(tests.id(700003),reda_dashboard_patient(tests.id(700003))->>'token',tests.id(720008),'approve_frame','Reviewed the complete fictional progression frame.')->'engine_result'->>'execution'='shadow','one-click frame approval stays in review mode');
select tests.ok(reda_dashboard_act(tests.id(700003),reda_dashboard_patient(tests.id(700003))->>'token',tests.id(720009),'evaluate','Pröva aktuellt underlag.')->>'plan_changed'='false','EI evaluation does not activate a patient plan');
set role anon;
select tests.denied('select reda_dashboard()','42501','anonymous access denied');
reset role;
select tests.ok((select not automatic_enabled and not ai_enabled from private.reda_engine_settings),'patient rollout flags are preserved');
select tests.ok((select count(*)=1 from reda_audit_events where action='clinic_action_approved' and metadata->>'request_id'=tests.id(720001)::text),'idempotence also applies to audit events');
-- Postgres plans/timing are recorded in CI for the 1,000-patient fixture.
set role authenticated;select tests.login(1,'aal2',103);select tests.workspace('dashboard-test');
explain(analyze,buffers)select reda_dashboard('','all',975);
reset role;
