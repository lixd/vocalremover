<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
  errorMessage?: string | null
  elapsedSeconds?: number
}>()

const statusConfig = computed(() => {
  switch (props.status) {
    case 'PENDING': return { text: '等待中...', icon: '⏳', color: 'var(--color-text-secondary)' }
    case 'PROCESSING': return { text: '正在分离...', icon: '🔄', color: 'var(--color-accent)' }
    case 'COMPLETED': return { text: '分离完成！', icon: '✅', color: 'var(--color-accent)' }
    case 'FAILED': return { text: '分离失败', icon: '❌', color: '#ff6b6b' }
    default: return { text: '加载中...', icon: '⏳', color: 'var(--color-text-secondary)' }
  }
})

// 仅在等待/处理中显示已等待时长
const showElapsed = computed(() =>
  props.status === 'PENDING' || props.status === 'PROCESSING'
)

function formatElapsed(s: number): string {
  const m = Math.floor(s / 60)
  const sec = s % 60
  return m > 0 ? `${m}分${sec}秒` : `${sec}秒`
}
</script>

<template>
  <div class="task-progress">
    <div class="progress-card">
      <div class="progress-icon">{{ statusConfig.icon }}</div>
      <div class="progress-text" :style="{ color: statusConfig.color }">
        {{ statusConfig.text }}
      </div>
      <div v-if="showElapsed && elapsedSeconds !== undefined" class="elapsed-text">
        已等待 {{ formatElapsed(elapsedSeconds) }}
      </div>
      <div v-if="status === 'PROCESSING'" class="progress-bar">
        <div class="progress-fill"></div>
      </div>
      <div v-if="status === 'FAILED' && errorMessage" class="error-msg">
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.task-progress {
  margin-bottom: 24px;
}

.progress-card {
  background: var(--color-bg-secondary);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
}

.progress-icon {
  font-size: 36px;
  margin-bottom: 12px;
}

.progress-text {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.elapsed-text {
  color: var(--color-text-secondary);
  font-size: 13px;
  font-family: monospace;
  margin-bottom: 16px;
}

.progress-bar {
  height: 4px;
  background: var(--color-border);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-accent), #00c853);
  border-radius: 2px;
  animation: progress 2s ease-in-out infinite;
  width: 60%;
}

@keyframes progress {
  0% { transform: translateX(-100%); }
  50% { transform: translateX(50%); }
  100% { transform: translateX(200%); }
}

.error-msg {
  margin-top: 12px;
  color: #ff6b6b;
  font-size: 14px;
  padding: 12px;
  background: rgba(255, 107, 107, 0.1);
  border-radius: 8px;
}
</style>
