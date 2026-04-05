OutSystems REST API Integration Guide
All APIs are already running via Docker Compose — no setup needed on your end. 
Just point your fetch/axios calls at the correct base URLs below.

Base URLs
Service
Base URL
Patient Service
https://personal-wv4mxqur.outsystemscloud.com/PatientService/rest/PatientAPI
Clinical Records Service
https://personal-iipxahjd.outsystemscloud.com/ClinicalRecordServices/rest/RecordsAPI
Consultation Service
https://personal-wv4mxqur.outsystemscloud.com/RecordVisitNotes/rest/ConsultationAPI


PatientAPI
GET /patient/{nric}
Fetch a patient by NRIC.
nric — path param, string, required
Response 200 — returns a single patient object:
{
  "patientId": 0,
  "nric": "",
  "name": "",
  "phoneNo": 0,
  "email": ""
}

Example:
const res = await fetch(`${PATIENT_BASE}/patient/${nric}`);
const patient = await res.json();


POST /patient
Create a new patient.
Body — NewPatient object, required
Request body:
{
  "nric": "",
  "name": "",
  "phoneNo": 0,
  "email": ""
}

Response 200 — returns new patientId as integer (plain text).
Example:
const res = await fetch(`${PATIENT_BASE}/patient`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ nric, name, phoneNo, email })
});
const newPatientId = await res.text(); // plain integer


RecordsAPI
GET /record/{patientId}
Fetch all clinical records for a patient.
PatientId — path param, integer, required
Response 200 — returns array of record objects:
[
  {
    "Id": 0,
    "patientId": 0,
    "date": "2014-12-31",
    "VisitNotes": "",
    "isClosed": false
  }
]

Example:
const res = await fetch(`${RECORDS_BASE}/record/${patientId}`);
const records = await res.json();


POST /Record
Create a new clinical record. Note the capital R in /Record.
Body — RecordInput object, required
Request body:
{
  "Id": 0,
  "patientId": 0,
  "date": "2014-12-31",
  "VisitNotes": "",
  "isClosed": false
}

Response 200 — returns new record Id as integer (plain text).
Example:
const res = await fetch(`${RECORDS_BASE}/Record`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ Id: 0, patientId, date, VisitNotes, isClosed: false })
});
const newRecordId = await res.text(); // plain integer


ConsultationAPI
POST /consultation/{nric}
Creates a new consultation record for a patient identified by NRIC, and returns both the new record and full visit history.
nric — path param, string, required
Body — { "visitNotes": "" }, required
Response 200 — returns object:
{
  "newRecord": {
    "recordId": 0,
    "patientId": 0,
    "date": "2014-12-31T23:59:59.938Z",
    "visitNotes": "",
    "isClosed": false
  },
  "history": [
    {
      "recordId": 0,
      "patientId": 0,
      "date": "2014-12-31T23:59:59.938Z",
      "visitNotes": "",
      "isClosed": false
    }
  ]
}

Example:
const res = await fetch(`${CONSULTATION_BASE}/consultation/${nric}`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ visitNotes })
});
const { newRecord, history } = await res.json();


Quick notes
text/plain responses (POST /patient and POST /Record) come back as a raw integer string — use res.text() not res.json().
application/json responses — use res.json().
Date format from RecordsAPI is YYYY-MM-DD. ConsultationAPI returns full ISO 8601 with time (YYYY-MM-DDTHH:mm:ss.sssZ).
Id / VisitNotes in the Records schema are capitalised — match this exactly in your request body.
For new records, pass Id: 0 — the backend assigns the real ID and returns it.

