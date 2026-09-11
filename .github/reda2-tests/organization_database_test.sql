-- Continue after the original engine/concurrency tests. All identities are fictional.
-- Arrange the independently verified single-owner legacy bootstrap, then create
-- additional clinics AFTER migration to test shared staff and separate patients.
alter table auth.users add column email text;
update auth.users set email='fictional-owner@example.invalid' where id=tests.id(1);
create table reda_clinician_allowlist(email text primary key);
insert into reda_clinician_allowlist values('fictional-owner@example.invalid');
update reda_patients set clinician_id=tests.id(1);
update reda_plans set clinician_id=tests.id(1);
update reda_progression_frames set clinician_id=tests.id(1);
update reda_decision_reviews set clinician_id=tests.id(1);
update private.reda_engine_settings set automatic_enabled=false,ai_enabled=false;
select set_config('tests.before_plans',(select md5(string_agg(id::text||payload::text,'' order by id)) from reda_plans),false);
\ir ../../reda-2/secure/organizations.sql
\ir ../../reda-2/secure/organization-runtime.sql
select tests.ok((select md5(string_agg(id::text||payload::text,'' order by id)) from reda_plans)=current_setting('tests.before_plans'),'migration preserves every plan payload and ID');
create function tests.org(slug text) returns uuid language sql stable security definer set search_path='' as $$select id from public.reda_organizations o where o.slug=$1$$;
create function tests.workspace(slug text) returns void language sql as $$select set_config('request.headers',jsonb_build_object('x-reda-organization',tests.org(slug))::text,false)$$;
grant execute on function tests.org(text),tests.workspace(text) to authenticated,anon,service_role;
insert into auth.users(id) select tests.id(n) from generate_series(5,8)n;
insert into auth.sessions select tests.id(100+n),tests.id(n) from generate_series(5,8)n;
insert into reda_profiles(user_id,role) values(tests.id(5),'patient'),(tests.id(6),'patient'),(tests.id(7),'patient'),(tests.id(8),'patient');
insert into reda_organizations(id,slug,name,kind) values(tests.id(9100),'clinic-b','Fictional clinic B','clinic');
insert into reda_memberships(organization_id,user_id,role,clinical_access,display_name) values
 (tests.org('kansei'),tests.id(5),'owner',false,'Fictional nonclinical owner'),
 (tests.org('kansei'),tests.id(6),'admin',false,'Fictional administrator'),
 (tests.org('kansei'),tests.id(7),'finance',false,'Fictional finance'),
 (tests.org('clinic-b'),tests.id(1),'owner',true,'Same clinician in clinic B'),
 (tests.org('clinic-b'),tests.id(4),'member',true,'Other clinician in clinic B');
insert into reda_patients(id,organization_id,clinician_id,display_name) values
 (tests.id(9111),tests.org('clinic-b'),tests.id(1),'Fictional B assigned to owner'),
 (tests.id(9112),tests.org('clinic-b'),tests.id(4),'Fictional B other assignment');
insert into reda_plans(id,patient_id,clinician_id,version,status,payload) values
 (tests.id(9121),tests.id(9111),tests.id(1),1,'active',tests.plan(8)),
 (tests.id(9122),tests.id(9112),tests.id(4),1,'active',tests.plan(8));
select set_config('tests.a_plan',(select id::text from reda_plans where patient_id=tests.id(11) and status='active'),false);
select set_config('tests.a_frame',(select id::text from reda_progression_frames where patient_id=tests.id(11) order by approved_at desc limit 1),false);
select set_config('tests.a_case',(select id::text from reda_review_cases where patient_id=tests.id(11) limit 1),false);
select set_config('tests.a_decision',(select id::text from reda_engine_decisions where patient_id=tests.id(11) limit 1),false);

