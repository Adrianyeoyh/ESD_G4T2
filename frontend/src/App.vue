<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import axios from 'axios'
import { loadStripe } from '@stripe/stripe-js'
import { useRoute, useRouter } from 'vue-router'
import {
  AlertCircle,
  ArrowUpDown,
  ChevronDown,
  ChevronUp,
  CircleCheckBig,
  CreditCard,
  FileText,
  LoaderCircle,
  Pill,
  Plus,
  SquarePen,
  Trash2,
  UserPlus,
  Wallet,
  X,
} from 'lucide-vue-next'
import ConsultationReview from './views/ConsultationReview.vue'

const ENDPOINTS = {
  drugsPrimary: 'http://localhost:5081/drug',
  drugsAlt: 'http://localhost:5081/drug/',
  billing: 'http://localhost:5005/make_payment/initiate-payment',
  billingHealth: 'http://localhost:5005/health',
  records: 'https://personal-iipxahjd.outsystemscloud.com/ClinicalRecordServices/rest/RecordsAPI/',
  recordsByPatient:
    'https://personal-iipxahjd.outsystemscloud.com/ClinicalRecordServices/rest/RecordsAPI/record/',
  prescriptionByPatientBase:
    import.meta.env.VITE_PRESCRIPTION_BY_PATIENT_BASE || 'http://localhost:5006',
  consultationBase:
    import.meta.env.VITE_CONSULTATION_BASE ||
    'https://personal-wv4mxqur.outsystemscloud.com/RecordVisitNotes/rest/ConsultationAPI',
  patientRegistration:
    'https://personal-wv4mxqur.outsystemscloud.com/PatientService/rest/PatientAPI/patient',
}

const STRIPE_PUBLISHABLE_KEY =
  'pk_test_51TEPPgIzFKBN2ZMzfqH1p0EdpZa9vVTC4swDFcrucVz92XxrODFkQkHc26zgHg4kzEcECKKklUCcef94CRK1NjOB00pHJb9cDX'

const route = useRoute()
const router = useRouter()
const CONSULTATION_DRAFT_KEY = 'consultation:pending-draft'

const activeView = ref('inventory')
const isConsultationReviewPage = computed(() => route.name === 'consultation-review')

const inventory = ref([])
const records = ref([])
const loadingInventory = ref(false)
const loadingRecords = ref(false)
const inventoryError = ref('')
const recordsError = ref('')

// Inventory search & filter
const inventorySearch = ref('')
const inventoryNotice = ref('')

// Inventory sorting state
const inventorySortKey = ref('name') // 'name' | 'stock' | 'price'
const inventorySortOrder = ref('asc') // 'asc' | 'desc'

// Inventory CRUD state
const deletingDrugId = ref(null)
const deletingDrugError = ref('')
const expandedDrugIds = ref([])

// Add drug modal state
const addDrugModalOpen = ref(false)
const addingDrug = ref(false)
const addDrugError = ref('')
const addDrugForm = ref({
  drugName: '',
  quantity: 0,
  price: 0,
  purpose: '',
  dosage: '',
  remarks: '',
})

// Edit drug modal state
const editDrugModalOpen = ref(false)
const editingDrug = ref(false)
const editDrugError = ref('')
const editDrugForm = ref({
  drugId: null,
  drugName: '',
  quantity: 0,
  price: 0,
  purpose: '',
  dosage: '',
  remarks: '',
})

// Toast notifications
const toasts = ref([])
let toastCounter = 0

const dismissToast = (toastId) => {
  toasts.value = toasts.value.filter((item) => item.id !== toastId)
}

const showToast = (message, type = 'success') => {
  const id = toastCounter++
  toasts.value = [...toasts.value, { id, message, type }]
  window.setTimeout(() => {
    dismissToast(id)
  }, 3000)
}

// Helper functions for drug data
const getDrugId = (drug) => Number(drug?.drugId ?? drug?.drug_id ?? drug?.id ?? 0)

const normalizeDrug = (drug) => {
  const normalizedId = getDrugId(drug)
  const normalizedQuantity = Number(drug?.quantity ?? drug?.stock ?? 0)
  const normalizedPrice = Number(drug?.price ?? 0)
  const normalizedDosage = String(
    drug?.dosage ?? drug?.recommendedDosage ?? drug?.recommended_dosage ?? '',
  ).trim()
  return {
    ...drug,
    id: normalizedId,
    drugId: normalizedId,
    name: drug?.name ?? drug?.drugName ?? drug?.drug_name ?? '',
    drugName: drug?.name ?? drug?.drugName ?? drug?.drug_name ?? '',
    quantity: Number.isFinite(normalizedQuantity) ? normalizedQuantity : 0,
    price: Number.isFinite(normalizedPrice) ? normalizedPrice : 0,
    purpose: String(drug?.purpose ?? '').trim(),
    dosage: normalizedDosage,
    recommendedDosage: normalizedDosage,
    remarks: String(drug?.remarks ?? '').trim(),
  }
}

// Filtered inventory (search)
const filteredInventory = computed(() => {
  const query = String(inventorySearch.value || '').trim().toLowerCase()
  if (!query) {
    return inventory.value
  }
  return inventory.value.filter((drug) =>
    String(drug.name ?? drug.drugName ?? '').toLowerCase().includes(query) ||
    String(drug.purpose ?? '').toLowerCase().includes(query),
  )
})

// Sorted inventory (applies sorting to filtered results)
const sortedInventory = computed(() => {
  const sorted = [...filteredInventory.value]
  const key = inventorySortKey.value
  const order = inventorySortOrder.value

  sorted.sort((a, b) => {
    let aVal, bVal
    if (key === 'name') {
      aVal = String(a.name ?? a.drug_name ?? '').toLowerCase()
      bVal = String(b.name ?? b.drug_name ?? '').toLowerCase()
      return order === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
    } else if (key === 'stock') {
      aVal = Number(a.quantity ?? a.stock ?? 0)
      bVal = Number(b.quantity ?? b.stock ?? 0)
    } else if (key === 'price') {
      aVal = Number(a.price ?? 0)
      bVal = Number(b.price ?? 0)
    }
    return order === 'asc' ? aVal - bVal : bVal - aVal
  })

  return sorted
})

const toggleInventorySort = (key) => {
  if (inventorySortKey.value === key) {
    inventorySortOrder.value = inventorySortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    inventorySortKey.value = key
    inventorySortOrder.value = 'asc'
  }
}

const patientHistoryForm = ref({
  patientId: '',
})
const loadingPatientHistory = ref(false)
const patientHistoryError = ref('')
const patientHistoryPrescriptionError = ref('')
const patientHistoryRecords = ref([])
const patientHistoryPrescriptions = ref([])

const patientModalOpen = ref(false)
const submittingPatient = ref(false)
const patientFormError = ref('')
const patientFormSuccess = ref('')
const patientForm = ref({
  nric: '',
  name: '',
  phoneNo: '',
  email: '',
})

const paymentStep = ref(1)
const selectedInvoice = ref(null)
const paymentIntentId = ref('')
const clientSecret = ref('')
const paymentError = ref('')
const paymentVerifiedMessage = ref('')

const stripe = ref(null)
const elements = ref(null)
const cardElement = ref(null)
const stripeReady = ref(false)
const confirmingPayment = ref(false)
const stripeError = ref('')

const paymentConsoleLogs = ref([])

const outsystemsSyncCounter = ref(0)
const outsystemsSyncing = computed(() => outsystemsSyncCounter.value > 0)

const consultationForm = ref({
  patientId: '',
  visitNotes: '',
})
const consultationDrugSearch = ref('')
const consultationDrugSelections = ref({})
const submittingConsultation = ref(false)
const consultationError = ref('')
const consultationSuccess = ref('')
const consultationNewRecord = ref(null)
const consultationRecordId = ref(null)
const consultationHistory = ref([])

const normalizeConsultationDrug = (drug, idx) => ({
  id: Number(drug.drugId ?? drug.id ?? drug.Id ?? idx + 1),
  name:
    String(
      drug.drugName ?? drug.name ?? drug.DrugName ?? drug.drug_name ?? 'Unnamed Drug',
    ).trim() || 'Unnamed Drug',
  quantity: Math.max(0, Number(drug.quantity ?? drug.stock ?? drug.Quantity ?? 0)),
  price: Number(drug.price ?? drug.Price ?? 0),
  raw: drug,
})

const consultationDrugCatalogue = computed(() => inventory.value.map(normalizeConsultationDrug))

