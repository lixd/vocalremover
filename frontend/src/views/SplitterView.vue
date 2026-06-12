<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import FileUploader from '@/components/FileUploader.vue'
import ModeSelector from '@/components/ModeSelector.vue'
import { createTask } from '@/api/client'

const router = useRouter()
const selectedFile = ref<File | null>(null)
const mode = ref<'2stems' | '4stems'>('4stems')
const isUploading = ref(false)
const error = ref<string | null>(null)

async function handleSubmit() {
  if (!selectedFile.value) return

  isUploading.value = true
  error.value = null

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('mode', mode.value)

    const task = await createTask(formData)
    router.push({ name: 'result', params: { taskId: task.id } })
  } catch (err) {
    error.value = err instanceof Error ? err.message : '上传失败，请重试'
  } finally {
    isUploading.value = false
  }
}

function handleFileSelected(file: File) {
  selectedFile.value = file
}
</script>

<template>
  <div class="splitter-view">
    <header class="page-header">
      <h1 class="title">AI 分离器</h1>
      <h3 class="subtitle">将歌曲分离为多个独立音轨</h3>
    </header>

    <div class="upload-card">
      <FileUploader @file-selected="handleFileSelected" />

      <div class="options-row">
        <ModeSelector v-model="mode" />
      </div>

      <button
        class="submit-btn"
        :disabled="!selectedFile || isUploading"
        @click="handleSubmit"
      >
        <span v-if="isUploading" class="spinner"></span>
        {{ isUploading ? '上传中...' : '开始分离' }}
      </button>

      <div v-if="error" class="error-msg">{{ error }}</div>
    </div>

    <section class="description-section">
      <h2 class="section-title">智能音轨分离</h2>
      <p class="section-text">
        通过先进的人工智能技术，将歌曲智能分离为多个独立音轨。支持人声、鼓、贝斯、
        其他乐器等多轨分离，为您提供专业级的音轨拆分结果，适用于混音、采样、学习等场景。
      </p>
    </section>
  </div>
</template>

<style scoped>
.splitter-view {
  max-width: 720px;
  margin: 0 auto;
  font-family: var(--font-family);
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.title {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 16px;
}

.subtitle {
  font-size: 1.4rem;
  font-weight: 300;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.upload-card {
  background: var(--color-bg-secondary);
  border-radius: 16px;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.options-row {
  display: flex;
  justify-content: center;
}

.submit-btn {
  width: 100%;
  padding: 14px 24px;
  background: transparent;
  color: var(--color-text-primary);
  border: 2px solid var(--color-accent);
  border-radius: 32px;
  font-size: 16px;
  font-weight: 400;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.submit-btn:hover:not(:disabled) {
  opacity: 0.8;
}

.submit-btn:disabled {
  border-color: var(--color-border);
  color: var(--color-text-secondary);
  cursor: not-allowed;
  opacity: 0.5;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-msg {
  color: var(--color-error);
  font-size: 14px;
  text-align: center;
  padding: 12px;
  background: rgba(255, 107, 107, 0.1);
  border-radius: 8px;
}

.description-section {
  margin-top: 48px;
  text-align: center;
}

.section-title {
  font-size: 1.8rem;
  font-weight: 500;
  color: var(--color-text-primary);
  margin: 0 0 16px;
}

.section-text {
  font-size: 1rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}
</style>
