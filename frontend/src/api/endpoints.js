const KONG_BASE = import.meta.env.VITE_KONG_BASE || 'http://localhost:8000'

const OUTSYSTEMS_RECORDS = 'https://personal-iipxahjd.outsystemscloud.com/ClinicalRecordServices/rest/RecordsAPI'
const OUTSYSTEMS_PATIENT = 'https://personal-wv4mxqur.outsystemscloud.com/PatientService/rest/PatientAPI'
const OUTSYSTEMS_CONSULTATION = 'https://personal-wv4mxqur.outsystemscloud.com/RecordVisitNotes/rest/ConsultationAPI'

export const ENDPOINTS = {
  // Kong internal services
  drugsPrimary: `${KONG_BASE}/drug`,
  drugsAlt: `${KONG_BASE}/drug/`,
  initiatePayment: `${KONG_BASE}/make_payment/initiate-payment`,
  retryPayment: `${KONG_BASE}/make_payment/retry-payment`,
  paymentEvents: `${KONG_BASE}/make_payment/payment-events`,
  prescriptionByPatientBase:
    import.meta.env.VITE_PRESCRIPTION_BY_PATIENT_BASE || `${KONG_BASE}/prescription`,
  prescribeMedicineBase:
    import.meta.env.VITE_PRESCRIBE_MEDICINE_BASE || `${KONG_BASE}/prescribe`,
  invoices: `${KONG_BASE}/invoice`,

  // OutSystems direct
  records: `${OUTSYSTEMS_RECORDS}/`,
  recordsByPatient: `${OUTSYSTEMS_RECORDS}/record/`,
  consultationBase: import.meta.env.VITE_CONSULTATION_BASE || OUTSYSTEMS_CONSULTATION,
  patientRegistration: `${OUTSYSTEMS_PATIENT}/patient`,
  patientById: `${OUTSYSTEMS_PATIENT}/patientId/`,
  patientsList: `${OUTSYSTEMS_PATIENT}/patients`,
}

export const STRIPE_PUBLISHABLE_KEY = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || ''

export const CONSULTATION_DRAFT_KEY = 'consultation:pending-draft'
