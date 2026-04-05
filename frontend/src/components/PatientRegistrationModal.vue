<script setup>
import { LoaderCircle, Plus } from 'lucide-vue-next'
import { usePatients } from '../composables/usePatients'

const {
  patientModalOpen,
  submittingPatient,
  patientFormError,
  patientFormSuccess,
  patientForm,
  closePatientModal,
  submitPatient,
} = usePatients()
</script>

<template>
  <div
    v-if="patientModalOpen"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4"
  >
    <div class="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
      <div class="mb-5 flex items-center justify-between">
        <h3 class="text-xl font-semibold">Register Patient</h3>
        <button class="rounded-lg p-2 hover:bg-[#F1F3F4]" @click="closePatientModal">
          <Plus class="h-4 w-4 rotate-45" />
        </button>
      </div>

      <div class="grid gap-4">
        <input
          v-model="patientForm.patientId"
          class="rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
          placeholder="Patient ID (NRIC - 9 characters)"
        />
        <input
          v-model="patientForm.name"
          class="rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
          placeholder="Full Name"
        />
        <input
          v-model="patientForm.phoneNo"
          class="rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
          placeholder="Phone Number"
        />
        <input
          v-model="patientForm.email"
          class="rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
          placeholder="Email"
        />
      </div>

      <p v-if="patientFormError" class="mt-4 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">
        {{ patientFormError }}
      </p>
      <p v-if="patientFormSuccess" class="mt-4 rounded-lg bg-[#E6F4EA] p-3 text-sm text-[#188038]">
        {{ patientFormSuccess }}
      </p>

      <div class="mt-5 flex justify-end gap-3">
        <button class="rounded-lg border border-[#DADCE0] px-4 py-2 text-sm" @click="closePatientModal">
          Cancel
        </button>
        <button
          class="inline-flex items-center gap-2 rounded-lg bg-[#1a73e8] px-4 py-2 text-sm font-medium text-white hover:bg-[#1765cc] disabled:opacity-60"
          :disabled="submittingPatient"
          @click="submitPatient"
        >
          <LoaderCircle v-if="submittingPatient" class="h-4 w-4 animate-spin" />
          Submit
        </button>
      </div>
    </div>
  </div>
</template>
