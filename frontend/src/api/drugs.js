import axios from 'axios'
import { ENDPOINTS } from './endpoints'
import { normalizeArrayResponse, normalizeDrug } from '../utils/normalizers'

export const fetchDrugsApi = async () => {
  let response
  try {
    response = await axios.get(ENDPOINTS.drugsPrimary)
  } catch {
    response = await axios.get(ENDPOINTS.drugsAlt)
  }
  return normalizeArrayResponse(response.data).map(normalizeDrug)
}

export const addDrugApi = async (drugData) => {
  return axios.post(ENDPOINTS.drugsPrimary, {
    ...drugData,
    recommendedDosage: drugData.dosage,
  })
}

export const updateDrugApi = async (drugId, drugData) => {
  return axios.put(`${ENDPOINTS.drugsPrimary}/${drugId}`, drugData)
}

export const deleteDrugApi = async (drugId) => {
  return axios.delete(`${ENDPOINTS.drugsPrimary}/${drugId}`)
}
