<template>
  <el-menu
    :default-active="$route.path"
    class="sidebar-menu"
    :collapse="uiStore.isCollapsed"
    router
  >
    <el-menu-item index="/">
      <el-icon><House /></el-icon>
      <span>首页</span>
    </el-menu-item>
    <el-menu-item index="/dashboard">
      <el-icon><Monitor /></el-icon>
      <span>仪表板</span>
    </el-menu-item>
    <el-menu-item index="/data-management">
      <el-icon><Document /></el-icon>
      <span>数据管理</span>
    </el-menu-item>
    <el-sub-menu index="training">
      <template #title>
        <el-icon><Setting /></el-icon>
        <span>模型训练</span>
      </template>
      <el-menu-item index="/training/tasks">
        <el-icon><List /></el-icon>
        <span>训练任务</span>
      </el-menu-item>
      <el-menu-item index="/training/models">
        <el-icon><Cpu /></el-icon>
        <span>模型管理</span>
      </el-menu-item>
    </el-sub-menu>
  </el-menu>
</template>

<script setup lang="ts">
import { useUIStore } from '../../store/ui'
import { House, Monitor, Document, Setting, List, Cpu } from '@element-plus/icons-vue'

const uiStore = useUIStore()
</script>

<style scoped>
.sidebar-menu {
  height: 100%;
  border-right: none;
}
</style>