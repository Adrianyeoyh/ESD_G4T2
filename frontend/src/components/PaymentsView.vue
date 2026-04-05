<script setup>
import { computed, ref, watch } from 'vue'
import { ChevronLeft, ChevronRight, LoaderCircle } from 'lucide-vue-next'
import { useInvoices } from '../composables/useInvoices'
import { usePayment } from '../composables/usePayment'

const {
  loadingInvoices,
  invoicesError,
  enrichedInvoices,
  pendingInvoices,
} = useInvoices()

const {
  paymentStep,
  selectedInvoice,
  paymentIntentId,
  paymentError,
  paymentVerifiedMessage,
  paymentStatusMessage,
  stripeReady,
  confirmingPayment,
  stripeError,
  paymentConsoleLogs,
  selectInvoice,
  handleConfirmAndPay,
  resetPaymentFlow,
} = usePayment()

// Billing table filter + pagination
const billingFilter = ref('all')
const billingPage = ref(1)
const BILLING_PER_PAGE = 10

watch(billingFilter, () => { billingPage.value = 1 })

const statuses = computed(() => {
  const counts = {}
  for (const inv of enrichedInvoices.value) {
    counts[inv.status] = (counts[inv.status] || 0) + 1
  }
  return counts
})

const filteredBilling = computed(() => {
  if (billingFilter.value === 'all') return enrichedInvoices.value
  return enrichedInvoices.value.filter((inv) => inv.status === billingFilter.value)
})

const billingTotalPages = computed(() => Math.max(1, Math.ceil(filteredBilling.value.length / BILLING_PER_PAGE)))
const paginatedBilling = computed(() => {
  const start = (billingPage.value - 1) * BILLING_PER_PAGE
  return filteredBilling.value.slice(start, start + BILLING_PER_PAGE)
})
</script>

