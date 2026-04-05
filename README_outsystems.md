# ESD_G4T2 — Outsystems REST API Integration Guide

All APIs are already running via Docker Compose, no setup needed on your end. Just point your fetch/axios calls at the correct base URLs below.

---

## Overall & Base URL

Consultation API              # Record Visit Notes composite service, Orchestrates all services
 https://personal-wv4mxqur.outsystemscloud.com/RecordVisitNotes/rest/ConsultationAPI

Patient API                   # Patient atomic service
https://personal-wv4mxqur.outsystemscloud.com/PatientService/rest/PatientAPI

Records API                   # Clinical Records atomic service
https://personal-wv4mxqur.outsystemscloud.com/ClinicalRecordServices/rest/RecordsAPI


## Patient API

POST/patient
Create a new patient.
NewPatient object, required (body)
Request body:
{
  "patientId": "",
  "name": "",
  "phoneNo": 0,
  "email": ""
}
Response 200 — successful creation.

GET/patientId/{patientId}
Fetch a patient by patientId.
patientId string, required (path)
Response 200: returns a single patient object:
{
  "patientId": 0,
  "name": "",
  "phoneNo": 0,
  "email": ""
}

GET/patients
Get list of all patients.
No parameters
Response 200: returns array of patient objects:
[
  {
    "patientId": "",
    "name": "",
    "phoneNo": 0,
    "email": ""
  }
]

## Records API

POST/Record
Create a new record.
Record input object, required (body)
Request body:
{
  "VisitNotes": "",
  "PatientId": ""
}
Response 200 — returns new record.
{
  "Date": "2014-12-31",
  "isClosed": false,
  "recordId": 0
}

GET/record/{patientId}
Fetch a record(s) by patientId.
patientId string, required (path)
Response 200: returns array of record objects:
[
  {
    "Id": 1234567891234567,
    "date": "2014-12-31",
    "VisitNotes": "",
    "isClosed": false,
    "patientId": ""
  }
]

GET/recordId/{recordId}
Fetch a record by recordId.
recordId integer, required (path)
Response 200: returns record object:
{
  "Id": 1234567891234567,
  "date": "2014-12-31",
  "VisitNotes": "",
  "isClosed": false,
  "patientId": ""
}

## Consultation API

POST/consultation/{patientId}
Start Consultation.
patientId string, required (path)
visitNotes string, required (body)
Request body:
{
  "VisitNotes": ""
}
Response 200 — returns new record object and an array of historical record objects.
{
  "newRecord": {
    "recordId": 0,
    "patientId": "",
    "date": "2014-12-31T23:59:59.938Z",
    "visitNotes": "",
    "isClosed": false
  },
  "history": [
    {
      "recordId": 0,
      "patientId": "",
      "date": "2014-12-31T23:59:59.938Z",
      "visitNotes": "",
      "isClosed": false
    }
  ]
}