<template>
  <div class="sidebar">
    <el-menu
      :default-active="currentRoute"
      class="sidebar-menu"
      :collapse="isCollapsed"
      router
    >
      <el-menu-item index="/">
        <span>首页</span>
      </el-menu-item>
      <el-menu-item index="/dashboard">
        <span>仪表盘</span>
      </el-menu-item>
      <el-menu-item index="/data-management">
        <span>数据管理</span>
      </el-menu-item>
      <el-menu-item index="/training">
        <span>训练任务</span>
      </el-menu-item>
      <el-menu-item index="/models">
        <span>模型管理</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUIStore } from '@/store/ui'

const route = useRoute()
const uiStore = useUIStore()

const isCollapsed = computed(() => uiStore.isCollapsed)
const currentRoute = computed(() => route.path)
</script>

<style scoped>
.sidebar {
  height: 100%;
}

.sidebar-menu {
  height: 100%;
  border-right: none;
}
</style>
