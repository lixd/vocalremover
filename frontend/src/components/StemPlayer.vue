<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import WaveSurfer from 'wavesurfer.js'

const props = defineProps<{
  stemName: string
  streamUrl: string
  downloadUrl: string
}>()

const waveformRef = ref<HTMLElement | null>(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const isLoading = ref(true)
const hasError = ref(false)

let wavesurfer: WaveSurfer | null = null

const STEM_LABELS: Record<string, string> = {
  vocals: '人声',
  accompaniment: '伴奏',
  drums: '鼓',
  bass: '贝斯',
  other: '其他',
}

const STEM_COLORS: Record<string, string> = {
  vocals: '#00e676',
  accompaniment: '#448aff',
  drums: '#ff6e40',
  bass: '#e040fb',
  other: '#ffab40',
}

function initWaveSurfer() {
  if (!waveformRef.value) return

  const style = getComputedStyle(document.documentElement)
  const textPrimary = style.getPropertyValue('--color-text-primary').trim() || '#eeeeee'

  wavesurfer = WaveSurfer.create({
    container: waveformRef.value,
    waveColor: STEM_COLORS[stemName] || '#00e676',
    progressColor: textPrimary,
    cursorColor: textPrimary,
    barWidth: 2,
    barGap: 1,
    barRadius: 2,
    height: 64,
    normalize: true,
  })

  wavesurfer.on('ready', () => {
    isLoading.value = false
    duration.value = wavesurfer!.getDuration()
  })

  wavesurfer.on('play', () => { isPlaying.value = true })
  wavesurfer.on('pause', () => { isPlaying.value = false })
  wavesurfer.on('timeupdate', (t: number) => { currentTime.value = t })
  wavesurfer.on('finish', () => { isPlaying.value = false })
  wavesurfer.on('error', () => { hasError.value = true; isLoading.value = false })

  wavesurfer.load(props.streamUrl)
}

function togglePlay() {
  wavesurfer?.playPause()
}

function formatTime(s: number): string {
  if (!s || !isFinite(s)) return '0:00'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

onMounted(initWaveSurfer)
onUnmounted(() => { wavesurfer?.destroy(); wavesurfer = null })
</script>

<template>
  <div class="stem-card">
    <div class="stem-header">
      <div class="stem-label">
        <span class="stem-dot" :style="{ background: STEM_COLORS[stemName] || '#00e676' }"></span>
        <span class="stem-name">{{ STEM_LABELS[stemName] || stemName }}</span>
      </div>
      <a :href="downloadUrl" :download="`${stemName}.mp3`" class="download-btn" @click.stop>
        ⬇️
      </a>
    </div>

    <div v-if="isLoading" class="loading-bar">
      <div class="loading-pulse"></div>
    </div>

    <div v-else-if="hasError" class="error-text">音频加载失败</div>

    <div v-else class="player-body">
      <div ref="waveformRef" class="waveform"></div>
      <div class="controls">
        <button class="play-btn" @click="togglePlay">
          {{ isPlaying ? '⏸' : '▶' }}
        </button>
        <span class="time">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stem-card {
  background: var(--color-bg-secondary);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}

.stem-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.stem-label {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stem-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.stem-name {
  font-weight: 600;
  font-size: 16px;
  color: var(--color-text-primary);}

.download-btn {
  font-size: 20px;
  text-decoration: none;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.download-btn:hover {
  background: var(--color-border);
}

.waveform {
  margin-bottom: 12px;
  border-radius: 8px;
  overflow: hidden;
}

.controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.play-btn {
  background: var(--color-accent);
  color: #000;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.play-btn:hover {
  background: #00c853;
  transform: scale(1.05);
}

.time {
  color: var(--color-text-secondary);
  font-family: monospace;
  font-size: 14px;
}

.loading-bar {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-pulse {
  width: 100%;
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

.error-text {
  color: #ff6b6b;
  text-align: center;
  padding: 24px;
  font-size: 14px;
}
</style>
