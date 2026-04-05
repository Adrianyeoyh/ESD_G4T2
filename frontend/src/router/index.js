import { createRouter, createWebHistory } from 'vue-router'

import InventoryView from '../components/InventoryView.vue'
import ConsultationView from '../components/ConsultationView.vue'
import PastConsultationsView from '../components/PastConsultationsView.vue'
import PatientHistoryView from '../components/PatientHistoryView.vue'
import PatientsView from '../components/PatientsView.vue'
import PaymentsView from '../components/PaymentsView.vue'
import ConsultationReview from '../views/ConsultationReview.vue'
import PaymentSuccess from '../views/PaymentSuccess.vue'

const routes = [
  { path: '/', name: 'inventory', component: InventoryView },
  { path: '/consultation', name: 'consultation', component: ConsultationView },
  { path: '/consultation/review', name: 'consultation-review', component: ConsultationReview },
  { path: '/past-consultations', name: 'past-consultations', component: PastConsultationsView },
  { path: '/patient-history', name: 'patient-history', component: PatientHistoryView },
  { path: '/patients', name: 'patients', component: PatientsView },
  { path: '/payments', name: 'payments', component: PaymentsView },
  { path: '/payment-success', name: 'payment-success', component: PaymentSuccess },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
