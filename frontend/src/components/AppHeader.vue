<script setup>
import { LoaderCircle } from 'lucide-vue-next'

defineProps({
  title: { type: String, required: true },
  syncing: { type: Boolean, default: false },
})
const emit = defineEmits(['refresh'])
</script>

<template>
  <header class="mb-8 flex items-center justify-between">
    <div>
      <h2 class="text-3xl font-semibold tracking-tight">{{ title }}</h2>
      <p class="mt-1 text-sm text-[#5f6368]">
        Google Stitch-inspired layout with spacing-first clinical clarity.
      </p>
    </div>

    <div class="flex items-center gap-3">
      <span
        v-if="syncing"
        class="rounded-full bg-[#E8F0FE] px-3 py-1 text-xs font-semibold text-[#1a73e8]"
      >
        Syncing...
      </span>
      <button
        class="inline-flex items-center gap-2 rounded-lg bg-[#1a73e8] px-4 py-2 text-sm font-medium text-white hover:bg-[#1765cc]"
        @click="emit('refresh')"
      >
        <LoaderCircle class="h-4 w-4" /> Refresh
      </button>
    </div>
  </header>
</template>
