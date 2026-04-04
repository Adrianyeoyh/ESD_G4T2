<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, CheckCircle2, FileText, LoaderCircle, Pill } from 'lucide-vue-next'

const router = useRouter()

const ENDPOINTS = {
  consultationBase:
    import.meta.env.VITE_CONSULTATION_BASE ||
    'https://personal-wv4mxqur.outsystemscloud.com/RecordVisitNotes/rest/ConsultationAPI',
  prescribeMedicineBase:
    import.meta.env.VITE_PRESCRIBE_MEDICINE_BASE || 'http://localhost:5007',
}

const CONSULTATION_DRAFT_KEY = 'consultation:pending-draft'

const loadingDraft = ref(true)
const submittingConsultation = ref(false)
const reviewError = ref('')
const reviewSuccess = ref('')
const consultationDraft = ref(null)

const selectedDrugs = computed(() => consultationDraft.value?.drugs ?? [])
const selectedDrugCount = computed(() =>
  selectedDrugs.value.reduce((total, drug) => total + Number(drug.quantity || 0), 0),
)
const selectedDrugTotal = computed(() =>
  selectedDrugs.value.reduce(
    (total, drug) => total + Number(drug.quantity || 0) * Number(drug.price || 0),
    0,
  ),
)

const composedVisitNotes = computed(() => {
  let rawNotes = String(consultationDraft.value?.visitNotes || '').trim()
  // Replace escaped newlines with actual newlines
  rawNotes = rawNotes.replace(/\\n/g, '\n')
  
  const drugs = selectedDrugs.value

  if (!drugs.length) {
    return rawNotes
  }

  const drugSummary = drugs
    .map((drug) => `- ${drug.name} x${drug.quantity} (available ${drug.availableQuantity})`)
    .join('\n')

  return [rawNotes, 'Prescribed Drugs:', drugSummary].filter(Boolean).join(' ')
})

const loadDraft = () => {
  reviewError.value = ''

  try {
    const saved = sessionStorage.getItem(CONSULTATION_DRAFT_KEY)
    if (!saved) {
      consultationDraft.value = null
      reviewError.value = 'No consultation draft was found. Please start from the consultation form.'
      return
    }

    consultationDraft.value = JSON.parse(saved)
  } catch (error) {
    consultationDraft.value = null
    reviewError.value = error?.message || 'Unable to load the consultation draft.'
  } finally {
    loadingDraft.value = false
  }
}

const backToConsultation = () => {
  router.push('/')
}

const extractStatus = (payload) => {
  const status = payload?.status ?? payload?.Status ?? null
  return typeof status === 'string' ? status.trim().toLowerCase() : null
}

const extractRecordId = (payload) =>
  payload?.newRecord?.recordId ??
  payload?.newRecord?.RecordId ??
  payload?.recordId ??
  payload?.RecordId ??
  null

const parseResponsePayload = async (response) => {
  const rawText = await response.text()
  if (!rawText) {
    return {}
  }

  try {
    return JSON.parse(rawText)
  } catch {
    return { message: rawText }
  }
}

