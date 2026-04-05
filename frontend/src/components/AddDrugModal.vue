<script setup>
import { LoaderCircle, X } from 'lucide-vue-next'
import { useInventory } from '../composables/useInventory'

const {
  addDrugModalOpen,
  addingDrug,
  addDrugError,
  addDrugForm,
  closeAddDrugModal,
  updateAddDrugField,
  submitAddDrug,
} = useInventory()
</script>

<template>
  <div
    v-if="addDrugModalOpen"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4"
  >
    <div class="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
      <div class="mb-5 flex items-center justify-between">
        <h3 class="text-xl font-semibold">Add New Drug</h3>
        <button class="rounded-lg p-2 hover:bg-[#F1F3F4]" @click="closeAddDrugModal">
          <X class="h-4 w-4" />
        </button>
      </div>

      <div class="grid gap-4">
        <div>
          <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Drug Name</label>
          <input v-model="addDrugForm.drugName" class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Unit Price ($)</label>
          <input v-model.number="addDrugForm.price" type="number" min="0.01" step="0.01" class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Stock Quantity</label>
          <input v-model.number="addDrugForm.quantity" type="number" min="0" class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm" />
        </div>
      </div>

      <p v-if="addDrugError" class="mt-4 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ addDrugError }}</p>

      <div class="mt-5 flex justify-end gap-3">
        <button class="rounded-lg border border-[#DADCE0] px-4 py-2 text-sm" @click="closeAddDrugModal">Cancel</button>
        <button
          class="inline-flex items-center gap-2 rounded-lg bg-[#1a73e8] px-4 py-2 text-sm font-medium text-white hover:bg-[#1765cc] disabled:opacity-60"
          :disabled="addingDrug"
          @click="submitAddDrug"
        >
          <LoaderCircle v-if="addingDrug" class="h-4 w-4 animate-spin" />
          Save
        </button>
      </div>
    </div>
  </div>
</template>
