import { ref } from 'vue'

const toasts = ref([])
let toastCounter = 0

export function useToast() {
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

  return { toasts, showToast, dismissToast }
}
