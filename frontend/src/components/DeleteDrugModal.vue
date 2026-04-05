<script setup>
import { LoaderCircle, X } from 'lucide-vue-next'
import { useInventory } from '../composables/useInventory'

const {
  deleteDrugConfirmOpen,
  deleteDrugTarget,
  deletingDrugId,
  closeDeleteDrugConfirm,
  deleteDrug,
} = useInventory()
</script>

<template>
  <div
    v-if="deleteDrugConfirmOpen"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4"
  >
    <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
      <div class="mb-4 flex items-center justify-between">
        <h3 class="text-xl font-semibold text-[#202124]">Confirm Deletion</h3>
        <button class="rounded-lg p-2 hover:bg-[#F1F3F4]" @click="closeDeleteDrugConfirm">
          <X class="h-4 w-4" />
        </button>
      </div>

      <p class="text-sm text-[#5f6368]">
        Are you sure you want to delete
        <span class="font-semibold text-[#202124]">{{ deleteDrugTarget?.drugName || 'this drug' }}</span>
        from inventory?
      </p>
      <p class="mt-2 text-xs text-[#B3261E]">This action cannot be undone.</p>

      <div class="mt-6 flex justify-end gap-3">
        <button class="rounded-lg border border-[#DADCE0] px-4 py-2 text-sm" @click="closeDeleteDrugConfirm">
          Cancel
        </button>
        <button
          class="inline-flex items-center gap-2 rounded-lg bg-[#B3261E] px-4 py-2 text-sm font-medium text-white hover:bg-[#8e1f16] disabled:opacity-60"
          :disabled="deletingDrugId !== null"
          @click="deleteDrug"
        >
          <LoaderCircle v-if="deletingDrugId !== null" class="h-4 w-4 animate-spin" />
          Delete Drug
        </button>
      </div>
    </div>
  </div>
</template>
