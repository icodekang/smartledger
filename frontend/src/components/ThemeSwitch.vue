<template>
  <div class="theme-switch" @click="toggleTheme" :title="isDark ? '切换到亮色模式' : '切换到深色模式'">
    <div class="switch-container" :class="{ 'is-dark': isDark }">
      <!-- 太阳图标 -->
      <svg class="icon sun" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="5"></circle>
        <line x1="12" y1="1" x2="12" y2="3"></line>
        <line x1="12" y1="21" x2="12" y2="23"></line>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
        <line x1="1" y1="12" x2="3" y2="12"></line>
        <line x1="21" y1="12" x2="23" y2="12"></line>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
      </svg>
      
      <!-- 月亮图标 -->
      <svg class="icon moon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
      </svg>
      
      <!-- 滑动球 -->
      <div class="switch-thumb"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()

const isDark = computed(() => themeStore.theme === 'dark')

function toggleTheme() {
  themeStore.toggleTheme()
}
</script>

<style scoped>
.theme-switch {
  display: inline-flex;
  cursor: pointer;
  padding: 4px;
  border-radius: 20px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  transition: all 0.3s ease;
}

.theme-switch:hover {
  border-color: var(--el-color-primary-light-5);
  box-shadow: var(--el-box-shadow-light);
}

.switch-container {
  position: relative;
  width: 56px;
  height: 28px;
  border-radius: 14px;
  background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 50%, #f59e0b 100%);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.switch-container.is-dark {
  background: linear-gradient(135deg, #4338ca 0%, #6366f1 50%, #4338ca 100%);
}

.switch-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.switch-container.is-dark .switch-thumb {
  transform: translateX(28px);
}

.icon {
  position: absolute;
  top: 50%;
  width: 14px;
  height: 14px;
  transform: translateY(-50%);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.sun {
  left: 6px;
  color: #ffffff;
  opacity: 1;
  transform: translateY(-50%) rotate(0deg) scale(1);
}

.moon {
  right: 6px;
  color: #ffffff;
  opacity: 0;
  transform: translateY(-50%) rotate(90deg) scale(0.5);
}

.switch-container.is-dark .sun {
  opacity: 0;
  transform: translateY(-50%) rotate(-90deg) scale(0.5);
}

.switch-container.is-dark .moon {
  opacity: 1;
  transform: translateY(-50%) rotate(0deg) scale(1);
}
</style>
