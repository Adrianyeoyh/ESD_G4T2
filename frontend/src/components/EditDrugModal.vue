<script setup>
import { LoaderCircle, X } from 'lucide-vue-next'
import { useInventory } from '../composables/useInventory'

const {
  editDrugModalOpen,
  editingDrug,
  editDrugError,
  editDrugForm,
  closeEditDrugModal,
  updateEditDrugField,
  submitEditDrug,
} = useInventory()
</script>

<template>
  <div
    v-if="editDrugModalOpen"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4"
  >
    <div class="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
      <div class="mb-5 flex items-center justify-between">
        <h3 class="text-xl font-semibold">Edit Drug</h3>
        <button class="rounded-lg p-2 hover:bg-[#F1F3F4]" @click="closeEditDrugModal">
          <X class="h-4 w-4" />
        </button>
      </div>

      <div class="grid gap-4">
        <div>
          <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Drug Name</label>
          <input :value="editDrugForm.drugName" disabled class="w-full rounded-lg border border-[#DADCE0] bg-[#F8F9FA] px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Unit Price ($)</label>
          <input v-model.number="editDrugForm.price" type="number" min="0.01" step="0.01" class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Stock Quantity</label>
          <input v-model.number="editDrugForm.quantity" type="number" min="0" class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm" />
        </div>
      </div>

      <p v-if="editDrugError" class="mt-4 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ editDrugError }}</p>

      <div class="mt-5 flex justify-end gap-3">
        <button class="rounded-lg border border-[#DADCE0] px-4 py-2 text-sm" @click="closeEditDrugModal">Cancel</button>
        <button
          class="inline-flex items-center gap-2 rounded-lg bg-[#1a73e8] px-4 py-2 text-sm font-medium text-white hover:bg-[#1765cc] disabled:opacity-60"
          :disabled="editingDrug"
          @click="submitEditDrug"
        >
          <LoaderCircle v-if="editingDrug" class="h-4 w-4 animate-spin" />
          Update
        </button>
      </div>
    </div>
  </div>
</template>
