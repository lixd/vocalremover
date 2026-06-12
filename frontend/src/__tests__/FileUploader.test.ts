import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FileUploader from '@/components/FileUploader.vue'

describe('FileUploader', () => {
  it('renders upload area', () => {
    const wrapper = mount(FileUploader)
    expect(wrapper.find('[data-testid="upload-area"]').exists()).toBe(true)
  })

  it('accepts valid audio file via input', async () => {
    const wrapper = mount(FileUploader)
    const input = wrapper.find('input[type="file"]')
    const file = new File(['audio content'], 'song.mp3', { type: 'audio/mpeg' })

    Object.defineProperty(input.element, 'files', {
      value: [file],
    })
    await input.trigger('change')

    expect(wrapper.emitted('file-selected')).toBeTruthy()
    expect(wrapper.emitted('file-selected')![0]).toEqual([file])
  })

  it('rejects unsupported file format', async () => {
    const wrapper = mount(FileUploader)
    const input = wrapper.find('input[type="file"]')
    const file = new File(['text'], 'readme.txt', { type: 'text/plain' })

    Object.defineProperty(input.element, 'files', {
      value: [file],
    })
    await input.trigger('change')

    expect(wrapper.emitted('file-selected')).toBeFalsy()
    expect(wrapper.emitted('error')).toBeTruthy()
  })

  it('rejects file exceeding 20MB', async () => {
    const wrapper = mount(FileUploader)
    const input = wrapper.find('input[type="file"]')
    const largeFile = new File(['x'.repeat(20 * 1024 * 1024 + 1)], 'large.mp3', {
      type: 'audio/mpeg',
    })

    Object.defineProperty(input.element, 'files', {
      value: [largeFile],
    })
    await input.trigger('change')

    expect(wrapper.emitted('file-selected')).toBeFalsy()
    expect(wrapper.emitted('error')).toBeTruthy()
  })

  it('shows selected file name', async () => {
    const wrapper = mount(FileUploader)
    const input = wrapper.find('input[type="file"]')
    const file = new File(['audio'], 'my-song.mp3', { type: 'audio/mpeg' })

    Object.defineProperty(input.element, 'files', {
      value: [file],
    })
    await input.trigger('change')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('my-song.mp3')
  })
})
