<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CONSULTATION_DRAFT_KEY } from './api/endpoints'
import { useInventory } from './composables/useInventory'
import { useRecords } from './composables/useRecords'
import { usePatients } from './composables/usePatients'
import { useConsultation } from './composables/useConsultation'
import { useInvoices } from './composables/useInvoices'
import { usePayment } from './composables/usePayment'
import { useOutsystemsSync } from './composables/useOutsystemsSync'

import ToastContainer from './components/ToastContainer.vue'
import AppSidebar from './components/AppSidebar.vue'
import AppHeader from './components/AppHeader.vue'
import PatientRegistrationModal from './components/PatientRegistrationModal.vue'
import PatientDetailsModal from './components/PatientDetailsModal.vue'
import DeleteDrugModal from './components/DeleteDrugModal.vue'
import AddDrugModal from './components/AddDrugModal.vue'
import EditDrugModal from './components/EditDrugModal.vue'

const route = useRoute()
const router = useRouter()

const fullScreenRoutes = ['consultation-review', 'payment-success']
const isFullScreen = computed(() => fullScreenRoutes.includes(route.name))

const navLabels = {
  inventory: 'Inventory',
  consultation: 'Create Consultation',
  'past-consultations': 'Past Consultations',
  'patient-history': 'Patient History',
  patients: 'All Patients',
  payments: 'Payments',
}
const pageTitle = computed(() => navLabels[route.name] ?? '')

const { fetchDrugs } = useInventory()
const { fetchRecords } = useRecords()
const { fetchPatients, openPatientModal } = usePatients()
const { resetConsultationState, syncConsultationDrugSelections } = useConsultation()
const { fetchInvoices } = useInvoices()
const { outsystemsSyncing } = useOutsystemsSync()
const {
  paymentStep,
  selectedInvoice,
  paymentIntentId,
  initializeStripe,
} = usePayment()

const refreshAll = async () => {
  await Promise.all([fetchDrugs(), fetchPatients()])
  syncConsultationDrugSelections()
  await fetchRecords()
  fetchInvoices()
}

watch(
  () => route.name,
  (newName, oldName) => {
    if (oldName === 'consultation' && newName !== 'consultation' && newName !== 'consultation-review') {
      sessionStorage.removeItem(CONSULTATION_DRAFT_KEY)
      resetConsultationState()
    }
    if (oldName === 'consultation-review' && newName !== 'consultation-review') {
      const hasPendingDraft = Boolean(sessionStorage.getItem(CONSULTATION_DRAFT_KEY))
      if (!hasPendingDraft) {
        resetConsultationState()
      }
    }
  },
)

onMounted(async () => {
  if (window.location.pathname === '/success') {
    window.history.replaceState({}, '', `/payment-success${window.location.search}`)
  }

  if (route.name === 'payment-success') {
    const query = new URLSearchParams(window.location.search)
    paymentStep.value = 3
    paymentIntentId.value = query.get('paymentIntentId') || ''
    const successInvoiceId = query.get('invoiceId') || ''
    selectedInvoice.value = successInvoiceId
      ? {
          invoiceId: successInvoiceId,
          patientName: 'N/A',
          amount: 0,
          currency: 'SGD',
          status: 'PAID',
          diagnosis: 'N/A',
        }
      : null
  }
  await initializeStripe()
  await refreshAll()
})
</script>

<template>
  <!-- Full-screen routes (no sidebar layout) -->
  <router-view v-if="isFullScreen" />

  <!-- Dashboard layout -->
  <div v-else class="min-h-screen bg-[#F8F9FA] text-[#202124]">
    <ToastContainer />

    <div class="mx-auto flex min-h-screen max-w-[1440px]">
      <AppSidebar @register-patient="openPatientModal" />

      <main class="flex-1 px-10 py-8">
        <AppHeader
          :title="pageTitle"
          :syncing="outsystemsSyncing"
          @refresh="refreshAll"
        />

        <router-view />
      </main>
    </div>

    <PatientRegistrationModal />
    <PatientDetailsModal />
    <DeleteDrugModal />
    <AddDrugModal />
    <EditDrugModal />
  </div>
</template>
