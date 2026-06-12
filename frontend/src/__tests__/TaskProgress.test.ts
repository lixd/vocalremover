import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskProgress from '@/components/TaskProgress.vue'

describe('TaskProgress', () => {
  it('shows waiting state for PENDING', () => {
    const wrapper = mount(TaskProgress, {
      props: { status: 'PENDING' },
    })
    expect(wrapper.text()).toContain('Waiting')
  })

  it('shows processing state with progress', () => {
    const wrapper = mount(TaskProgress, {
      props: { status: 'PROCESSING' },
    })
    expect(wrapper.text()).toContain('Processing')
  })

  it('shows completed state', () => {
    const wrapper = mount(TaskProgress, {
      props: { status: 'COMPLETED' },
    })
    expect(wrapper.text()).toContain('Completed')
  })

  it('shows failed state with error message', () => {
    const wrapper = mount(TaskProgress, {
      props: { status: 'FAILED', errorMessage: 'Spleeter inference failed' },
    })
    expect(wrapper.text()).toContain('Failed')
    expect(wrapper.text()).toContain('Spleeter inference failed')
  })

  it('shows network error', () => {
    const wrapper = mount(TaskProgress, {
      props: { status: 'PENDING', networkError: 'Network error, please refresh' },
    })
    expect(wrapper.text()).toContain('Network error')
  })
})
