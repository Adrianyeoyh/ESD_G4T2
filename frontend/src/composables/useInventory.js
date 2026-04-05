import { computed, ref } from 'vue'
import { fetchDrugsApi, addDrugApi, updateDrugApi, deleteDrugApi } from '../api/drugs'
import { getDrugId } from '../utils/normalizers'
import { useToast } from './useToast'

const inventory = ref([])
const loadingInventory = ref(false)
const inventoryError = ref('')
const inventoryNotice = ref('')
const inventorySearch = ref('')
const inventorySortKey = ref('name')
const inventorySortOrder = ref('asc')
const expandedDrugIds = ref([])
const deletingDrugId = ref(null)
const deletingDrugError = ref('')
const deleteDrugConfirmOpen = ref(false)
const deleteDrugTarget = ref(null)

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

export function useInventory() {
  const { showToast } = useToast()

  const filteredInventory = computed(() => {
    const query = String(inventorySearch.value || '').trim().toLowerCase()
    if (!query) return inventory.value
    return inventory.value.filter(
      (drug) =>
        String(drug.name ?? drug.drugName ?? '').toLowerCase().includes(query) ||
        String(drug.purpose ?? '').toLowerCase().includes(query),
    )
  })

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

  const fetchDrugs = async () => {
    loadingInventory.value = true
    inventoryError.value = ''
    inventoryNotice.value = ''

    try {
      const rows = await fetchDrugsApi()
      inventory.value = rows
      if (!rows.length) {
        inventoryNotice.value = 'Connected to the drug service via Kong. Inventory is currently empty.'
      }
    } catch (error) {
      console.error('Drug API Error:', error?.response)
      inventoryError.value =
        error?.response?.data?.message ||
        'Unable to load Drug Service via Kong. Check route/service health.'
    } finally {
      loadingInventory.value = false
    }
  }

  const openAddDrugModal = () => {
    addDrugError.value = ''
    addDrugForm.value = { drugName: '', quantity: 0, price: 0, purpose: '', dosage: '', remarks: '' }
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

    if (!drugData.drugName) { addDrugError.value = 'Drug Name is required.'; return }
    if (!Number.isFinite(drugData.quantity) || drugData.quantity < 0) { addDrugError.value = 'Stock Quantity must be 0 or greater.'; return }
    if (!Number.isFinite(drugData.price) || drugData.price <= 0) { addDrugError.value = 'Unit Price must be greater than 0.'; return }

    addingDrug.value = true
    try {
      await addDrugApi(drugData)
      await fetchDrugs()
      closeAddDrugModal()
      showToast(`Drug ${drugData.drugName} added successfully!`, 'success')
    } catch (error) {
      addDrugError.value = error?.response?.data?.error || error?.response?.data?.message || 'Unable to add drug.'
      showToast(addDrugError.value, 'error')
    } finally {
      addingDrug.value = false
    }
  }

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

    if (!Number.isFinite(drugId) || drugId <= 0) { editDrugError.value = 'Invalid drug selected.'; return }
    if (!Number.isFinite(quantity) || quantity < 0) { editDrugError.value = 'Stock Quantity must be 0 or greater.'; return }
    if (!Number.isFinite(price) || price <= 0) { editDrugError.value = 'Unit Price must be greater than 0.'; return }

    editingDrug.value = true
    try {
      const drugName = String(editDrugForm.value.drugName || '').trim()
      if (!drugName) { editDrugError.value = 'Drug Name is required.'; return }

      await updateDrugApi(drugId, { drugName, quantity, price })
      await fetchDrugs()
      closeEditDrugModal()
      showToast('Inventory updated successfully!', 'success')
    } catch (error) {
      editDrugError.value = error?.response?.data?.error || error?.response?.data?.message || 'Unable to update drug.'
      showToast(editDrugError.value, 'error')
    } finally {
      editingDrug.value = false
    }
  }

  const openDeleteDrugConfirm = (drug) => {
    const drugId = getDrugId(drug)
    const drugName = drug?.name ?? drug?.drugName ?? 'this drug'
    deletingDrugError.value = ''
    if (!Number.isFinite(drugId) || drugId <= 0) {
      deletingDrugError.value = 'Invalid drugId selected for deletion.'
      return
    }
    deleteDrugTarget.value = { drugId, drugName }
    deleteDrugConfirmOpen.value = true
  }

  const closeDeleteDrugConfirm = () => {
    deleteDrugConfirmOpen.value = false
    deleteDrugTarget.value = null
  }

  const deleteDrug = async () => {
    const drugId = Number(deleteDrugTarget.value?.drugId)
    const drugName = String(deleteDrugTarget.value?.drugName || 'this drug')
    deletingDrugError.value = ''

    if (!Number.isFinite(drugId) || drugId <= 0) {
      deletingDrugError.value = 'Invalid drugId selected for deletion.'
      closeDeleteDrugConfirm()
      return
    }

    deletingDrugId.value = drugId
    try {
      await deleteDrugApi(drugId)
      expandedDrugIds.value = expandedDrugIds.value.filter((id) => id !== drugId)
      await fetchDrugs()
      showToast(`Drug ${drugName} removed from inventory.`, 'success')
      closeDeleteDrugConfirm()
    } catch (error) {
      deletingDrugError.value = error?.response?.data?.error || error?.response?.data?.message || 'Unable to delete drug.'
      showToast(deletingDrugError.value, 'error')
    } finally {
      deletingDrugId.value = null
    }
  }

  const toggleDrugDetails = (drugId) => {
    const normalizedId = Number(drugId)
    if (!Number.isFinite(normalizedId) || normalizedId <= 0) return
    if (expandedDrugIds.value.includes(normalizedId)) {
      expandedDrugIds.value = expandedDrugIds.value.filter((id) => id !== normalizedId)
      return
    }
    expandedDrugIds.value = [...expandedDrugIds.value, normalizedId]
  }

  const isDrugExpanded = (drugId) => expandedDrugIds.value.includes(Number(drugId))

  return {
    inventory,
    loadingInventory,
    inventoryError,
    inventoryNotice,
    inventorySearch,
    inventorySortKey,
    inventorySortOrder,
    filteredInventory,
    sortedInventory,
    toggleInventorySort,
    fetchDrugs,
    expandedDrugIds,
    deletingDrugId,
    deletingDrugError,
    deleteDrugConfirmOpen,
    deleteDrugTarget,
    openDeleteDrugConfirm,
    closeDeleteDrugConfirm,
    deleteDrug,
    toggleDrugDetails,
    isDrugExpanded,
    addDrugModalOpen,
    addingDrug,
    addDrugError,
    addDrugForm,
    openAddDrugModal,
    closeAddDrugModal,
    updateAddDrugField,
    submitAddDrug,
    editDrugModalOpen,
    editingDrug,
    editDrugError,
    editDrugForm,
    openEditDrugModal,
    closeEditDrugModal,
    updateEditDrugField,
    submitEditDrug,
  }
}
