\ir ../../reda-2/secure/plan-options.sql
create function tests.options_plan() returns jsonb language sql as $$
 with b as(select jsonb_set(tests.plan(8),'{exercises,0,dose,sets}','3')p)
 select p||jsonb_build_object('planOptions',jsonb_build_object('schema',1,'approved',true,'source',private.reda_options_binding(p),'items',jsonb_build_array(jsonb_build_object('id','less-rounds','label','Kortare pass','reason','time','context',p->'context','exercises',jsonb_set(p->'exercises','{0,dose,sets}','2'))))) from b;
$$;
select tests.ok(private.reda_options_valid(tests.options_plan()),'approved options bind to exact prescription');
select tests.ok(not private.reda_options_valid(jsonb_set(tests.options_plan(),'{goal}','"changed"')),'changed goal invalidates approval');
select tests.ok(not private.reda_options_valid(jsonb_set(tests.options_plan(),'{planOptions,approved}','false')),'unreviewed options rejected');
select tests.ok(not private.reda_options_valid(tests.options_plan()||'{"progressionDraft":{}}'),'options cannot mix with progression drafts');
select tests.ok(not private.reda_validate_frame(jsonb_set(tests.policy(),'{steps,0,plan}',tests.options_plan())),'progression cannot use an option plan');
select tests.ok(private.reda_validate_frame(tests.policy()),'existing frames still validate');
reset role;
-- Dedicated fictional plan, never production activation.
update reda_plans set status='superseded' where patient_id=tests.id(700003) and status='active';
insert into reda_plans(id,patient_id,clinician_id,version,status,payload)values(tests.id(796000),tests.id(700003),tests.id(1),50,'active',tests.options_plan());
select tests.denied('update reda_plans set payload=payload-''planOptions'' where id=tests.id(796000)','22023','active option package cannot be rewritten');
set role authenticated;select tests.login(9,'aal1',109);
select set_config('tests.option_start','{"optionId":"less-rounds","exercises":[{"exerciseId":"extension","status":"pending","roundsDone":0,"feedback":null}]}',false);
select set_config('tests.option_id',reda_sync_session(tests.id(796001),tests.id(796000),'started',now(),null,current_setting('tests.option_start')::jsonb)::text,false);
select tests.denied('select reda_sync_session(tests.id(796001),tests.id(796000),''partial'',now(),null,current_setting(''tests.option_start'')::jsonb-''optionId'')','22023','cannot remove choice from open session');
select tests.denied('select reda_sync_session(tests.id(796002),tests.id(796000),''started'',now(),null,jsonb_set(current_setting(''tests.option_start'')::jsonb,''{optionId}'',''"forged"''))','22023','unknown options rejected at server');
select tests.denied('select reda_sync_session(tests.id(796001),tests.id(796000),''completed'',now(),now(),''{"optionId":"less-rounds","exercises":[{"exerciseId":"extension","status":"completed","roundsDone":3}]}''::jsonb)','22023','base dose cannot masquerade as alternate completion');
select set_config('tests.option_done','{"optionId":"less-rounds","exercises":[{"exerciseId":"extension","status":"completed","roundsDone":2,"feedback":"okay"}]}',false);
select tests.ok(reda_sync_session(tests.id(796001),tests.id(796000),'completed',now(),now(),current_setting('tests.option_done')::jsonb)::text=current_setting('tests.option_id'),'short option closes with its exact dose');
select tests.ok(reda_sync_session(tests.id(796001),tests.id(796000),'completed',now(),now(),current_setting('tests.option_done')::jsonb)::text=current_setting('tests.option_id'),'lost completion receipt retries idempotently');
select tests.login(2,'aal1',101);
select tests.denied('select reda_sync_session(tests.id(796003),tests.id(796000),''started'',now(),null,current_setting(''tests.option_start'')::jsonb)','42501','another patient cannot use options');
select tests.login(1,'aal2',103);select tests.workspace('dashboard-test');
select tests.ok(reda_dashboard_patient(tests.id(700003))->'plan'?'planOptions','dashboard includes approved source');
select tests.ok(jsonb_array_length(reda_dashboard_patient(tests.id(700003))->'option_sessions')=1,'dashboard includes current option usage only');
select tests.workspace('clinic-b');
select tests.denied('select reda_dashboard_patient(tests.id(700003))','42501','option usage remains workspace scoped');
reset role;
