/**
 * 组件加载器
 *
 * 负责动态加载 Vue 组件
 *
 * @module router/core/ComponentLoader
 * @author Art Design Pro Team
 */

import { h } from 'vue'

const COMPONENT_LOAD_TIMEOUT = 15000

export class ComponentLoader {
  private modules: Record<string, () => Promise<any>>

  constructor() {
    this.modules = import.meta.glob('../../views/**/*.vue')
  }

  load(componentPath: string): () => Promise<any> {
    if (!componentPath) {
      return this.createEmptyComponent()
    }

    const fullPath = `../../views${componentPath}.vue`
    const fullPathWithIndex = `../../views${componentPath}/index.vue`

    const module = this.modules[fullPath] || this.modules[fullPathWithIndex]

    if (!module) {
      console.error(
        `[ComponentLoader] 未找到组件: ${componentPath}，尝试过的路径: ${fullPath} 和 ${fullPathWithIndex}`
      )
      return this.createErrorComponent(componentPath)
    }

    const loader = module
    return () => {
      return Promise.race([
        loader(),
        new Promise<never>((_, reject) =>
          setTimeout(
            () => reject(new Error(`组件加载超时: ${componentPath}`)),
            COMPONENT_LOAD_TIMEOUT
          )
        )
      ]).catch((err) => {
        console.error(`[ComponentLoader] 组件加载失败: ${componentPath}`, err)
        return {
          render() {
            return h('div', { class: 'component-error' }, `页面加载失败，请刷新重试`)
          }
        }
      })
    }
  }

  /**
   * 加载布局组件
   */
  loadLayout(): () => Promise<any> {
    return () => import('@/views/index/index.vue')
  }

  /**
   * 加载 iframe 组件
   */
  loadIframe(): () => Promise<any> {
    return () => import('@/views/outside/Iframe.vue')
  }

  /**
   * 创建空组件
   */
  private createEmptyComponent(): () => Promise<any> {
    return () =>
      Promise.resolve({
        render() {
          return h('div', {})
        }
      })
  }

  /**
   * 创建错误提示组件
   */
  private createErrorComponent(componentPath: string): () => Promise<any> {
    return () =>
      Promise.resolve({
        render() {
          return h('div', { class: 'route-error' }, `组件未找到: ${componentPath}`)
        }
      })
  }
}