const consultationFilteredDrugs = computed(() => {
  const search = String(consultationDrugSearch.value || '').trim().toLowerCase()
  if (!search) {
    return consultationDrugCatalogue.value
  }

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

const getConsultationDrugQuantity = (drugId) => Number(consultationDrugSelections.value[drugId] ?? 0)

const setConsultationDrugQuantity = (drugId, rawValue) => {
  const drug = consultationDrugCatalogue.value.find((item) => item.id === Number(drugId))
  if (!drug) {
    return
  }

  const parsedQuantity = Number.parseInt(String(rawValue ?? ''), 10)
  const nextQuantity = Number.isFinite(parsedQuantity) ? parsedQuantity : 0

  consultationDrugSelections.value = {
    ...consultationDrugSelections.value,
    [drug.id]: Math.max(0, Math.min(nextQuantity, drug.quantity)),
  }
}

const composeConsultationVisitNotes = (visitNotes, drugs) => {
  const trimmedNotes = String(visitNotes || '').trim()
  if (!drugs.length) {
    return trimmedNotes
  }

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

const dispensingRecordId = ref(null)
const dispenseError = ref('')
const dispenseSuccess = ref('')

const billingRows = ref([])
const loadingBilling = ref(false)
const billingError = ref('')
const markingPaidId = ref(null)
const billingSuccess = ref('')

const navItems = [
  { key: 'inventory', label: 'Inventory', icon: Pill },
  { key: 'records', label: 'Records', icon: FileText },
  { key: 'history', label: 'Patient History', icon: FileText },
  { key: 'payments', label: 'Payments', icon: CreditCard },
]

const pendingInvoices = computed(() =>
  records.value
    .map((record, index) => ({
      invoiceId: String(
        record.invoiceId ??
          record.InvoiceId ??
          record.invoice_id ??
          record.id ??
          index + 1,
      ).trim(),
      patientName: (
        record.patientName ??
        record.PatientName ??
        record.name ??
        'Unknown patient'
      ).trim(),
      amount: Number(record.amount ?? record.total_amount ?? record.TotalAmount ?? 0),
      currency: String(record.currency ?? record.Currency ?? 'SGD').trim(),
      status: String(record.status ?? record.Status ?? 'PENDING').toUpperCase().trim(),
      diagnosis: String(record.diagnosis ?? record.Diagnosis ?? 'N/A').trim(),
    }))
    .filter((item) => item.status !== 'PAID'),
)

const normalizedRecords = computed(() =>
  records.value.map((record, idx) => {
    const id = record.Id ?? record.id ?? idx + 1
    const patientId = record.patientId ?? record.PatientId ?? null
    const visitNotes = record.VisitNotes ?? record.visitNotes ?? record.notes ?? ''
    const date = record.date ?? record.Date ?? record.visitDate ?? record.VisitDate ?? ''
    const isClosed = Boolean(record.isClosed ?? record.IsClosed ?? false)
    const statusRaw = String(record.status ?? record.Status ?? '').toUpperCase().trim()

    return {
      ...record,
      Id: Number(id),
      patientId: patientId !== null ? String(patientId).trim() : null,
      date,
      VisitNotes: String(visitNotes),
      isClosed,
      patientName:
        record.patientName ??
        record.PatientName ??
        record.name ??
        'Unknown patient',
      nric: record.nric ?? record.NRIC ?? record.Nric ?? 'N/A',
      email: record.email ?? record.Email ?? '',
      status: statusRaw || (isClosed ? 'CLOSED' : 'OPEN'),
    }
  }),
)

const normalizeArrayResponse = (payload) => {
  if (Array.isArray(payload)) {
    return payload
  }

  for (const key of ['data', 'items', 'records', 'Records', 'result']) {
    if (Array.isArray(payload?.[key])) {
      return payload[key]
    }
  }

  return []
}

const normalizeObjectArrayResponse = (payload) => {
  if (Array.isArray(payload)) {
    return payload
  }

  for (const key of ['data', 'items', 'records', 'result', 'value']) {
    if (Array.isArray(payload?.[key])) {
      return payload[key]
    }
  }

  return []
}

const parseErrorMessage = (error, fallbackMessage) => {
  if (String(error?.message || '').toLowerCase() === 'network error') {
    return `${fallbackMessage} Service may be down or blocked by CORS.`
  }

  const data = error?.response?.data
  if (typeof data === 'string' && data.trim()) {
    return data.trim()
  }

  for (const key of ['message', 'error', 'details']) {
    const candidate = data?.[key]
    if (typeof candidate === 'string' && candidate.trim()) {
      return candidate.trim()
    }
  }

  return error?.message || fallbackMessage
}

const normalizePrescriptionRows = (rows) =>
  rows.map((row, idx) => ({
    id: row.id ?? row.Id ?? row.prescriptionId ?? row.PrescriptionId ?? idx + 1,
    drugName:
      row.drugName ?? row.DrugName ?? row.medicationName ?? row.MedicationName ?? 'N/A',
    quantity: row.quantity ?? row.Quantity ?? row.qty ?? row.Qty ?? 'N/A',
    dosage: row.dosage ?? row.Dosage ?? row.instructions ?? row.Instructions ?? 'N/A',
    date: row.date ?? row.Date ?? row.createdAt ?? row.CreatedAt ?? 'N/A',
    raw: row,
  }))

const fetchPrescriptionsByPatientId = async (patientId) => {
  const base = ENDPOINTS.prescriptionByPatientBase.replace(/\/$/, '')
  const candidates = [
    `${base}/prescription/patient/${patientId}`,
    `${base}/prescriptions/patient/${patientId}`,
    `${base}/prescription/${patientId}`,
  ]

  let lastError = null
  for (const url of candidates) {
    try {
      const response = await axios.get(url)
      return normalizeObjectArrayResponse(response.data)
    } catch (error) {
      lastError = error
    }
  }

  throw lastError || new Error('Unable to retrieve prescriptions for this patient.')
}

const fetchPatientHistory = async () => {
  patientHistoryError.value = ''
  patientHistoryPrescriptionError.value = ''
  patientHistoryRecords.value = []
  patientHistoryPrescriptions.value = []

  const patientId = String(patientHistoryForm.value.patientId || '').trim()
  if (!patientId || patientId.length !== 9) {
    patientHistoryError.value = 'Please enter a valid 9-character patientId.'
    return
  }

  loadingPatientHistory.value = true
  beginOutsystemsSync()

  try {
    const [recordsResult, prescriptionResult] = await Promise.allSettled([
      axios.get(`${ENDPOINTS.recordsByPatient}${encodeURIComponent(String(patientId))}`),
      fetchPrescriptionsByPatientId(patientId),
    ])

    if (recordsResult.status === 'fulfilled') {
      patientHistoryRecords.value = normalizeObjectArrayResponse(recordsResult.value.data)
    } else {
      patientHistoryError.value = parseErrorMessage(
        recordsResult.reason,
        'Unable to fetch clinical records for this patient.',
      )
    }

    if (prescriptionResult.status === 'fulfilled') {
      patientHistoryPrescriptions.value = normalizePrescriptionRows(prescriptionResult.value)
    } else {
      patientHistoryPrescriptionError.value = parseErrorMessage(
        prescriptionResult.reason,
        'Unable to fetch prescriptions for this patient.',
      )
    }
  } finally {
    loadingPatientHistory.value = false
    endOutsystemsSync()
  }
}

const beginOutsystemsSync = () => {
  outsystemsSyncCounter.value += 1
}

const endOutsystemsSync = () => {
  outsystemsSyncCounter.value = Math.max(0, outsystemsSyncCounter.value - 1)
}

const fetchDrugs = async () => {
  loadingInventory.value = true
  inventoryError.value = ''
  inventoryNotice.value = ''

  try {
    let response
    try {
      response = await axios.get(ENDPOINTS.drugsPrimary)
    } catch (firstError) {
      response = await axios.get(ENDPOINTS.drugsAlt)
    }

    const rows = normalizeArrayResponse(response.data).map(normalizeDrug)
    inventory.value = rows
    syncConsultationDrugSelections()

    if (!rows.length) {
      inventoryNotice.value = 'Connected to localhost drug service. Inventory is currently empty.'
    }
  } catch (error) {
    console.error('Drug API Error:', error?.response)
    inventoryError.value =
      error?.response?.data?.message ||
      'Unable to load Drug Service on port 5081. Check route/CORS/service health.'
  } finally {
    loadingInventory.value = false
  }
}

// Add Drug Modal Functions
const openAddDrugModal = () => {
  addDrugError.value = ''
  addDrugForm.value = {
    drugName: '',
    quantity: 0,
    price: 0,
    purpose: '',
    dosage: '',
    remarks: '',
  }
  addDrugModalOpen.value = true
}

const closeAddDrugModal = () => {
  addDrugModalOpen.value = false
}

const updateAddDrugField = (key, value) => {
  addDrugForm.value = { ...addDrugForm.value, [key]: value }
}

const submitAddDrug = async () => {
  addDrugError.value = ''
  const drugData = {
    drugName: String(addDrugForm.value.drugName || '').trim(),
    quantity: Number(addDrugForm.value.quantity),
    price: Number(addDrugForm.value.price),
    purpose: String(addDrugForm.value.purpose || '').trim() || null,
    dosage: String(addDrugForm.value.dosage || '').trim() || null,
    remarks: String(addDrugForm.value.remarks || '').trim() || null,
  }

  if (!drugData.drugName) {
    addDrugError.value = 'Drug Name is required.'
    return
  }
  if (!Number.isFinite(drugData.quantity) || drugData.quantity < 0) {
    addDrugError.value = 'Stock Quantity must be 0 or greater.'
    return
  }
  if (!Number.isFinite(drugData.price) || drugData.price <= 0) {
    addDrugError.value = 'Unit Price must be greater than 0.'
    return
  }

  addingDrug.value = true
  try {
    await axios.post(ENDPOINTS.drugsPrimary, {
      ...drugData,
      recommendedDosage: drugData.dosage,
    })
    await fetchDrugs()
    closeAddDrugModal()
    showToast(`Drug ${drugData.drugName} added successfully!`, 'success')
  } catch (error) {
    addDrugError.value =
      error?.response?.data?.error ||
      error?.response?.data?.message ||
      'Unable to add drug.'
    showToast(addDrugError.value, 'error')
  } finally {
    addingDrug.value = false
  }
}

// Edit Drug Modal Functions
const openEditDrugModal = (drug) => {
  editDrugError.value = ''
  editDrugForm.value = {
    drugId: getDrugId(drug),
    drugName: drug.name ?? drug.drugName ?? drug.drug_name ?? '',
    quantity: Number(drug.quantity ?? drug.stock ?? 0),
    price: Number(drug.price ?? 0),
    purpose: String(drug.purpose || ''),
    dosage: String(drug.dosage || drug.recommendedDosage || ''),
    remarks: String(drug.remarks || ''),
  }
  editDrugModalOpen.value = true
}

const closeEditDrugModal = () => {
  editDrugModalOpen.value = false
}

const updateEditDrugField = (key, value) => {
  editDrugForm.value = { ...editDrugForm.value, [key]: value }
}

const submitEditDrug = async () => {
  editDrugError.value = ''
  const drugId = Number(editDrugForm.value.drugId)
  const quantity = Number(editDrugForm.value.quantity)
  const price = Number(editDrugForm.value.price)
  const purpose = String(editDrugForm.value.purpose || '').trim() || null
  const dosage = String(editDrugForm.value.dosage || '').trim() || null
  const remarks = String(editDrugForm.value.remarks || '').trim() || null

  if (!Number.isFinite(drugId) || drugId <= 0) {
    editDrugError.value = 'Invalid drug selected.'
    return
  }
  if (!Number.isFinite(quantity) || quantity < 0) {
    editDrugError.value = 'Stock Quantity must be 0 or greater.'
    return
  }
  if (!Number.isFinite(price) || price <= 0) {
    editDrugError.value = 'Unit Price must be greater than 0.'
    return
  }

  editingDrug.value = true
  try {
    await axios.put(`${ENDPOINTS.drugsPrimary}/${drugId}`, {
      quantity,
      price,
      purpose,
      dosage,
      remarks,
      recommendedDosage: dosage,
    })
    await fetchDrugs()
    closeEditDrugModal()
    showToast('Inventory updated successfully!', 'success')
  } catch (error) {
    editDrugError.value =
      error?.response?.data?.error ||
      error?.response?.data?.message ||
      'Unable to update drug.'
    showToast(editDrugError.value, 'error')
  } finally {
    editingDrug.value = false
  }
}

// Delete Drug Function
const deleteDrug = async (drug) => {
  const drugId = getDrugId(drug)
  const drugName = drug?.name ?? drug?.drugName ?? 'this drug'
  deletingDrugError.value = ''

  if (!window.confirm(`Delete ${drugName} from inventory?`)) {
    return
  }

  deletingDrugId.value = drugId
  try {
    await axios.delete(`${ENDPOINTS.drugsPrimary}/${drugId}`)
    expandedDrugIds.value = expandedDrugIds.value.filter((id) => id !== drugId)
    await fetchDrugs()
    showToast('Drug removed from inventory.', 'success')
  } catch (error) {
    deletingDrugError.value =
      error?.response?.data?.error ||
      error?.response?.data?.message ||
      'Unable to delete drug.'
    showToast(deletingDrugError.value, 'error')
  } finally {
    deletingDrugId.value = null
  }
}

// Expandable Drug Details
const toggleDrugDetails = (drugId) => {
  const normalizedId = Number(drugId)
  if (!Number.isFinite(normalizedId) || normalizedId <= 0) {
    return
  }
  if (expandedDrugIds.value.includes(normalizedId)) {
    expandedDrugIds.value = expandedDrugIds.value.filter((id) => id !== normalizedId)
    return
  }
  expandedDrugIds.value = [...expandedDrugIds.value, normalizedId]
}

const isDrugExpanded = (drugId) => expandedDrugIds.value.includes(Number(drugId))

const fetchRecords = async () => {
  loadingRecords.value = true
  recordsError.value = ''
  beginOutsystemsSync()

  try {
    const response = await axios.get(ENDPOINTS.records)
    records.value = normalizeArrayResponse(response.data)
  } catch (error) {
    recordsError.value =
      error?.response?.data?.message ||
      'Unable to load Clinical Records from OutSystems.'
    records.value = []
  } finally {
    loadingRecords.value = false
    endOutsystemsSync()
  }
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

  const draft = buildConsultationDraft()

  submittingConsultation.value = true
  try {
    sessionStorage.setItem(CONSULTATION_DRAFT_KEY, JSON.stringify(draft))
    await router.push({ name: 'consultation-review' })
  } catch (error) {
    consultationError.value =
      error?.message || 'Unable to open the consultation review page.'
  } finally {
    submittingConsultation.value = false
  }
}

const dispenseRecord = async (record) => {
  dispenseError.value = ''
  dispenseSuccess.value = ''
  if (record?.isClosed) {
    dispenseError.value = `Record ${record.Id} is already closed.`
    return
  }

  dispensingRecordId.value = record.Id
  beginOutsystemsSync()

  const payload = {
    Id: Number(record.Id),
    patientId: String(record.patientId || '').trim(),
    date: String(record.date || '').slice(0, 10),
    VisitNotes: String(record.VisitNotes || ''),
    isClosed: true,
  }

  try {
    const response = await fetch(`${ENDPOINTS.records}Record`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(errorText || `Dispense action failed (${response.status})`)
    }

    // OutSystems POST /Record returns raw integer.
    const updatedRecordId = Number.parseInt((await response.text()).trim(), 10)
    if (Number.isNaN(updatedRecordId)) {
      throw new Error('Record close response is not a numeric record ID.')
    }

    records.value = records.value.map((item) => {
      const currentId = Number(item.Id ?? item.id)
      if (currentId !== updatedRecordId) {
        return item
      }
      return {
        ...item,
        isClosed: true,
        status: 'CLOSED',
      }
    })

    // Reflect stock update logic-wise by decrementing one in-stock item.
    const stockIdx = inventory.value.findIndex((item) => Number(item.quantity ?? item.stock ?? 0) > 0)
    if (stockIdx >= 0) {
      const stockItem = inventory.value[stockIdx]
      const currentQty = Number(stockItem.quantity ?? stockItem.stock ?? 0)
      const nextQty = Math.max(0, currentQty - 1)
      inventory.value[stockIdx] = {
        ...stockItem,
        quantity: nextQty,
        stock: nextQty,
      }
    }

    dispenseSuccess.value = `Record ${updatedRecordId} dispensed and closed.`
    await loadBillingRows()
  } catch (error) {
    dispenseError.value = error?.message || 'Unable to dispense this record.'
  } finally {
    dispensingRecordId.value = null
    endOutsystemsSync()
  }
}

const loadBillingRows = async () => {
  loadingBilling.value = true
  billingError.value = ''
  billingSuccess.value = ''

  try {
    const base = ENDPOINTS.consultationBase.replace(/\/$/, '')
    let response = await fetch(`${base}/billing/closed-records`)
    if (!response.ok) {
      response = await fetch(`${base}/billing`)
    }
    if (!response.ok) {
      throw new Error('Fallback to local closed records')
    }
    // Billing GET calls return JSON.
    const payload = await response.json()
    const rows = Array.isArray(payload)
      ? payload
      : Array.isArray(payload?.data)
        ? payload.data
        : []
    billingRows.value = rows.map((row, idx) => ({
      Id: Number(row.Id ?? row.id ?? idx + 1),
      patientName: row.patientName ?? row.name ?? 'Unknown patient',
      nric: row.nric ?? 'N/A',
      VisitNotes: row.VisitNotes ?? row.visitNotes ?? '',
      email: row.email ?? '',
      isPaid: Boolean(row.isPaid ?? row.paid ?? false),
    }))
  } catch {
    // Fallback: derive billing-ready rows from closed records.
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
  } finally {
    loadingBilling.value = false
  }
}

const markAsPaid = async (row) => {
  billingError.value = ''
  billingSuccess.value = ''
  markingPaidId.value = row.Id
  beginOutsystemsSync()

  try {
    const base = ENDPOINTS.consultationBase.replace(/\/$/, '')
    const body = JSON.stringify({
      Id: Number(row.Id),
      email: row.email || null,
    })
    const headers = {
      'Content-Type': 'application/json',
    }

    // Preferred: explicit receipt-generation endpoint (ExecuteNonQuery in OutSystems action).
    let response = await fetch(
      `${base}/billing/generate-receipt/${encodeURIComponent(String(row.Id))}`,
      { method: 'POST', headers, body },
    )
    // Backward-compatible fallback to previously used endpoint.
    if (!response.ok) {
      response = await fetch(
        `${base}/billing/mark-paid/${encodeURIComponent(String(row.Id))}`,
        { method: 'POST', headers, body },
      )
    }

    if (!response.ok) {
      throw new Error(`Generate Receipt failed (${response.status})`)
    }

    billingRows.value = billingRows.value.map((item) =>
      item.Id === row.Id ? { ...item, isPaid: true } : item,
    )
    records.value = records.value.map((item) => {
      const itemId = Number(item.Id ?? item.id)
      if (itemId !== Number(row.Id)) {
        return item
      }
      return {
        ...item,
        status: 'PAID',
      }
    })
    billingSuccess.value = `Receipt generated and record ${row.Id} marked as paid.`
  } catch (error) {
    billingError.value = error?.message || 'Unable to generate receipt.'
  } finally {
    markingPaidId.value = null
    endOutsystemsSync()
  }
}

const openPatientModal = () => {
  patientFormError.value = ''
  patientFormSuccess.value = ''
  patientModalOpen.value = true
}

const closePatientModal = () => {
  patientModalOpen.value = false
}

const submitPatient = async () => {
  submittingPatient.value = true
  patientFormError.value = ''
  patientFormSuccess.value = ''
  beginOutsystemsSync()

  const payload = {
    nric: String(patientForm.value.nric ?? '').trim(),
    name: String(patientForm.value.name ?? '').trim(),
    phoneNo: Number(patientForm.value.phoneNo),
    email: String(patientForm.value.email ?? '').trim(),
  }

  try {
    const response = await fetch(ENDPOINTS.patientRegistration, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(errorText || `Patient registration failed (${response.status})`)
    }

    // OutSystems POST /patient returns a raw integer id in text form.
    const createdPatientId = Number.parseInt((await response.text()).trim(), 10)
    if (Number.isNaN(createdPatientId)) {
      throw new Error('OutSystems Patient API did not return a numeric patient ID.')
    }

    patientFormSuccess.value = `Patient registered successfully via OutSystems (ID: ${createdPatientId}).`
  } catch (error) {
    if (String(error?.message || '').includes('500')) {
      patientFormError.value =
        'Registration failed (500). Please verify NRIC uniqueness and backend validation rules.'
    } else {
      patientFormError.value = error?.message || 'Unable to register patient right now.'
    }
  } finally {
    submittingPatient.value = false
    endOutsystemsSync()
  }
}

const initializeStripe = async () => {
  stripeError.value = ''
  stripe.value = await loadStripe(STRIPE_PUBLISHABLE_KEY)
  stripeReady.value = Boolean(stripe.value)

  if (!stripeReady.value) {
    stripeError.value = 'Unable to initialize Stripe Elements with the provided publishable key.'
  }
}

const unmountCardElement = () => {
  if (cardElement.value) {
    cardElement.value.unmount()
  }
  cardElement.value = null
  elements.value = null
}

const mountCardElement = async () => {
  if (!stripe.value || cardElement.value) {
    return
  }

  const cardMountNode = document.getElementById('card-element')
  if (!cardMountNode) {
    return
  }

  elements.value = stripe.value.elements()
  cardElement.value = elements.value.create('card', {
    style: {
      base: {
        fontFamily: 'Inter, Segoe UI, sans-serif',
        fontSize: '16px',
        color: '#202124',
        '::placeholder': { color: '#9aa0a6' },
      },
    },
  })

  cardElement.value.mount('#card-element')
}

const selectInvoice = async (invoice) => {
  selectedInvoice.value = invoice
  paymentError.value = ''
  stripeError.value = ''
  paymentVerifiedMessage.value = ''
  paymentStep.value = 2
  await nextTick()
  await mountCardElement()
}

const createPaymentIntent = async () => {
  if (!selectedInvoice.value) {
    throw new Error('Please select an invoice first.')
  }

  const invoiceId = Number(String(selectedInvoice.value.invoiceId).trim())
  if (!Number.isFinite(invoiceId)) {
    throw new Error(`Invalid invoiceId from OutSystems record: ${selectedInvoice.value.invoiceId}`)
  }

  console.log('Sending request to:', ENDPOINTS.billing)
  const response = await axios.post(ENDPOINTS.billing, {
    invoiceId,
  })
  const payload = response.data?.data || response.data || {}

  const resolvedClientSecret = payload?.clientSecret || payload?.client_secret || ''
  const resolvedPaymentIntentId =
    payload?.paymentIntentId || payload?.payment_intent_id || ''

  if (!resolvedClientSecret) {
    throw new Error('Billing did not return client_secret. Verify /make_payment response.')
  }

  clientSecret.value = resolvedClientSecret
  paymentIntentId.value = resolvedPaymentIntentId
}

const handleConfirmAndPay = async () => {
  paymentError.value = ''
  stripeError.value = ''
  paymentVerifiedMessage.value = ''
  confirmingPayment.value = true

  try {
    await createPaymentIntent()

    if (!stripe.value || !cardElement.value) {
      stripeError.value = 'Stripe card component is not ready. Please retry.'
      return
    }

    const { error, paymentIntent } = await stripe.value.confirmCardPayment(clientSecret.value, {
      payment_method: {
        card: cardElement.value,
      },
    })

    if (error) {
      stripeError.value = error.message || 'Stripe confirmation failed.'
      return
    }

    if (paymentIntent?.status === 'succeeded') {
      paymentVerifiedMessage.value = '✅ Payment Verified in Stripe Sandbox'
      console.log('Stripe paymentIntent.id:', paymentIntent.id)
      paymentConsoleLogs.value.unshift(
        `${new Date().toLocaleTimeString()} | paymentIntent.id=${paymentIntent.id} | status=${paymentIntent.status}`,
      )
      window.location.assign(
        `/payment-success?invoiceId=${encodeURIComponent(String(selectedInvoice.value?.invoiceId || ''))}&paymentIntentId=${encodeURIComponent(String(paymentIntent.id || paymentIntentId.value || ''))}`,
      )
      return
    }

    stripeError.value = `Stripe returned status: ${paymentIntent?.status || 'unknown'}`
  } catch (error) {
    if (error?.response?.status === 503) {
      alert('Backend Orchestrator is offline, but Stripe Library is successfully initialized.')
    }

    console.error('FastAPI validation detail:', error?.response?.data)
    paymentError.value =
      error?.response?.data?.message ||
      error?.message ||
      'Stop 1 failed: Could not initialize payment with localhost:5005/make_payment/initiate-payment.'
  } finally {
    confirmingPayment.value = false
  }
}

const resetPaymentFlow = () => {
  paymentStep.value = 1
  selectedInvoice.value = null
  paymentIntentId.value = ''
  clientSecret.value = ''
  paymentError.value = ''
  stripeError.value = ''
  paymentVerifiedMessage.value = ''
  unmountCardElement()
}

const refreshAll = async () => {
  await Promise.all([fetchDrugs(), fetchRecords()])
  await loadBillingRows()
}

onMounted(async () => {
  const query = new URLSearchParams(window.location.search)
  if (window.location.pathname === '/success') {
    window.history.replaceState({}, '', `/payment-success${window.location.search}`)
  }

  if (window.location.pathname === '/payment-success') {
    activeView.value = 'payments'
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
  <ConsultationReview v-if="isConsultationReviewPage" />
  <div v-else class="min-h-screen bg-[#F8F9FA] text-[#202124]">
    <!-- Toast Notifications -->
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

    <div class="mx-auto flex min-h-screen max-w-[1440px]">
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
          @click="openPatientModal"
        >
          <UserPlus class="h-4 w-4" /> Register Patient
        </button>

        <nav class="space-y-2">
          <button
            v-for="item in navItems"
            :key="item.key"
            class="flex w-full items-center gap-3 rounded-lg px-4 py-3 text-left text-sm transition"
            :class="
              activeView === item.key
                ? 'bg-[#E8F0FE] text-[#1a73e8]'
                : 'text-[#5f6368] hover:bg-[#F1F3F4] hover:text-[#202124]'
            "
            @click="activeView = item.key"
          >
            <component :is="item.icon" class="h-4 w-4" />
            {{ item.label }}
          </button>
        </nav>
      </aside>

      <main class="flex-1 px-10 py-8">
        <header class="mb-8 flex items-center justify-between">
          <div>
            <h2 class="text-3xl font-semibold tracking-tight">{{ navItems.find((item) => item.key === activeView)?.label }}</h2>
            <p class="mt-1 text-sm text-[#5f6368]">Google Stitch-inspired layout with spacing-first clinical clarity.</p>
          </div>

          <div class="flex items-center gap-3">
            <span v-if="outsystemsSyncing" class="rounded-full bg-[#E8F0FE] px-3 py-1 text-xs font-semibold text-[#1a73e8]">
              Syncing...
            </span>
            <button
              class="inline-flex items-center gap-2 rounded-lg bg-[#1a73e8] px-4 py-2 text-sm font-medium text-white hover:bg-[#1765cc]"
              @click="refreshAll"
            >
              <LoaderCircle class="h-4 w-4" /> Refresh
            </button>
          </div>
        </header>

        <section v-if="activeView === 'inventory'" class="rounded-2xl border border-[#E8EAED] bg-white p-6">
          <div class="mb-6 flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <Pill class="h-5 w-5 text-[#1a73e8]" />
              <h3 class="text-lg font-semibold">Drug Inventory</h3>
            </div>
            <button
              class="inline-flex items-center gap-2 rounded-lg bg-[#1a73e8] px-3 py-2 text-sm font-medium text-white hover:bg-[#1765cc]"
              @click="openAddDrugModal"
            >
              <Plus class="h-4 w-4" />
              Add New Drug
            </button>
          </div>

          <div class="mb-4">
            <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">
              Search Drug
            </label>
            <input
              v-model="inventorySearch"
              class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm focus:border-[#1a73e8] focus:outline-none"
              placeholder="Search by drug name or purpose..."
            />
          </div>

          <p v-if="loadingInventory" class="text-sm text-[#5f6368]">Loading inventory...</p>
          <p v-else-if="!inventoryError && inventory.length === 0" class="rounded-lg bg-[#FFF8E1] p-3 text-sm text-[#7A5C00]">
            Inventory is currently empty.
          </p>
          <p v-else-if="!inventoryError && filteredInventory.length === 0" class="rounded-lg bg-[#F8F9FA] p-3 text-sm text-[#5f6368]">
            No drugs match your search.
          </p>
          <p v-else-if="inventoryNotice" class="rounded-lg bg-[#E8F0FE] p-3 text-sm text-[#1a73e8]">{{ inventoryNotice }}</p>
          <p v-else-if="inventoryError" class="rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ inventoryError }}</p>
          <p v-else-if="deletingDrugError" class="rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ deletingDrugError }}</p>

          <div v-else class="overflow-hidden rounded-xl border border-[#E8EAED]">
            <table class="min-w-full divide-y divide-[#E8EAED] text-sm">
              <thead class="bg-[#F8F9FA]">
                <tr class="text-left text-[#5f6368]">
                  <th 
                    class="cursor-pointer select-none px-4 py-3 font-medium transition hover:bg-[#E8EAED]"
                    @click="toggleInventorySort('name')"
                  >
                    <span class="inline-flex items-center gap-1">
                      Drug
                      <ChevronUp v-if="inventorySortKey === 'name' && inventorySortOrder === 'asc'" class="h-3.5 w-3.5" />
                      <ChevronDown v-else-if="inventorySortKey === 'name' && inventorySortOrder === 'desc'" class="h-3.5 w-3.5" />
                      <ArrowUpDown v-else class="h-3.5 w-3.5 opacity-40" />
                    </span>
                  </th>
                  <th 
                    class="cursor-pointer select-none px-4 py-3 font-medium transition hover:bg-[#E8EAED]"
                    @click="toggleInventorySort('stock')"
                  >
                    <span class="inline-flex items-center gap-1">
                      Stock
                      <ChevronUp v-if="inventorySortKey === 'stock' && inventorySortOrder === 'asc'" class="h-3.5 w-3.5" />
                      <ChevronDown v-else-if="inventorySortKey === 'stock' && inventorySortOrder === 'desc'" class="h-3.5 w-3.5" />
                      <ArrowUpDown v-else class="h-3.5 w-3.5 opacity-40" />
                    </span>
                  </th>
                  <th 
                    class="cursor-pointer select-none px-4 py-3 font-medium transition hover:bg-[#E8EAED]"
                    @click="toggleInventorySort('price')"
                  >
                    <span class="inline-flex items-center gap-1">
                      Price (SGD)
                      <ChevronUp v-if="inventorySortKey === 'price' && inventorySortOrder === 'asc'" class="h-3.5 w-3.5" />
                      <ChevronDown v-else-if="inventorySortKey === 'price' && inventorySortOrder === 'desc'" class="h-3.5 w-3.5" />
                      <ArrowUpDown v-else class="h-3.5 w-3.5 opacity-40" />
                    </span>
                  </th>
                  <th class="px-4 py-3 font-medium">Action</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#F1F3F4] bg-white">
                <template v-for="(drug, idx) in sortedInventory" :key="drug.id ?? idx">
                  <tr class="hover:bg-[#F8F9FA]">
                    <td class="px-4 py-3">{{ drug.name ?? drug.drugName ?? 'Unnamed Drug' }}</td>
                    <td class="px-4 py-3">{{ drug.quantity ?? 0 }}</td>
                    <td class="px-4 py-3">{{ Number(drug.price ?? 0).toFixed(2) }}</td>
                    <td class="px-4 py-3">
                      <div class="flex flex-wrap items-center gap-2">
                        <button
                          class="inline-flex items-center gap-1 rounded-lg border border-[#DADCE0] px-2.5 py-1.5 text-xs font-medium text-[#202124] hover:bg-[#F1F3F4]"
                          @click="openEditDrugModal(drug)"
                        >
                          <SquarePen class="h-3.5 w-3.5" />
                          Edit
                        </button>
                        <button
                          class="inline-flex items-center gap-1 rounded-lg border border-[#DADCE0] px-2.5 py-1.5 text-xs font-medium text-[#1a73e8] hover:bg-[#E8F0FE]"
                          @click="toggleDrugDetails(drug.id)"
                        >
                          <ChevronUp v-if="isDrugExpanded(drug.id)" class="h-3.5 w-3.5" />
                          <ChevronDown v-else class="h-3.5 w-3.5" />
                          Details
                        </button>
                        <button
                          class="inline-flex items-center gap-1 rounded-lg border border-[#F4C7C3] px-2.5 py-1.5 text-xs font-medium text-[#B3261E] hover:bg-[#FDECEC] disabled:opacity-60"
                          :disabled="deletingDrugId === drug.id"
                          @click="deleteDrug(drug)"
                        >
                          <LoaderCircle v-if="deletingDrugId === drug.id" class="h-3.5 w-3.5 animate-spin" />
                          <Trash2 v-else class="h-3.5 w-3.5" />
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="isDrugExpanded(drug.id)" class="bg-[#F8F9FA]">
                    <td colspan="4" class="px-4 py-3">
                      <p class="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-[#1a73e8]">Drug Details</p>
                      <div class="grid gap-3 md:grid-cols-3">
                        <div>
                          <p class="text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Purpose</p>
                          <p class="mt-1 text-sm text-[#202124]">{{ drug.purpose || 'N/A' }}</p>
                        </div>
                        <div>
                          <p class="text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Recommended Dosage</p>
                          <p class="mt-1 text-sm text-[#202124]">{{ drug.dosage || drug.recommendedDosage || 'N/A' }}</p>
                        </div>
                        <div>
                          <p class="text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Remarks</p>
                          <p class="mt-1 text-sm text-[#202124]">{{ drug.remarks || 'None' }}</p>
                        </div>
                      </div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </section>

        <section v-if="activeView === 'records'" class="space-y-5">
          <div class="rounded-2xl border border-[#E8EAED] bg-white p-6">
            <div class="mb-2 flex items-center gap-2">
              <FileText class="h-5 w-5 text-[#1a73e8]" />
              <h3 class="text-lg font-semibold">Clinical Records</h3>
            </div>
            <p class="text-sm text-[#5f6368]">Source: OutSystems RecordsAPI</p>
          </div>

          <div class="rounded-2xl border border-[#E8EAED] bg-white p-6">
            <h4 class="text-lg font-semibold">Consultation</h4>
            <p class="mt-1 text-sm text-[#5f6368]">
              Submits visit notes.
            </p>
            <div class="mt-4 grid gap-3 md:grid-cols-2">
              <input
                v-model="consultationForm.patientId"
                class="rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
                placeholder="Patient ID"
              />
              <input
                v-model="consultationForm.visitNotes"
                class="rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
                placeholder="visitNotes"
              />
            </div>
            <div class="mt-5 rounded-2xl border border-[#E8EAED] bg-[#F8F9FA] p-4">
              <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h5 class="text-base font-semibold">Drug Catalogue</h5>
                  <p class="text-sm text-[#5f6368]">
                    Search the catalogue and set the quantity for each drug before review.
                  </p>
                </div>
                <div class="w-full md:max-w-sm">
                  <input
                    v-model="consultationDrugSearch"
                    class="w-full rounded-lg border border-[#DADCE0] bg-white px-3 py-2 text-sm"
                    placeholder="Search drugs by name or ID"
                  />
                </div>
              </div>

              <div class="mt-4">
                <p v-if="loadingInventory" class="text-sm text-[#5f6368]">Loading drug catalogue...</p>
                <p v-else-if="inventoryError" class="rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">
                  {{ inventoryError }}
                </p>
                <p v-else-if="consultationFilteredDrugs.length === 0" class="text-sm text-[#5f6368]">
                  No drugs match your search.
                </p>
                <div v-else class="overflow-hidden rounded-xl border border-[#E8EAED] bg-white">
                  <table class="min-w-full divide-y divide-[#E8EAED] text-sm">
                    <thead class="bg-[#F8F9FA] text-left text-[#5f6368]">
                      <tr>
                        <th class="px-4 py-3 font-medium">Drug</th>
                        <th class="px-4 py-3 font-medium">Available</th>
                        <th class="px-4 py-3 font-medium">Price (SGD)</th>
                        <th class="px-4 py-3 font-medium">Quantity</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-[#F1F3F4] bg-white">
                      <tr v-for="drug in consultationFilteredDrugs" :key="drug.id" class="hover:bg-[#F8F9FA]">
                        <td class="px-4 py-3 font-medium text-[#202124]">{{ drug.name }}</td>
                        <td class="px-4 py-3">{{ drug.quantity }}</td>
                        <td class="px-4 py-3">{{ Number(drug.price || 0).toFixed(2) }}</td>
                        <td class="px-4 py-3">
                          <input
                            :value="getConsultationDrugQuantity(drug.id)"
                            type="number"
                            min="0"
                            :max="drug.quantity"
                            step="1"
                            class="w-24 rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
                            @input="setConsultationDrugQuantity(drug.id, $event.target.value)"
                          />
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div class="mt-4 flex flex-wrap gap-4 text-sm text-[#5f6368]">
                <span>Selected drugs: {{ consultationSelectedDrugs.length }}</span>
                <span>Total units: {{ consultationSelectedDrugCount }}</span>
                <span>Total value: SGD {{ consultationSelectedDrugTotal.toFixed(2) }}</span>
              </div>
            </div>
            <button
              class="mt-4 rounded-lg bg-[#1a73e8] px-4 py-2 text-sm font-medium text-white hover:bg-[#1765cc] disabled:opacity-60"
              :disabled="submittingConsultation"
              @click="submitConsultation"
            >
              <span class="inline-flex items-center gap-2">
                <LoaderCircle v-if="submittingConsultation" class="h-4 w-4 animate-spin" />
                Submit Consultation
              </span>
            </button>
            <p v-if="consultationError" class="mt-3 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ consultationError }}</p>
            <p v-if="consultationSuccess" class="mt-3 rounded-lg bg-[#E6F4EA] p-3 text-sm text-[#188038]">{{ consultationSuccess }}</p>

            <div v-if="consultationNewRecord || consultationHistory.length" class="mt-4 rounded-lg border border-[#E8EAED] bg-[#F8F9FA] p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.12em] text-[#5f6368]">Consultation Response</p>
              <p v-if="consultationRecordId !== null" class="mt-2 text-sm text-[#202124]">
                Record ID: {{ consultationRecordId }}
              </p>
              <p v-if="consultationNewRecord" class="mt-2 text-sm text-[#202124]">
                New Record: {{ JSON.stringify(consultationNewRecord) }}
              </p>
              <p class="mt-2 text-sm text-[#5f6368]">History Count: {{ consultationHistory.length }}</p>
            </div>
          </div>

          <p v-if="loadingRecords" class="text-sm text-[#5f6368]">Loading records...</p>
          <p v-else-if="recordsError" class="rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ recordsError }}</p>
          <p v-else-if="dispenseError" class="rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ dispenseError }}</p>
          <p v-else-if="dispenseSuccess" class="rounded-lg bg-[#E6F4EA] p-3 text-sm text-[#188038]">{{ dispenseSuccess }}</p>

          <div v-else class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <article
              v-for="(record, idx) in normalizedRecords"
              :key="record.Id ?? idx"
              class="rounded-2xl border border-[#E8EAED] bg-white p-5 shadow-sm transition hover:bg-[#F8F9FA]"
            >
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-[#5f6368]">Record #{{ record.Id ?? idx + 1 }}</p>
              <h4 class="mt-2 text-lg font-semibold">{{ record.patientName ?? record.name ?? 'Unknown patient' }}</h4>
              <p class="mt-1 text-sm text-[#5f6368]">{{ record.VisitNotes || record.diagnosis || 'No notes available' }}</p>
              <p class="mt-3 text-sm text-[#5f6368]">Visit: {{ record.date || 'N/A' }}</p>
              <p class="mt-1 text-sm text-[#5f6368]">Status: {{ record.status }}</p>
              <button
                class="mt-4 rounded-lg bg-[#0B8043] px-4 py-2 text-sm font-medium text-white hover:bg-[#0A6E3A] disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="record.isClosed || dispensingRecordId === record.Id"
                @click="dispenseRecord(record)"
              >
                <span class="inline-flex items-center gap-2">
                  <LoaderCircle v-if="dispensingRecordId === record.Id" class="h-4 w-4 animate-spin" />
                  {{ record.isClosed ? 'Medication Dispensed' : 'Dispense Medication' }}
                </span>
              </button>
              <p class="mt-2 text-xs text-[#5f6368]">
                Closing this record (<code>isClosed=true</code>) is the trigger that medication has been
                dispensed and billing is ready.
              </p>
            </article>
          </div>
        </section>

        <section v-if="activeView === 'history'" class="space-y-5">
          <div class="rounded-2xl border border-[#E8EAED] bg-white p-6">
            <div class="mb-2 flex items-center gap-2">
              <FileText class="h-5 w-5 text-[#1a73e8]" />
              <h3 class="text-lg font-semibold">Patient History</h3>
            </div>
            <p class="text-sm text-[#5f6368]">
              Retrieves all clinical records and prescriptions by patientId.
            </p>

            <div class="mt-4 flex flex-col gap-3 md:flex-row md:items-center">
              <input
                v-model="patientHistoryForm.patientId"
                class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm md:max-w-xs"
                placeholder="Enter patientId"
              />
              <button
                class="inline-flex items-center justify-center gap-2 rounded-lg bg-[#1a73e8] px-4 py-2 text-sm font-medium text-white hover:bg-[#1765cc] disabled:opacity-60"
                :disabled="loadingPatientHistory"
                @click="fetchPatientHistory"
              >
                <LoaderCircle v-if="loadingPatientHistory" class="h-4 w-4 animate-spin" />
                Get Patient History
              </button>
            </div>

            <p v-if="patientHistoryError" class="mt-4 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">
              {{ patientHistoryError }}
            </p>
          </div>

          <div class="grid gap-5 xl:grid-cols-2">
            <div class="rounded-2xl border border-[#E8EAED] bg-white p-6">
              <h4 class="text-base font-semibold">Clinical Records</h4>
              <p v-if="loadingPatientHistory" class="mt-3 text-sm text-[#5f6368]">Loading records...</p>
              <p v-else-if="patientHistoryRecords.length === 0" class="mt-3 text-sm text-[#5f6368]">
                No records found for this patientId.
              </p>
              <div v-else class="mt-4 overflow-hidden rounded-xl border border-[#E8EAED]">
                <table class="min-w-full divide-y divide-[#E8EAED] text-sm">
                  <thead class="bg-[#F8F9FA]">
                    <tr class="text-left text-[#5f6368]">
                      <th class="px-4 py-3 font-medium">Record ID</th>
                      <th class="px-4 py-3 font-medium">Visit Date</th>
                      <th class="px-4 py-3 font-medium">Visit Notes</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-[#F1F3F4] bg-white">
                    <tr v-for="(row, idx) in patientHistoryRecords" :key="row.Id ?? row.id ?? idx">
                      <td class="px-4 py-3">{{ row.Id ?? row.id ?? 'N/A' }}</td>
                      <td class="px-4 py-3">{{ row.date ?? row.Date ?? row.visitDate ?? 'N/A' }}</td>
                      <td class="px-4 py-3">{{ row.VisitNotes ?? row.visitNotes ?? row.notes ?? 'N/A' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="rounded-2xl border border-[#E8EAED] bg-white p-6">
              <h4 class="text-base font-semibold">Prescriptions</h4>
              <p v-if="patientHistoryPrescriptionError" class="mt-3 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">
                {{ patientHistoryPrescriptionError }}
              </p>
              <p v-if="loadingPatientHistory" class="mt-3 text-sm text-[#5f6368]">Loading prescriptions...</p>
              <p v-else-if="patientHistoryPrescriptions.length === 0" class="mt-3 text-sm text-[#5f6368]">
                No prescriptions found for this patientId.
              </p>
              <div v-else class="mt-4 overflow-hidden rounded-xl border border-[#E8EAED]">
                <table class="min-w-full divide-y divide-[#E8EAED] text-sm">
                  <thead class="bg-[#F8F9FA]">
                    <tr class="text-left text-[#5f6368]">
                      <th class="px-4 py-3 font-medium">Prescription ID</th>
                      <th class="px-4 py-3 font-medium">Drug</th>
                      <th class="px-4 py-3 font-medium">Qty</th>
                      <th class="px-4 py-3 font-medium">Dosage</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-[#F1F3F4] bg-white">
                    <tr v-for="row in patientHistoryPrescriptions" :key="row.id">
                      <td class="px-4 py-3">{{ row.id }}</td>
                      <td class="px-4 py-3">{{ row.drugName }}</td>
                      <td class="px-4 py-3">{{ row.quantity }}</td>
                      <td class="px-4 py-3">{{ row.dosage }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        <section v-if="activeView === 'payments'" class="space-y-6">
          <div class="rounded-2xl border border-[#E8EAED] bg-white p-6">
            <h3 class="text-lg font-semibold">Billing (Closed Records)</h3>
            <p class="mt-1 text-sm text-[#5f6368]">
              Fetches closed records with patient details (JOIN-style billing view), then allows Mark as Paid updates.
            </p>
            <p v-if="billingError" class="mt-3 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ billingError }}</p>
            <p v-if="billingSuccess" class="mt-3 rounded-lg bg-[#E6F4EA] p-3 text-sm text-[#188038]">{{ billingSuccess }}</p>

            <div v-if="loadingBilling" class="mt-4 text-sm text-[#5f6368]">Loading billing records...</div>
            <div v-else-if="billingRows.length === 0" class="mt-4 text-sm text-[#5f6368]">No closed records found for billing.</div>
            <div v-else class="mt-4 overflow-hidden rounded-xl border border-[#E8EAED]">
              <table class="min-w-full divide-y divide-[#E8EAED] text-sm">
                <thead class="bg-[#F8F9FA]">
                  <tr class="text-left text-[#5f6368]">
                    <th class="px-4 py-3 font-medium">Record ID</th>
                    <th class="px-4 py-3 font-medium">Patient</th>
                    <th class="px-4 py-3 font-medium">NRIC</th>
                    <th class="px-4 py-3 font-medium">VisitNotes</th>
                    <th class="px-4 py-3 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#F1F3F4] bg-white">
                  <tr v-for="row in billingRows" :key="row.Id">
                    <td class="px-4 py-3">{{ row.Id }}</td>
                    <td class="px-4 py-3">{{ row.patientName }}</td>
                    <td class="px-4 py-3">{{ row.nric }}</td>
                    <td class="px-4 py-3">{{ row.VisitNotes || 'N/A' }}</td>
                    <td class="px-4 py-3">
                      <button
                        class="rounded-lg bg-[#1a73e8] px-3 py-1.5 text-xs font-medium text-white hover:bg-[#1765cc] disabled:cursor-not-allowed disabled:opacity-60"
                        :disabled="row.isPaid || markingPaidId === row.Id"
                        @click="markAsPaid(row)"
                      >
                        <span class="inline-flex items-center gap-2">
                          <LoaderCircle v-if="markingPaidId === row.Id" class="h-3.5 w-3.5 animate-spin" />
                          {{ row.isPaid ? 'Receipt Generated' : 'Generate Receipt' }}
                        </span>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="rounded-2xl border border-[#E8EAED] bg-white p-6">
            <h3 class="text-lg font-semibold">3-Stop Payment Wizard</h3>
            <div class="mt-4 grid grid-cols-3 gap-2 text-xs font-medium">
              <div class="rounded-lg px-3 py-2" :class="paymentStep >= 1 ? 'bg-[#E8F0FE] text-[#1a73e8]' : 'bg-[#F1F3F4] text-[#5f6368]'">1. Select Invoice</div>
              <div class="rounded-lg px-3 py-2" :class="paymentStep >= 2 ? 'bg-[#E8F0FE] text-[#1a73e8]' : 'bg-[#F1F3F4] text-[#5f6368]'">2. Enter Card</div>
              <div class="rounded-lg px-3 py-2" :class="paymentStep >= 3 ? 'bg-[#E8F0FE] text-[#1a73e8]' : 'bg-[#F1F3F4] text-[#5f6368]'">3. Success</div>
            </div>
          </div>

          <div v-if="paymentStep === 1" class="rounded-2xl border border-[#E8EAED] bg-white p-6">
            <h4 class="mb-4 font-semibold">Select Invoice To Pay</h4>
            <p v-if="pendingInvoices.length === 0" class="text-sm text-[#5f6368]">No pending invoices found.</p>
            <div v-else class="space-y-3">
              <article
                v-for="invoice in pendingInvoices"
                :key="invoice.invoiceId"
                class="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-[#E8EAED] p-4"
              >
                <div>
                  <p class="text-sm font-semibold">{{ invoice.invoiceId }} - {{ invoice.patientName }}</p>
                  <p class="text-xs text-[#5f6368]">{{ invoice.diagnosis }}</p>
                </div>
                <div class="flex items-center gap-3">
                  <p class="text-sm font-semibold">{{ invoice.currency }} {{ invoice.amount.toFixed(2) }}</p>
                  <button
                    class="rounded-lg bg-[#1a73e8] px-4 py-2 text-sm font-medium text-white hover:bg-[#1765cc]"
                    @click="selectInvoice(invoice)"
                  >
                    Select Invoice
                  </button>
                </div>
              </article>
            </div>
            <p v-if="paymentError" class="mt-4 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ paymentError }}</p>
          </div>

          <div v-if="paymentStep === 2" class="rounded-2xl border border-[#E8EAED] bg-white p-6">
            <h4 class="font-semibold">Enter Card Details</h4>
            <p class="mt-1 text-sm text-[#5f6368]">
              Invoice {{ selectedInvoice?.invoiceId }} for {{ selectedInvoice?.currency }} {{ selectedInvoice?.amount?.toFixed(2) }}
            </p>

            <div class="mt-4 rounded-lg border border-[#DADCE0] bg-white p-4">
              <div id="card-element" class="min-h-[22px]"></div>
            </div>

            <p v-if="paymentError" class="mt-4 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ paymentError }}</p>
            <p v-if="stripeError" class="mt-4 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ stripeError }}</p>

            <div class="mt-5 flex gap-3">
              <button
                class="rounded-lg bg-[#1a73e8] px-5 py-2.5 text-sm font-medium text-white hover:bg-[#1765cc] disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="confirmingPayment || !stripeReady"
                @click="handleConfirmAndPay"
              >
                <span class="inline-flex items-center gap-2">
                  <LoaderCircle v-if="confirmingPayment" class="h-4 w-4 animate-spin" />
                  {{ confirmingPayment ? 'Processing Payment...' : 'Confirm and Pay' }}
                </span>
              </button>
              <button
                class="rounded-lg border border-[#DADCE0] px-5 py-2.5 text-sm font-medium text-[#5f6368] hover:bg-[#F1F3F4]"
                @click="resetPaymentFlow"
              >
                Retry
              </button>
            </div>
          </div>

          <div v-if="paymentStep === 3" class="rounded-2xl border border-[#CEEAD6] bg-white p-6">
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-[#188038]">Payment Completed</p>
            <h4 class="mt-2 text-2xl font-semibold">Payment Received</h4>
            <p class="mt-2 text-sm text-[#5f6368]">
              Payment intent {{ paymentIntentId || 'N/A' }} succeeded for invoice {{ selectedInvoice?.invoiceId }}.
            </p>
            <p v-if="paymentVerifiedMessage" class="mt-3 rounded-lg bg-[#E6F4EA] p-3 text-sm font-medium text-[#188038]">
              {{ paymentVerifiedMessage }}
            </p>
            <button class="mt-5 rounded-lg bg-[#1a73e8] px-5 py-2.5 text-sm font-medium text-white hover:bg-[#1765cc]">
              Download Receipt (Placeholder)
            </button>
          </div>

          <div class="rounded-2xl border border-[#E8EAED] bg-white p-4">
            <h4 class="text-sm font-semibold text-[#202124]">Stripe Live Console Logs</h4>
            <div class="mt-3 max-h-36 overflow-auto rounded-lg border border-[#E8EAED] bg-[#F8F9FA] p-3 font-mono text-xs text-[#5f6368]">
              <p v-if="paymentConsoleLogs.length === 0">No payment intent logs yet.</p>
              <p v-for="(entry, index) in paymentConsoleLogs" :key="index">{{ entry }}</p>
            </div>
          </div>
        </section>
      </main>
    </div>

    <div v-if="patientModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">
      <div class="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
        <div class="mb-5 flex items-center justify-between">
          <h3 class="text-xl font-semibold">Register Patient</h3>
          <button class="rounded-lg p-2 hover:bg-[#F1F3F4]" @click="closePatientModal">
            <Plus class="h-4 w-4 rotate-45" />
          </button>
        </div>

        <div class="grid gap-4">
          <input v-model="patientForm.nric" class="rounded-lg border border-[#DADCE0] px-3 py-2 text-sm" placeholder="NRIC" />
          <input v-model="patientForm.name" class="rounded-lg border border-[#DADCE0] px-3 py-2 text-sm" placeholder="Full Name" />
          <input v-model="patientForm.phoneNo" class="rounded-lg border border-[#DADCE0] px-3 py-2 text-sm" placeholder="Phone Number" />
          <input v-model="patientForm.email" class="rounded-lg border border-[#DADCE0] px-3 py-2 text-sm" placeholder="Email" />
        </div>

        <p v-if="patientFormError" class="mt-4 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ patientFormError }}</p>
        <p v-if="patientFormSuccess" class="mt-4 rounded-lg bg-[#E6F4EA] p-3 text-sm text-[#188038]">{{ patientFormSuccess }}</p>

        <div class="mt-5 flex justify-end gap-3">
          <button class="rounded-lg border border-[#DADCE0] px-4 py-2 text-sm" @click="closePatientModal">Cancel</button>
          <button
            class="inline-flex items-center gap-2 rounded-lg bg-[#1a73e8] px-4 py-2 text-sm font-medium text-white hover:bg-[#1765cc] disabled:opacity-60"
            :disabled="submittingPatient"
            @click="submitPatient"
          >
            <LoaderCircle v-if="submittingPatient" class="h-4 w-4 animate-spin" />
            Submit
          </button>
        </div>
      </div>
    </div>

    <!-- Add Drug Modal -->
    <div v-if="addDrugModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">
      <div class="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
        <div class="mb-5 flex items-center justify-between">
          <h3 class="text-xl font-semibold">Add New Drug</h3>
          <button class="rounded-lg p-2 hover:bg-[#F1F3F4]" @click="closeAddDrugModal">
            <X class="h-4 w-4" />
          </button>
        </div>

        <div class="grid gap-4">
          <div>
            <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Drug Name</label>
            <input
              v-model="addDrugForm.drugName"
              class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Unit Price ($)</label>
            <input
              v-model.number="addDrugForm.price"
              type="number"
              min="0.01"
              step="0.01"
              class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Stock Quantity</label>
            <input
              v-model.number="addDrugForm.quantity"
              type="number"
              min="0"
              class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Purpose (Optional)</label>
            <input
              :value="addDrugForm.purpose"
              @input="updateAddDrugField('purpose', $event.target.value)"
              class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
              placeholder="e.g. Pain relief"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Recommended Dosage (Optional)</label>
            <input
              :value="addDrugForm.dosage"
              @input="updateAddDrugField('dosage', $event.target.value)"
              class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
              placeholder="e.g. 3 times a day"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Remarks (Optional)</label>
            <textarea
              :value="addDrugForm.remarks"
              @input="updateAddDrugField('remarks', $event.target.value)"
              rows="3"
              class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
              placeholder="Any notes for pharmacy staff"
            ></textarea>
          </div>
        </div>

        <p v-if="addDrugError" class="mt-4 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ addDrugError }}</p>

        <div class="mt-5 flex justify-end gap-3">
          <button class="rounded-lg border border-[#DADCE0] px-4 py-2 text-sm" @click="closeAddDrugModal">Cancel</button>
          <button
            class="inline-flex items-center gap-2 rounded-lg bg-[#1a73e8] px-4 py-2 text-sm font-medium text-white hover:bg-[#1765cc] disabled:opacity-60"
            :disabled="addingDrug"
            @click="submitAddDrug"
          >
            <LoaderCircle v-if="addingDrug" class="h-4 w-4 animate-spin" />
            Save
          </button>
        </div>
      </div>
    </div>

    <!-- Edit Drug Modal -->
    <div v-if="editDrugModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">
      <div class="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
        <div class="mb-5 flex items-center justify-between">
          <h3 class="text-xl font-semibold">Edit Drug</h3>
          <button class="rounded-lg p-2 hover:bg-[#F1F3F4]" @click="closeEditDrugModal">
            <X class="h-4 w-4" />
          </button>
        </div>

        <div class="grid gap-4">
          <div>
            <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Drug Name</label>
            <input
              :value="editDrugForm.drugName"
              disabled
              class="w-full rounded-lg border border-[#DADCE0] bg-[#F8F9FA] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Unit Price ($)</label>
            <input
              v-model.number="editDrugForm.price"
              type="number"
              min="0.01"
              step="0.01"
              class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Stock Quantity</label>
            <input
              v-model.number="editDrugForm.quantity"
              type="number"
              min="0"
              class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Purpose (Optional)</label>
            <input
              :value="editDrugForm.purpose"
              @input="updateEditDrugField('purpose', $event.target.value)"
              class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Recommended Dosage (Optional)</label>
            <input
              :value="editDrugForm.dosage"
              @input="updateEditDrugField('dosage', $event.target.value)"
              class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold uppercase tracking-[0.08em] text-[#5f6368]">Remarks (Optional)</label>
            <textarea
              :value="editDrugForm.remarks"
              @input="updateEditDrugField('remarks', $event.target.value)"
              rows="3"
              class="w-full rounded-lg border border-[#DADCE0] px-3 py-2 text-sm"
            ></textarea>
          </div>
        </div>

        <p v-if="editDrugError" class="mt-4 rounded-lg bg-[#FDECEC] p-3 text-sm text-[#B3261E]">{{ editDrugError }}</p>

        <div class="mt-5 flex justify-end gap-3">
          <button class="rounded-lg border border-[#DADCE0] px-4 py-2 text-sm" @click="closeEditDrugModal">Cancel</button>
          <button
            class="inline-flex items-center gap-2 rounded-lg bg-[#1a73e8] px-4 py-2 text-sm font-medium text-white hover:bg-[#1765cc] disabled:opacity-60"
            :disabled="editingDrug"
            @click="submitEditDrug"
          >
            <LoaderCircle v-if="editingDrug" class="h-4 w-4 animate-spin" />
            Update
          </button>
        </div>
      </div>
    </div>
  </div>
</template>