<script setup lang="ts">
import { ref } from 'vue'
import { audioBufferToMp3 } from '@/utils/audio'

interface AudioItem {
  file: File
  name: string
  duration: number
}

const audioFiles = ref<AudioItem[]>([])
const isProcessing = ref(false)
const error = ref<string | null>(null)
const success = ref(false)

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const files = input.files
  if (!files) return
  error.value = null
  success.value = false

  for (const file of Array.from(files)) {
    const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
    if (!['mp3', 'wav', 'flac', 'ogg', 'm4a'].includes(ext)) {
      error.value = `不支持的格式: ${file.name}`
      return
    }
    audioFiles.value.push({ file, name: file.name, duration: 0 })
  }

  // Calculate durations
  audioFiles.value.forEach((item, idx) => {
    if (item.duration === 0) {
      const audio = new Audio(URL.createObjectURL(item.file))
      audio.addEventListener('loadedmetadata', () => {
        audioFiles.value[idx].duration = audio.duration
        URL.revokeObjectURL(audio.src)
      })
    }
  })

  // Reset input
  input.value = ''
}

function removeFile(index: number) {
  audioFiles.value.splice(index, 1)
}

function moveUp(index: number) {
  if (index > 0) {
    const temp = audioFiles.value[index]
    audioFiles.value[index] = audioFiles.value[index - 1]
    audioFiles.value[index - 1] = temp
  }
}

function moveDown(index: number) {
  if (index < audioFiles.value.length - 1) {
    const temp = audioFiles.value[index]
    audioFiles.value[index] = audioFiles.value[index + 1]
    audioFiles.value[index + 1] = temp
  }
}

