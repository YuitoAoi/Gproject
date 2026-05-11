<template>
  <ElConfigProvider size="default" :locale="zh" :z-index="3000" :card="{ shadow: 'never' }">
    <RouterView />
  </ElConfigProvider>
</template>

<script setup lang="ts">
  import { useUserStore } from './store/modules/user'
  import zh from 'element-plus/es/locale/lang/zh-cn'
  import { LanguageEnum } from '@/enums/appEnum'
  import { checkStorageCompatibility } from './utils/storage'
  import { initializeTheme } from './hooks/core/useTheme'

  const userStore = useUserStore()

  onBeforeMount(() => {
    initializeTheme()
  })

  onMounted(() => {
    checkStorageCompatibility()
    // 默认使用中文
    userStore.setLanguage(LanguageEnum.ZH)
  })
</script>
