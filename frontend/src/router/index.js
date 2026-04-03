import { createRouter, createWebHistory } from 'vue-router'
import InvoiceSelection from '../views/InvoiceSelection.vue'
import PaymentPortal from '../views/PaymentPortal.vue'
import PaymentSuccess from '../views/PaymentSuccess.vue'
import ConsultationReview from '../views/ConsultationReview.vue'

const routes = [
  {
    path: '/',
    name: 'invoice-selection',
    component: InvoiceSelection,
  },
  {
    path: '/payment/:invoiceId',
    name: 'payment-portal',
    component: PaymentPortal,
    props: true,
  },
  {
    path: '/payment-success',
    name: 'payment-success',
    component: PaymentSuccess,
  },
  {
    path: '/consultation/review',
    name: 'consultation-review',
    component: ConsultationReview,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
