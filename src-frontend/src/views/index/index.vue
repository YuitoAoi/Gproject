<!-- 布局容器 -->
<template>
  <div class="app-layout">
    <aside id="app-sidebar">
      <LfpSidebarMenu />
    </aside>

    <main id="app-main">
      <div id="app-header">
        <LfpHeaderBar />
      </div>
      <div id="app-content">
        <LfpPageContent />
      </div>
    </main>

    <div id="app-global">
      <LfpGlobalComponent />
    </div>
  </div>
</template>

<script setup lang="ts">
  defineOptions({ name: 'AppLayout' })
</script>

<style lang="scss" scoped>
  @use './style';
</style>