set role authenticated;
select tests.login(1,'aal1',103);
select tests.denied('select reda_my_workspaces()','42501','workspace discovery requires MFA');
select tests.login(1,'aal2',103);
select tests.ok(jsonb_array_length(reda_my_workspaces())=3,'one staff identity has independent clinic and direct memberships');
select set_config('request.headers','{}',false);
select tests.ok((select count(*)=0 from reda_patients),'no workspace means no clinical patient list');
select tests.workspace('kansei');
select tests.ok((select count(*)=2 from reda_patients),'legacy relations bound to Kansei');
select tests.workspace('clinic-b');
select tests.ok((select count(*)=1 from reda_patients),'same clinician sees only current workspace and own assignment');
select tests.ok((select count(*)=1 from reda_plans),'plan list remains scoped');
select tests.ok((select count(*)=0 from reda_sessions),'foreign session list hidden');
select tests.ok((select count(*)=0 from reda_training_responses),'foreign response list hidden');
select tests.ok((select count(*)=0 from reda_progression_frames),'foreign frame list hidden');
select tests.ok((select count(*)=0 from reda_engine_decisions),'foreign decision list hidden');
select tests.ok((select count(*)=0 from reda_review_cases),'foreign case list hidden');
select tests.ok((select count(*)=0 from reda_decision_reviews),'foreign review list hidden');
select tests.ok((reda_clinic_inbox()->>'total')::int=0,'definer inbox cannot span same clinician memberships');
select tests.denied('select reda_approve_frame(current_setting(''tests.a_plan'')::uuid,tests.policy())','42501','cannot approve another workspace frame');
select tests.denied('select reda_revoke_frame(current_setting(''tests.a_frame'')::uuid)','42501','cannot revoke another workspace frame');
select tests.denied('select reda_handle_case(current_setting(''tests.a_case'')::uuid,''resolved'',''Fictional review'')','42501','cannot handle another workspace case');
select tests.denied('select reda_evaluate_progression(tests.id(11),tests.id(9200))','42501','cannot evaluate another workspace patient');
select tests.denied('select reda_review_decision(current_setting(''tests.a_decision'')::uuid,''agree'',''Fictional review'')','42501','cannot review another workspace decision');
select tests.denied('select reda_approve_frame(tests.id(9122),tests.policy())','42501','same clinic does not grant another clinician assignment');
select tests.ok(reda_approve_frame(tests.id(9121),tests.policy())->>'execution'='shadow','own assigned patient still supports frame approval');
select tests.ok(reda_evaluate_progression(tests.id(9111),tests.id(9201))->>'applied'='false','shadow evaluation remains available in chosen workspace');
select tests.denied('insert into reda_patients(organization_id,clinician_id,display_name) values(tests.org(''kansei''),tests.id(1),''Wrong workspace'')','42501','forged organization rejected on insert');
select tests.denied('update reda_patients set organization_id=tests.org(''kansei'') where id=tests.id(9111)','23514','patient cannot be moved to another clinic');
select tests.denied('update reda_patients set clinician_id=tests.id(4) where id=tests.id(9111)','23514','assignment cannot be silently replaced');
select tests.denied('update reda_patients set auth_user_id=tests.id(8) where id=tests.id(9111)','42501','browser cannot attach arbitrary patient login');
insert into reda_patients(id,organization_id,clinician_id,display_name) values(tests.id(9113),tests.org('clinic-b'),tests.id(1),'Own fictional draft patient');
insert into reda_plans(id,patient_id,clinician_id,version,status,payload) values(tests.id(9123),tests.id(9113),tests.id(1),1,'draft',tests.plan(8));
update reda_plans set payload=tests.plan(9) where id=tests.id(9123);
select tests.ok((select payload=tests.plan(9) from reda_plans where id=tests.id(9123)),'draft creation and editing still work');
select tests.denied('update reda_plans set patient_id=tests.id(9111) where id=tests.id(9123)','23514','draft cannot be rebound to another patient');
select tests.workspace('reda-direct');
select tests.ok((select count(*)=0 from reda_patients),'direct business owner cannot see clinic patients');
select tests.denied('insert into reda_patients(organization_id,clinician_id,display_name) values(tests.org(''reda-direct''),tests.id(1),''Not a direct onboarding'')','42501','direct workspace cannot bypass self-guided onboarding');
select tests.denied('select reda_clinic_inbox()','42501','direct owner has no clinical inbox');
select tests.denied('select reda_update_membership(tests.id(1),''owner'',true,''active'',1)','42501','clinic qualification cannot turn direct business into clinic');

