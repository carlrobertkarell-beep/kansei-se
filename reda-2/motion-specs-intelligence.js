/* Reda motion specs · Exercise Intelligence. Each materially different advanced variant gets its own spec. */
(function(root){'use strict';const M=root.RedaMotionSpecs;if(!M?.specs)return;const S=M.specs,add=(key,kind,opt={})=>S[key]={key,kind,version:2,review:'clinical-review-required',camera:opt.camera||'side',equipment:opt.equipment||[],range:opt.range||1,pause:opt.pause||0,tempo:opt.tempo||'controlled',label:opt.label||key};
add('leg-press.bilateral','legPress',{equipment:['machine'],label:'Benpress två ben'});add('leg-press.single','legPressSingle',{equipment:['machine'],label:'Benpress ett ben'});
add('knee-extension.machine','kneeExtensionMachine',{equipment:['machine'],label:'Knäextension i maskin'});add('knee-extension.machine-heavy','kneeExtensionMachine',{equipment:['machine','load'],tempo:'slow',label:'Tung långsam knäextension'});
add('spanish-squat.iso','spanishSquat',{equipment:['band'],pause:.45,range:.8,label:'Isometrisk Spanish squat'});add('spanish-squat.dynamic','spanishSquat',{equipment:['band'],label:'Dynamisk Spanish squat'});
add('split-squat.rfess','rfess',{equipment:['bench'],label:'Bakre fot upphöjd split squat'});add('split-squat.rfess-loaded','rfess',{equipment:['bench','load'],label:'Belastad bakre fot upphöjd split squat'});
add('single-leg-squat.box-high','singleLegBox',{equipment:['box'],range:.65,label:'Enbensknäböj mot hög box'});add('single-leg-squat.box-low','singleLegBox',{equipment:['box'],label:'Enbensknäböj mot låg box'});
add('pogo.bilateral','pogo',{equipment:[],tempo:'elastic',range:.55,label:'Pogo-hopp två ben'});
add('shoulder-er.cable','cableER',{equipment:['cable'],label:'Utåtrotation i kabel'});add('shoulder-er.cable-elevated','cableERElevated',{equipment:['cable'],label:'Utåtrotation i kabel med högre armposition'});
add('landmine.two','landmine',{equipment:['barbell'],label:'Tvåhands landmine press'});add('landmine.single','landmineSingle',{equipment:['barbell'],label:'Enarms landmine press'});
add('carry.suitcase','suitcaseCarry',{equipment:['load'],label:'Suitcase carry'});
add('calf-loaded.bilateral','calfLoaded',{equipment:['load','support'],tempo:'slow',label:'Tung stående tåhävning två ben'});add('calf-loaded.single','calfLoadedSingle',{equipment:['load','support'],tempo:'slow',label:'Tung stående tåhävning ett ben'});
add('soleus.loaded','seatedCalfLoaded',{equipment:['chair','load'],tempo:'slow',label:'Tung sittande vadpress'});
add('hip-thrust.bilateral','hipThrust',{equipment:['bench','load'],label:'Hip thrust två ben'});add('hip-thrust.single','hipThrustSingle',{equipment:['bench'],label:'Hip thrust ett ben'});
add('step-down.lateral-loaded','lateralStepDown',{equipment:['step','load'],label:'Lateral step-down med belastning'});
M.version='2.6.0';})(typeof window!=='undefined'?window:globalThis);