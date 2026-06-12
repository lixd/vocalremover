<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const modes = [
  { value: '2stems', label: '人声 + 伴奏', icon: '🎤', desc: '分离为人声和伴奏' },
  { value: '4stems', label: '4 音轨', icon: '🥁', desc: '分离为人声、鼓、贝斯、其他' },
]

function selectMode(value: string) {
  emit('update:modelValue', value)
}
</script>

<template>
  <div class="mode-selector">
    <button
      v-for="m in modes"
      :key="m.value"
      class="mode-btn"
      :class="{ active: modelValue === m.value }"
      @click="selectMode(m.value)"
    >
      <span class="mode-icon">{{ m.icon }}</span>
      <span class="mode-label">{{ m.label }}</span>
      <span class="mode-desc">{{ m.desc }}</span>
    </button>
  </div>
</template>

<style scoped>
.mode-selector {
  display: flex;
  gap: 12px;
  width: 100%;
}

.mode-btn {
  flex: 1;
  background: var(--color-bg-primary);
  border: 2px solid var(--color-border);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  text-align: center;
  transition: all 0.2s;
  color: var(--color-text-primary);
}

.mode-btn:hover {
  border-color: var(--color-accent);
  background: #16162a;
}

.mode-btn.active {
  border-color: var(--color-accent);
  background: rgba(0, 230, 118, 0.08);
}

.mode-icon {
  font-size: 24px;
  display: block;
  margin-bottom: 8px;
}

.mode-label {
  font-weight: 600;
  font-size: 14px;
  display: block;
  margin-bottom: 4px;
}

.mode-desc {
  font-size: 12px;
  color: var(--color-text-secondary);
}
</style>
