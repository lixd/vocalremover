/**
 * BPM detection using autocorrelation on onset strength.
 * Key detection using chroma features and Krumhansl-Schmuckler algorithm.
 */

const NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'] as const
type NoteName = (typeof NOTE_NAMES)[number]

const KEY_PROFILES = {
  major: [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88],
  minor: [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17],
}

interface BpmResult {
  bpm: number
  confidence: number
}

interface KeyResult {
  key: NoteName
  mode: 'major' | 'minor'
  confidence: number
}

interface AnalysisResult {
  bpm: BpmResult
  key: KeyResult
  duration: number
}

/**
 * Detect BPM from an AudioBuffer using autocorrelation on onset envelope.
 */
export function detectBpm(buffer: AudioBuffer, minBpm = 60, maxBpm = 200): BpmResult {
  const sampleRate = buffer.sampleRate
  const channelData = buffer.getChannelData(0)

  // Downsample for performance: use ~11025 Hz effective rate
  const downsampleFactor = Math.max(1, Math.floor(sampleRate / 11025))
  const downsampledLength = Math.floor(channelData.length / downsampleFactor)
  const downsampled = new Float32Array(downsampledLength)
  for (let i = 0; i < downsampledLength; i++) {
    downsampled[i] = channelData[i * downsampleFactor]
  }

  const effectiveRate = sampleRate / downsampleFactor
  const hopSize = 512
  const frameSize = 2048
  const numFrames = Math.floor((downsampledLength - frameSize) / hopSize)

  if (numFrames < 10) {
    return { bpm: 0, confidence: 0 }
  }

  // Compute spectral flux (onset strength)
  const onsetEnvelope = new Float32Array(numFrames)
  let prevSpectrum: Float32Array | null = null

  for (let f = 0; f < numFrames; f++) {
    const spectrum = new Float32Array(frameSize / 2)
    for (let k = 0; k < frameSize / 2; k++) {
      let real = 0
      let imag = 0
      for (let n = 0; n < frameSize; n++) {
        const sample = downsampled[f * hopSize + n] * (0.5 - 0.5 * Math.cos((2 * Math.PI * n) / frameSize))
        const angle = (2 * Math.PI * k * n) / frameSize
        real += sample * Math.cos(angle)
        imag -= sample * Math.sin(angle)
      }
      spectrum[k] = Math.sqrt(real * real + imag * imag)
    }

    if (prevSpectrum) {
      let flux = 0
      for (let k = 0; k < spectrum.length; k++) {
        const diff = spectrum[k] - prevSpectrum[k]
        if (diff > 0) flux += diff
      }
      onsetEnvelope[f] = flux
    }

    prevSpectrum = spectrum
  }

  // Normalize onset envelope
  let maxOnset = 0
  for (let i = 0; i < onsetEnvelope.length; i++) {
    if (onsetEnvelope[i] > maxOnset) maxOnset = onsetEnvelope[i]
  }
  if (maxOnset > 0) {
    for (let i = 0; i < onsetEnvelope.length; i++) {
      onsetEnvelope[i] /= maxOnset
    }
  }

  // Autocorrelation on onset envelope
  const hopRate = effectiveRate / hopSize
  const minLag = Math.floor(hopRate * 60 / maxBpm)
  const maxLag = Math.floor(hopRate * 60 / minBpm)
  const corrLength = Math.min(onsetEnvelope.length, maxLag * 2)

  let bestLag = minLag
  let bestCorr = -Infinity

  for (let lag = minLag; lag <= maxLag && lag < corrLength; lag++) {
    let corr = 0
    let norm1 = 0
    let norm2 = 0
    for (let i = 0; i < corrLength - lag; i++) {
      corr += onsetEnvelope[i] * onsetEnvelope[i + lag]
      norm1 += onsetEnvelope[i] * onsetEnvelope[i]
      norm2 += onsetEnvelope[i + lag] * onsetEnvelope[i + lag]
    }
    const denom = Math.sqrt(norm1 * norm2)
    const normalizedCorr = denom > 0 ? corr / denom : 0

    if (normalizedCorr > bestCorr) {
      bestCorr = normalizedCorr
      bestLag = lag
    }
  }

  const bpm = Math.round((hopRate * 60) / bestLag)
  const clampedBpm = Math.max(minBpm, Math.min(maxBpm, bpm))

  return { bpm: clampedBpm, confidence: Math.min(1, Math.max(0, bestCorr)) }
}

