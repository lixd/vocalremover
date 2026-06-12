<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import TaskProgress from '@/components/TaskProgress.vue'
import StemPlayer from '@/components/StemPlayer.vue'
import DownloadPanel from '@/components/DownloadPanel.vue'
import { useTask } from '@/composables/useTask'
import { getStemStreamUrl, getStemDownloadUrl, getDownloadAllUrl } from '@/api/client'

const route = useRoute()
const taskId = route.params.taskId as string

const { task, isLoading, error, startPolling } = useTask(taskId)

onMounted(startPolling)

const stemEntries = computed(() => {
  if (!task.value || task.value.status !== 'COMPLETED') return []
  return Object.keys(task.value.stems).map((name) => ({
    name,
    streamUrl: getStemStreamUrl(taskId, name),
    downloadUrl: getStemDownloadUrl(taskId, name),
  }))
})

const downloadAllUrl = computed(() => getDownloadAllUrl(taskId))
</script>

<template>
  <div class="result-view">
    <header class="page-header">
      <router-link to="/" class="back-link">← 返回上传</router-link>
      <h1 class="title">{{ task?.original_filename ?? '处理中...' }}</h1>
    </header>

    <TaskProgress
      v-if="task"
      :status="task.status"
      :error-message="task.error_message"
    />

    <div v-if="task?.status === 'COMPLETED'" class="stems-container">
      <StemPlayer
        v-for="stem in stemEntries"
        :key="stem.name"
        :stem-name="stem.name"
        :stream-url="stem.streamUrl"
        :download-url="stem.downloadUrl"
      />
      <DownloadPanel :download-all-url="downloadAllUrl" />
    </div>

    <div v-if="isLoading && !task" class="loading">
      <div class="loading-pulse"></div>
    </div>
  </div>
</template>

<style scoped>
.result-view {
  max-width: 720px;
  margin: 0 auto;
  font-family: var(--font-family);
}

.page-header {
  margin-bottom: 24px;
}

.back-link {
  color: var(--color-text-secondary);
  font-size: 14px;
  text-decoration: none;
  display: inline-block;
  margin-bottom: 16px;
  transition: color 0.2s;
}

.back-link:hover {
  color: var(--color-accent);
}

.title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
  word-break: break-all;
}

.stems-container {
  margin-top: 24px;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}

.loading-pulse {
  width: 200px;
  height: 4px;
  background: var(--color-border);
  border-radius: 2px;
  overflow: hidden;
}

.loading-pulse::after {
  content: '';
  display: block;
  width: 40%;
  height: 100%;
  background: var(--color-accent);
  border-radius: 2px;
  animation: slide 1.5s ease-in-out infinite;
}

@keyframes slide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}
</style>
