<!-- 顶部栏 -->
<template>
  <div class="w-full bg-[var(--default-bg-color)]">
    <div class="relative box-border flex-b h-15 leading-15 select-none">
      <!-- 左侧区域 -->
      <div class="flex-c flex-1 min-w-0 leading-15" style="display: flex">
        <!-- 菜单折叠按钮 -->
        <LfpIconButton
          icon="ri:menu-2-fill"
          class="ml-3 max-sm:ml-[7px]"
          @click="toggleSidebar"
        />

        <!-- 面包屑 -->
        <LfpBreadcrumb class="ml-3 max-sm:!hidden" />
      </div>

      <!-- 右侧区域 -->
      <div class="flex-c pr-4 gap-1">
        <!-- 全屏按钮 -->
        <LfpIconButton
          :icon="isFullscreen ? 'ri:fullscreen-exit-line' : 'ri:fullscreen-line'"
          @click="toggleFullscreen"
        />

        <!-- 暗色模式切换 -->
        <LfpIconButton
          :icon="appStore.isDark ? 'ri:sun-line' : 'ri:moon-line'"
          @click="appStore.toggleDark()"
        />

        <!-- 用户菜单 -->
        <LfpUserMenu />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { useAppStore } from '@/store/modules/app'
  import { useFullscreen } from '@vueuse/core'

  defineOptions({ name: 'LfpHeaderBar' })

  const appStore = useAppStore()
  const { isFullscreen, toggle: toggleFullscreen } = useFullscreen()

  const toggleSidebar = () => {
    appStore.toggleSidebar()
  }
</script>
