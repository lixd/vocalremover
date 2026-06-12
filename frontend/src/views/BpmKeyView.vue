<script setup lang="ts">
import { ref } from 'vue'
import { analyzeAudio } from '@/utils/bpm-key'

const audioFile = ref<File | null>(null)
const isAnalyzing = ref(false)
const error = ref<string | null>(null)
const result = ref<{
  bpm: number
  bpmConfidence: number
  key: string
  mode: string
  keyConfidence: number
  duration: number
} | null>(null)

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  audioFile.value = file
  error.value = null
  result.value = null
  input.value = ''
}

function formatDuration(s: number): string {
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

function confidenceLabel(confidence: number): string {
  if (confidence >= 0.8) return '高'
  if (confidence >= 0.5) return '中'
  return '低'
}

function confidenceColor(confidence: number): string {
  const style = getComputedStyle(document.documentElement)
  if (confidence >= 0.8) return style.getPropertyValue('--color-accent').trim()
  if (confidence >= 0.5) return '#ffc107'
  return style.getPropertyValue('--color-error').trim()
}

async function handleAnalyze() {
  if (!audioFile.value) return

  isAnalyzing.value = true
  error.value = null
  result.value = null

  try {
    const analysis = await analyzeAudio(audioFile.value)
    result.value = {
      bpm: analysis.bpm.bpm,
      bpmConfidence: analysis.bpm.confidence,
      key: analysis.key.key,
      mode: analysis.key.mode === 'major' ? '大调' : '小调',
      keyConfidence: analysis.key.confidence,
      duration: analysis.duration,
    }
  } catch (e) {
    error.value = '分析失败：' + (e instanceof Error ? e.message : '未知错误')
  } finally {
    isAnalyzing.value = false
  }
}

function triggerFileInput() {
  document.getElementById('bpm-file-input')?.click()
}
</script>

<template>
  <div class="bpm-view">
    <header class="page-header">
      <h1 class="title">BPM/调性查询</h1>
      <p class="subtitle">检测音频的 BPM 速度和调性信息</p>
    </header>

    <div class="card">
      <div class="upload-area" @click="triggerFileInput">
        <input id="bpm-file-input" type="file" accept=".mp3,.wav,.flac,.ogg,.m4a" style="display: none" @change="handleFileChange" />
        <div v-if="!audioFile" class="upload-prompt">
          <span class="upload-icon">🎵</span>
          <span>点击选择音频文件</span>
        </div>
        <div v-else class="file-info">
          <span>🎵 {{ audioFile.name }}</span>
        </div>
      </div>

      <button v-if="audioFile" class="submit-btn" :disabled="isAnalyzing" @click="handleAnalyze">
        <span v-if="isAnalyzing" class="spinner"></span>
        {{ isAnalyzing ? '分析中...' : '🔍 开始分析' }}
      </button>

      <div v-if="result" class="result-grid">
        <div class="result-item">
          <span class="result-label">BPM</span>
          <span class="result-value bpm-value">{{ result.bpm }}</span>
          <span class="result-confidence" :style="{ color: confidenceColor(result.bpmConfidence) }">
            置信度：{{ confidenceLabel(result.bpmConfidence) }}（{{ (result.bpmConfidence * 100).toFixed(0) }}%）
          </span>
        </div>
        <div class="result-item">
          <span class="result-label">调性</span>
          <span class="result-value key-value">{{ result.key }} {{ result.mode }}</span>
          <span class="result-confidence" :style="{ color: confidenceColor(result.keyConfidence) }">
            置信度：{{ confidenceLabel(result.keyConfidence) }}（{{ (result.keyConfidence * 100).toFixed(0) }}%）
          </span>
        </div>
        <div class="result-item">
          <span class="result-label">时长</span>
          <span class="result-value">{{ formatDuration(result.duration) }}</span>
        </div>
      </div>

      <div v-if="error" class="error-msg">{{ error }}</div>
    </div>
  </div>
</template>

<style scoped>
.bpm-view { max-width: 600px; margin: 0 auto; font-family: var(--font-family); }
.page-header { text-align: center; margin-bottom: 32px; }
.title { font-size: 28px; font-weight: 700; color: var(--color-text-primary); margin: 0 0 12px; }
.subtitle { color: var(--color-text-secondary); font-size: 15px; margin: 0; }
.card { background: var(--color-bg-secondary); border-radius: 16px; padding: 32px; display: flex; flex-direction: column; gap: 20px; }
.upload-area {
  border: 1px dashed var(--color-upload-border); border-radius: 12px; padding: 32px;
  text-align: center; cursor: pointer; transition: all 0.2s; background: transparent;
}
.upload-area:hover { border-color: var(--color-accent); }
.upload-prompt { display: flex; flex-direction: column; align-items: center; gap: 8px; color: var(--color-text-secondary); }
.upload-icon { font-size: 32px; }
.file-info { color: var(--color-text-primary); font-weight: 600; }
.submit-btn {
  width: 100%; padding: 14px; background: transparent; color: var(--color-text-primary);
  border: 2px solid var(--color-accent); border-radius: 32px; font-size: 16px; font-weight: 400;
  cursor: pointer; transition: all 0.2s;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}
.submit-btn:hover:not(:disabled) { opacity: 0.8; }
.submit-btn:disabled { border-color: var(--color-border); color: var(--color-text-secondary); cursor: not-allowed; opacity: 0.5; }
.spinner { width: 18px; height: 18px; border: 2px solid transparent; border-top-color: currentColor; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.result-grid { display: flex; flex-direction: column; gap: 16px; }
.result-item {
  background: var(--color-bg-primary); border-radius: 10px; padding: 16px;
  display: flex; flex-direction: column; gap: 6px;
}
.result-label { color: var(--color-text-secondary); font-size: 13px; text-transform: uppercase; letter-spacing: 1px; }
.result-value { color: var(--color-text-primary); font-size: 24px; font-weight: 700; }
.bpm-value { color: var(--color-accent); }
.key-value { color: #7c4dff; }
.result-confidence { font-size: 12px; }
.error-msg { color: var(--color-error); font-size: 14px; text-align: center; padding: 12px; background: color-mix(in srgb, var(--color-error) 10%, transparent); border-radius: 8px; }
</style>
