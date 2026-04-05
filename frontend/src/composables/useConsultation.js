import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { normalizeConsultationDrug } from '../utils/normalizers'
import { CONSULTATION_DRAFT_KEY } from '../api/endpoints'
import { verifyPatientExistsApi } from '../api/patients'
import { useInventory } from './useInventory'

const consultationForm = ref({ patientId: '', visitNotes: '' })
const consultationDrugSearch = ref('')
const consultationDrugSelections = ref({})
const submittingConsultation = ref(false)
const consultationError = ref('')
const consultationSuccess = ref('')
const consultationNewRecord = ref(null)
const consultationRecordId = ref(null)
const consultationHistory = ref([])

export function useConsultation() {
  const router = useRouter()
  const { inventory } = useInventory()

  const consultationDrugCatalogue = computed(() =>
    inventory.value.map(normalizeConsultationDrug),
  )

  const consultationFilteredDrugs = computed(() => {
    const search = String(consultationDrugSearch.value || '').trim().toLowerCase()
    if (!search) return consultationDrugCatalogue.value

    return consultationDrugCatalogue.value.filter((drug) => {
      const normalizedName = String(drug.name || '').toLowerCase()
      const nameTokens = normalizedName.split(/\s+/).filter(Boolean)
      const idPrefixMatch = String(drug.id).toLowerCase().startsWith(search)
      const namePrefixMatch =
        normalizedName.startsWith(search) ||
        nameTokens.some((token) => token.startsWith(search))
      return namePrefixMatch || idPrefixMatch
    })
  })

  const consultationSelectedDrugs = computed(() =>
    consultationDrugCatalogue.value
      .map((drug) => ({
        ...drug,
        selectedQuantity: Math.max(0, Number(consultationDrugSelections.value[drug.id] ?? 0)),
      }))
      .filter((drug) => drug.selectedQuantity > 0),
  )

  const consultationSelectedDrugCount = computed(() =>
    consultationSelectedDrugs.value.reduce((total, drug) => total + drug.selectedQuantity, 0),
  )

  const consultationSelectedDrugTotal = computed(() =>
    consultationSelectedDrugs.value.reduce(
      (total, drug) => total + drug.selectedQuantity * Number(drug.price || 0),
      0,
    ),
  )

  const syncConsultationDrugSelections = () => {
    const nextSelections = {}
    for (const drug of consultationDrugCatalogue.value) {
      const currentQuantity = Number(consultationDrugSelections.value[drug.id] ?? 0)
      nextSelections[drug.id] = Math.max(
        0,
        Math.min(Number.isFinite(currentQuantity) ? currentQuantity : 0, drug.quantity),
      )
    }
    consultationDrugSelections.value = nextSelections
  }

  const getConsultationDrugQuantity = (drugId) =>
    Number(consultationDrugSelections.value[drugId] ?? 0)

  const setConsultationDrugQuantity = (drugId, rawValue) => {
    const drug = consultationDrugCatalogue.value.find((item) => item.id === Number(drugId))
    if (!drug) return
    const parsedQuantity = Number.parseInt(String(rawValue ?? ''), 10)
    const nextQuantity = Number.isFinite(parsedQuantity) ? parsedQuantity : 0
    consultationDrugSelections.value = {
      ...consultationDrugSelections.value,
      [drug.id]: Math.max(0, Math.min(nextQuantity, drug.quantity)),
    }
  }

  const composeConsultationVisitNotes = (visitNotes, drugs) => {
    const trimmedNotes = String(visitNotes || '').trim()
    if (!drugs.length) return trimmedNotes
    const drugSummary = drugs
      .map((drug) => `- ${drug.name} x${drug.selectedQuantity} (available ${drug.quantity})`)
      .join('\n')
    return [trimmedNotes, 'Prescribed Drugs:', drugSummary].filter(Boolean).join('\n\n')
  }

  const buildConsultationDraft = () => {
    const patientId = String(consultationForm.value.patientId || '').trim()
    const visitNotes = String(consultationForm.value.visitNotes || '').trim()
    const drugs = consultationSelectedDrugs.value.map((drug) => ({
      drugId: drug.id,
      name: drug.name,
      quantity: drug.selectedQuantity,
      availableQuantity: drug.quantity,
      price: drug.price,
    }))
    return {
      patientId,
      visitNotes,
      drugs,
      selectedDrugCount: consultationSelectedDrugCount.value,
      selectedDrugTotal: consultationSelectedDrugTotal.value,
      composedVisitNotes: composeConsultationVisitNotes(visitNotes, drugs),
    }
  }

  const resetConsultationState = () => {
    consultationForm.value = { patientId: '', visitNotes: '' }
    consultationDrugSearch.value = ''
    consultationDrugSelections.value = {}
    consultationError.value = ''
    consultationSuccess.value = ''
    consultationNewRecord.value = null
    consultationRecordId.value = null
    consultationHistory.value = []
  }

  const submitConsultation = async () => {
    consultationError.value = ''
    consultationSuccess.value = ''
    consultationNewRecord.value = null
    consultationRecordId.value = null
    consultationHistory.value = []

    const patientId = String(consultationForm.value.patientId || '').trim()
    const visitNotes = String(consultationForm.value.visitNotes || '').trim()
    if (!patientId || !visitNotes) {
      consultationError.value = 'patientId and visitNotes are required.'
      return
    }

    submittingConsultation.value = true
    try {
      await verifyPatientExistsApi(patientId)
    } catch (error) {
      if (error?.response?.status === 404) {
        consultationError.value = `Patient "${patientId}" does not exist. Please register the patient first.`
      } else {
        consultationError.value = 'Unable to verify patient. Patient service may be down.'
      }
      submittingConsultation.value = false
      return
    }

    const draft = buildConsultationDraft()
    try {
      sessionStorage.setItem(CONSULTATION_DRAFT_KEY, JSON.stringify(draft))
      await router.push({ name: 'consultation-review' })
    } catch (error) {
      consultationError.value = error?.message || 'Unable to open the consultation review page.'
    } finally {
      submittingConsultation.value = false
    }
  }

  return {
    consultationForm,
    consultationDrugSearch,
    consultationDrugSelections,
    submittingConsultation,
    consultationError,
    consultationSuccess,
    consultationNewRecord,
    consultationRecordId,
    consultationHistory,
    consultationDrugCatalogue,
    consultationFilteredDrugs,
    consultationSelectedDrugs,
    consultationSelectedDrugCount,
    consultationSelectedDrugTotal,
    syncConsultationDrugSelections,
    getConsultationDrugQuantity,
    setConsultationDrugQuantity,
    buildConsultationDraft,
    resetConsultationState,
    submitConsultation,
  }
}
