/**
 * 全局组件配置
 *
 * 管理系统级全局组件的注册
 */
import { defineAsyncComponent } from 'vue'

export interface GlobalComponentConfig {
  name: string
  key: string
  component: any
  enabled?: boolean
}

export const globalComponentsConfig: GlobalComponentConfig[] = [
  {
    name: '全局搜索',
    key: 'global-search',
    component: defineAsyncComponent(
      () => import('@/components/core/layouts/art-global-search/index.vue')
    ),
    enabled: true
  }
]

export const getEnabledGlobalComponents = () => {
  return globalComponentsConfig.filter((config) => config.enabled !== false)
}
