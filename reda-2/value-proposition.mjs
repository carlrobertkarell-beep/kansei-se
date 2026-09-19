export const redaValuePillars=[
 {id:'autonomy',audience:['clinic'],title:'EI driver rehab mellan besöken',proof:'Godkända progressionsramar kan köras autonomt med hold, regress och eskalering.'},
 {id:'exceptions',audience:['clinic'],title:'Arbeta med undantagen',proof:'Klinikern ser patienterna EI inte kan lösa, inte hela populationen.'},
 {id:'continuity',audience:['clinic','consumer'],title:'Planen förändras med träningen',proof:'Registrerade pass och uppföljningar följer samma versionsspårade rehabloop.'},
 {id:'transparent',audience:['consumer'],title:'Du ser vad som ändrats',proof:'Varje EI-driven planversion kan förklaras med exakt ordinationsdiff.'},
 {id:'help',audience:['consumer'],title:'En väg tillbaka till en människa',proof:'Det här fungerar inte stoppar automatiken och går in i behandlarens arbetskö.'}
];
export function valuePillars(audience){return redaValuePillars.filter(x=>x.audience.includes(audience))}
