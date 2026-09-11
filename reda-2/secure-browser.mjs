import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.116.0?bundle'
const cfg=window.REDA_BACKEND
if(!cfg?.url||!cfg?.publishableKey) throw new Error('Reda backend saknas')
export const db=createClient(cfg.url,cfg.publishableKey,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true}})
// A separate data client captures a fixed workspace per request. The auth client
// remains the single owner of the session; workspace choice is not shared across tabs.
let workspace=null, scoped=null;
export function setWorkspace(next){
 workspace=next?{...next}:null;
 scoped=next?createClient(cfg.url,cfg.publishableKey,{accessToken:async()=>{const {data,error}=await db.auth.getSession();if(error)throw error;return data.session?.access_token??null},global:{headers:{'x-reda-organization':next.id}}}):null;
}
const clinicalClient=()=>{if(!scoped)throw Error('Välj en arbetsyta först.');return scoped};
export async function listWorkspaces(){return rpc('reda_my_workspaces',{},db)}
export async function workspaceTeam(){return rpc('reda_workspace_team',{},clinicalClient())}
export async function updateMembership(member,changes){return rpc('reda_update_membership',{p_user_id:member.user_id,p_revision:member.revision,p_role:changes.role,p_clinical_access:changes.clinical_access,p_status:changes.status},clinicalClient())}
export async function currentUser(){const {data:{user},error}=await db.auth.getUser();if(error)throw error;return user}
export async function signIn(email,password){const {error}=await db.auth.signInWithPassword({email,password});if(error)throw error}
export async function signUp(){throw new Error('Nya behandlarkonton skapas endast av Reda-administratör.')}
export async function sendPatientMagicLink(email){const {error}=await db.auth.signInWithOtp({email:String(email||'').trim().toLowerCase(),options:{emailRedirectTo:cfg.patientUrl,shouldCreateUser:false}});if(error)throw error}
export async function signOut(){setWorkspace(null);await db.auth.signOut()}
export async function aal(){const {data,error}=await db.auth.mfa.getAuthenticatorAssuranceLevel();if(error)throw error;return data}
export async function factors(){const {data,error}=await db.auth.mfa.listFactors();if(error)throw error;return data}
export async function enrollTotp(){const {data,error}=await db.auth.mfa.enroll({factorType:'totp',friendlyName:'Reda klinik'});if(error)throw error;return data}
export async function verifyTotp(factorId,code){const {data,error}=await db.auth.mfa.challengeAndVerify({factorId,code});if(error)throw error;return data}
export async function claimClinician(){const {data,error}=await db.functions.invoke('claim-clinician');if(error)throw error;if(data?.error)throw new Error(data.error);return data}
export async function clinicianProfile(){const u=await currentUser();if(!u)return null;const {data,error}=await db.from('reda_profiles').select('role,display_name').eq('user_id',u.id).maybeSingle();if(error)throw error;return data}
export async function listPatients(){const c=clinicalClient(),org=workspace.id;const u=await currentUser();const {data,error}=await c.from('reda_patients').select('id,display_name,status,updated_at,auth_user_id').eq('organization_id',org).eq('clinician_id',u.id).eq('status','active').order('updated_at',{ascending:false});if(error)throw error;return data||[]}
export async function createPatient(displayName){const c=clinicalClient(),org=workspace.id;const u=await currentUser();const {data,error}=await c.from('reda_patients').insert({organization_id:org,clinician_id:u.id,display_name:String(displayName).trim()}).select('id,display_name').single();if(error)throw error;return data}
export async function trainingResponses(patientId,c=scoped||db){try{const {data,error}=await c.from('reda_training_responses').select('id,session_id,plan_id,plan_version,created_at,answers').eq('patient_id',patientId).order('created_at',{ascending:false}).limit(100);return {responses:data||[],responseError:error?error.message:null}}catch(e){return {responses:[],responseError:e.message||'Återkopplingen kunde inte hämtas'}}}
export async function submitTrainingResponse(sessionId,requestId,answers){const {data,error}=await db.rpc('reda_submit_training_response',{p_session_id:sessionId,p_request_id:requestId,p_answers:answers});if(error)throw error;return data}
export async function patientSummary(patientId){const c=clinicalClient();const [plans,sessions,response]=await Promise.all([c.from('reda_plans').select('id,version,status,activated_at,created_at,payload').eq('patient_id',patientId).order('version',{ascending:false}),c.from('reda_sessions').select('id,client_session_id,plan_id,status,started_at,completed_at,plan_version,payload').eq('patient_id',patientId).order('started_at',{ascending:false}).limit(30),trainingResponses(patientId,c)]);if(plans.error)throw plans.error;if(sessions.error)throw sessions.error;return {plans:plans.data||[],sessions:sessions.data||[],...response}}
export async function createDraft(patientId,payload){const c=clinicalClient();const u=await currentUser();const {data:last,error:lErr}=await c.from('reda_plans').select('version').eq('patient_id',patientId).order('version',{ascending:false}).limit(1);if(lErr)throw lErr;const version=(last?.[0]?.version||0)+1;const {data,error}=await c.from('reda_plans').insert({patient_id:patientId,clinician_id:u.id,version,status:'draft',payload}).select('id,version').single();if(error)throw error;return data}
export async function activatePlan(planId){const {data,error}=await clinicalClient().functions.invoke('activate-plan',{body:{plan_id:planId,organization_id:workspace.id}});if(error)throw error;if(data?.error)throw new Error(data.error);return data}
export async function invitePatient(patientId,email){const {data,error}=await clinicalClient().functions.invoke('invite-patient',{body:{patient_id:patientId,email,organization_id:workspace.id}});if(error)throw error;if(data?.error)throw new Error(data.error);return data}
export async function patientBootstrap(){const u=await currentUser();if(!u)throw new Error('Logga in först');const {data:patient,error:pErr}=await db.from('reda_patients').select('id,display_name').eq('auth_user_id',u.id).eq('status','active').single();if(pErr)throw pErr;const {data:plan,error}=await db.from('reda_plans').select('id,version,payload,activated_at').eq('patient_id',patient.id).eq('status','active').single();if(error)throw error;const {data:sessions,error:sErr}=await db.from('reda_sessions').select('id,client_session_id,plan_id,status,started_at,completed_at,plan_version,payload').eq('patient_id',patient.id).order('started_at',{ascending:false}).limit(30);if(sErr)throw sErr;return {userId:u.id,patient,plan,sessions:sessions||[],...await trainingResponses(patient.id,db)}}
export async function saveSession(planId,session){const body={client_session_id:session.clientSessionId,plan_id:planId,status:session.status,started_at:session.startedAt,completed_at:session.completedAt||null,payload:session.payload||{}};const {data,error}=await db.functions.invoke('save-session',{body});if(error)throw error;if(data?.error)throw new Error(data.error);return data}
export async function engineOverview(patientId){const c=clinicalClient();const [frames,decisions,cases]=await Promise.all([c.from('reda_progression_frames').select('id,policy,execution,status,current_step,current_plan_id,approved_at').eq('patient_id',patientId).order('approved_at',{ascending:false}).limit(20),c.from('reda_engine_decisions').select('id,action,code,applied,result_plan_id,created_at,metrics,review:reda_decision_reviews!reda_decision_reviews_decision_id_fkey(verdict,note,created_at)').eq('patient_id',patientId).order('created_at',{ascending:false}).limit(20),c.from('reda_review_cases').select('id,code,status,handling_note,created_at,response_id,plan_id,response:reda_training_responses!reda_review_cases_response_id_fkey(plan_version,answers)').eq('patient_id',patientId).order('status',{ascending:true}).order('created_at',{ascending:false}).limit(50)]);for(const r of [frames,decisions,cases])if(r.error)throw r.error;return {frames:frames.data||[],decisions:decisions.data||[],cases:cases.data||[]}}
async function rpc(name,args,c=scoped||db){const {data,error}=await c.rpc(name,args);if(error)throw error;return data}
export const approveFrame=(planId,policy)=>rpc('reda_approve_frame',{p_plan_id:planId,p_policy:policy,p_execution:'shadow'});
export const revokeFrame=frameId=>rpc('reda_revoke_frame',{p_frame_id:frameId});
export const handleCase=(caseId,status,note)=>rpc('reda_handle_case',{p_case_id:caseId,p_status:status,p_note:note});
export const evaluateProgression=(patientId,requestId)=>rpc('reda_evaluate_progression',{p_patient_id:patientId,p_request_id:requestId});
export async function dialogue(planId,action,question,conversation){const {data,error}=await db.functions.invoke('reda-dialogue',{body:{plan_id:planId,action,...(conversation?{conversation}:{}),...(question?{question}:{})}});if(error)throw Error('AI-stödet kunde inte nås. Använd planens instruktioner eller försök igen.');if(data?.error)throw Error(data.error);return data}

export const clinicInbox=(status='unresolved',code='all',offset=0)=>rpc('reda_clinic_inbox',{p_status:status,p_code:code,p_offset:offset});
export const reviewDecision=(decisionId,verdict,note)=>rpc('reda_review_decision',{p_decision_id:decisionId,p_verdict:verdict,p_note:note});

export const dashboard=(search='',filter='priority',offset=0)=>rpc('reda_dashboard',{p_search:search,p_filter:filter,p_offset:offset},clinicalClient());
export const dashboardPatient=patientId=>rpc('reda_dashboard_patient',{p_patient_id:patientId},clinicalClient());
export const dashboardAct=({patientId,token,requestId,action,note,due})=>rpc('reda_dashboard_act',{p_patient_id:patientId,p_token:token,p_request_id:requestId,p_action:action,p_note:note,p_due_date:due},clinicalClient());

export const patientMessages=()=>rpc('reda_patient_messages',{},db);
export const patientReply=(messageId,requestId,body)=>rpc('reda_patient_reply',{p_message_id:messageId,p_request_id:requestId,p_body:body},db);
