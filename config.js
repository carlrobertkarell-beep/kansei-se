// Kansei sajtconfig. Ändra värdena här, spara, klart, alla sidor uppdateras.
window.KANSEI = {
  kampanjSlut: "30 september",   // visas i alla "t.o.m."-texter
  bokning: "https://www.bokadirekt.se/places/kansei-rehabcenter-48847"            // målet för generella Boka tid-knappar (tjänstespecifika länkar påverkas inte)
  ,halsningsvideo: ""             // sätt till "/assets/halsning.mp4" när videon är uppladdad
};

// Inkorgen för patientloggar. Tomt = lokal inkorg i webbläsaren (för test).
// Fyll i från Supabase-projektet (Settings > API) så skickas loggar dit i stället, utan mejl.
window.KANSEI.inkorg = {
  url: "",          // t.ex. "https://xyzabc.supabase.co"
  anonKey: "",      // "anon public"-nyckeln, är avsedd att ligga i klienten
  tabell: "loggar"
};
