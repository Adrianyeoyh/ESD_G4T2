<script setup>
import { computed, ref } from 'vue'
import { ChevronLeft, ChevronRight, FileText, LoaderCircle } from 'lucide-vue-next'
import { usePatientHistory } from '../composables/usePatientHistory'

const {
  patientHistoryForm,
  loadingPatientHistory,
  patientHistoryError,
  patientHistoryPrescriptionError,
  enrichedRecords,
  fetchPatientHistory,
} = usePatientHistory()

const ITEMS_PER_PAGE = 10
const page = ref(1)
const totalPages = computed(() => Math.max(1, Math.ceil(enrichedRecords.value.length / ITEMS_PER_PAGE)))
const paginatedRecords = computed(() => {
  const start = (page.value - 1) * ITEMS_PER_PAGE
  return enrichedRecords.value.slice(start, start + ITEMS_PER_PAGE)
})

const handleFetch = () => {
  page.value = 1
  fetchPatientHistory()
}
</script>

<template>
  <section class="space-y-5">
    <div class="rounded-2xl border border-[#E8EAED] bg-white p-6">
      <div class="mb-2 flex items-center gap-2">
        <FileText class="h-5 w-5 text-[#1a73e8]" />
        <h3 class="text-lg font-semibold">Patient History</h3>
      </div>
      <p class="text-sm text-[#5f6368]">Retrieves all clinical records and prescriptions by patientId.</p>

      <div class="mt-4 flex flex-col gap-3 md:flex-row md:items-center">
        <input
          v-model="patientHistoryForm.patientId"
          class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm md:max-w-xs"
          placeholder="Enter patientId"
        />
        <button
          class="inline-flex items-center justify-center gap-2 rounded-lg bg-[#1a73e8] px-4 py-2 text-sm font-medium text-white hover:bg-[#1765cc] disabled:opacity-60"
          :disabled="loadingPatientHistory"
          @click="handleFetch"
        >
          <LoaderCircle v-if="loadingPatientHistory" class="h-4 w-4 animate-spin" />
          Get Patient History
        </button>
      </div>

      <p v-if="patientHistoryError" class="mt-4 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">
        {{ patientHistoryError }}
      </p>
      <p v-if="patientHistoryPrescriptionError" class="mt-4 rounded-lg bg-[#FFF8E1] p-3 text-sm text-[#7A5C00]">
        {{ patientHistoryPrescriptionError }}
      </p>
    </div>

    <div class="rounded-2xl border border-[#E8EAED] bg-white p-6">
      <h4 class="text-base font-semibold">Clinical Records</h4>
      <p v-if="loadingPatientHistory" class="mt-3 text-sm text-[#5f6368]">Loading records...</p>
      <p v-else-if="enrichedRecords.length === 0" class="mt-3 text-sm text-[#5f6368]">
        No records found for this patientId.
      </p>
      <template v-else>
        <div class="mt-4 overflow-hidden rounded-xl border border-[#E8EAED]">
          <table class="min-w-full divide-y divide-[#E8EAED] text-sm">
            <thead class="bg-[#F8F9FA]">
              <tr class="text-left text-[#5f6368]">
                <th class="px-4 py-3 font-medium">Record ID</th>
                <th class="px-4 py-3 font-medium">Visit Date</th>
                <th class="px-4 py-3 font-medium">Visit Notes</th>
                <th class="px-4 py-3 font-medium">Prescriptions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[#F1F3F4] bg-white">
              <tr v-for="row in paginatedRecords" :key="row.recordId" class="align-top hover:bg-[#F8F9FA]">
                <td class="px-4 py-3">{{ row.recordId }}</td>
                <td class="px-4 py-3">{{ row.date ?? row.Date ?? row.visitDate ?? 'N/A' }}</td>
                <td class="max-w-[250px] px-4 py-3">
                  <p class="truncate" :title="row.VisitNotes ?? row.visitNotes ?? row.notes ?? ''">
                    {{ row.VisitNotes ?? row.visitNotes ?? row.notes ?? 'N/A' }}
                  </p>
                </td>
                <td class="px-4 py-3">
                  <span v-if="row.prescriptions.length === 0" class="text-[#5f6368]">None</span>
                  <div v-else class="space-y-1">
                    <div
                      v-for="rx in row.prescriptions"
                      :key="rx.id"
                      class="rounded-md bg-[#F8F9FA] px-2 py-1 text-xs"
                    >
                      <span class="font-medium text-[#202124]">{{ rx.drugName }}</span>
                      <span class="text-[#5f6368]"> x{{ rx.quantity }}</span>
                      <span class="ml-1 text-[#9AA0A6]">#{{ rx.id }}</span>
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="totalPages > 1" class="mt-4 flex items-center justify-center gap-2">
          <button
            class="rounded-lg border border-[#DADCE0] p-2 text-[#5f6368] hover:bg-[#F1F3F4] disabled:opacity-40"
            :disabled="page <= 1"
            @click="page--"
          >
            <ChevronLeft class="h-4 w-4" />
          </button>
          <span class="text-sm text-[#5f6368]">Page {{ page }} of {{ totalPages }}</span>
          <button
            class="rounded-lg border border-[#DADCE0] p-2 text-[#5f6368] hover:bg-[#F1F3F4] disabled:opacity-40"
            :disabled="page >= totalPages"
            @click="page++"
          >
            <ChevronRight class="h-4 w-4" />
          </button>
        </div>
      </template>
    </div>
  </section>
</template>
