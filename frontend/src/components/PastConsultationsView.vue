<script setup>
import { computed, ref, watch } from 'vue'
import { ChevronLeft, ChevronRight, FileText } from 'lucide-vue-next'
import { useRecords } from '../composables/useRecords'

const { loadingRecords, recordsError, normalizedRecords, openRecords, closedRecords } = useRecords()

const filter = ref('all')
const ITEMS_PER_PAGE = 10
const page = ref(1)

watch(filter, () => { page.value = 1 })

const sortedByLatest = (records) => [...records].sort((a, b) => b.Id - a.Id)

const filteredRecords = computed(() => {
  if (filter.value === 'open') return sortedByLatest(openRecords.value)
  if (filter.value === 'closed') return sortedByLatest(closedRecords.value)
  return sortedByLatest(normalizedRecords.value)
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRecords.value.length / ITEMS_PER_PAGE)))
const paginatedRecords = computed(() => {
  const start = (page.value - 1) * ITEMS_PER_PAGE
  return filteredRecords.value.slice(start, start + ITEMS_PER_PAGE)
})
</script>

<template>
  <section class="space-y-5">
    <div class="rounded-2xl border border-[#E8EAED] bg-white p-6">
      <div class="mb-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div class="flex items-center gap-2">
          <FileText class="h-5 w-5 text-[#1a73e8]" />
          <h3 class="text-lg font-semibold">Past Consultations</h3>
          <span class="rounded-full bg-[#E8F0FE] px-2 py-0.5 text-xs font-semibold text-[#1a73e8]">{{ filteredRecords.length }}</span>
        </div>

        <div class="flex gap-1 rounded-lg border border-[#DADCE0] p-1">
          <button
            class="rounded-md px-3 py-1.5 text-xs font-medium transition"
            :class="filter === 'all' ? 'bg-[#1a73e8] text-white' : 'text-[#5f6368] hover:bg-[#F1F3F4]'"
            @click="filter = 'all'"
          >
            All ({{ normalizedRecords.length }})
          </button>
          <button
            class="rounded-md px-3 py-1.5 text-xs font-medium transition"
            :class="filter === 'open' ? 'bg-[#1a73e8] text-white' : 'text-[#5f6368] hover:bg-[#F1F3F4]'"
            @click="filter = 'open'"
          >
            Open ({{ openRecords.length }})
          </button>
          <button
            class="rounded-md px-3 py-1.5 text-xs font-medium transition"
            :class="filter === 'closed' ? 'bg-[#1a73e8] text-white' : 'text-[#5f6368] hover:bg-[#F1F3F4]'"
            @click="filter = 'closed'"
          >
            Closed ({{ closedRecords.length }})
          </button>
        </div>
      </div>

      <p v-if="loadingRecords" class="text-sm text-[#5f6368]">Loading records...</p>
      <p v-else-if="recordsError" class="rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ recordsError }}</p>
      <p v-else-if="filteredRecords.length === 0" class="text-sm text-[#5f6368]">No consultations found.</p>

      <template v-else>
        <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <article
            v-for="record in paginatedRecords"
            :key="record.Id"
            class="rounded-2xl border border-[#E8EAED] bg-white p-5 shadow-sm transition hover:bg-[#F8F9FA]"
          >
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-[#5f6368]">Record #{{ record.Id }}</p>
            <h4 class="mt-2 text-lg font-semibold">{{ record.patientName }}</h4>
            <p class="mt-1 text-xs text-[#5f6368]">{{ record.patientId }}</p>
            <p class="mt-2 text-sm text-[#5f6368]">{{ record.VisitNotes || 'No notes available' }}</p>
            <p class="mt-3 text-sm text-[#5f6368]">Visit: {{ record.date || 'N/A' }}</p>
            <span
              class="mt-2 inline-block rounded-full px-2 py-0.5 text-xs font-semibold"
              :class="record.isClosed ? 'bg-[#E6F4EA] text-[#188038]' : 'bg-[#FFF8E1] text-[#7A5C00]'"
            >
              {{ record.isClosed ? 'Closed' : 'Open' }}
            </span>
          </article>
        </div>

        <div v-if="totalPages > 1" class="mt-6 flex items-center justify-center gap-2">
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
