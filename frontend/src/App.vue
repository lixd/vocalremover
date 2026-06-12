<script setup lang="ts">
</script>

<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <svg class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 18V5l12-2v13" stroke-linecap="round" stroke-linejoin="round" />
          <circle cx="6" cy="18" r="3" />
          <circle cx="18" cy="16" r="3" />
        </svg>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item" exact-active-class="active">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke-linecap="round" stroke-linejoin="round" />
            <line x1="12" y1="19" x2="12" y2="23" stroke-linecap="round" stroke-linejoin="round" />
            <line x1="8" y1="23" x2="16" y2="23" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <span class="nav-label">去人声</span>
        </router-link>

        <router-link to="/splitter" class="nav-item" active-class="active">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <span class="nav-label">分离器</span>
        </router-link>

        <router-link to="/cutter" class="nav-item" active-class="active">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="6" cy="6" r="3" />
            <circle cx="6" cy="18" r="3" />
            <line x1="20" y1="4" x2="8.12" y2="15.88" stroke-linecap="round" stroke-linejoin="round" />
            <line x1="14.47" y1="14.48" x2="20" y2="20" stroke-linecap="round" stroke-linejoin="round" />
            <line x1="8.12" y1="8.12" x2="12" y2="12" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <span class="nav-label">剪辑器</span>
        </router-link>

        <router-link to="/merger" class="nav-item" active-class="active">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" stroke-linecap="round" stroke-linejoin="round" />
            <polyline points="15 3 21 3 21 9" stroke-linecap="round" stroke-linejoin="round" />
            <line x1="10" y1="14" x2="21" y2="3" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <span class="nav-label">合并器</span>
        </router-link>

        <router-link to="/bpm-key" class="nav-item" active-class="active">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 18V5l12-2v13" stroke-linecap="round" stroke-linejoin="round" />
            <circle cx="6" cy="18" r="3" />
            <circle cx="18" cy="16" r="3" />
          </svg>
          <span class="nav-label">BPM/调性查询</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <a href="#" class="nav-item help-link">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" stroke-linecap="round" stroke-linejoin="round" />
            <line x1="12" y1="17" x2="12.01" y2="17" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <span class="nav-label">帮助</span>
        </a>
      </div>
    </aside>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  font-family: var(--font-family);
  background: var(--color-bg-secondary);
}

.sidebar {
  position: fixed;
  width: var(--sidebar-width);
  height: 100vh;
  background: var(--color-bg-primary);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.sidebar-header {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px 0;
  border-bottom: 1px solid var(--color-border);
}

.logo-icon {
  width: 28px;
  height: 28px;
  color: var(--color-accent);
}

.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 4px;
  border-radius: 8px;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: background 0.2s, color 0.2s;
}

.nav-item:hover {
  background: var(--color-active-bg);
  color: var(--color-text-primary);
}

.nav-item.active {
  background: var(--color-active-bg);
  color: var(--color-active-text);
}

.nav-icon {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
}

.nav-label {
  font-size: 10px;
  font-weight: 500;
  line-height: 1.2;
  text-align: center;
}

.sidebar-footer {
  padding: 12px 8px;
  border-top: 1px solid var(--color-border);
}

.help-link {
  cursor: pointer;
}

.main-content {
  margin-left: var(--sidebar-width);
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 100vh;
  width: 0;
  min-width: 0;
  touch-action: pan-y;
  overscroll-behavior: contain;
}
</style>
