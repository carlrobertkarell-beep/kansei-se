"""Real PostgreSQL connections; fictional CI database only."""
import concurrent.futures,json,subprocess,threading,time
CMD=['sudo','-u','postgres','psql','-X','-qAt','-v','ON_ERROR_STOP=1','-d','reda_ei_test']
def sql(text):
 p=subprocess.run(CMD,input=text,text=True,capture_output=True,timeout=25)
 if p.returncode:raise AssertionError(p.stderr)
 return p.stdout.strip()
login="set role authenticated;select tests.login(1,'aal2',103);select tests.workspace('dashboard-test');"
sql("""create function tests.clinical_try(rid integer,rev integer)returns jsonb language plpgsql as $$begin
 return public.reda_save_clinical_ei_mandate(tests.id(rid),rev,true,1);
 exception when serialization_failure then return jsonb_build_object('error',sqlstate);end$$;""")
def pair(ids):
 rev=json.loads(sql(login+'select reda_clinical_ei_settings()').splitlines()[-1])['revision']
 barrier=threading.Barrier(2)
 def run(rid):
  barrier.wait();return json.loads(sql(login+f'select tests.clinical_try({rid},{rev})').splitlines()[-1])
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:return list(pool.map(run,ids))
a,b=pair([856001,856001]);assert a==b and 'error'not in a,(a,b)
a,b=pair([856002,856003]);assert sum(x.get('error')=='40001'for x in [a,b])==1,(a,b)
print('PASS: simultaneous mandate retries produce one receipt; competing revisions reject stale authority')

def locked_race(lock_sql,mutation,request,expected):
 holder=subprocess.Popen(CMD,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
 holder.stdin.write("begin;"+lock_sql+";select 'LOCKED';\n");holder.stdin.flush()
 while holder.stdout.readline().strip()!='LOCKED':
  if holder.poll()is not None:raise AssertionError(holder.stderr.read())
 try:
  with concurrent.futures.ThreadPoolExecutor(max_workers=1)as pool:
   result=pool.submit(sql,"set application_name='clinical-mandate-race';"+login+request)
   # Prove the evaluator/approver actually reached and waited on the lock.
   deadline=time.monotonic()+10
   while sql("select count(*)from pg_stat_activity where application_name='clinical-mandate-race'and wait_event_type='Lock'")!='1':
    assert not result.done(),'request bypassed authority lock'
    assert time.monotonic()<deadline,'request never reached authority lock'
    time.sleep(.05)
   holder.stdin.write(mutation+";commit;\\q\n");holder.stdin.flush();holder.wait(timeout=10)
   assert holder.returncode==0,holder.stderr.read()
   output=result.result(timeout=15).splitlines()[-1]
   assert output==expected,(output,expected)
 finally:
  if holder.poll()is None:holder.kill();holder.wait()

sql('update private.reda_engine_settings set automatic_enabled=true')
rev=int(sql("select revision from private.reda_clinical_ei_mandates where organization_id=tests.org('dashboard-test')"))
locked_race("select 1 from reda_organizations where id=tests.org('dashboard-test')for update",
 login+f'select reda_save_clinical_ei_mandate(tests.id(856004),{rev},false,1)',
 "select reda_evaluate_progression(tests.id(850001),tests.id(856010))->>'code'",'mandate_disabled')
# Approval must also see revocation that committed while it waited for the clinic.
sql("insert into reda_patients(id,organization_id,clinician_id,display_name)values(tests.id(850100),tests.org('dashboard-test'),tests.id(1),'Fictional race patient');insert into reda_plans(id,patient_id,clinician_id,version,status,payload)values(tests.id(850101),tests.id(850100),tests.id(1),1,'active',tests.plan(8));create function tests.approval_try()returns text language plpgsql as $$begin perform reda_approve_frame(tests.id(850101),tests.policy(),'automatic');return 'unexpected approval';exception when insufficient_privilege then return sqlstate;end$$;")
rev+=1
sql(login+f'select reda_save_clinical_ei_mandate(tests.id(856005),{rev},true,1)');rev+=1
locked_race("select 1 from reda_organizations where id=tests.org('dashboard-test')for update",
 login+f'select reda_save_clinical_ei_mandate(tests.id(856006),{rev},false,1)',
 'select tests.approval_try()','42501')
locked_race('select 1 from private.reda_engine_settings for update',
 'update private.reda_engine_settings set automatic_enabled=false',
 "select reda_evaluate_progression(tests.id(850001),tests.id(856011))->>'code'",'execution_closed')
assert sql('select automatic_enabled or ai_enabled from private.reda_engine_settings')=='f'
print('PASS: runtime and approval wait for mandate revocation; runtime waits for global kill switch')
