<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from 'vue'
import { audioBufferToMp3 } from '@/utils/audio'

const audioFile = ref<File | null>(null)
const isProcessing = ref(false)
const error = ref<string | null>(null)
const success = ref(false)

const startTime = ref(0)
const endTime = ref(0)
const duration = ref(0)
const fadeIn = ref(0)
const fadeOut = ref(0)
const currentTime = ref(0)

const waveformContainer = ref<HTMLElement | null>(null)
const waveformArea = ref<HTMLElement | null>(null)
const isPlaying = ref(false)
let wavesurfer: any = null
let RegionPlugin: any = null
let wsRegions: any = null
let activeRegion: any = null

const selectionFillStyle = computed(() => ({
  left: duration.value > 0 ? `${(startTime.value / duration.value) * 100}%` : '0%',
  width: duration.value > 0 ? `${((endTime.value - startTime.value) / duration.value) * 100}%` : '0%',
}))

// Dim overlay for unselected region (left side)
const dimLeftWidth = computed(() =>
  duration.value > 0 ? `${(startTime.value / duration.value) * 100}%` : '0%'
)
// Dim overlay for unselected region (right side)
const dimRightWidth = computed(() =>
  duration.value > 0 ? `${((duration.value - endTime.value) / duration.value) * 100}%` : '0%'
)

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  audioFile.value = file
  error.value = null
  success.value = false
  loadWaveform(file)
}

async function loadWaveform(file: File) {
  const WaveSurfer = (await import('wavesurfer.js')).default
  const regions = (await import('wavesurfer.js/dist/plugins/regions.esm.js')).default
  RegionPlugin = regions

  if (wavesurfer) wavesurfer.destroy()
  if (!waveformContainer.value) return

  wavesurfer = WaveSurfer.create({
    container: waveformContainer.value,
    waveColor: '#00e676',
    progressColor: '#00c853',
    cursorColor: '#ffffff',
    barWidth: 2,
    barGap: 1,
    height: 160,
    normalize: true,
    interact: true,
    autoScroll: false,
    autoCenter: false,
  })

  const url = URL.createObjectURL(file)
  wavesurfer.load(url)

  wsRegions = wavesurfer.registerPlugin(RegionPlugin.create())

  wavesurfer.on('ready', () => {
    duration.value = wavesurfer.getDuration()
    endTime.value = duration.value

    activeRegion = wsRegions.addRegion({
      start: 0,
      end: duration.value,
      color: 'rgba(102, 93, 195, 0.35)',
      drag: false,
      resize: true,
      minLength: 0.1,
    })
  })

  wsRegions.on('region-updated', (region: any) => {
    startTime.value = region.start
    endTime.value = region.end
  })

  wavesurfer.on('timeupdate', (time: number) => {
    currentTime.value = time
  })

  wavesurfer.on('play', () => { isPlaying.value = true })
  wavesurfer.on('pause', () => { isPlaying.value = false })
  wavesurfer.on('finish', () => { isPlaying.value = false })
}

