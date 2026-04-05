import { computed, ref } from 'vue'

const outsystemsSyncCounter = ref(0)

export function useOutsystemsSync() {
  const outsystemsSyncing = computed(() => outsystemsSyncCounter.value > 0)

  const beginOutsystemsSync = () => {
    outsystemsSyncCounter.value += 1
  }

  const endOutsystemsSync = () => {
    outsystemsSyncCounter.value = Math.max(0, outsystemsSyncCounter.value - 1)
  }

  return { outsystemsSyncing, beginOutsystemsSync, endOutsystemsSync }
}