const confirmSubmission = async () => {
  reviewError.value = ''
  reviewSuccess.value = ''

  let visitNotes = String(composedVisitNotes.value || '').trim()
  // Remove literal \n escape sequences and replace actual newlines with spaces for API payload
  visitNotes = visitNotes.replace(/\\n/g, ' ').replace(/\n/g, ' ')
  
  const patientId = String(consultationDraft.value?.patientId || '').trim()
  const selectedDrugItems = selectedDrugs.value
    .map((drug) => ({
      drugId: Number(drug.drugId ?? drug.id ?? 0),
      quantity: Number(drug.quantity || 0),
    }))
    .filter((item) => Number.isFinite(item.drugId) && item.drugId > 0 && item.quantity > 0)

  if (!patientId || !visitNotes) {
    reviewError.value = 'The consultation draft is incomplete.'
    return
  }

  if (!selectedDrugItems.length) {
    reviewError.value = 'Please select at least one drug with quantity greater than 0.'
    return
  }

  submittingConsultation.value = true

  try {
    const consultationResponse = await fetch(
      `${ENDPOINTS.consultationBase.replace(/\/$/, '')}/consultation/${encodeURIComponent(patientId)}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(visitNotes),
      },
    )

    const consultationPayload = await parseResponsePayload(consultationResponse)

    if (!consultationResponse.ok) {
      throw new Error(
        consultationPayload?.message ||
          consultationPayload?.error ||
          `Consultation failed (${consultationResponse.status})`,
      )
    }

    const consultationStatus = extractStatus(consultationPayload)
    if (consultationStatus && consultationStatus !== 'success') {
      throw new Error(
        consultationPayload?.message ||
          consultationPayload?.error ||
          `Consultation returned status '${consultationStatus}'.`,
      )
    }

    const recordId = extractRecordId(consultationPayload)
    if (recordId === null || recordId === undefined || String(recordId).trim() === '') {
      throw new Error('Consultation succeeded but no recordId was returned.')
    }

    const prescribeResponse = await fetch(
      `${ENDPOINTS.prescribeMedicineBase.replace(/\/$/, '')}/prescribe/${encodeURIComponent(String(recordId))}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(selectedDrugItems),
      },
    )

    const prescribePayload = await parseResponsePayload(prescribeResponse)
    if (!prescribeResponse.ok) {
      throw new Error(
        prescribePayload?.message ||
          prescribePayload?.error ||
          `Prescribe medicine failed (${prescribeResponse.status})`,
      )
    }

    const prescribeStatus = extractStatus(prescribePayload)
    if (prescribeStatus !== 'success') {
      throw new Error(
        prescribePayload?.message ||
          prescribePayload?.error ||
          `Prescribe medicine returned status '${prescribeStatus || 'unknown'}'.`,
      )
    }

    sessionStorage.removeItem(CONSULTATION_DRAFT_KEY)
    reviewSuccess.value = `Consultation and prescription submitted successfully. Record ID: ${recordId}`
  } catch (error) {
    reviewError.value = error?.message || 'Unable to submit consultation right now.'
  } finally {
    submittingConsultation.value = false
  }
}

onMounted(loadDraft)
</script>

