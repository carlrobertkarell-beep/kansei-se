# Fictional preprovisioned clinic; future activation is enabled only in legacy UI tests.
WORKSPACE_MOCK="""
export async function listWorkspaces(){return [{id:'fictional-clinic',name:'Fiktiv klinik',kind:'clinic',role:'owner',clinical_access:true,activation_enabled:true}]}
export function setWorkspace(){}
export async function workspaceTeam(){return {can_manage:false,members:[],events:[]}}
"""
