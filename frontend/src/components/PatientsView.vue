<script setup>
import { computed, ref } from 'vue'
import { ChevronLeft, ChevronRight, LoaderCircle, Users } from 'lucide-vue-next'
import { usePatients } from '../composables/usePatients'

const {
  patientsSearch,
  loadingPatients,
  patientsError,
  selectedPatientDetails,
  filteredPatients,
  fetchPatients,
} = usePatients()

const ITEMS_PER_PAGE = 10
const page = ref(1)
const totalPages = computed(() => Math.max(1, Math.ceil(filteredPatients.value.length / ITEMS_PER_PAGE)))
const paginatedPatients = computed(() => {
  const start = (page.value - 1) * ITEMS_PER_PAGE
  return filteredPatients.value.slice(start, start + ITEMS_PER_PAGE)
})
</script>

<template>
  <section class="space-y-5">
    <div class="rounded-2xl border border-[#E8EAED] bg-white p-6">
      <div class="mb-4 flex items-center gap-2">
        <Users class="h-5 w-5 text-[#1a73e8]" />
        <h3 class="text-lg font-semibold">All Patients</h3>
      </div>
      <p class="text-sm text-[#5f6368]">Search and view all registered patients with detailed information.</p>

      <div class="mt-4 flex flex-col gap-3 md:flex-row md:items-center">
        <input
          v-model="patientsSearch"
          class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm placeholder:text-[#9CA3AF] md:max-w-sm"
          placeholder="Search by name, patient ID, or email..."
          @input="page = 1"
        />
        <button
          class="inline-flex items-center justify-center gap-2 rounded-lg bg-[#1a73e8] px-4 py-2 text-sm font-medium text-white hover:bg-[#1765cc] disabled:opacity-60"
          :disabled="loadingPatients"
          @click="fetchPatients"
        >
          <LoaderCircle v-if="loadingPatients" class="h-4 w-4 animate-spin" />
          Refresh
        </button>
      </div>

      <p v-if="patientsError" class="mt-4 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ patientsError }}</p>

      <div v-if="loadingPatients" class="mt-4 text-sm text-[#5f6368]">Loading patients...</div>
      <div v-else-if="filteredPatients.length === 0 && !patientsError" class="mt-4 text-sm text-[#5f6368]">
        No patients found.
      </div>
      <template v-else-if="filteredPatients.length > 0">
        <div class="mt-4 overflow-hidden rounded-xl border border-[#E8EAED]">
          <table class="min-w-full divide-y divide-[#E8EAED] text-sm">
            <thead class="bg-[#F8F9FA]">
              <tr class="text-left text-[#5f6368]">
                <th class="px-4 py-3 font-medium">Patient ID</th>
                <th class="px-4 py-3 font-medium">Name</th>
                <th class="px-4 py-3 font-medium">Email</th>
                <th class="px-4 py-3 font-medium">Phone</th>
                <th class="px-4 py-3 font-medium">Action</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[#F1F3F4] bg-white">
              <tr v-for="patient in paginatedPatients" :key="patient.patientId">
                <td class="px-4 py-3 font-medium">{{ patient.patientId }}</td>
                <td class="px-4 py-3">{{ patient.name }}</td>
                <td class="px-4 py-3">{{ patient.email || 'N/A' }}</td>
                <td class="px-4 py-3">{{ patient.phoneNo || 'N/A' }}</td>
                <td class="px-4 py-3">
                  <button
                    class="rounded-lg bg-[#1a73e8] px-3 py-1 text-xs font-medium text-white hover:bg-[#1765cc]"
                    @click="selectedPatientDetails = patient"
                  >
                    Details
                  </button>
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
