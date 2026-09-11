"""Independent connections must serialize approvals against exact evidence."""
import concurrent.futures,json,subprocess,threading
CMD=['sudo','-u','postgres','psql','-X','-qAt','-v','ON_ERROR_STOP=1','-d','reda_ei_test']
def sql(text):
 p=subprocess.run(CMD,input=text,text=True,capture_output=True,timeout=30)
 if p.returncode:raise AssertionError(p.stderr)
 return p.stdout.strip()
login="set role authenticated;select tests.login(1,'aal2',103);select tests.workspace('dashboard-test');"
sql("""create function tests.dashboard_try(token text,rid integer) returns jsonb language plpgsql as $$begin
 return public.reda_dashboard_act(tests.id(700010),token,tests.id(rid),'follow_up','Concurrent fictional follow-up.',current_date+1);
 exception when serialization_failure then return jsonb_build_object('error',sqlstate);end$$;""")
def pair(ids):
 token=json.loads(sql(login+"select reda_dashboard_patient(tests.id(700010));").splitlines()[-1])['token']
 barrier=threading.Barrier(2)
 def run(rid):
  barrier.wait();return json.loads(sql(login+"select tests.dashboard_try('%s',%d);"%(token,rid)).splitlines()[-1])
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:return list(pool.map(run,ids))
a,b=pair([750001,750001]);assert a==b and 'error'not in a,(a,b)
assert sql("select count(*) from private.reda_clinic_action_receipts where request_id=tests.id(750001)")=='1'
a,b=pair([750002,750003]);assert sum(x.get('error')=='40001' for x in[a,b])==1,(a,b)
assert sql("select count(*) from private.reda_followups where patient_id=tests.id(700010)")=='1'
assert sql("select count(*) from reda_audit_events where patient_id=tests.id(700010) and action='clinic_action_approved'")=='2'
print('PASS: simultaneous identical approvals return one receipt; competing approvals reject stale evidence and never duplicate tasks')
