import { ref, onUnmounted } from 'vue'
import type { Task } from '@/types'
import { getTaskStatus } from '@/api/client'

const POLL_INTERVAL_MS = 3000
const MAX_CONSECUTIVE_ERRORS = 3

export function useTask(taskId: string) {
  const task = ref<Task | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  let pollTimer: ReturnType<typeof setInterval> | null = null
  let consecutiveErrors = 0

  async function fetchTask() {
    try {
      isLoading.value = true
      task.value = await getTaskStatus(taskId)
      error.value = null
      consecutiveErrors = 0

      if (task.value.status === 'COMPLETED' || task.value.status === 'FAILED') {
        stopPolling()
      }
    } catch (err) {
      consecutiveErrors += 1
      if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
        error.value = 'Network error, please refresh the page'
        stopPolling()
      }
    } finally {
      isLoading.value = false
    }
  }

  function startPolling() {
    if (pollTimer) return
    fetchTask()
    pollTimer = setInterval(fetchTask, POLL_INTERVAL_MS)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  onUnmounted(stopPolling)

  return {
    task,
    isLoading,
    error,
    startPolling,
    stopPolling,
  }
}
