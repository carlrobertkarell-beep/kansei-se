// Files stay in memory. Only the reviewed patient's mapped fields are saved.
export const importFields={name:'Fullständigt namn',first_name:'Förnamn',last_name:'Efternamn',email:'E-post',phone:'Telefon',external_id:'Kund-ID',focus:'Behandlingsfokus',goal:'Patientens mål'};
const aliases={name:['namn','name','fullname','fullständigt namn','patientnamn','kundnamn'],first_name:['förnamn','firstname','first name'],last_name:['efternamn','lastname','last name'],email:['e-post','epost','email','e-mail','emailaddress'],phone:['telefon','mobil','phone','mobile','telefonnummer','mobilnummer'],external_id:['kund-id','kundid','customerid','customer id','patientid','patient id'],focus:['behandlingsfokus','focus'],goal:['mål','goal']};
const key=s=>s.trim().toLowerCase().replace(/[_-]/g,'').replace(/\s/g,'');
export function parsePatientFile(text){
 if(typeof text!=='string'||text.length>2_000_000)throw Error('Filen är för stor. Välj en CSV-fil på högst 2 MB.');
 text=text.replace(/^\uFEFF/,'');if(text.includes('\uFFFD')||text.includes('\0'))throw Error('Spara filen som CSV UTF-8 och försök igen.');
 const first=text.split(/\r?\n/)[0]||'',delimiter=[';',',','\t'].sort((a,b)=>first.split(b).length-first.split(a).length)[0];
 let rows=[],row=[],cell='',quoted=false,closed=false;
 const addCell=()=>{row.push(cell.trim());cell='';closed=false};
 const addRow=()=>{addCell();if(row.some(Boolean))rows.push(row);row=[];if(rows.length>10001)throw Error('Välj högst 10 000 patienter per fil.')};
 for(let i=0;i<text.length;i++){
  const c=text[i];
  if(quoted){if(c==='"'){if(text[i+1]==='"'){cell+='"';i++}else{quoted=false;closed=true}}else cell+=c;continue}
  if(c===delimiter){addCell();continue}if(c==='\n'||c==='\r'){if(c==='\r'&&text[i+1]==='\n')i++;addRow();continue}
  if(c==='"'){if(cell||closed)throw Error('Ogiltiga citattecken i CSV-filen.');quoted=true;continue}
  if(closed&&!/\s/.test(c))throw Error('Kontrollera avgränsarna i CSV-filen.');if(!closed)cell+=c;
 }
 if(quoted)throw Error('En citerad cell saknar avslutande citattecken.');if(cell||row.length||closed)addRow();
 if(rows.length<2)throw Error('Filen behöver en rubrikrad och minst en patient.');
 const headers=rows.shift();if(headers.length>60||rows.some(r=>r.length!==headers.length))throw Error('Alla rader måste ha samma antal kolumner, högst 60.');
 const mapping={};for(const [field,names]of Object.entries(aliases)){const found=headers.map((h,i)=>names.some(n=>key(n)===key(h))?i:-1).filter(i=>i>=0);mapping[field]=found.length===1?found[0]:-1}
 return {headers,rows,mapping};
}
export function mappedPatient(row,mapping){
 const get=field=>Number.isInteger(mapping[field])&&mapping[field]>=0?String(row[mapping[field]]||'').trim():'';
 return {name:get('name')||[get('first_name'),get('last_name')].filter(Boolean).join(' '),email:get('email'),phone:get('phone'),external_id:get('external_id'),focus:get('focus'),goal:get('goal')};
}
