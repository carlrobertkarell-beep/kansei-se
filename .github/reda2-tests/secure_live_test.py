from pathlib import Path
R=Path(__file__).resolve().parents[2]
def read(p): return (R/p).read_text(encoding='utf-8')
required=['reda-2/klinik-live.html','reda-2/patient.html','reda-2/clinic-live.mjs','reda-2/patient-live.mjs','reda-2/secure-browser.mjs','reda-2/backend-config.js']
for p in required:
    assert (R/p).is_file(),p
cfg=read('reda-2/backend-config.js')
assert 'sb_publishable_' in cfg
assert 'service_role' not in cfg.lower() and 'sb_secret_' not in cfg
client=read('reda-2/secure-browser.mjs')
assert '@supabase/supabase-js@2.116.0' in client
assert "functions.invoke('activate-plan'" in client
assert "functions.invoke('save-session'" in client
assert "functions.invoke('invite-patient'" in client
assert "functions.invoke('claim-clinician'" in client
assert 'signInWithOtp' in client and 'shouldCreateUser:false' in client and 'emailRedirectTo:cfg.patientUrl' in client
assert ".rpc('reda_activate_plan" not in client and ".rpc('reda_save_session" not in client
clinic=read('reda-2/clinic-live.mjs')
assert 'getAuthenticatorAssuranceLevel' not in clinic or 'finishClinicianAuth' in clinic
assert 'claimClinician' in clinic and 'createDraft' in clinic and 'activatePlan' in clinic
patient=read('reda-2/patient-live.mjs')
patient_html=read('reda-2/patient.html')
assert 'crypto.randomUUID()' in patient and "sync('started')" in patient and 'patientBootstrap' in patient
assert 'sendPatientMagicLink' in patient and 'magicLink' in patient
assert 'type="password"' not in patient_html and 'Du behöver inget lösenord' in patient_html
assert 'noindex,nofollow' in read('reda-2/klinik-live.html') and 'noindex,nofollow' in patient_html
inflight=read('reda-2/supabase/migrations/20260909_007_inflight_session_version_lock.sql')
assert 'v_existing' in inflight and "status='active'" in inflight
allow=read('reda-2/supabase/migrations/20260909_006_clinician_allowlist.sql')
assert 'revoke all' in allow.lower() and 'authenticated' in allow
for fn in ['activate-plan','save-session','invite-patient','claim-clinician']:
    text=read(f'reda-2/supabase/functions/{fn}/index.ts')
    assert '@supabase/server@1.5.3' in text and 'corsHeaders' in text
invite=read('reda-2/supabase/functions/invite-patient/index.ts')
assert 'inviteUserByEmail' not in invite and '403' in invite
assert 'supabaseAdmin' not in read('reda-2/supabase/functions/claim-clinician/index.ts')
assert 'reda_sync_session' in read('reda-2/supabase/functions/save-session/index.ts')
print('PASS: secure live Reda client/auth/sync guardrails including passwordless patient access')
