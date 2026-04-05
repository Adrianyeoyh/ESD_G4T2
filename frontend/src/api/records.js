import axios from 'axios'
import { ENDPOINTS } from './endpoints'
import { normalizeObjectArrayResponse } from '../utils/normalizers'

export const fetchRecordsByPatientApi = async (patientId) => {
  const response = await axios.get(
    `${ENDPOINTS.recordsByPatient}${encodeURIComponent(String(patientId))}`,
  )
  return normalizeObjectArrayResponse(response.data)
}
