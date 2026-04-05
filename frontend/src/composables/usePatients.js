import { computed, ref } from 'vue'
import { fetchPatientsApi, registerPatientApi } from '../api/patients'
import { useOutsystemsSync } from './useOutsystemsSync'

const patientsData = ref([])
const patientsSearch = ref('')
const loadingPatients = ref(false)
const patientsError = ref('')
const selectedPatientDetails = ref(null)

const patientModalOpen = ref(false)
const submittingPatient = ref(false)
const patientFormError = ref('')
const patientFormSuccess = ref('')
const patientForm = ref({
  patientId: '',
  name: '',
  phoneNo: '',
  email: '',
})

export function usePatients() {
  const { beginOutsystemsSync, endOutsystemsSync } = useOutsystemsSync()

  const filteredPatients = computed(() => {
    const query = String(patientsSearch.value || '').trim().toLowerCase()
    if (!query) return patientsData.value
    return patientsData.value.filter(
      (patient) =>
        String(patient.name || '').toLowerCase().includes(query) ||
        String(patient.patientId || '').toLowerCase().includes(query) ||
        String(patient.email || '').toLowerCase().includes(query),
    )
  })

  const fetchPatients = async () => {
    loadingPatients.value = true
    patientsError.value = ''
    try {
      patientsData.value = await fetchPatientsApi()
    } catch (error) {
      patientsError.value = error?.message || 'Unable to fetch patients list.'
    } finally {
      loadingPatients.value = false
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
      patientId: String(patientForm.value.patientId ?? '').trim(),
      name: String(patientForm.value.name ?? '').trim(),
      phoneNo: Number(patientForm.value.phoneNo ?? 0),
      email: String(patientForm.value.email ?? '').trim(),
    }

    if (!payload.patientId || payload.patientId.length !== 9) {
      patientFormError.value = 'Patient ID (NRIC) must be exactly 9 characters.'
      submittingPatient.value = false
      endOutsystemsSync()
      return
    }

    try {
      await registerPatientApi(payload)
      patientFormSuccess.value = `Patient registered successfully with ID: ${payload.patientId}`
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

  return {
    patientsData,
    patientsSearch,
    loadingPatients,
    patientsError,
    selectedPatientDetails,
    filteredPatients,
    fetchPatients,
    patientModalOpen,
    submittingPatient,
    patientFormError,
    patientFormSuccess,
    patientForm,
    openPatientModal,
    closePatientModal,
    submitPatient,
  }
}
