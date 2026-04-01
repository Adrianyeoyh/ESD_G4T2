<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { recordsApi } from '../services/api'

const router = useRouter()
const invoices = ref([])
const loading = ref(false)
const error = ref('')

const normalizeInvoices = (payload) => {
  if (Array.isArray(payload)) {
    return payload
  }

  const candidates = [payload?.data, payload?.records, payload?.Records, payload?.items]
  for (const maybeArray of candidates) {
    if (Array.isArray(maybeArray)) {
      return maybeArray
    }
  }

  return []
}

const toNumber = (value) => {
  const n = Number(value)
  return Number.isFinite(n) ? n : 0
}

const pendingInvoices = computed(() => {
  return invoices.value
    .map((item, index) => ({
      invoiceId: item.invoice_id ?? item.InvoiceId ?? item.id ?? index + 1,
      patientName: item.patient_name ?? item.PatientName ?? item.name ?? 'Unknown patient',
      amount: toNumber(item.amount ?? item.total_amount ?? item.TotalAmount),
      currency: item.currency ?? item.Currency ?? 'SGD',
      dueDate: item.due_date ?? item.DueDate ?? 'N/A',
      status: String(item.status ?? item.Status ?? 'pending').toLowerCase(),
    }))
    .filter((item) => item.status.includes('pending') || item.status.includes('unpaid') || item.status === '')
})

const loadInvoices = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await recordsApi.get('/')
    invoices.value = normalizeInvoices(response.data)
  } catch (err) {
    error.value = err?.response?.data?.message || 'Unable to fetch pending invoices from RecordsAPI.'
  } finally {
    loading.value = false
  }
}

const proceedToPayment = (invoice) => {
  router.push({
    name: 'payment-portal',
    params: { invoiceId: String(invoice.invoiceId) },
    query: {
      amount: String(invoice.amount || 0),
      currency: invoice.currency,
      patient: invoice.patientName,
    },
  })
}

onMounted(loadInvoices)
</script>

<template>
  <section class="space-y-6">
    <div class="rounded-2xl bg-gradient-to-r from-cyan-700 to-sky-700 p-6 text-white shadow-lg">
      <p class="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-100">Step 1</p>
      <h2 class="mt-2 text-2xl font-semibold">Select a Pending Invoice</h2>
      <p class="mt-2 text-sm text-cyan-100">
        Invoice data is loaded from OutSystems ClinicalRecordServices (RecordsAPI).
      </p>
    </div>

    <div v-if="loading" class="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
      Loading pending invoices...
    </div>

    <div v-else-if="error" class="rounded-xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700 shadow-sm">
      {{ error }}
      <button class="ml-3 rounded-md bg-rose-600 px-3 py-1.5 text-white" @click="loadInvoices">Retry</button>
    </div>

    <div v-else-if="pendingInvoices.length === 0" class="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
      No pending invoices were found.
    </div>

    <div v-else class="grid gap-4">
      <article
        v-for="invoice in pendingInvoices"
        :key="invoice.invoiceId"
        class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-cyan-300 hover:shadow-md"
      >
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700">Invoice #{{ invoice.invoiceId }}</p>
            <h3 class="mt-1 text-lg font-semibold text-slate-900">{{ invoice.patientName }}</h3>
            <p class="mt-1 text-sm text-slate-500">Due: {{ invoice.dueDate }}</p>
          </div>
          <div class="text-right">
            <p class="text-xs text-slate-500">Amount</p>
            <p class="text-2xl font-semibold text-slate-900">{{ invoice.currency }} {{ invoice.amount.toFixed(2) }}</p>
          </div>
        </div>

        <button
          class="mt-4 rounded-lg bg-cyan-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-cyan-800"
          @click="proceedToPayment(invoice)"
        >
          Proceed To Payment
        </button>
      </article>
    </div>
  </section>
</template>
