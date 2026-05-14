<!-- 页面内容区域 -->
<template>
  <div class="layout-content" :class="{ 'overflow-auto': isFullPage }" :style="containerStyle">
    <div id="app-content-header">
      <LfpFestivalTextScroll v-if="!isFullPage" />
    </div>

    <RouterView v-slot="{ Component, route }">
      <Transition name="fade" mode="out-in" appear>
        <component class="lfp-page-view" :is="Component" :key="route.path" />
      </Transition>
    </RouterView>
  </div>
</template>

<script setup lang="ts">
  import type { CSSProperties } from 'vue'
  import { useRoute } from 'vue-router'
  import { useAutoLayoutHeight } from '@/hooks/core/useLayoutHeight'

  defineOptions({ name: 'LfpPageContent' })

  const route = useRoute()
  const { containerMinHeight } = useAutoLayoutHeight()

  // 检查当前路由是否需要使用全屏模式
  const isFullPage = computed(() => route.matched.some((r) => r.meta?.isFullPage))

  const containerStyle = computed(
    (): CSSProperties =>
      isFullPage.value
        ? {
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            height: '100vh',
            zIndex: 2500,
            background: 'var(--default-bg-color)'
          }
        : {
            maxWidth: '100%',
            minHeight: containerMinHeight.value
          }
  )
</script>
