<script setup>
import { useRoute, useRouter } from 'vue-router'
import { CreditCard, FileText, History, Pill, UserPlus, Users, Wallet } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const emit = defineEmits(['registerPatient'])

const navItems = [
  { name: 'inventory', label: 'Inventory', icon: Pill },
  { name: 'consultation', label: 'Create Consultation', icon: FileText },
  { name: 'past-consultations', label: 'Past Consultations', icon: History },
  { name: 'patient-history', label: 'Patient History', icon: FileText },
  { name: 'patients', label: 'All Patients', icon: Users },
  { name: 'payments', label: 'Payments', icon: CreditCard },
]

const navigate = (routeName) => {
  router.push({ name: routeName })
}
</script>

<template>
  <aside class="w-72 border-r border-[#E8EAED] bg-white px-6 py-8">
    <div class="mb-10 flex items-center gap-3">
      <div class="rounded-xl bg-[#1a73e8] p-2 text-white">
        <Wallet class="h-5 w-5" />
      </div>
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.2em] text-[#5f6368]">MedFlow</p>
        <h1 class="text-xl font-semibold">Medical Dashboard</h1>
      </div>
    </div>

    <button
      class="mb-6 flex w-full items-center justify-center gap-2 rounded-lg border border-[#DADCE0] px-4 py-2 text-sm font-medium text-[#1a73e8] hover:bg-[#E8F0FE]"
      @click="emit('registerPatient')"
    >
      <UserPlus class="h-4 w-4" /> Register Patient
    </button>

    <nav class="space-y-2">
      <button
        v-for="item in navItems"
        :key="item.name"
        class="flex w-full items-center gap-3 rounded-lg px-4 py-3 text-left text-sm transition"
        :class="
          route.name === item.name
            ? 'bg-[#E8F0FE] text-[#1a73e8]'
            : 'text-[#5f6368] hover:bg-[#F1F3F4] hover:text-[#202124]'
        "
        @click="navigate(item.name)"
      >
        <component :is="item.icon" class="h-4 w-4" />
        {{ item.label }}
      </button>
    </nav>
  </aside>
</template>
