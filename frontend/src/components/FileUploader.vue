<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const emit = defineEmits<{
  'file-selected': [file: File]
}>()

const ALLOWED_EXTENSIONS = ['mp3', 'wav', 'flac', 'ogg', 'm4a']
const MAX_FILE_SIZE = 20 * 1024 * 1024

const selectedFile = ref<File | null>(null)

function validateFile(file: File): boolean {
  const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    ElMessage.error(`不支持的格式，仅支持：${ALLOWED_EXTENSIONS.join(', ')}`)
    return false
  }
  if (file.size > MAX_FILE_SIZE) {
    ElMessage.error('文件过大，最大支持 20MB')
    return false
  }
  return true
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (validateFile(file)) {
    selectedFile.value = file
    emit('file-selected', file)
  }
}

function triggerFileInput() {
  document.getElementById('file-input')?.click()
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<template>
  <div class="uploader">
    <input
      id="file-input"
      type="file"
      :accept="ALLOWED_EXTENSIONS.map((e) => `.${e}`).join(',')"
      style="display: none"
      @change="handleFileChange"
    />

    <button v-if="!selectedFile" class="upload-btn" @click="triggerFileInput">选择文件</button>

    <div v-else class="file-selected">
      <span class="file-name">{{ selectedFile.name }}</span>
      <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
    </div>
  </div>
</template>

<style scoped>
.uploader {
  text-align: center;
}

.upload-btn {
  display: inline-block;
  padding: 6px 22px;
  background: transparent;
  color: var(--color-text-primary);
  border: 2px solid var(--color-accent);
  border-radius: 32px;
  font-size: 16px;
  font-weight: 400;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-btn:hover {
  opacity: 0.8;
}

.file-selected {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
}

.file-name {
  font-weight: 600;
  color: var(--color-text-primary);
}

.file-size {
  color: var(--color-text-secondary);
  font-size: 14px;
}
</style>