<template>
  <section class="space-y-6">
    <!-- Billing table -->
    <div class="rounded-2xl border border-[#E8EAED] bg-white p-6">
      <div class="mb-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h3 class="text-lg font-semibold">Billing (Closed Records)</h3>
          <p class="mt-1 text-sm text-[#5f6368]">
            Billing rows from invoices linked to closed records, including paid invoices and their billing details.
          </p>
        </div>

        <div class="flex flex-wrap gap-1 rounded-lg border border-[#DADCE0] p-1">
          <button
            class="rounded-md px-3 py-1.5 text-xs font-medium transition"
            :class="billingFilter === 'all' ? 'bg-[#1a73e8] text-white' : 'text-[#5f6368] hover:bg-[#F1F3F4]'"
            @click="billingFilter = 'all'"
          >
            All ({{ enrichedInvoices.length }})
          </button>
          <button
            class="rounded-md px-3 py-1.5 text-xs font-medium transition"
            :class="billingFilter === 'PAID' ? 'bg-[#1a73e8] text-white' : 'text-[#5f6368] hover:bg-[#F1F3F4]'"
            @click="billingFilter = 'PAID'"
          >
            Paid ({{ statuses['PAID'] || 0 }})
          </button>
          <button
            class="rounded-md px-3 py-1.5 text-xs font-medium transition"
            :class="billingFilter === 'DRAFT' ? 'bg-[#1a73e8] text-white' : 'text-[#5f6368] hover:bg-[#F1F3F4]'"
            @click="billingFilter = 'DRAFT'"
          >
            Draft ({{ statuses['DRAFT'] || 0 }})
          </button>
          <button
            class="rounded-md px-3 py-1.5 text-xs font-medium transition"
            :class="billingFilter === 'PAYMENT_PENDING' ? 'bg-[#1a73e8] text-white' : 'text-[#5f6368] hover:bg-[#F1F3F4]'"
            @click="billingFilter = 'PAYMENT_PENDING'"
          >
            Pending ({{ statuses['PAYMENT_PENDING'] || 0 }})
          </button>
          <button
            class="rounded-md px-3 py-1.5 text-xs font-medium transition"
            :class="billingFilter === 'FAILED' ? 'bg-[#1a73e8] text-white' : 'text-[#5f6368] hover:bg-[#F1F3F4]'"
            @click="billingFilter = 'FAILED'"
          >
            Failed ({{ statuses['FAILED'] || 0 }})
          </button>
        </div>
      </div>

      <p v-if="loadingInvoices" class="text-sm text-[#5f6368]">Loading billing records...</p>
      <p v-else-if="invoicesError" class="rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ invoicesError }}</p>
      <p v-else-if="filteredBilling.length === 0" class="text-sm text-[#5f6368]">No invoices found.</p>
      <template v-else>
        <div class="overflow-hidden rounded-xl border border-[#E8EAED]">
          <table class="min-w-full divide-y divide-[#E8EAED] text-sm">
            <thead class="bg-[#F8F9FA]">
              <tr class="text-left text-[#5f6368]">
                <th class="px-4 py-3 font-medium">Invoice</th>
                <th class="px-4 py-3 font-medium">Record</th>
                <th class="px-4 py-3 font-medium">Patient</th>
                <th class="px-4 py-3 font-medium">NRIC</th>
                <th class="px-4 py-3 font-medium">Amount</th>
                <th class="px-4 py-3 font-medium">Status</th>
                <th class="px-4 py-3 font-medium">Visit Notes</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[#F1F3F4] bg-white">
              <tr v-for="inv in paginatedBilling" :key="inv.invoiceId" class="hover:bg-[#F8F9FA]">
                <td class="px-4 py-3 font-medium">#{{ inv.invoiceId }}</td>
                <td class="px-4 py-3">#{{ inv.recordId }}</td>
                <td class="px-4 py-3">{{ inv.patientName }}</td>
                <td class="px-4 py-3">{{ inv.nric || 'N/A' }}</td>
                <td class="px-4 py-3 font-medium">{{ inv.currency }} {{ inv.total.toFixed(2) }}</td>
                <td class="px-4 py-3">
                  <span
                    class="inline-block rounded-full px-2 py-0.5 text-xs font-semibold"
                    :class="{
                      'bg-[#E6F4EA] text-[#188038]': inv.status === 'PAID',
                      'bg-[#E8F0FE] text-[#1a73e8]': inv.status === 'PAYMENT_PENDING',
                      'bg-[#FFF8E1] text-[#EA8600]': inv.status === 'FAILED',
                      'bg-[#F1F3F4] text-[#5f6368]': inv.status === 'DRAFT',
                      'bg-[#FDECEC] text-[#B3261E]': inv.status === 'CANCELLED',
                    }"
                  >
                    {{ inv.status }}
                  </span>
                </td>
                <td class="max-w-[200px] truncate px-4 py-3 text-[#5f6368]" :title="inv.visitNotes">{{ inv.visitNotes || 'N/A' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="billingTotalPages > 1" class="mt-4 flex items-center justify-center gap-2">
          <button
            class="rounded-lg border border-[#DADCE0] p-2 text-[#5f6368] hover:bg-[#F1F3F4] disabled:opacity-40"
            :disabled="billingPage <= 1"
            @click="billingPage--"
          >
            <ChevronLeft class="h-4 w-4" />
          </button>
          <span class="text-sm text-[#5f6368]">Page {{ billingPage }} of {{ billingTotalPages }}</span>
          <button
            class="rounded-lg border border-[#DADCE0] p-2 text-[#5f6368] hover:bg-[#F1F3F4] disabled:opacity-40"
            :disabled="billingPage >= billingTotalPages"
            @click="billingPage++"
          >
            <ChevronRight class="h-4 w-4" />
          </button>
        </div>
      </template>
    </div>

    <!-- Payment wizard -->
    <div class="rounded-2xl border border-[#E8EAED] bg-white p-6">
      <h3 class="text-lg font-semibold">3-Stop Payment Wizard</h3>
      <div class="mt-4 grid grid-cols-3 gap-2 text-xs font-medium">
        <div
          class="rounded-lg px-3 py-2"
          :class="paymentStep >= 1 ? 'bg-[#E8F0FE] text-[#1a73e8]' : 'bg-[#F1F3F4] text-[#5f6368]'"
        >
          1. Select Invoice
        </div>
        <div
          class="rounded-lg px-3 py-2"
          :class="paymentStep >= 2 ? 'bg-[#E8F0FE] text-[#1a73e8]' : 'bg-[#F1F3F4] text-[#5f6368]'"
        >
          2. Enter Card
        </div>
        <div
          class="rounded-lg px-3 py-2"
          :class="paymentStep >= 3 ? 'bg-[#E8F0FE] text-[#1a73e8]' : 'bg-[#F1F3F4] text-[#5f6368]'"
        >
          3. Success
        </div>
      </div>
    </div>

    <div v-if="paymentStep === 1" class="rounded-2xl border border-[#E8EAED] bg-white p-6">
      <h4 class="mb-4 font-semibold">Select Invoice To Pay</h4>

      <p v-if="loadingInvoices" class="text-sm text-[#5f6368]">Loading invoices...</p>
      <p v-else-if="invoicesError" class="rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ invoicesError }}</p>
      <p v-else-if="pendingInvoices.length === 0" class="text-sm text-[#5f6368]">No pending invoices found.</p>

      <div v-else class="space-y-3">
        <article
          v-for="invoice in pendingInvoices"
          :key="invoice.invoiceId"
          class="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-[#E8EAED] p-4"
        >
          <div>
            <p class="text-sm font-semibold">Invoice #{{ invoice.invoiceId }}</p>
            <p class="mt-0.5 text-sm text-[#202124]">{{ invoice.patientName }}</p>
            <p class="text-xs text-[#5f6368]">{{ invoice.nric }} &middot; Record #{{ invoice.recordId }}</p>
          </div>
          <div class="flex items-center gap-3">
            <div class="text-right">
              <p class="text-lg font-semibold">{{ invoice.currency }} {{ invoice.total.toFixed(2) }}</p>
              <span
                class="inline-block rounded-full px-2 py-0.5 text-xs font-semibold"
                :class="{
                  'bg-[#F1F3F4] text-[#5f6368]': invoice.status === 'DRAFT',
                  'bg-[#E8F0FE] text-[#1a73e8]': invoice.status === 'PAYMENT_PENDING',
                  'bg-[#FFF8E1] text-[#EA8600]': invoice.status === 'FAILED',
                }"
              >
                {{ invoice.status === 'PAYMENT_PENDING' ? 'Processing' : invoice.status }}
              </span>
            </div>
            <button
              v-if="invoice.status !== 'PAYMENT_PENDING'"
              class="rounded-lg px-4 py-2 text-sm font-medium text-white hover:opacity-90"
              :class="invoice.status === 'FAILED' ? 'bg-[#EA8600]' : 'bg-[#1a73e8] hover:bg-[#1765cc]'"
              @click="selectInvoice({ ...invoice, amount: invoice.total })"
            >
              {{ invoice.status === 'FAILED' ? 'Retry Payment' : 'Pay Now' }}
            </button>
            <span v-else class="text-xs text-[#5f6368]">Awaiting confirmation...</span>
          </div>
        </article>
      </div>
      <p v-if="paymentError" class="mt-4 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ paymentError }}</p>
    </div>

    <div v-if="paymentStep === 2" class="rounded-2xl border border-[#E8EAED] bg-white p-6">
      <h4 class="font-semibold">Enter Card Details</h4>
      <p class="mt-1 text-sm text-[#5f6368]">
        Invoice #{{ selectedInvoice?.invoiceId }} &middot; {{ selectedInvoice?.currency }} {{ selectedInvoice?.amount?.toFixed(2) }}
      </p>
      <div class="mt-4 rounded-lg border border-[#DADCE0] bg-white p-4">
        <div id="card-element" class="min-h-[22px]"></div>
      </div>
      <p v-if="paymentStatusMessage" class="mt-4 rounded-lg bg-[#E8F0FE] p-3 text-sm text-[#1a73e8]">
        <span class="inline-flex items-center gap-2">
          <LoaderCircle class="h-4 w-4 animate-spin" />
          {{ paymentStatusMessage }}
        </span>
      </p>
      <p v-if="paymentError" class="mt-4 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ paymentError }}</p>
      <p v-if="stripeError" class="mt-4 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ stripeError }}</p>
      <div class="mt-5 flex gap-3">
        <button
          class="rounded-lg bg-[#1a73e8] px-5 py-2.5 text-sm font-medium text-white hover:bg-[#1765cc] disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="confirmingPayment || !stripeReady"
          @click="handleConfirmAndPay"
        >
          <span class="inline-flex items-center gap-2">
            <LoaderCircle v-if="confirmingPayment" class="h-4 w-4 animate-spin" />
            {{ confirmingPayment ? 'Processing...' : 'Confirm and Pay' }}
          </span>
        </button>
        <button
          class="rounded-lg border border-[#DADCE0] px-5 py-2.5 text-sm font-medium text-[#5f6368] hover:bg-[#F1F3F4]"
          @click="resetPaymentFlow"
        >
          Back
        </button>
      </div>
    </div>

    <div v-if="paymentStep === 3" class="rounded-2xl border border-[#CEEAD6] bg-white p-6">
      <p class="text-xs font-semibold uppercase tracking-[0.16em] text-[#188038]">Payment Completed</p>
      <h4 class="mt-2 text-2xl font-semibold">Payment Received</h4>
      <p class="mt-2 text-sm text-[#5f6368]">
        Payment intent {{ paymentIntentId || 'N/A' }} succeeded for invoice #{{ selectedInvoice?.invoiceId }}.
      </p>
      <p v-if="paymentVerifiedMessage" class="mt-3 rounded-lg bg-[#E6F4EA] p-3 text-sm font-medium text-[#188038]">
        {{ paymentVerifiedMessage }}
      </p>
      <button class="mt-5 rounded-lg bg-[#1a73e8] px-5 py-2.5 text-sm font-medium text-white hover:bg-[#1765cc]">
        Download Receipt (Placeholder)
      </button>
    </div>

    <div class="rounded-2xl border border-[#E8EAED] bg-white p-4">
      <h4 class="text-sm font-semibold text-[#202124]">Stripe Live Console Logs</h4>
      <div class="mt-3 max-h-36 overflow-auto rounded-lg border border-[#E8EAED] bg-[#F8F9FA] p-3 font-mono text-xs text-[#5f6368]">
        <p v-if="paymentConsoleLogs.length === 0">No payment intent logs yet.</p>
        <p v-for="(entry, index) in paymentConsoleLogs" :key="index">{{ entry }}</p>
      </div>
    </div>
  </section>
</template>
