import { ref, onUnmounted, type Ref } from 'vue'
import WaveSurfer from 'wavesurfer.js'

export function useAudioPlayer(waveformRef: Ref<HTMLElement | null>, url: string) {
  const isPlaying = ref(false)
  const currentTime = ref(0)
  const duration = ref(0)
  const isLoading = ref(true)
  const hasError = ref(false)
  let wavesurfer: WaveSurfer | null = null

  function init() {
    if (!waveformRef.value) return

    wavesurfer = WaveSurfer.create({
      container: waveformRef.value,
      url,
      height: 80,
      waveColor: '#409EFF',
      progressColor: '#1D9BF0',
      cursorColor: '#333',
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
    })

    wavesurfer.on('ready', () => {
      isLoading.value = false
      duration.value = wavesurfer!.getDuration()
    })

    wavesurfer.on('play', () => {
      isPlaying.value = true
    })

    wavesurfer.on('pause', () => {
      isPlaying.value = false
    })

    wavesurfer.on('timeupdate', (time: number) => {
      currentTime.value = time
    })

    wavesurfer.on('error', () => {
      hasError.value = true
      isLoading.value = false
    })
  }

  function play() {
    wavesurfer?.play()
  }

  function pause() {
    wavesurfer?.pause()
  }

  function togglePlay() {
    wavesurfer?.playPause()
  }

  function seekTo(time: number) {
    wavesurfer?.seekTo(time / duration.value)
  }

  function destroy() {
    wavesurfer?.destroy()
    wavesurfer = null
  }

  onUnmounted(destroy)

  return {
    isPlaying,
    currentTime,
    duration,
    isLoading,
    hasError,
    init,
    play,
    pause,
    togglePlay,
    seekTo,
    destroy,
  }
}
