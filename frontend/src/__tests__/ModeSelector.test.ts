import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ModeSelector from '@/components/ModeSelector.vue'

describe('ModeSelector', () => {
  it('renders two options', () => {
    const wrapper = mount(ModeSelector, { props: { modelValue: '2stems' } })
    expect(wrapper.find('[data-testid="mode-2stems"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="mode-4stems"]').exists()).toBe(true)
  })

  it('defaults to 2-stem mode', () => {
    const wrapper = mount(ModeSelector, { props: { modelValue: '2stems' } })
    expect(wrapper.emitted('update:modelValue')).toBeFalsy()
  })

  it('displays correct labels', () => {
    const wrapper = mount(ModeSelector, { props: { modelValue: '2stems' } })
    expect(wrapper.text()).toContain('2 Stems')
    expect(wrapper.text()).toContain('4 Stems')
  })
})
