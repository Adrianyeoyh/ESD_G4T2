<script setup>
import { LoaderCircle } from 'lucide-vue-next'
import { useConsultation } from '../composables/useConsultation'

const {
  consultationForm,
  submittingConsultation,
  consultationError,
  consultationSuccess,
  submitConsultation,
} = useConsultation()
</script>

<template>
  <section class="space-y-5">
    <div class="rounded-2xl border border-[#E8EAED] bg-white p-6">
      <h4 class="text-lg font-semibold">Create Consultation</h4>
      <p class="mt-1 text-sm text-[#5f6368]">Enter patient ID and visit notes, then proceed to the review page to add medication and confirm.</p>
      <div class="mt-4 grid gap-3 md:grid-cols-2">
        <input
          v-model="consultationForm.patientId"
          class="rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
          placeholder="Patient ID"
        />
        <input
          v-model="consultationForm.visitNotes"
          class="rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
          placeholder="Visit Notes"
        />
      </div>

      <button
        class="mt-4 rounded-lg bg-[#1a73e8] px-4 py-2 text-sm font-medium text-white hover:bg-[#1765cc] disabled:opacity-60"
        :disabled="submittingConsultation"
        @click="submitConsultation"
      >
        <span class="inline-flex items-center gap-2">
          <LoaderCircle v-if="submittingConsultation" class="h-4 w-4 animate-spin" />
          Proceed to Review
        </span>
      </button>
      <p v-if="consultationError" class="mt-3 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ consultationError }}</p>
      <p v-if="consultationSuccess" class="mt-3 rounded-lg bg-[#E6F4EA] p-3 text-sm text-[#188038]">{{ consultationSuccess }}</p>
    </div>
  </section>
</template>
