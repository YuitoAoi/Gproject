/**
 * 应用状态管理
 *
 * 管理应用级别的状态：主题、侧边栏、菜单等
 * 合并了原来的 setting store 和 menu store 的必要部分
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { businessRoutes } from '@/router/routes'
import type { RouteRecordRaw } from 'vue-router'

/** 菜单项类型 */
export interface MenuItem {
  path: string
  title: string
  icon?: string
  roles?: string[]
  hidden?: boolean
  children?: MenuItem[]
}

export const useAppStore = defineStore(
  'app',
  () => {
    /** 侧边栏是否展开 */
    const sidebarOpen = ref(true)
    /** 当前主题模式 */
    const isDark = ref(false)
    /** 主题色 */
    const themeColor = ref('#5D87FF')
    /** 侧边栏宽度 */
    const sidebarWidth = ref(230)

    /** 侧边栏实际宽度 */
    const sidebarWidthPx = computed(() => (sidebarOpen.value ? `${sidebarWidth.value}px` : '64px'))

    /**
     * 从路由配置生成菜单列表
     * 过滤掉 hidden 路由和无权限路由
     */
    const menuList = computed((): MenuItem[] => {
      return buildMenuFromRoutes(businessRoutes)
    })

    /**
     * 切换侧边栏
     */
    const toggleSidebar = () => {
      sidebarOpen.value = !sidebarOpen.value
    }

    /**
     * 设置侧边栏状态
     */
    const setSidebarOpen = (open: boolean) => {
      sidebarOpen.value = open
    }

    /**
     * 切换暗色模式
     */
    const toggleDark = () => {
      isDark.value = !isDark.value
      applyTheme()
    }

    /**
     * 设置暗色模式
     */
    const setDark = (dark: boolean) => {
      isDark.value = dark
      applyTheme()
    }

    /**
     * 应用主题到 DOM
     */
    const applyTheme = () => {
      if (isDark.value) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
    }

    return {
      sidebarOpen,
      isDark,
      themeColor,
      sidebarWidth,
      sidebarWidthPx,
      menuList,
      toggleSidebar,
      setSidebarOpen,
      toggleDark,
      setDark,
      applyTheme
    }
  },
  {
    persist: {
      key: 'app',
      storage: localStorage,
      pick: ['sidebarOpen', 'isDark', 'themeColor']
    }
  }
)

/**
 * 从路由配置构建菜单数据
 */
function buildMenuFromRoutes(routes: RouteRecordRaw[]): MenuItem[] {
  return routes
    .filter((route) => !route.meta?.hidden)
    .map((route) => {
      const item: MenuItem = {
        path: route.path,
        title: (route.meta?.title as string) || '',
        icon: route.meta?.icon as string,
        roles: route.meta?.roles as string[],
        hidden: route.meta?.hidden as boolean
      }

      if (route.children?.length) {
        item.children = route.children
          .filter((child) => !child.meta?.hidden)
          .map((child) => ({
            path: child.path.startsWith('/')
              ? child.path
              : `${route.path}/${child.path}`,
            title: (child.meta?.title as string) || '',
            icon: child.meta?.icon as string,
            roles: child.meta?.roles as string[],
            hidden: child.meta?.hidden as boolean
          }))
      }

      return item
    })
}
