import { Mp3Encoder } from '@breezystack/lamejs'

/**
 * Convert an AudioBuffer to MP3 Blob using lamejs.
 * Returns a Blob of type audio/mpeg.
 */
export function audioBufferToMp3(buffer: AudioBuffer, bitrate = 192): Blob {
  const numChannels = buffer.numberOfChannels
  const sampleRate = buffer.sampleRate
  const samples = buffer.length

  const mp3enc = new Mp3Encoder(numChannels, sampleRate, bitrate)
  const mp3Data: Int8Array[] = []

  const blockSize = 1152
  const leftData = buffer.getChannelData(0)
  const rightData = numChannels > 1 ? buffer.getChannelData(1) : leftData

  // Convert float32 to int16
  const left16 = new Int16Array(leftData.length)
  const right16 = new Int16Array(rightData.length)
  for (let i = 0; i < leftData.length; i++) {
    left16[i] = Math.max(-32768, Math.min(32767, Math.round(leftData[i] * 32767)))
    right16[i] = Math.max(-32768, Math.min(32767, Math.round(rightData[i] * 32767)))
  }

  for (let i = 0; i < samples; i += blockSize) {
    const leftChunk = left16.subarray(i, i + blockSize)
    const rightChunk = right16.subarray(i, i + blockSize)
    const mp3buf = mp3enc.encodeBuffer(leftChunk, rightChunk)
    if (mp3buf.length > 0) {
      mp3Data.push(mp3buf)
    }
  }

  const end = mp3enc.flush()
  if (end.length > 0) {
    mp3Data.push(end)
  }

  return new Blob(mp3Data, { type: 'audio/mpeg' })
}

/**
 * Resample an AudioBuffer to a target sample rate using OfflineAudioContext.
 */
export async function resampleBuffer(
  context: OfflineAudioContext,
  buffer: AudioBuffer,
  targetSampleRate: number
): Promise<AudioBuffer> {
  if (buffer.sampleRate === targetSampleRate) return buffer

  const length = Math.ceil(buffer.duration * targetSampleRate)
  const offline = new OfflineAudioContext(buffer.numberOfChannels, length, targetSampleRate)
  const source = offline.createBufferSource()
  source.buffer = buffer
  source.connect(offline.destination)
  source.start()
  return offline.startRendering()
}

/**
 * Concatenate multiple AudioBuffers into one.
 * All buffers must have the same sample rate and channel count.
 */
export function concatenateBuffers(buffers: AudioBuffer[]): AudioBuffer {
  if (buffers.length === 0) throw new Error('No buffers to concatenate')
  if (buffers.length === 1) return buffers[0]

  const sampleRate = buffers[0].sampleRate
  const numChannels = buffers[0].numberOfChannels
  const totalLength = buffers.reduce((sum, b) => sum + b.length, 0)

  const ctx = new OfflineAudioContext(numChannels, totalLength, sampleRate)
  let offset = 0

  for (const buffer of buffers) {
    const source = ctx.createBufferSource()
    source.buffer = buffer
    source.connect(ctx.destination)
    source.start(offset / sampleRate)
    offset += buffer.length
  }

  return ctx.startRendering()
}
