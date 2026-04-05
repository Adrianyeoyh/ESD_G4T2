import { computed, ref } from 'vue'
import { fetchRecordsByPatientApi } from '../api/records'
import { normalizeRecord } from '../utils/normalizers'
import { useOutsystemsSync } from './useOutsystemsSync'
import { usePatients } from './usePatients'
import { invoices } from './useInvoices'

const records = ref([])
const loadingRecords = ref(false)
const recordsError = ref('')

export function useRecords() {
  const { beginOutsystemsSync, endOutsystemsSync } = useOutsystemsSync()
  const { patientsData } = usePatients()

  const patientMap = computed(() => {
    const map = {}
    for (const p of patientsData.value) {
      const id = String(p.patientId || '').trim()
      if (id) map[id] = p
    }
    return map
  })

  const paidRecordIds = computed(() => {
    const ids = new Set()
    for (const inv of invoices.value) {
      const status = String(inv.status ?? '').toLowerCase()
      if (status === 'paid') {
        ids.add(Number(inv.recordId ?? inv.record_id))
      }
    }
    return ids
  })

  const normalizedRecords = computed(() =>
    records.value.map((record, idx) => {
      const base = normalizeRecord(record, idx)
      const patient = patientMap.value[base.patientId]
      if (patient) {
        base.patientName = patient.name || base.patientName
        base.nric = base.patientId
        base.email = patient.email || base.email
      }
      if (paidRecordIds.value.has(base.Id)) {
        base.isClosed = true
        base.status = 'CLOSED'
      }
      return base
    }),
  )

  const openRecords = computed(() =>
    normalizedRecords.value.filter((r) => !r.isClosed),
  )

  const closedRecords = computed(() =>
    normalizedRecords.value.filter((r) => r.isClosed),
  )

  const fetchRecords = async () => {
    loadingRecords.value = true
    recordsError.value = ''
    beginOutsystemsSync()

    try {
      const patients = patientsData.value
      if (!patients.length) {
        records.value = []
        return
      }

      const validPatientIds = patients
        .map((p) => String(p.patientId || '').trim())
        .filter((id) => id.length > 0)

      if (!validPatientIds.length) {
        records.value = []
        return
      }

      const results = await Promise.allSettled(
        validPatientIds.map((id) => fetchRecordsByPatientApi(id)),
      )

      const allRecords = []
      for (const result of results) {
        if (result.status === 'fulfilled' && Array.isArray(result.value)) {
          allRecords.push(...result.value)
        }
      }
      records.value = allRecords
    } catch (error) {
      recordsError.value =
        error?.response?.data?.message || 'Unable to load Clinical Records.'
      records.value = []
    } finally {
      loadingRecords.value = false
      endOutsystemsSync()
    }
  }

  return {
    records,
    loadingRecords,
    recordsError,
    normalizedRecords,
    openRecords,
    closedRecords,
    fetchRecords,
  }
}
