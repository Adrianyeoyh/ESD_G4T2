import axios from 'axios'
import { ENDPOINTS } from './endpoints'
import { normalizeObjectArrayResponse } from '../utils/normalizers'

export const fetchPrescriptionsByRecordIdApi = async (recordId) => {
  const base = ENDPOINTS.prescriptionByPatientBase.replace(/\/$/, '')
  const path = base.endsWith('/prescription')
    ? `/record/${recordId}`
    : `/prescription/record/${recordId}`
  const response = await axios.get(`${base}${path}`)
  return normalizeObjectArrayResponse(response.data)
}
