import axios from 'axios'
import { ENDPOINTS } from './endpoints'

export const initiatePaymentApi = async (invoiceId) => {
  const response = await axios.post(ENDPOINTS.initiatePayment, { invoiceId })
  return response.data?.data || response.data || {}
}

export const retryPaymentApi = async (invoiceId) => {
  const response = await axios.post(ENDPOINTS.retryPayment, { invoiceId })
  return response.data?.data || response.data || {}
}

export const notifyPaymentSucceededApi = async ({ invoiceId, recordId, paymentIntentId }) => {
  const response = await axios.post(ENDPOINTS.paymentEvents, {
    eventType: 'payment.succeeded',
    invoiceId,
    recordId,
    paymentIntentId,
  }, {
    headers: { 'X-Internal-Api-Key': 'changeme-dev-key' },
  })
  return response.data?.data || response.data || {}
}
