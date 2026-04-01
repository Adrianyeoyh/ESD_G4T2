<script setup>
import { computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'

const route = useRoute()
const invoiceId = computed(() => route.query.invoiceId || 'N/A')
const paymentIntentId = computed(() => route.query.paymentIntentId || 'N/A')
</script>

<template>
  <section class="mx-auto max-w-2xl">
    <div class="rounded-2xl border border-emerald-200 bg-white p-8 shadow-sm">
      <p class="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">Payment Complete</p>
      <h2 class="mt-2 text-3xl font-semibold text-slate-900">Payment Received</h2>
      <p class="mt-3 text-sm text-slate-600">
        Thank you. Your transaction has been confirmed in Stripe.
      </p>

      <dl class="mt-6 space-y-3 rounded-xl bg-emerald-50 p-4 text-sm">
        <div class="flex items-center justify-between gap-4">
          <dt class="font-medium text-slate-600">Invoice ID</dt>
          <dd class="font-semibold text-slate-900">{{ invoiceId }}</dd>
        </div>
        <div class="flex items-center justify-between gap-4">
          <dt class="font-medium text-slate-600">Payment Intent</dt>
          <dd class="max-w-[65%] truncate font-semibold text-slate-900">{{ paymentIntentId }}</dd>
        </div>
      </dl>

      <div class="mt-6 flex flex-wrap gap-3">
        <button class="rounded-lg bg-emerald-700 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-emerald-800">
          Download Receipt (Coming Soon)
        </button>
        <RouterLink
          to="/"
          class="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
        >
          Back To Invoices
        </RouterLink>
      </div>
    </div>
  </section>
</template>
