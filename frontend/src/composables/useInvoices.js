import { computed, ref } from 'vue'
import { fetchInvoicesApi } from '../api/invoices'
import { useRecords } from './useRecords'
import { usePatients } from './usePatients'

// Exported directly so useRecords can read it without circular dependency
export const invoices = ref([])
const loadingInvoices = ref(false)
const invoicesError = ref('')

export function useInvoices() {
  const { normalizedRecords } = useRecords()
  const { patientsData } = usePatients()

  const recordMap = computed(() => {
    const map = {}
    for (const r of normalizedRecords.value) {
      map[r.Id] = r
    }
    return map
  })

  const patientMap = computed(() => {
    const map = {}
    for (const p of patientsData.value) {
      const id = String(p.patientId || '').trim().toLowerCase()
      if (id) map[id] = p
    }
    return map
  })

  const enrichedInvoices = computed(() =>
    invoices.value.map((inv) => {
      const recordId = inv.recordId ?? inv.record_id
      const record = recordMap.value[recordId]
      const patientId = record?.patientId || ''
      const patient = patientMap.value[patientId.toLowerCase()]
      return {
        invoiceId: inv.invoiceId ?? inv.invoice_id,
        recordId,
        total: Number(inv.total ?? 0),
        status: String(inv.status ?? 'DRAFT').toUpperCase(),
        patientName: patient?.name ?? 'Unknown patient',
        patientId,
        nric: patientId,
        visitNotes: record?.VisitNotes ?? '',
        date: record?.date ?? '',
        currency: 'SGD',
      }
    }),
  )

  const pendingInvoices = computed(() =>
    enrichedInvoices.value.filter((inv) => inv.status !== 'PAID' && inv.status !== 'CANCELLED'),
  )

  const fetchInvoices = async () => {
    loadingInvoices.value = true
    invoicesError.value = ''
    try {
      invoices.value = await fetchInvoicesApi()
    } catch (error) {
      invoicesError.value = error?.message || 'Unable to fetch invoices.'
    } finally {
      loadingInvoices.value = false
    }
  }

  return {
    invoices,
    loadingInvoices,
    invoicesError,
    enrichedInvoices,
    pendingInvoices,
    fetchInvoices,
  }
}
