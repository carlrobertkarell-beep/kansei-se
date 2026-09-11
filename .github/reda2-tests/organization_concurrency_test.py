"""Independent database connections: workspace context and last-owner protection."""
import concurrent.futures,json,subprocess,threading
CMD=['sudo','-u','postgres','psql','-X','-qAt','-v','ON_ERROR_STOP=1','-d','reda_ei_test']
def sql(text):
 p=subprocess.run(CMD,input=text,text=True,capture_output=True,timeout=30)
 if p.returncode:raise AssertionError(p.stderr)
 return p.stdout.strip()
sql("""
insert into reda_organizations(slug,name,kind) values('concurrency','Fictional concurrency clinic','clinic');
insert into reda_memberships(organization_id,user_id,role) values(tests.org('concurrency'),tests.id(5),'owner'),(tests.org('concurrency'),tests.id(6),'owner');
create function tests.demote_self() returns text language plpgsql as $$
begin perform public.reda_update_membership(auth.uid(),'admin',false,'active',1);return 'saved';
exception when check_violation then return sqlstate;end$$;
""")
barrier=threading.Barrier(2)
def demote(n):
 barrier.wait()
 return sql("set role authenticated;select tests.login(%d,'aal2',%d);select tests.workspace('concurrency');select tests.demote_self();"%(n,n+100)).splitlines()[-1]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 results=list(pool.map(demote,[5,6]))
assert sorted(results)==['23514','saved'],results
assert sql("select count(*) from reda_memberships where organization_id=tests.org('concurrency') and role='owner' and status='active'")=='1'
assert sql("select count(*) from private.reda_membership_events where organization_id=tests.org('concurrency')")=='1'
# The same auth identity, in two simultaneous tabs, cannot change the other tab's scope.
def read_workspace(slug):
 return sql("set role authenticated;select tests.login(1,'aal2',103);select tests.workspace('%s');select count(*) from reda_patients;"%slug).splitlines()[-1]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 results=list(pool.map(read_workspace,['kansei','clinic-b']))
assert results==['0','2'],results  # Kansei membership was revoked; clinic B is independent.
print('PASS: concurrent owner changes retain one owner; separate sessions retain their own workspace and revocation state')
