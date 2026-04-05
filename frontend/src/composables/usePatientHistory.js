import { computed, ref } from 'vue'
import { fetchRecordsByPatientApi } from '../api/records'
import { fetchPrescriptionsByRecordIdApi } from '../api/prescriptions'
import { normalizePrescriptionRows, parseErrorMessage } from '../utils/normalizers'
import { useOutsystemsSync } from './useOutsystemsSync'

const patientHistoryForm = ref({ patientId: '' })
const loadingPatientHistory = ref(false)
const patientHistoryError = ref('')
const patientHistoryPrescriptionError = ref('')
const patientHistoryRecords = ref([])
const prescriptionsByRecord = ref({})

export function usePatientHistory() {
  const { beginOutsystemsSync, endOutsystemsSync } = useOutsystemsSync()

  const enrichedRecords = computed(() =>
    patientHistoryRecords.value.map((record) => {
      const recordId = Number(record.Id ?? record.id)
      const prescriptions = prescriptionsByRecord.value[recordId] || []
      return { ...record, recordId, prescriptions }
    }),
  )

  const fetchPatientHistory = async () => {
    patientHistoryError.value = ''
    patientHistoryPrescriptionError.value = ''
    patientHistoryRecords.value = []
    prescriptionsByRecord.value = {}

    const patientId = String(patientHistoryForm.value.patientId || '').trim()
    if (!patientId || patientId.length !== 9) {
      patientHistoryError.value = 'Please enter a valid 9-character patientId.'
      return
    }

    loadingPatientHistory.value = true
    beginOutsystemsSync()

    try {
      patientHistoryRecords.value = await fetchRecordsByPatientApi(patientId)

      if (!patientHistoryRecords.value.length) return

      const recordIds = patientHistoryRecords.value
        .map((record) => Number(record.Id ?? record.id ?? record.recordId ?? record.RecordId))
        .filter((recordId) => Number.isFinite(recordId) && recordId > 0)

      const prescriptionResults = await Promise.allSettled(
        recordIds.map((recordId) => fetchPrescriptionsByRecordIdApi(recordId)),
      )

      const map = {}
      for (let i = 0; i < recordIds.length; i++) {
        const result = prescriptionResults[i]
        if (result.status === 'fulfilled' && Array.isArray(result.value)) {
          map[recordIds[i]] = normalizePrescriptionRows(result.value)
        } else if (result.status === 'rejected') {
          const statusCode = result.reason?.response?.status
          if (statusCode !== 404) {
            patientHistoryPrescriptionError.value = parseErrorMessage(
              result.reason,
              'Unable to fetch prescriptions for this patient.',
            )
          }
        }
      }
      prescriptionsByRecord.value = map
    } finally {
      loadingPatientHistory.value = false
      endOutsystemsSync()
    }
  }

  return {
    patientHistoryForm,
    loadingPatientHistory,
    patientHistoryError,
    patientHistoryPrescriptionError,
    enrichedRecords,
    fetchPatientHistory,
  }
}
