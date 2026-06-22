<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'

const props = defineProps<{
  stemName: string
  streamUrl: string
  downloadUrl: string
}>()

const audioRef = ref<HTMLAudioElement | null>(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const isLoading = ref(true)
const hasError = ref(false)

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

const stemColor = computed(() => STEM_COLORS[props.stemName] || '#00e676')

// 进度 0-100，用于进度条宽度
const progressPercent = computed(() => {
  if (!duration.value) return 0
  return (currentTime.value / duration.value) * 100
})

function togglePlay() {
  const audio = audioRef.value
  if (!audio) return
  if (audio.paused) {
    audio.play()
  } else {
    audio.pause()
  }
}

function onLoadedMetadata() {
  isLoading.value = false
  duration.value = audioRef.value?.duration ?? 0
}

function onTimeUpdate() {
  currentTime.value = audioRef.value?.currentTime ?? 0
}

function onPlay() { isPlaying.value = true }
function onPause() { isPlaying.value = false }
function onEnded() { isPlaying.value = false }
function onError() {
  hasError.value = true
  isLoading.value = false
}

// 点击进度条 seek
function seekTo(event: MouseEvent) {
  const audio = audioRef.value
  const bar = event.currentTarget as HTMLElement
  if (!audio || !duration.value) return
  const rect = bar.getBoundingClientRect()
  const ratio = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1)
  audio.currentTime = ratio * duration.value
}

function formatTime(s: number): string {
  if (!s || !isFinite(s)) return '0:00'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

onMounted(() => {
  // 触发音频元数据加载；事件监听由模板中的 @* 绑定
  audioRef.value?.load()
})

onUnmounted(() => {
  audioRef.value?.pause()
})
</script>

<template>
  <div class="stem-card">
    <div class="stem-header">
      <div class="stem-label">
        <span class="stem-dot" :style="{ background: stemColor }"></span>
        <span class="stem-name">{{ STEM_LABELS[stemName] || stemName }}</span>
      </div>
      <a :href="downloadUrl" :download="`${stemName}.mp3`" class="download-btn" @click.stop>
        ⬇️
      </a>
    </div>

    <!-- 隐藏的原生 audio 元素，实际播放由它负责 -->
    <audio
      ref="audioRef"
      :src="streamUrl"
      preload="metadata"
      @loadedmetadata="onLoadedMetadata"
      @timeupdate="onTimeUpdate"
      @play="onPlay"
      @pause="onPause"
      @ended="onEnded"
      @error="onError"
    />

    <div v-if="isLoading" class="loading-bar">
      <div class="loading-pulse"></div>
    </div>

    <div v-else-if="hasError" class="error-text">音频加载失败</div>

    <div v-else class="player-body">
      <div class="progress-track" :style="{ '--stem-color': stemColor }" @click="seekTo">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        <div class="progress-thumb" :style="{ left: progressPercent + '%' }"></div>
      </div>
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
  color: var(--color-text-primary);
}

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

.player-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-track {
  position: relative;
  height: 6px;
  background: var(--color-border);
  border-radius: 3px;
  cursor: pointer;
}

.progress-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: var(--stem-color, var(--color-accent));
  border-radius: 3px;
  transition: width 0.1s linear;
}

.progress-thumb {
  position: absolute;
  top: 50%;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--stem-color, var(--color-accent));
  transform: translate(-50%, -50%);
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.2);
  transition: left 0.1s linear;
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
  height: 40px;
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