select tests.workspace('kansei');
select tests.login(5,'aal2',105);
select tests.ok((reda_workspace_team()->>'can_manage')::boolean,'nonclinical owner may manage team');
select tests.ok((select count(*)=0 from reda_patients),'ownership alone exposes no health data');
select tests.denied('select reda_clinic_inbox()','42501','owner without clinical access cannot read clinical inbox');
select tests.denied('select reda_update_membership(tests.id(5),''owner'',true,''active'',1)','42501','owner cannot self-approve clinical qualification');
select reda_update_membership(tests.id(1),'owner',true,'revoked',1);
select tests.ok(jsonb_array_length(reda_workspace_team()->'events')=1,'membership change has one scoped audit event');
select tests.denied('select reda_update_membership(tests.id(1),''owner'',true,''active'',1)','40001','stale role revision rejected');
select tests.denied('select reda_update_membership(tests.id(5),''admin'',false,''active'',1)','23514','last active owner cannot demote themselves');
select tests.login(1,'aal2',103);
select tests.ok((select count(*)=0 from reda_patients),'revoked membership takes effect in existing login');
select tests.denied('select reda_clinic_inbox()','42501','revoked membership blocks old definer RPC');
select tests.ok(jsonb_array_length(reda_my_workspaces())=2,'revoked workspace disappears without account deletion');
select tests.workspace('clinic-b');
select tests.ok((select count(*)=2 from reda_patients),'revocation does not erase independent clinic B membership');
select tests.login(2);
select tests.ok((select count(*)>0 from reda_sessions),'patient can still read own history when clinician is revoked');
select tests.ok(reda_evaluate_progression(tests.id(11),tests.id(9202))->>'code'='clinician_authority','patient engine stops when frame authority is revoked');
select tests.denied('select reda_dialogue_context(tests.id(9121))','42501','patient AI context cannot access another clinic plan');
select tests.ok((reda_dialogue_context(current_setting('tests.a_plan')::uuid)->>'enabled')::boolean=false,'own dialogue context stays scoped and AI disabled');
select tests.denied('select reda_sync_session(tests.id(9230),tests.id(9121),''started'',now(),null,''{}'')','42501','authenticated session writer rejects foreign plan');
select reda_sync_session(tests.id(9230),current_setting('tests.a_plan')::uuid,'started',now(),null,'{}');
select reda_sync_session(tests.id(9230),current_setting('tests.a_plan')::uuid,'completed',now(),now(),'{}');
select tests.login(2,'aal1',999);
select tests.ok((select count(*)=0 from reda_sessions),'revoked patient session cannot read historical rows');
select tests.denied('select reda_sync_session(tests.id(9231),current_setting(''tests.a_plan'')::uuid,''started'',now(),null,''{}'')','42501','session RPC validates live login');
select tests.login(6,'aal2',106);
select tests.workspace('kansei');
select tests.ok((select count(*)=0 from reda_plans),'administrator cannot read prescriptions');
select tests.denied('select reda_update_membership(tests.id(6),''owner'',false,''active'',1)','42501','administrator cannot promote self');
select tests.login(7,'aal2',107);
select tests.ok((select count(*)=0 from reda_training_responses),'finance role cannot read health answers');
select tests.denied('select reda_clinic_inbox()','42501','finance role cannot read clinical summaries');
select tests.login(4,'aal2',104);
select tests.workspace('clinic-b');
select tests.ok((select count(*)=1 from reda_patients),'assigned second clinician sees only own patient');
select tests.ok(not (reda_workspace_team()->>'can_manage')::boolean,'clinician cannot administer team');
select tests.denied('select * from reda_memberships','42501','raw membership enumeration forbidden');
select tests.denied('select * from reda_organizations','42501','raw organization enumeration forbidden');
select tests.denied('select * from private.reda_membership_events','42501','raw role audit forbidden');
set role anon;
select tests.denied('select reda_my_workspaces()','42501','anonymous workspace discovery forbidden');
reset role;

-- Database integrity, including service-side errors which bypass RLS.
select tests.denied('insert into reda_sessions(client_session_id,patient_id,plan_id,plan_version,status) values(tests.id(9300),tests.id(11),tests.id(9121),1,''started'')','23503','cross-clinic plan/session link rejected even by privileged writer');
select tests.denied('insert into reda_plans(patient_id,clinician_id,version,status,payload) values(tests.id(9111),tests.id(4),50,''draft'',''{}'')','23503','cross-assignment prescription binding rejected');
select tests.denied('update reda_progression_frames set current_plan_id=tests.id(9121) where id=current_setting(''tests.a_frame'')::uuid','23503','frame cannot use another clinic plan');
select tests.denied('update reda_engine_decisions set result_plan_id=tests.id(9121) where id=current_setting(''tests.a_decision'')::uuid','23503','decision cannot point to another clinic result');
select tests.denied('update reda_review_cases set plan_id=tests.id(9121) where id=current_setting(''tests.a_case'')::uuid','23503','case cannot point to another clinic evidence');
set role service_role;
select tests.denied('select reda_activate_plan_internal(tests.id(9123),tests.id(1))','42501','legacy service activation remains closed');
reset role;
update reda_organizations set status='disabled' where slug='kansei';
set role authenticated;
select tests.login(2);
select tests.ok((select count(*)=0 from reda_patients),'disabled organization hides patient relation');
select tests.denied('select reda_dialogue_context(current_setting(''tests.a_plan'')::uuid)','42501','disabled organization blocks AI context');
select tests.denied('select reda_submit_training_response(tests.id(31),tests.id(301),tests.answer())','42501','disabled organization blocks response retry');
select tests.denied('select reda_evaluate_progression(tests.id(11),tests.id(9301))','42501','disabled organization blocks engine');
reset role;
update reda_organizations set status='active' where slug='kansei';
select tests.ok((select not automatic_enabled and not ai_enabled from private.reda_engine_settings),'all patient automation flags remain off');
