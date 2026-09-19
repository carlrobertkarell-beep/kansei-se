# Multi-clinic/B2B · organisationslager

Reda får ett explicit enhetslager under organisationen: `organization → units → unit memberships → clinicians → patients`. En patient kan bindas till en enhet med en komposit foreign key som garanterar att enheten tillhör samma organisation.

Organisationsrollerna `owner/admin` är överordnade enhetsgränsen för administration. Övriga användare kräver aktiv `reda_unit_membership` med rollen `unit_admin`, `clinician` eller `viewer`. Detta är en ny operativ scope ovanpå befintlig patientägare/klinikerrelation; den senare tas inte bort i detta block.

`reda_units()` ger en MFA-skyddad organisationslista med antal aktiva medlemmar och patienter per enhet, utan patientidentiteter. Nästa block ska föra in `unit_id` i dashboard/Fleet/QA-filter och därefter lägga create/update/member-RPC med revision/audit istället för direkt tabellskrivning.
