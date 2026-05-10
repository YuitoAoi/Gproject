/**
 * 组件预取工具模块
 *
 * 在用户悬停菜单项时提前加载对应的 Vue 组件，
 * 消除点击导航后的懒加载延迟
 *
 * @module utils/navigation/prefetch
 */
const viewModules = import.meta.glob('../../views/**/*.vue')

export function prefetchComponent(componentPath: string): void {
  if (!componentPath) return

  const fullPath = `../../views${componentPath}.vue`
  const fullPathWithIndex = `../../views${componentPath}/index.vue`

  const loader = viewModules[fullPath] || viewModules[fullPathWithIndex]
  if (loader) {
    loader()
  }
}
