import axios from 'axios'
import { ENDPOINTS } from './endpoints'

export const fetchInvoicesApi = async () => {
  const response = await axios.get(ENDPOINTS.invoices)
  return Array.isArray(response.data) ? response.data : []
}

export const fetchInvoiceByIdApi = async (invoiceId) => {
  const response = await axios.get(`${ENDPOINTS.invoices}/${invoiceId}`)
  return response.data
}
