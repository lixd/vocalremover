import { ref, onUnmounted } from 'vue'
import type { Task } from '@/types'
import { getTaskStatus } from '@/api/client'

const POLL_INTERVAL_MS = 3000
const MAX_CONSECUTIVE_ERRORS = 3
const ELAPSED_TICK_MS = 1000

export function useTask(taskId: string) {
  const task = ref<Task | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  // 已等待秒数（仅在 PENDING/PROCESSING 期间累加）
  const elapsedSeconds = ref(0)
  let pollTimer: ReturnType<typeof setInterval> | null = null
  let elapsedTimer: ReturnType<typeof setInterval> | null = null
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
        error.value = '网络异常，请刷新页面重试'
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
    elapsedTimer = setInterval(() => {
      elapsedSeconds.value += 1
    }, ELAPSED_TICK_MS)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
    if (elapsedTimer) {
      clearInterval(elapsedTimer)
      elapsedTimer = null
    }
  }

  onUnmounted(stopPolling)

  return {
    task,
    isLoading,
    error,
    elapsedSeconds,
    startPolling,
    stopPolling,
  }
}
