<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { loadStripe } from '@stripe/stripe-js'
import { billingApi } from '../services/api'

const route = useRoute()
const router = useRouter()

const invoiceId = computed(() => route.params.invoiceId)
const patientName = computed(() => route.query.patient || 'Patient')
const amount = computed(() => Number(route.query.amount || 0).toFixed(2))
const currency = computed(() => route.query.currency || 'SGD')

const stripe = ref(null)
const elements = ref(null)
const cardElement = ref(null)
const cardMount = ref(null)

const loadingStripe = ref(false)
const attemptingPayment = ref(false)
const stop1Error = ref('')
const stop2Error = ref('')
const paymentIntentId = ref('')

const initializeStripe = async () => {
  loadingStripe.value = true
  stop2Error.value = ''

  try {
    const publishableKey = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY
    if (!publishableKey) {
      stop2Error.value = 'Missing VITE_STRIPE_PUBLISHABLE_KEY in your frontend environment.'
      return
    }

    stripe.value = await loadStripe(publishableKey)
    if (!stripe.value) {
      stop2Error.value = 'Stripe failed to initialize in browser.'
      return
    }

    elements.value = stripe.value.elements()
    cardElement.value = elements.value.create('card', {
      style: {
        base: {
          color: '#0f172a',
          fontFamily: '"Segoe UI", "Avenir Next", sans-serif',
          fontSize: '16px',
          '::placeholder': { color: '#64748b' },
        },
      },
    })
    cardElement.value.mount(cardMount.value)
  } catch (err) {
    stop2Error.value = err?.message || 'Unable to initialize Stripe Elements.'
  } finally {
    loadingStripe.value = false
  }
}

const extractPaymentPayload = (payload) => {
  const result = payload?.data || payload || {}
  const clientSecret = result?.clientSecret || result?.client_secret
  const intentId = result?.paymentIntentId || result?.payment_intent_id

  return {
    clientSecret,
    intentId,
  }
}

const startPayment = async () => {
  stop1Error.value = ''
  stop2Error.value = ''

  if (!stripe.value || !cardElement.value) {
    stop2Error.value = 'Stripe card input is not ready yet. Please wait and try again.'
    return
  }

  attemptingPayment.value = true

  try {
    // Stop 1: Initial Request to local billing orchestration service.
    const stop1Response = await billingApi.post('/make_payment/initiate-payment', {
      invoiceId: Number(invoiceId.value),
    })

    const { clientSecret, intentId } = extractPaymentPayload(stop1Response.data)

    if (!clientSecret || !intentId) {
      stop1Error.value = 'Billing service did not return client_secret and payment_intent_id.'
      return
    }

    paymentIntentId.value = intentId

    // Stop 2: Stripe browser handshake with client secret.
    const { error, paymentIntent } = await stripe.value.confirmCardPayment(clientSecret, {
      payment_method: {
        card: cardElement.value,
        billing_details: {
          name: String(patientName.value),
        },
      },
    })

    if (error) {
      stop2Error.value = error.message || 'Stripe payment confirmation failed.'
      return
    }

    if (paymentIntent?.status === 'succeeded') {
      // Stop 3: Frontend finality route.
      // Webhook note: invoice status update, record closure, and Twilio notification are backend webhook duties.
      router.push({
        name: 'payment-success',
        query: {
          invoiceId: String(invoiceId.value),
          paymentIntentId: String(paymentIntent.id || paymentIntentId.value),
        },
      })
      return
    }

    stop2Error.value = `Stripe returned status: ${paymentIntent?.status || 'unknown'}`
  } catch (err) {
    stop1Error.value =
      err?.response?.data?.error ||
      err?.response?.data?.message ||
      err?.message ||
      'Failed to initiate payment with Billing service.'
  } finally {
    attemptingPayment.value = false
  }
}

const retryPayment = () => {
  stop1Error.value = ''
  stop2Error.value = ''
}

onMounted(initializeStripe)
</script>

<template>
  <section class="space-y-6">
    <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <p class="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-700">Secure Checkout</p>
      <h2 class="mt-2 text-2xl font-semibold text-slate-900">Payment Portal</h2>
      <p class="mt-1 text-sm text-slate-600">Invoice #{{ invoiceId }} for {{ patientName }}</p>
      <p class="mt-2 text-3xl font-semibold text-slate-900">{{ currency }} {{ amount }}</p>
    </div>

    <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <h3 class="text-sm font-semibold uppercase tracking-[0.15em] text-slate-500">Card Details</h3>
      <div class="mt-3 rounded-xl border border-slate-300 bg-slate-50 p-4">
        <div v-if="loadingStripe" class="text-sm text-slate-500">Loading Stripe payment form...</div>
        <div ref="cardMount" />
      </div>

      <div v-if="attemptingPayment" class="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
        Attempting Payment... Please wait while we complete Stop 1 and Stop 2.
      </div>

      <div v-if="stop1Error" class="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
        Stop 1 Error: {{ stop1Error }}
      </div>

      <div v-if="stop2Error" class="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
        Stop 2 Error: {{ stop2Error }}
      </div>

      <div class="mt-5 flex flex-wrap gap-3">
        <button
          class="rounded-lg bg-cyan-700 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-cyan-800 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="attemptingPayment || loadingStripe"
          @click="startPayment"
        >
          Pay Now
        </button>

        <button
          class="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
          :disabled="attemptingPayment"
          @click="retryPayment"
        >
          Retry
        </button>
      </div>
    </div>
  </section>
</template>
