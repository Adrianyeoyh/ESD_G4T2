import { nextTick, ref } from 'vue'
import { loadStripe } from '@stripe/stripe-js'
import { STRIPE_PUBLISHABLE_KEY } from '../api/endpoints'
import { initiatePaymentApi, retryPaymentApi, notifyPaymentSucceededApi } from '../api/payment'
import { fetchInvoiceByIdApi } from '../api/invoices'

const paymentStep = ref(1)
const selectedInvoice = ref(null)
const paymentIntentId = ref('')
const paymentError = ref('')
const paymentVerifiedMessage = ref('')
const paymentStatusMessage = ref('')

const stripe = ref(null)
const elements = ref(null)
const cardElement = ref(null)
const stripeReady = ref(false)
const confirmingPayment = ref(false)
const stripeError = ref('')
const paymentConsoleLogs = ref([])

const pollInvoiceStatus = async (invoiceId, maxAttempts = 15, intervalMs = 2000) => {
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise((resolve) => setTimeout(resolve, intervalMs))
    try {
      const invoice = await fetchInvoiceByIdApi(invoiceId)
      const status = String(invoice.status ?? '').toLowerCase()
      paymentStatusMessage.value = `Confirming payment... (${status})`
      if (status === 'paid') return 'paid'
      if (status === 'failed') return 'failed'
    } catch {
      // ignore polling errors, keep trying
    }
  }
  return 'timeout'
}

export function usePayment() {
  const initializeStripe = async () => {
    stripeError.value = ''
    stripe.value = await loadStripe(STRIPE_PUBLISHABLE_KEY)
    stripeReady.value = Boolean(stripe.value)
    if (!stripeReady.value) {
      stripeError.value = 'Unable to initialize Stripe. Check your publishable key.'
    }
  }

  const unmountCardElement = () => {
    if (cardElement.value) cardElement.value.unmount()
    cardElement.value = null
    elements.value = null
  }

  const mountCardElement = async () => {
    if (!stripe.value || cardElement.value) return
    const cardMountNode = document.getElementById('card-element')
    if (!cardMountNode) return

    elements.value = stripe.value.elements()
    cardElement.value = elements.value.create('card', {
      style: {
        base: {
          fontFamily: 'Inter, Segoe UI, sans-serif',
          fontSize: '16px',
          color: '#202124',
          '::placeholder': { color: '#9aa0a6' },
        },
      },
    })
    cardElement.value.mount('#card-element')
  }

  const selectInvoice = async (invoice) => {
    selectedInvoice.value = invoice
    paymentError.value = ''
    stripeError.value = ''
    paymentVerifiedMessage.value = ''
    paymentStatusMessage.value = ''
    paymentStep.value = 2
    await nextTick()
    await mountCardElement()
  }

  const handleConfirmAndPay = async () => {
    paymentError.value = ''
    stripeError.value = ''
    paymentVerifiedMessage.value = ''
    paymentStatusMessage.value = ''
    confirmingPayment.value = true

    try {
      const invoiceId = selectedInvoice.value?.invoiceId
      if (!invoiceId) {
        throw new Error('No invoice selected.')
      }

      // Step 1: Create payment intent via backend orchestrator
      const invoiceStatus = String(selectedInvoice.value?.status || '').toUpperCase()
      const payFn = invoiceStatus === 'FAILED' ? retryPaymentApi : initiatePaymentApi
      paymentStatusMessage.value = 'Creating payment intent...'
      const result = await payFn(invoiceId)
      const clientSecret = result.clientSecret
      if (!clientSecret) {
        throw new Error('Backend did not return a client secret. Payment could not be initiated.')
      }

      paymentIntentId.value = result.paymentIntentId || ''

      // Step 2: Confirm payment with Stripe using card element
      if (!stripe.value || !cardElement.value) {
        throw new Error('Stripe is not initialized. Please refresh and try again.')
      }

      paymentStatusMessage.value = 'Processing card payment...'
      const { error, paymentIntent } = await stripe.value.confirmCardPayment(clientSecret, {
        payment_method: { card: cardElement.value },
      })

      if (error) {
        paymentConsoleLogs.value.unshift(
          `${new Date().toLocaleTimeString()} | error=${error.message}`,
        )
        throw new Error(error.message)
      }

      paymentConsoleLogs.value.unshift(
        `${new Date().toLocaleTimeString()} | paymentIntent=${paymentIntent.id} | stripeStatus=${paymentIntent.status}`,
      )

      // Step 3: Notify backend that payment succeeded (in case webhook is delayed)
      paymentStatusMessage.value = 'Confirming payment with backend...'
      try {
        await notifyPaymentSucceededApi({
          invoiceId,
          recordId: selectedInvoice.value?.recordId ?? result.recordId,
          paymentIntentId: paymentIntent.id,
        })
        paymentConsoleLogs.value.unshift(
          `${new Date().toLocaleTimeString()} | invoice=${invoiceId} | backend notified`,
        )
      } catch (notifyError) {
        paymentConsoleLogs.value.unshift(
          `${new Date().toLocaleTimeString()} | backend notify failed: ${notifyError?.response?.data?.error || notifyError?.message}`,
        )
      }

      // Step 4: Poll to confirm invoice is marked paid
      paymentStatusMessage.value = 'Verifying invoice status...'
      const finalStatus = await pollInvoiceStatus(invoiceId, 10, 1500)

      if (finalStatus === 'paid') {
        paymentVerifiedMessage.value = 'Payment confirmed. Invoice marked as paid.'
        paymentConsoleLogs.value.unshift(
          `${new Date().toLocaleTimeString()} | invoice=${invoiceId} | status=paid`,
        )
        paymentStep.value = 3
      } else if (finalStatus === 'failed') {
        throw new Error('Payment was processed by Stripe but the backend marked it as failed. Please contact support.')
      } else {
        paymentVerifiedMessage.value = 'Payment was charged successfully. Invoice status will update momentarily.'
        paymentConsoleLogs.value.unshift(
          `${new Date().toLocaleTimeString()} | invoice=${invoiceId} | status=confirming`,
        )
        paymentStep.value = 3
      }
    } catch (error) {
      const serverError = error?.response?.data?.error || error?.response?.data?.message || ''
      const httpStatus = error?.response?.status

      if (httpStatus === 409 && serverError.includes('payment_pending')) {
        paymentError.value = 'This invoice is already being processed. Please wait for it to complete or check the billing table.'
      } else if (httpStatus === 409) {
        paymentError.value = `This invoice cannot be paid right now: ${serverError}`
      } else {
        paymentError.value = serverError || error?.message || 'Payment failed. Please try again.'
      }
      paymentConsoleLogs.value.unshift(
        `${new Date().toLocaleTimeString()} | error=${paymentError.value}`,
      )
    } finally {
      confirmingPayment.value = false
      paymentStatusMessage.value = ''
    }
  }

  const resetPaymentFlow = () => {
    paymentStep.value = 1
    selectedInvoice.value = null
    paymentIntentId.value = ''
    paymentError.value = ''
    stripeError.value = ''
    paymentVerifiedMessage.value = ''
    paymentStatusMessage.value = ''
    unmountCardElement()
  }

  return {
    paymentStep,
    selectedInvoice,
    paymentIntentId,
    paymentError,
    paymentVerifiedMessage,
    paymentStatusMessage,
    stripe,
    stripeReady,
    confirmingPayment,
    stripeError,
    paymentConsoleLogs,
    initializeStripe,
    selectInvoice,
    handleConfirmAndPay,
    resetPaymentFlow,
  }
}
