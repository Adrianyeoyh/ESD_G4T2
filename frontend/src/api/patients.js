import axios from 'axios'
import { ENDPOINTS } from './endpoints'

export const fetchPatientsApi = async () => {
  const response = await axios.get(ENDPOINTS.patientsList)
  return Array.isArray(response.data) ? response.data : response.data?.data || []
}

export const verifyPatientExistsApi = async (patientId) => {
  const response = await axios.get(
    `${ENDPOINTS.patientById}${encodeURIComponent(patientId)}`,
  )
  return response.data
}

export const registerPatientApi = async (payload) => {
  const response = await fetch(ENDPOINTS.patientRegistration, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || `Patient registration failed (${response.status})`)
  }
  return response
}
