<script setup>
import { X } from 'lucide-vue-next'
import { usePatients } from '../composables/usePatients'

const { selectedPatientDetails } = usePatients()
</script>

<template>
  <div
    v-if="selectedPatientDetails"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4"
  >
    <div class="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
      <div class="mb-5 flex items-center justify-between">
        <h3 class="text-xl font-semibold">Patient Details</h3>
        <button class="rounded-lg p-2 hover:bg-[#F1F3F4]" @click="selectedPatientDetails = null">
          <X class="h-4 w-4" />
        </button>
      </div>

      <div class="space-y-4">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.14em] text-[#5f6368]">Patient ID (NRIC)</p>
          <p class="mt-1 text-lg font-semibold">{{ selectedPatientDetails.patientId }}</p>
        </div>
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.14em] text-[#5f6368]">Full Name</p>
          <p class="mt-1 text-lg font-semibold">{{ selectedPatientDetails.name }}</p>
        </div>
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.14em] text-[#5f6368]">Email</p>
          <p class="mt-1 text-base">{{ selectedPatientDetails.email || 'N/A' }}</p>
        </div>
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.14em] text-[#5f6368]">Phone Number</p>
          <p class="mt-1 text-base">{{ selectedPatientDetails.phoneNo || 'N/A' }}</p>
        </div>
      </div>

      <div class="mt-6 flex justify-end">
        <button
          class="rounded-lg border border-[#DADCE0] px-4 py-2 text-sm font-medium text-[#5f6368] hover:bg-[#F1F3F4]"
          @click="selectedPatientDetails = null"
        >
          Close
        </button>
      </div>
    </div>
  </div>
</template>
