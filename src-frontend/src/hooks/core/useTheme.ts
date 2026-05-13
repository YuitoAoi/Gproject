/**
 * useTheme - 系统主题管理
 *
 * 提供暗色/亮色主题切换功能
 */
import { useAppStore } from '@/store/modules/app'
import { usePreferredDark } from '@vueuse/core'
import { watch } from 'vue'

export function useTheme() {
  const appStore = useAppStore()
  const prefersDark = usePreferredDark()

  /** 切换暗色模式 */
  const toggleDark = () => {
    appStore.toggleDark()
  }

  /** 设置暗色模式 */
  const setDark = (dark: boolean) => {
    appStore.setDark(dark)
  }

  return {
    toggleDark,
    setDark,
    prefersDark,
    isDark: computed(() => appStore.isDark)
  }
}

/**
 * 初始化主题系统
 * 在应用启动时调用，应用持久化的主题设置
 */
export function initializeTheme() {
  const appStore = useAppStore()
  const prefersDark = usePreferredDark()

  // 应用持久化的主题
  appStore.applyTheme()

  // 监听系统主题偏好变化
  watch(prefersDark, (dark) => {
    // 可选：跟随系统主题
    // appStore.setDark(dark)
  })
}
