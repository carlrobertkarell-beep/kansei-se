-- Fictional ephemeral database only. Verify the actual guarded deployment artifact.
\ir ../../reda-2/supabase/migrations/20260920042105_shadow_fleet_preview.sql
insert into reda_patients(id,organization_id,clinician_id,display_name)values(tests.id(860001),tests.org('dashboard-test'),tests.id(1),'Fictional ready preview');
insert into reda_plans(id,patient_id,clinician_id,version,status,payload)values(tests.id(860002),tests.id(860001),tests.id(1),1,'active',tests.plan(8));
reset role;update private.reda_engine_settings set automatic_enabled=true;
set role authenticated;select tests.login(1,'aal2',103);select tests.workspace('dashboard-test');
select reda_approve_frame(tests.id(860002),tests.policy(),'automatic');
reset role;
update reda_progression_frames set started_at=now()-interval '10 days'where patient_id=tests.id(860001)and status='approved';
insert into reda_sessions(id,client_session_id,patient_id,plan_id,plan_version,status,started_at,created_at,completed_at,payload)
select tests.id(862000+i),tests.id(863000+i),tests.id(860001),tests.id(860002),1,'completed',now()-make_interval(days=>10-2*i),now()-make_interval(days=>10-2*i),now()-make_interval(days=>10-2*i),'{"exercises":[{"exerciseId":"extension","status":"completed","roundsDone":1,"feedback":"okay"}]}'::jsonb from generate_series(1,3)i;
insert into reda_training_responses(request_id,session_id,patient_id,plan_id,plan_version,reported_by,created_at,answers)
select tests.id(864000+i),tests.id(862000+i),tests.id(860001),tests.id(860002),1,tests.id(2),now()-make_interval(days=>9-2*i),tests.answer()||'{"environment":"same"}'::jsonb from generate_series(1,3)i;
create function tests.preview_fingerprint()returns text language sql as $$select md5((select jsonb_agg(to_jsonb(p)order by id)::text from reda_plans p)||(select jsonb_agg(to_jsonb(f)order by id)::text from reda_progression_frames f)||(select count(*)::text from reda_engine_decisions)||(select count(*)::text from reda_audit_events))$$;
select set_config('tests.preview_before',tests.preview_fingerprint(),false);
set role authenticated;
select set_config('tests.preview_ready',(reda_preview_progression_batch(tests.id(860000))->'items'->0->'decision')::text,false);
select tests.ok(current_setting('tests.preview_ready')::jsonb->>'code'='ready','preview derives readiness from shared motor');
select tests.ok(current_setting('tests.preview_ready')::jsonb->>'applied'='false','preview never applies even with automatic approval and global execution open');
select tests.ok(reda_preview_progression_batch(tests.id(860000))->'items'->0->'decision'=current_setting('tests.preview_ready')::jsonb,'repeated previews produce same clinical result');
select tests.denied('select private.reda_progression_decision(tests.id(860001),null,true)','42501','shared core cannot be called directly');
reset role;
select tests.ok(tests.preview_fingerprint()=current_setting('tests.preview_before'),'preview and retry change no plan, frame, decision or audit');
update private.reda_engine_settings set automatic_enabled=false;
set role authenticated;
select tests.ok(reda_preview_progression_batch(tests.id(860000))->'items'->0->'decision'->>'code'='ready','readiness preview remains possible with execution closed');
select tests.ok(reda_preview_progression_batch(tests.id(860000))->'items'->0->'decision'->>'execution_open'='false','closed execution is reported separately');
select tests.ok(reda_evaluate_progression(tests.id(860001),tests.id(865001))->>'code'='execution_closed','normal evaluation still enforces global gate');
reset role;update private.reda_engine_settings set automatic_enabled=true;
set role authenticated;
select set_config('tests.preview_actual',reda_evaluate_progression(tests.id(860001),tests.id(865002))::text,false);
select tests.ok(current_setting('tests.preview_actual')::jsonb->>'applied'='true','normal evaluation still applies authorized exact next step');
select tests.ok(current_setting('tests.preview_actual')::jsonb->>'code'=current_setting('tests.preview_ready')::jsonb->>'code','preview and actual execution agree on readiness');
select tests.ok(reda_evaluate_progression(tests.id(860001),tests.id(865002))=current_setting('tests.preview_actual')::jsonb,'saved evaluation retries retain exact receipt');
reset role;update private.reda_engine_settings set automatic_enabled=false;
-- A large new workspace checks complete keyset coverage, with no arbitrary 500/1000 cap.
insert into reda_organizations(slug,name,kind)values('preview-test','Fictional preview scope','clinic');
insert into reda_memberships(organization_id,user_id,role,clinical_access)values(tests.org('preview-test'),tests.id(1),'owner',true),(tests.org('preview-test'),tests.id(4),'member',true);
insert into reda_patients(id,organization_id,clinician_id,display_name,status)
select tests.id(870000+i),tests.org('preview-test'),tests.id(1),'Fictional preview '||i,case when i=1007 then 'archived' else 'active'end from generate_series(1,1007)i;
insert into reda_plans(id,patient_id,clinician_id,version,status,payload)
select tests.id(880000+i),tests.id(870000+i),tests.id(1),1,'active',tests.plan(8)from generate_series(1,1007)i where i<>1006;
insert into reda_patients(id,organization_id,clinician_id,display_name)values(tests.id(872000),tests.org('preview-test'),tests.id(4),'Other clinician');
insert into reda_plans(id,patient_id,clinician_id,version,status,payload)values(tests.id(882000),tests.id(872000),tests.id(4),1,'active',tests.plan(8));
set role authenticated;select tests.workspace('preview-test');
do $$declare result jsonb;cursor_id uuid;ids uuid[]:='{}';item jsonb;begin
 loop
  result=reda_preview_progression_batch(cursor_id);
  perform tests.ok(jsonb_array_length(result->'items')<=25,'batch bounded to 25');
  for item in select value from jsonb_array_elements(result->'items')loop
   perform tests.ok(item->'decision'->>'code'='no_frame','unapproved plans remain uncovered, not ready');
   ids=array_append(ids,(item->>'patient_id')::uuid);
  end loop;
  cursor_id=(result->>'next_cursor')::uuid;exit when cursor_id is null;
 end loop;
 perform tests.ok(cardinality(ids)=1005 and (select count(distinct v)from unnest(ids)v)=1005,'all 1005 assigned active plans covered once, other staff/archive/no-plan excluded');
end$$;
select tests.login(2);
select tests.denied('select reda_preview_progression_batch()','42501','patient cannot preview clinic');
select tests.login(1,'aal1',103);
select tests.denied('select reda_preview_progression_batch()','42501','MFA required');
select tests.login(1,'aal2',999);
select tests.denied('select reda_preview_progression_batch()','42501','revoked session cannot resume preview');
select tests.login(1,'aal2',103);
reset role;update reda_memberships set status='revoked'where organization_id=tests.org('preview-test')and user_id=tests.id(1);
set role authenticated;
select tests.denied('select reda_preview_progression_batch(tests.id(870025))','42501','live membership revocation stops next batch');
reset role;update reda_memberships set status='active'where organization_id=tests.org('preview-test')and user_id=tests.id(1);
set role anon;
select tests.denied('select reda_preview_progression_batch()','42501','anonymous preview denied');
reset role;
select tests.ok((select not automatic_enabled and not ai_enabled from private.reda_engine_settings),'rollout stays closed');
