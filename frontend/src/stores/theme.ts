import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type Theme = 'light' | 'dark'

export const useThemeStore = defineStore('theme', () => {
  // 从 localStorage 读取主题设置，默认亮色
  const storedTheme = localStorage.getItem('smartledger-theme') as Theme | null
  const theme = ref<Theme>(storedTheme || 'light')

  // 切换主题
  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  // 设置指定主题
  function setTheme(newTheme: Theme) {
    theme.value = newTheme
  }

  // 初始化主题（应用主题到 DOM）
  function initTheme() {
    applyTheme(theme.value)
  }

  // 应用主题到 HTML 元素
  function applyTheme(currentTheme: Theme) {
    const html = document.documentElement
    
    if (currentTheme === 'dark') {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }

  // 监听主题变化，保存到 localStorage 并应用到 DOM
  watch(theme, (newTheme) => {
    localStorage.setItem('smartledger-theme', newTheme)
    applyTheme(newTheme)
  })

  return {
    theme,
    toggleTheme,
    setTheme,
    initTheme,
    applyTheme
  }
})
