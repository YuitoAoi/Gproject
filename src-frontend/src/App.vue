<template>
  <ElConfigProvider size="default" :locale="zh" :z-index="3000" :card="{ shadow: 'never' }">
    <RouterView />
  </ElConfigProvider>
</template>

<script setup lang="ts">
  import zh from 'element-plus/es/locale/lang/zh-cn'
  import { useAppStore } from './store/modules/app'

  onMounted(() => {
    // 应用持久化的主题设置
    useAppStore().applyTheme()
  })
</script>
