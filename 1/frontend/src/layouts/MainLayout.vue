<template>
  <el-container class="main-container">
    <el-header class="main-header">
      <TheHeader />
    </el-header>
    <el-container class="main-content">
      <el-aside :width="uiStore.isCollapsed ? '64px' : '200px'" class="main-sidebar">
        <TheSidebar />
      </el-aside>
      <el-main class="main-view">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import TheHeader from '../components/layout/TheHeader.vue'
import TheSidebar from '../components/layout/TheSidebar.vue'
import { useUIStore } from '../store/ui'

const uiStore = useUIStore()
</script>

<style scoped>
.main-container {
  height: 100vh;
}

.main-header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.main-content {
  flex: 1;
}

.main-sidebar {
  background-color: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  transition: width 0.3s;
  overflow: hidden;
}

.main-view {
  background-color: #fafafa;
  padding: 20px;
}
</style>