function formatTime(s: number): string {
  if (!s || !isFinite(s)) return '00:00.0'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  const ms = Math.floor((s % 1) * 10)
  return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}.${ms}`
}

function togglePlay() {
  if (wavesurfer) wavesurfer.playPause()
}

async function handleCut() {
  if (!audioFile.value) return
  if (startTime.value >= endTime.value) {
    error.value = '起始时间必须小于结束时间'
    return
  }

  isProcessing.value = true
  error.value = null
  success.value = false

  try {
    const audioContext = new AudioContext()
    const arrayBuffer = await audioFile.value.arrayBuffer()
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

    const sampleRate = audioBuffer.sampleRate
    const numChannels = audioBuffer.numberOfChannels
    const startSample = Math.floor(startTime.value * sampleRate)
    const endSample = Math.floor(endTime.value * sampleRate)
    const cutLength = endSample - startSample

    if (cutLength <= 0) {
      error.value = '无效的时间范围'
      return
    }

    const cutBuffer = new AudioBuffer({
      numberOfChannels: numChannels,
      length: cutLength,
      sampleRate,
    })

    for (let ch = 0; ch < numChannels; ch++) {
      const sourceData = audioBuffer.getChannelData(ch)
      const cutData = cutBuffer.getChannelData(ch)

      for (let i = 0; i < cutLength; i++) {
        let sample = sourceData[startSample + i]
        if (fadeIn.value > 0) {
          const fadeInSamples = fadeIn.value * sampleRate
          if (i < fadeInSamples) sample *= i / fadeInSamples
        }
        if (fadeOut.value > 0) {
          const fadeOutSamples = fadeOut.value * sampleRate
          const fadeStart = cutLength - fadeOutSamples
          if (i > fadeStart) sample *= (cutLength - i) / fadeOutSamples
        }
        cutData[i] = sample
      }
    }

    const mp3Blob = audioBufferToMp3(cutBuffer)
    const filename = audioFile.value.name.replace(/\.[^.]+$/, '') + '_cut.mp3'
    downloadBlob(mp3Blob, filename)
    success.value = true
  } catch (e) {
    error.value = '处理失败：' + (e instanceof Error ? e.message : '未知错误')
  } finally {
    isProcessing.value = false
  }
}

function handleRemove() {
  startTime.value = 0
  endTime.value = duration.value
  if (activeRegion) {
    activeRegion.setOptions({ start: 0, end: duration.value })
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

function triggerFileInput() {
  document.getElementById('cutter-file-input')?.click()
}

onBeforeUnmount(() => {
  if (wavesurfer) wavesurfer.destroy()
})
</script>

<template>
  <div class="cutter-view">
    <header class="page-header">
      <h1 class="title">音频切割器</h1>
      <h3 class="subtitle">能够在线剪切任何音频文件免费编辑器</h3>
    </header>

    <input id="cutter-file-input" type="file" accept=".mp3,.wav,.flac,.ogg,.m4a" style="display: none" @change="handleFileChange" />
    <button v-if="!audioFile" class="upload-btn" @click="triggerFileInput">选择文件</button>

    <template v-if="audioFile">
      <div class="waveform-wrapper">
        <div class="waveform-header">
          <span class="file-name">{{ audioFile.name }}</span>
          <span class="current-time">{{ formatTime(currentTime) }}</span>
        </div>
        <div ref="waveformArea" class="waveform-area">
          <div ref="waveformContainer" class="waveform-box"></div>

          <!-- Dim overlays for unselected region -->
          <div class="dim-overlay dim-left" :style="{ width: dimLeftWidth }"></div>
          <div class="dim-overlay dim-right" :style="{ width: dimRightWidth }"></div>
        </div>
        <div class="selection-bar">
          <div class="selection-track">
            <div class="selection-fill" :style="selectionFillStyle"></div>
          </div>
          <div class="selection-labels">
            <span>{{ formatTime(startTime) }}</span>
            <span>{{ formatTime(endTime) }}</span>
          </div>
        </div>
        <div class="waveform-timebar">
          <span>00:00.0</span>
          <span v-if="duration > 0">{{ formatTime(duration) }}</span>
        </div>
      </div>

      <div class="controls-bar">
        <div class="time-info">
          <span class="time-label">{{ formatTime(startTime) }}</span>
          <span class="time-separator">—</span>
          <span class="time-label">{{ formatTime(endTime) }}</span>
        </div>

        <div class="action-buttons">
          <button class="action-btn primary" @click="handleCut" :disabled="isProcessing">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/><line x1="8.12" y1="8.12" x2="12" y2="12"/></svg>
            <span>{{ isProcessing ? '处理中...' : '裁剪' }}</span>
          </button>
          <button class="action-btn" @click="handleRemove">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            <span>移除</span>
          </button>
        </div>
      </div>

      <div class="fade-controls">
        <div class="fade-group">
          <label>淡入（秒）</label>
          <input type="number" v-model.number="fadeIn" :min="0" :max="10" :step="0.1" class="time-input" />
        </div>
        <div class="fade-group">
          <label>淡出（秒）</label>
          <input type="number" v-model.number="fadeOut" :min="0" :max="10" :step="0.1" class="time-input" />
        </div>
      </div>
    </template>

    <div v-if="success" class="success-msg">✅ 导出成功！</div>
    <div v-if="error" class="error-msg">{{ error }}</div>

    <section class="description-section">
      <h2 class="section-title">如何切割音频</h2>
      <p class="section-text">
        此应用可以用来剪辑音轨，或是删除一段音频片段。它可以轻松地淡入和淡出你的音乐，使音频听起来更加和谐。
      </p>
      <p class="section-text">
        它运行快速且十分易于使用。你可以将音频文件保存为任何格式（编解码器参数已为您配置好）
      </p>
      <p class="section-text">
        它直接在浏览器中工作，不需要安装任何软件，可用于移动设备。
      </p>
      <h2 class="section-title">保证隐私和安全</h2>
      <p class="section-text">
        这是无服务器应用程序。你的文件不会离开你的设备
      </p>
    </section>
  </div>
</template>

<style scoped>
.cutter-view {
  font-family: var(--font-family);
  text-align: center;
  max-width: 100%;
  overflow-x: hidden;
  padding: 0 24px;
  box-sizing: border-box;
}

.page-header { margin-bottom: 40px; }

.title {
  font-size: 46px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 16px;
}

.subtitle {
  font-size: 23px;
  font-weight: 300;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
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
.upload-btn:hover { opacity: 0.8; }

/* Waveform area */
.waveform-wrapper {
  text-align: left;
  width: 100%;
  box-sizing: border-box;
}

.waveform-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.file-name {
  color: var(--color-text-secondary);
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.current-time {
  color: var(--color-text-primary);
  font-size: 16px;
  font-weight: 700;
  background: var(--color-border);
  border-radius: 4px;
  padding: 2px 8px;
  white-space: nowrap;
}

.waveform-area {
  background: var(--color-bg-primary);
  border-radius: 8px;
  padding: 16px 20px;
  overflow: hidden;
  position: relative;
}

.waveform-box {
  min-height: 160px;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
}

/* Dim overlays for unselected regions */
.dim-overlay {
  position: absolute;
  top: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.45);
  pointer-events: none;
  z-index: 10;
}
.dim-left { left: 0; }
.dim-right { right: 0; }

/* Selection bar */
.selection-bar {
  margin-top: 8px;
}

.selection-track {
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  position: relative;
  overflow: hidden;
}

.selection-fill {
  position: absolute;
  top: 0;
  bottom: 0;
  background: #00e676;
  border-radius: 3px;
  transition: left 0.1s, width 0.1s;
}

.selection-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-family: monospace;
}

.waveform-timebar {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-family: monospace;
}

/* Controls bar */
.controls-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 24px;
  margin-bottom: 16px;
}

.time-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.time-separator {
  color: var(--color-text-secondary);
  opacity: 0.5;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: transparent;
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 400;
  cursor: pointer;
  transition: all 0.2s;
  font-family: var(--font-family);
}

.action-btn:hover:not(:disabled) {
  border-color: var(--color-accent);
  opacity: 0.8;
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.action-btn.primary {
  border-color: var(--color-accent);
}

.action-btn svg {
  flex-shrink: 0;
}

/* Fade controls */
.fade-controls {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.fade-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: left;
}

.fade-group label {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.time-input {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 10px 12px;
  color: var(--color-text-primary);
  font-size: 15px;
  width: 100%;
  box-sizing: border-box;
}

.time-input:focus {
  border-color: var(--color-accent);
  outline: none;
}

/* Messages */
.success-msg {
  color: var(--color-accent);
  font-weight: 600;
  margin-top: 16px;
}

.error-msg {
  color: var(--color-error);
  font-size: 14px;
  padding: 12px;
  background: color-mix(in srgb, var(--color-error) 10%, transparent);
  border-radius: 8px;
  margin-top: 16px;
}

/* Description */
.description-section {
  margin-top: 48px;
  text-align: left;
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
  margin: 0 0 16px;
}
</style>

<!-- Non-scoped: use ::part() to penetrate wavesurfer's Shadow DOM -->
<style>
/* Lock the scroll container — no horizontal dragging */
.waveform-box::part(scroll) {
  overflow-x: hidden !important;
  pointer-events: none;
}

/* Make the region overlay visible */
.waveform-box::part(regions-container) {
  overflow: visible !important;
  pointer-events: auto !important;
}

/* Style the region handles — visible, thick, draggable */
.waveform-box::part(region-handle) {
  width: 20px !important;
  background: rgba(255, 255, 255, 0.92) !important;
  border: none !important;
  border-radius: 4px !important;
  cursor: ew-resize !important;
  z-index: 20 !important;
  pointer-events: auto !important;
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.4) !important;
}

.waveform-box::part(region-handle-left) {
  border-left: 2px solid rgba(255, 255, 255, 0.8) !important;
}

.waveform-box::part(region-handle-right) {
  border-right: 2px solid rgba(255, 255, 255, 0.8) !important;
}
</style>
