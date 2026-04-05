import { ref } from 'vue'
import { useRecords } from './useRecords'

const billingRows = ref([])
const loadingBilling = ref(false)
const billingError = ref('')
const billingSuccess = ref('')
const markingPaidId = ref(null)

export function useBilling() {
  const { records, normalizedRecords } = useRecords()

  const loadBillingRows = () => {
    loadingBilling.value = true
    billingError.value = ''
    billingSuccess.value = ''

    billingRows.value = normalizedRecords.value
      .filter((row) => row.isClosed)
      .map((row) => ({
        Id: row.Id,
        patientName: row.patientName,
        nric: row.nric,
        VisitNotes: row.VisitNotes,
        email: row.email,
        isPaid: String(row.status).toUpperCase() === 'PAID',
      }))

    loadingBilling.value = false
  }

  const markAsPaid = (row) => {
    billingError.value = ''
    billingSuccess.value = ''
    markingPaidId.value = row.Id

    billingRows.value = billingRows.value.map((item) =>
      item.Id === row.Id ? { ...item, isPaid: true } : item,
    )
    records.value = records.value.map((item) => {
      const itemId = Number(item.Id ?? item.id)
      if (itemId !== Number(row.Id)) return item
      return { ...item, status: 'PAID' }
    })
    billingSuccess.value = `Record ${row.Id} marked as paid.`
    markingPaidId.value = null
  }

  return {
    billingRows,
    loadingBilling,
    billingError,
    billingSuccess,
    markingPaidId,
    loadBillingRows,
    markAsPaid,
  }
}
