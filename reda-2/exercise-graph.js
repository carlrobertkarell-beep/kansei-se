/* Reda 2.3 · clinician-owned exercise graph. Graph order never unlocks progression. */
(function(root){'use strict';
const D=root.RedaData;
const manual={
 'chair.support':['sit_to_stand','sit-to-stand.support',1], 'chair.free':['sit_to_stand','sit-to-stand.free',2],
 'extension.easy':['knee_extension','knee-extension.seated',1], 'extension.pause':['knee_extension','knee-extension.pause',2],
 'quad_iso.supported':['knee_extension','quad-isometric',0], 'knee_extension_band.light':['knee_extension','knee-extension.band',3], 'knee_extension_band.loaded':['knee_extension','knee-extension.band-loaded',4],
 'calf.both':['calf_raise','calf-raise.bilateral',1], 'calf.single':['calf_raise','calf-raise.unilateral',3],
 'soleus.body':['calf_raise','soleus.seated',0], 'soleus.loaded':['calf_raise','soleus.loaded',2],
 'heel_raise_ecc.both':['calf_raise','calf-raise.eccentric-bilateral',2], 'heel_raise_ecc.single':['calf_raise','calf-raise.eccentric-unilateral',4],
 'plantar_calf.both':['calf_raise','calf-raise.bilateral',1], 'plantar_calf.single':['calf_raise','calf-raise.unilateral',3],
 'bridge.low':['bridge','bridge.bilateral',1], 'bridge.pause':['bridge','bridge.pause',2],
 'clam.body':['hip_abduction','clam.body',1], 'clam.band':['hip_abduction','clam.band',2],
 'abduction.support':['hip_abduction','hip-abduction.standing',1], 'abduction.build':['hip_abduction','hip-abduction.standing-build',2],
 'hip_abduction_band.light':['hip_abduction','side-step.band',2], 'hip_abduction_band.loaded':['hip_abduction','side-step.band-loaded',3],
 'side_step.light':['hip_abduction','side-step.band',2], 'side_step.loaded':['hip_abduction','side-step.band-loaded',3],
 'row.light':['shoulder_pull','row.band',1], 'row.build':['shoulder_pull','row.band-build',2], 'sit_row.light':['shoulder_pull','row.seated',0], 'sit_row.build':['shoulder_pull','row.seated-build',1],
 'rotation.light':['shoulder_er','shoulder-er.band',1], 'rotation.build':['shoulder_er','shoulder-er.band-build',2], 'isometric_er.wall':['shoulder_er','shoulder-er.isometric',0],
 'scaption.short':['shoulder_elevation','scaption.short',1], 'scaption.loaded':['shoulder_elevation','scaption.loaded',2],
 'balance.support':['balance','balance.supported',1], 'balance.light':['balance','balance.light-support',2],
 'wall_sit.high':['knee_function','wall-sit.high',1], 'wall_sit.deep':['knee_function','wall-sit.deep',2],
 'step_up.low':['knee_function','step-up.supported',1], 'step_up.standard':['knee_function','step-up.standard',2],
 'step_down.supported':['knee_function','step-down.supported',2], 'step_down.standard':['knee_function','step-down.standard',3],
 'split_squat.supported':['knee_function','split-squat.supported',2], 'split_squat.standard':['knee_function','split-squat.standard',3],
 'dead_bug.heel':['core','dead-bug.heel',1], 'dead_bug.alternating':['core','dead-bug.alternating',2],
 'bird_dog.leg':['core','bird-dog.leg',1], 'bird_dog.opposite':['core','bird-dog.opposite',2],
 'neck_rotation.gentle':['neck','neck-rotation.gentle',1], 'chin_nod.seated':['neck','chin-nod.seated',1],
 'lumbar_extension.standing':['lumbar','lumbar-extension.standing',1], 'nerve_slider.seated':['nerve','nerve-slider.seated',1],
 'wrist_extension.light':['wrist','wrist-extension.light',1], 'wrist_extension.ecc':['wrist','wrist-extension.eccentric',2]
};
const nodes={};
for(const e of D.exercises){e.variants.forEach((v,ix)=>{const id=e.id+'.'+v.id,m=manual[id]||[e.id,v.pose,ix+1];v.motion=m[1];v.pose=m[1];nodes[id]={id,exercise:e.id,variant:v.id,name:e.name+' · '+v.name,family:m[0],rank:m[2],motion:m[1],equipment:e.equipment,previous:[],next:[],review:'clinical-review-required'};});}
const families={};for(const n of Object.values(nodes))(families[n.family]??=[]).push(n);
for(const list of Object.values(families)){list.sort((a,b)=>a.rank-b.rank||a.id.localeCompare(b.id));for(let i=0;i<list.length;i++){const n=list[i],lower=list.filter(x=>x.rank<n.rank),higher=list.filter(x=>x.rank>n.rank);if(lower.length){const r=Math.max(...lower.map(x=>x.rank));n.previous=lower.filter(x=>x.rank===r).map(x=>x.id);}if(higher.length){const r=Math.min(...higher.map(x=>x.rank));n.next=higher.filter(x=>x.rank===r).map(x=>x.id);}}}
function node(exercise,variant){return nodes[exercise+'.'+variant]||null;}
function family(id){return (families[id]||[]).slice().sort((a,b)=>a.rank-b.rank||a.id.localeCompare(b.id));}
function canTransition(from,to){const a=nodes[from],b=nodes[to];return !!(a&&b&&a.family===b.family&&(a.next.includes(to)||a.previous.includes(to)));}
root.RedaGraph={version:'2.3.0',nodes,families,node,family,canTransition,progression:'clinician_only'};
})(typeof window!=='undefined'?window:globalThis);
