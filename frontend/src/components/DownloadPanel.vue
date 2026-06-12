<script setup lang="ts">
defineProps<{
  downloadAllUrl: string
}>()
</script>

<template>
  <div class="download-panel">
    <a :href="downloadAllUrl" download class="download-all-btn">
      📦 下载全部音轨（ZIP）
    </a>
  </div>
</template>

<style scoped>
.download-panel {
  text-align: center;
  margin: 32px 0;
}

.download-all-btn {
  display: inline-block;
  background: var(--color-accent);
  color: #000000;
  font-weight: 600;
  padding: 14px 36px;
  border-radius: 12px;
  font-size: 16px;
  text-decoration: none;
  transition: all 0.2s;
}

.download-all-btn:hover {
  background: #00c853;
  transform: translateY(-2px);
  color: #000000;
}
</style>