/**
 * Detect musical key from an AudioBuffer using chroma features and K-S algorithm.
 */
export function detectKey(buffer: AudioBuffer): KeyResult {
  const sampleRate = buffer.sampleRate
  const channelData = buffer.getChannelData(0)

  // Downsample for performance
  const downsampleFactor = Math.max(1, Math.floor(sampleRate / 11025))
  const downsampledLength = Math.floor(channelData.length / downsampleFactor)
  const downsampled = new Float32Array(downsampledLength)
  for (let i = 0; i < downsampledLength; i++) {
    downsampled[i] = channelData[i * downsampleFactor]
  }

  const effectiveRate = sampleRate / downsampleFactor
  const hopSize = 2048
  const frameSize = 4096
  const numFrames = Math.floor((downsampledLength - frameSize) / hopSize)

  if (numFrames < 1) {
    return { key: 'C', mode: 'major', confidence: 0 }
  }

  // Accumulate chroma across all frames
  const chroma = new Float32Array(12)
  const a4 = 440
  const noteFreqs = new Float32Array(12)
  for (let n = 0; n < 12; n++) {
    noteFreqs[n] = a4 * Math.pow(2, (n - 9) / 12)
  }

  for (let f = 0; f < numFrames; f++) {
    const offset = f * hopSize

    // Compute magnitude spectrum via DFT
    const spectrum = new Float32Array(frameSize / 2)
    for (let k = 0; k < frameSize / 2; k++) {
      let real = 0
      let imag = 0
      for (let n = 0; n < frameSize; n++) {
        const sample = downsampled[offset + n] * (0.5 - 0.5 * Math.cos((2 * Math.PI * n) / frameSize))
        const angle = (2 * Math.PI * k * n) / frameSize
        real += sample * Math.cos(angle)
        imag -= sample * Math.sin(angle)
      }
      spectrum[k] = Math.sqrt(real * real + imag * imag)
    }

    // Map frequency bins to chroma
    for (let k = 1; k < frameSize / 2; k++) {
      const freq = (k * effectiveRate) / frameSize
      if (freq < 60 || freq > 5000) continue

      const midiNote = 12 * Math.log2(freq / a4) + 69
      const chromaBin = Math.round(midiNote) % 12
      const binIndex = ((chromaBin % 12) + 12) % 12
      chroma[binIndex] += spectrum[k]
    }
  }

  // Normalize chroma
  let chromaMax = 0
  for (let i = 0; i < 12; i++) {
    if (chroma[i] > chromaMax) chromaMax = chroma[i]
  }
  if (chromaMax > 0) {
    for (let i = 0; i < 12; i++) {
      chroma[i] /= chromaMax
    }
  }

  // Krumhansl-Schmuckler key-finding algorithm
  let bestKey: NoteName = 'C'
  let bestMode: 'major' | 'minor' = 'major'
  let bestCorr = -Infinity

  for (let root = 0; root < 12; root++) {
    // Rotate chroma to start at this root
    const rotatedChroma = new Float32Array(12)
    for (let i = 0; i < 12; i++) {
      rotatedChroma[i] = chroma[(i + root) % 12]
    }

    for (const mode of ['major', 'minor'] as const) {
      const profile = KEY_PROFILES[mode]
      const corr = pearsonCorrelation(rotatedChroma, new Float32Array(profile))

      if (corr > bestCorr) {
        bestCorr = corr
        bestKey = NOTE_NAMES[root]
        bestMode = mode
      }
    }
  }

  return { key: bestKey, mode: bestMode, confidence: Math.min(1, Math.max(0, bestCorr)) }
}

function pearsonCorrelation(x: Float32Array, y: Float32Array): number {
  const n = x.length
  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0
  for (let i = 0; i < n; i++) {
    sumX += x[i]
    sumY += y[i]
    sumXY += x[i] * y[i]
    sumX2 += x[i] * x[i]
    sumY2 += y[i] * y[i]
  }
  const num = n * sumXY - sumX * sumY
  const den = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY))
  return den === 0 ? 0 : num / den
}

/**
 * Full analysis: BPM + Key detection.
 */
export async function analyzeAudio(file: File): Promise<AnalysisResult> {
  const arrayBuffer = await file.arrayBuffer()
  const audioContext = new AudioContext()
  const buffer = await audioContext.decodeAudioData(arrayBuffer)
  await audioContext.close()

  const bpm = detectBpm(buffer)
  const key = detectKey(buffer)

  return { bpm, key, duration: buffer.duration }
}