function formatDuration(s: number): string {
  if (!s || !isFinite(s)) return '0:00'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

async function handleMerge() {
  if (audioFiles.value.length < 2) {
    error.value = '请至少添加两个音频文件'
    return
  }

  isProcessing.value = true
  error.value = null
  success.value = false

  try {
    const audioContext = new AudioContext()
    const buffers: AudioBuffer[] = []

    // Decode all files
    for (const item of audioFiles.value) {
      const arrayBuffer = await item.file.arrayBuffer()
      const buffer = await audioContext.decodeAudioData(arrayBuffer)
      buffers.push(buffer)
    }

    // Normalize: resample to highest sample rate, max channels
    const targetSampleRate = Math.max(...buffers.map(b => b.sampleRate))
    const targetChannels = Math.max(...buffers.map(b => b.numberOfChannels))

    const normalizedBuffers: AudioBuffer[] = []
    for (const buffer of buffers) {
      let normalized = buffer
      if (buffer.sampleRate !== targetSampleRate || buffer.numberOfChannels !== targetChannels) {
        const length = Math.ceil(buffer.duration * targetSampleRate)
        const offline = new OfflineAudioContext(targetChannels, length, targetSampleRate)
        const source = offline.createBufferSource()
        // Mix down or up channels
        if (buffer.numberOfChannels < targetChannels) {
          const merger = offline.createChannelMerger(targetChannels)
          for (let ch = 0; ch < targetChannels; ch++) {
            const gain = offline.createGain()
            source.connect(gain)
            gain.connect(merger, 0, Math.min(ch, buffer.numberOfChannels - 1))
          }
          source.connect(merger)
        } else {
          source.connect(offline.destination)
        }
        source.buffer = buffer
        source.start()
        normalized = await offline.startRendering()
      }
      normalizedBuffers.push(normalized)
    }

    // Concatenate
    const totalLength = normalizedBuffers.reduce((sum, b) => sum + b.length, 0)
    const concatBuffer = new AudioBuffer({
      numberOfChannels: targetChannels,
      length: totalLength,
      sampleRate: targetSampleRate,
    })

    let offset = 0
    for (const buffer of normalizedBuffers) {
      for (let ch = 0; ch < targetChannels; ch++) {
        const srcCh = Math.min(ch, buffer.numberOfChannels - 1)
        const srcData = buffer.getChannelData(srcCh)
        concatBuffer.getChannelData(ch).set(srcData, offset)
      }
      offset += buffer.length
    }

    // Encode to MP3
    const mp3Blob = audioBufferToMp3(concatBuffer)
    const filename = 'merged_' + new Date().toISOString().slice(0, 10) + '.mp3'
    downloadBlob(mp3Blob, filename)
    success.value = true
  } catch (e) {
    error.value = '合并失败：' + (e instanceof Error ? e.message : '未知错误')
  } finally {
    isProcessing.value = false
  }
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="merger-view">
    <header class="page-header">
      <h1 class="title">音频合并器</h1>
      <p class="subtitle">将多个音频文件按顺序合并为一个 MP3 文件</p>
    </header>

    <div class="card">
      <!-- File list -->
      <div v-if="audioFiles.length > 0" class="file-list">
        <div v-for="(item, index) in audioFiles" :key="index" class="file-item">
          <span class="file-index">{{ index + 1 }}</span>
          <span class="file-name">{{ item.name }}</span>
          <span class="file-duration">{{ formatDuration(item.duration) }}</span>
          <div class="file-actions">
            <button class="action-btn" @click="moveUp(index)" :disabled="index === 0">↑</button>
            <button class="action-btn" @click="moveDown(index)" :disabled="index === audioFiles.length - 1">↓</button>
            <button class="action-btn remove" @click="removeFile(index)">✕</button>
          </div>
        </div>
      </div>

      <!-- Add files -->
      <label class="add-files-btn">
        <input type="file" accept=".mp3,.wav,.flac,.ogg,.m4a" multiple style="display: none" @change="handleFileChange" />
        <span>➕ 添加音频文件</span>
      </label>

      <button v-if="audioFiles.length >= 2" class="submit-btn" :disabled="isProcessing" @click="handleMerge">
        <span v-if="isProcessing" class="spinner"></span>
        {{ isProcessing ? '合并中...' : '🔗 合并并导出 MP3' }}
      </button>

      <div v-if="success" class="success-msg">✅ 导出成功！</div>
      <div v-if="error" class="error-msg">{{ error }}</div>
    </div>
  </div>
</template>

<style scoped>
.merger-view { max-width: 600px; margin: 0 auto; font-family: var(--font-family); }
.page-header { text-align: center; margin-bottom: 32px; }
.title { font-size: 28px; font-weight: 700; color: var(--color-text-primary); margin: 0 0 12px; }
.subtitle { color: var(--color-text-secondary); font-size: 15px; margin: 0; }
.card { background: var(--color-bg-secondary); border-radius: 16px; padding: 32px; display: flex; flex-direction: column; gap: 16px; }
.file-list { display: flex; flex-direction: column; gap: 8px; }
.file-item {
  display: flex; align-items: center; gap: 12px;
  background: var(--color-bg-primary); border-radius: 10px; padding: 12px 16px;
}
.file-index {
  background: var(--color-accent); color: var(--color-bg-primary); font-weight: 700; font-size: 13px;
  width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.file-name { flex: 1; color: var(--color-text-primary); font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-duration { color: var(--color-text-secondary); font-family: monospace; font-size: 13px; flex-shrink: 0; }
.file-actions { display: flex; gap: 4px; flex-shrink: 0; }
.action-btn {
  background: var(--color-border); border: none; border-radius: 6px;
  color: var(--color-text-primary); width: 28px; height: 28px; cursor: pointer; font-size: 12px;
}
.action-btn:hover:not(:disabled) { background: color-mix(in srgb, var(--color-border) 100%, white 15%); }
.action-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.action-btn.remove:hover { background: var(--color-error); }
.add-files-btn {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 16px; border: 2px dashed var(--color-border); border-radius: 12px;
  color: var(--color-text-secondary); cursor: pointer; transition: all 0.2s; font-size: 15px;
}
.add-files-btn:hover { border-color: var(--color-accent); color: var(--color-text-primary); }
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
.success-msg { color: var(--color-accent); text-align: center; font-weight: 600; }
.error-msg { color: var(--color-error); font-size: 14px; text-align: center; padding: 12px; background: color-mix(in srgb, var(--color-error) 10%, transparent); border-radius: 8px; }
</style>
