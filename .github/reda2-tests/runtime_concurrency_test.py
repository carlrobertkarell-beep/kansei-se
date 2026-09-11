"""Two independent PostgreSQL sessions must not publish two progression steps."""
import json,subprocess,concurrent.futures,threading
CMD=['sudo','-u','postgres','psql','-X','-qAt','-v','ON_ERROR_STOP=1','-d','reda_ei_test']
def sql(text):
 p=subprocess.run(CMD,input=text,text=True,capture_output=True,timeout=30)
 if p.returncode:raise AssertionError(p.stderr)
 return p.stdout.strip()
sql("""
update reda_sessions set created_at=now()-interval '40 days' where client_session_id=tests.id(801);
select tests.login(1,'aal2',103);
select set_config('tests.concurrent_frame',(reda_approve_frame((select id from reda_plans where patient_id=tests.id(11) and status='active'),jsonb_set(jsonb_set(jsonb_set(tests.policy(),'{steps,0,plan}',tests.plan(10)),'{steps,1,plan}',tests.plan(12)),'{steps,2,plan}',tests.plan(14)),'automatic')->>'id'),false);
update reda_progression_frames set started_at=now()-interval '10 days' where id=current_setting('tests.concurrent_frame')::uuid;
insert into reda_sessions(id,client_session_id,patient_id,plan_id,plan_version,status,started_at,created_at,completed_at,payload)
select tests.id(1000+i),tests.id(1100+i),tests.id(11),p.id,p.version,'completed',now()-make_interval(days=>10-2*i),now()-make_interval(days=>10-2*i),now()-make_interval(days=>10-2*i),'{"exercises":[{"exerciseId":"extension","status":"completed","roundsDone":1,"feedback":"light"}]}'::jsonb from generate_series(1,3)i cross join reda_plans p where p.patient_id=tests.id(11) and p.status='active';
insert into reda_training_responses(request_id,session_id,patient_id,plan_id,plan_version,reported_by,created_at,answers)
select tests.id(1200+i),s.id,s.patient_id,s.plan_id,s.plan_version,tests.id(2),now()-make_interval(days=>9-2*i),tests.answer()||'{"environment":"same"}'::jsonb from generate_series(1,3)i join reda_sessions s on s.id=tests.id(1000+i);
""")
barrier=threading.Barrier(2)
def run(n):
 barrier.wait()
 out=sql("set role authenticated; select tests.login(2); select reda_evaluate_progression(tests.id(11),tests.id(%d));"%n)
 return json.loads(out.splitlines()[-1])
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 a,b=list(pool.map(run,[1301,1302]))
assert sum(x['applied'] for x in [a,b])==1,(a,b)
assert sorted(x['code'] for x in [a,b])==['context','ready'],(a,b)
assert sql("select count(*) from reda_plans where patient_id=tests.id(11) and status='active' and payload=tests.plan(12)")=='1'
# A lost response can be retried from a new connection without another version.
for n,d in zip([1301,1302],[a,b]):
 again=json.loads(sql('set role authenticated;select tests.login(2);select reda_evaluate_progression(tests.id(11),tests.id(%d));'%n).splitlines()[-1]);assert again==d
print('PASS: simultaneous evaluations publish exactly one adjacent version; both retries are stable')
