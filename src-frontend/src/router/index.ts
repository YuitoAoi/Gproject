/**
 * 路由入口
 *
 * 创建路由实例，配置简单的导航守卫
 * 守卫职责：未登录跳转登录页，已登录访问登录页跳转首页
 */
import type { App } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import NProgress from 'nprogress'
import { publicRoutes, businessRoutes } from './routes'
import { useUserStore } from '@/store/modules/user'

// 创建路由实例
export const router = createRouter({
  history: createWebHashHistory(),
  routes: [...publicRoutes, ...businessRoutes]
})

/** 默认首页路径 */
export const HOME_PATH = '/workbench/dashboard'

/** 不需要登录的路由路径前缀 */
const isPublicPath = (path: string): boolean => {
  return (
    path === '/' ||
    path.startsWith('/auth/') ||
    path === '/403' ||
    path === '/500'
  )
}

/**
 * 路由前置守卫
 * - 未登录 → 跳转登录页
 * - 已登录访问登录页 → 跳转首页
 * - 角色权限检查
 */
router.beforeEach((to) => {
  NProgress.start()

  const userStore = useUserStore()

  // 公开页面直接放行
  if (isPublicPath(to.path)) {
    // 已登录用户访问登录页，重定向到首页
    if (to.path === '/auth/login' && userStore.isLogin) {
      return { path: HOME_PATH, replace: true }
    }
    return true
  }

  // 未登录跳转登录页
  if (!userStore.isLogin) {
    return {
      path: '/auth/login',
      query: { redirect: to.fullPath }
    }
  }

  // 角色权限检查
  const requiredRoles = to.meta.roles as string[] | undefined
  if (requiredRoles && requiredRoles.length > 0) {
    const userRoles = userStore.info?.roles || []
    const hasPermission = requiredRoles.some((role) => userRoles.includes(role))
    if (!hasPermission) {
      return { path: '/403' }
    }
  }

  return true
})

/**
 * 路由后置守卫
 */
router.afterEach((to) => {
  NProgress.done()
  // 设置页面标题
  const title = to.meta.title as string
  if (title) {
    document.title = `${title} - LLaMA-Factory Workstation`
  }
})

/**
 * 初始化路由
 */
export function initRouter(app: App<Element>): void {
  NProgress.configure({ showSpinner: false })
  app.use(router)
}
