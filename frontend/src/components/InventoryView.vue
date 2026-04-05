<script setup>
import {
  ArrowUpDown,
  ChevronDown,
  ChevronUp,
  LoaderCircle,
  Pill,
  Plus,
  SquarePen,
  Trash2,
} from 'lucide-vue-next'
import { useInventory } from '../composables/useInventory'

const {
  loadingInventory,
  inventoryError,
  inventoryNotice,
  inventorySearch,
  inventorySortKey,
  inventorySortOrder,
  filteredInventory,
  sortedInventory,
  toggleInventorySort,
  deletingDrugId,
  deletingDrugError,
  openAddDrugModal,
  openEditDrugModal,
  openDeleteDrugConfirm,
  inventory,
} = useInventory()
</script>

<template>
  <section class="rounded-2xl border border-[#E8EAED] bg-white p-6">
    <div class="mb-6 flex items-center justify-between gap-2">
      <div class="flex items-center gap-2">
        <Pill class="h-5 w-5 text-[#1a73e8]" />
        <h3 class="text-lg font-semibold">Drug Inventory</h3>
      </div>
      <button
        class="inline-flex items-center gap-2 rounded-lg bg-[#1a73e8] px-3 py-2 text-sm font-medium text-white hover:bg-[#1765cc]"
        @click="openAddDrugModal"
      >
        <Plus class="h-4 w-4" />
        Add New Drug
      </button>
    </div>

    <div class="mb-4">
      <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">
        Search Drug
      </label>
      <input
        v-model="inventorySearch"
        class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm focus:border-[#1a73e8] focus:outline-none"
        placeholder="Search by drug name or purpose..."
      />
    </div>

    <p v-if="loadingInventory" class="text-sm text-[#5f6368]">Loading inventory...</p>
    <p
      v-else-if="!inventoryError && inventory.length === 0"
      class="rounded-lg bg-[#FFF8E1] p-3 text-sm text-[#7A5C00]"
    >
      Inventory is currently empty.
    </p>
    <p
      v-else-if="!inventoryError && filteredInventory.length === 0"
      class="rounded-lg bg-[#F8F9FA] p-3 text-sm text-[#5f6368]"
    >
      No drugs match your search.
    </p>
    <p
      v-else-if="inventoryNotice"
      class="rounded-lg bg-[#E8F0FE] p-3 text-sm text-[#1a73e8]"
    >
      {{ inventoryNotice }}
    </p>
    <p
      v-else-if="inventoryError"
      class="rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]"
    >
      {{ inventoryError }}
    </p>
    <p
      v-else-if="deletingDrugError"
      class="rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]"
    >
      {{ deletingDrugError }}
    </p>

    <div v-else class="overflow-hidden rounded-xl border border-[#E8EAED]">
      <table class="min-w-full divide-y divide-[#E8EAED] text-sm">
        <thead class="bg-[#F8F9FA]">
          <tr class="text-left text-[#5f6368]">
            <th
              class="cursor-pointer select-none px-4 py-3 font-medium transition hover:bg-[#E8EAED]"
              @click="toggleInventorySort('name')"
            >
              <span class="inline-flex items-center gap-1">
                Drug
                <ChevronUp v-if="inventorySortKey === 'name' && inventorySortOrder === 'asc'" class="h-3.5 w-3.5" />
                <ChevronDown v-else-if="inventorySortKey === 'name' && inventorySortOrder === 'desc'" class="h-3.5 w-3.5" />
                <ArrowUpDown v-else class="h-3.5 w-3.5 opacity-40" />
              </span>
            </th>
            <th
              class="cursor-pointer select-none px-4 py-3 font-medium transition hover:bg-[#E8EAED]"
              @click="toggleInventorySort('stock')"
            >
              <span class="inline-flex items-center gap-1">
                Stock
                <ChevronUp v-if="inventorySortKey === 'stock' && inventorySortOrder === 'asc'" class="h-3.5 w-3.5" />
                <ChevronDown v-else-if="inventorySortKey === 'stock' && inventorySortOrder === 'desc'" class="h-3.5 w-3.5" />
                <ArrowUpDown v-else class="h-3.5 w-3.5 opacity-40" />
              </span>
            </th>
            <th
              class="cursor-pointer select-none px-4 py-3 font-medium transition hover:bg-[#E8EAED]"
              @click="toggleInventorySort('price')"
            >
              <span class="inline-flex items-center gap-1">
                Price (SGD)
                <ChevronUp v-if="inventorySortKey === 'price' && inventorySortOrder === 'asc'" class="h-3.5 w-3.5" />
                <ChevronDown v-else-if="inventorySortKey === 'price' && inventorySortOrder === 'desc'" class="h-3.5 w-3.5" />
                <ArrowUpDown v-else class="h-3.5 w-3.5 opacity-40" />
              </span>
            </th>
            <th class="px-4 py-3 font-medium">Action</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-[#F1F3F4] bg-white">
          <template v-for="(drug, idx) in sortedInventory" :key="drug.id ?? idx">
            <tr class="hover:bg-[#F8F9FA]">
              <td class="px-4 py-3">{{ drug.name ?? drug.drugName ?? 'Unnamed Drug' }}</td>
              <td class="px-4 py-3">{{ drug.quantity ?? 0 }}</td>
              <td class="px-4 py-3">{{ Number(drug.price ?? 0).toFixed(2) }}</td>
              <td class="px-4 py-3">
                <div class="flex flex-wrap items-center gap-2">
                  <button
                    class="inline-flex items-center gap-1 rounded-lg border border-[#DADCE0] px-2.5 py-1.5 text-xs font-medium text-[#202124] hover:bg-[#F1F3F4]"
                    @click="openEditDrugModal(drug)"
                  >
                    <SquarePen class="h-3.5 w-3.5" /> Edit
                  </button>
                  <button
                    class="inline-flex items-center gap-1 rounded-lg border border-[#F4C7C3] px-2.5 py-1.5 text-xs font-medium text-[#B3261E] hover:bg-[#FDECEC] disabled:opacity-60"
                    :disabled="deletingDrugId === drug.id"
                    @click="openDeleteDrugConfirm(drug)"
                  >
                    <LoaderCircle v-if="deletingDrugId === drug.id" class="h-3.5 w-3.5 animate-spin" />
                    <Trash2 v-else class="h-3.5 w-3.5" />
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </section>
</template>
