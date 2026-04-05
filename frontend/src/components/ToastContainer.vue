<script setup>
import { AlertCircle, CircleCheckBig } from 'lucide-vue-next'
import { useToast } from '../composables/useToast'

const { toasts } = useToast()
</script>

<template>
  <div class="pointer-events-none fixed right-4 top-4 z-[70] flex w-full max-w-sm flex-col gap-2">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="pointer-events-auto rounded-xl border px-4 py-3 shadow-lg"
      :class="
        toast.type === 'success'
          ? 'border-[#B7DFBD] bg-[#E6F4EA] text-[#188038]'
          : 'border-[#F4C7C3] bg-[#FDECEC] text-[#B3261E]'
      "
    >
      <div class="flex items-start gap-2">
        <CircleCheckBig v-if="toast.type === 'success'" class="mt-0.5 h-4 w-4 shrink-0" />
        <AlertCircle v-else class="mt-0.5 h-4 w-4 shrink-0" />
        <p class="text-sm font-medium">{{ toast.message }}</p>
      </div>
    </div>
  </div>
</template>