<template>
  <section class="min-h-screen bg-[#F8F9FA] px-4 py-8 text-[#202124] md:px-10">
    <div class="mx-auto max-w-6xl space-y-6">
      <div class="rounded-3xl bg-gradient-to-r from-[#1a73e8] to-[#0f9d58] p-6 text-white shadow-lg">
        <p class="text-xs font-semibold uppercase tracking-[0.2em] text-white/80">Review Step</p>
        <h1 class="mt-2 text-3xl font-semibold">Confirm Consultation Details</h1>
        <p class="mt-2 max-w-3xl text-sm text-white/85">
          Review the patient details, visit notes, and prescribed drugs before the consultation is
          submitted.
        </p>
      </div>

      <div v-if="loadingDraft" class="rounded-2xl border border-[#E8EAED] bg-white p-6 text-sm text-[#5f6368] shadow-sm">
        Loading consultation draft...
      </div>

      <div v-else-if="reviewError && !consultationDraft" class="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700 shadow-sm">
        {{ reviewError }}
        <button
          class="ml-4 rounded-lg bg-rose-600 px-4 py-2 text-white transition hover:bg-rose-700"
          @click="backToConsultation"
        >
          Go Back
        </button>
      </div>

      <div v-else class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div class="space-y-6">
          <div class="rounded-2xl border border-[#E8EAED] bg-white p-6 shadow-sm">
            <div class="flex items-center gap-2">
              <FileText class="h-5 w-5 text-[#1a73e8]" />
              <h2 class="text-lg font-semibold">Consultation Summary</h2>
            </div>

            <div class="mt-5 grid gap-4 md:grid-cols-2">
              <div class="rounded-xl bg-[#F8F9FA] p-4">
                <p class="text-xs font-semibold uppercase tracking-[0.14em] text-[#5f6368]">Patient ID</p>
                <p class="mt-1 text-lg font-semibold">{{ consultationDraft.patientId }}</p>
              </div>
              <div v-if="selectedDrugs.length > 0" class="rounded-xl bg-[#F8F9FA] p-4">
                <p class="text-xs font-semibold uppercase tracking-[0.14em] text-[#5f6368]">Selected Drugs</p>
                <p class="mt-1 text-lg font-semibold">{{ selectedDrugs.length }} items / {{ selectedDrugCount }} units</p>
              </div>
            </div>

            <div class="mt-5 rounded-2xl border border-[#E8EAED] bg-[#F8F9FA] p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.14em] text-[#5f6368]">Visit Notes</p>
              <p class="mt-2 whitespace-pre-wrap text-sm leading-6 text-[#202124]">
                {{ consultationDraft.visitNotes }}
              </p>
            </div>

            <div class="mt-5 rounded-2xl border border-[#E8EAED] bg-[#F8F9FA] p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.14em] text-[#5f6368]">Final Submission Payload</p>
              <p class="mt-2 whitespace-pre-wrap text-sm leading-6 text-[#202124]">
                {{ composedVisitNotes }}
              </p>
            </div>
          </div>

          <div class="rounded-2xl border border-[#E8EAED] bg-white p-6 shadow-sm">
            <div class="flex items-center gap-2">
              <Pill class="h-5 w-5 text-[#1a73e8]" />
              <h2 class="text-lg font-semibold">Prescription Review</h2>
            </div>

            <div v-if="selectedDrugs.length === 0" class="mt-4 rounded-xl bg-[#FFF8E1] p-4 text-sm text-[#7A5C00]">
              No drugs were selected for this consultation.
            </div>

            <div v-else class="mt-4 overflow-hidden rounded-xl border border-[#E8EAED]">
              <table class="min-w-full divide-y divide-[#E8EAED] text-sm">
                <thead class="bg-[#F8F9FA] text-left text-[#5f6368]">
                  <tr>
                    <th class="px-4 py-3 font-medium">Drug</th>
                    <th class="px-4 py-3 font-medium">Selected</th>
                    <th class="px-4 py-3 font-medium">Available</th>
                    <th class="px-4 py-3 font-medium">Price</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#F1F3F4] bg-white">
                  <tr v-for="drug in selectedDrugs" :key="drug.drugId">
                    <td class="px-4 py-3 font-medium">{{ drug.name }}</td>
                    <td class="px-4 py-3">{{ drug.quantity }}</td>
                    <td class="px-4 py-3">{{ drug.availableQuantity }}</td>
                    <td class="px-4 py-3">SGD {{ Number(drug.price || 0).toFixed(2) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <p v-if="selectedDrugs.length > 0" class="mt-4 text-sm text-[#5f6368]">
              Estimated drug value: SGD {{ selectedDrugTotal.toFixed(2) }}
            </p>
          </div>
        </div>

        <div class="space-y-6">
          <div class="rounded-2xl border border-[#E8EAED] bg-white p-6 shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-[#1a73e8]">Action</p>
            <h2 class="mt-2 text-xl font-semibold">Ready to submit?</h2>
            <p class="mt-2 text-sm text-[#5f6368]">
              Confirming will send the composed consultation notes to the backend.
            </p>

            <div v-if="reviewError" class="mt-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">
              {{ reviewError }}
            </div>

            <div v-if="reviewSuccess" class="mt-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">
              {{ reviewSuccess }}
            </div>

            <div class="mt-5 flex flex-wrap gap-3">
              <button
                class="inline-flex items-center gap-2 rounded-lg border border-[#DADCE0] px-4 py-2 text-sm font-medium text-[#5f6368] transition hover:bg-[#F1F3F4]"
                @click="backToConsultation"
              >
                <ArrowLeft class="h-4 w-4" />
                Back to Edit
              </button>

              <button
                class="inline-flex items-center gap-2 rounded-lg bg-[#1a73e8] px-4 py-2 text-sm font-medium text-white transition hover:bg-[#1765cc] disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="submittingConsultation || Boolean(reviewSuccess)"
                @click="confirmSubmission"
              >
                <LoaderCircle v-if="submittingConsultation" class="h-4 w-4 animate-spin" />
                <CheckCircle2 v-else class="h-4 w-4" />
                {{ submittingConsultation ? 'Submitting...' : 'Confirm Submission' }}
              </button>
            </div>
          </div>

          <div class="rounded-2xl border border-[#E8EAED] bg-white p-6 shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-[#5f6368]">Notes</p>
            <ul class="mt-3 space-y-2 text-sm text-[#5f6368]">
              <li>Drug quantities are capped by the stock returned from the catalogue API.</li>
              <li>The review page is loaded from the same consultation draft session.</li>
              <li>Returning to the dashboard keeps your form inputs intact until you refresh the page.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>