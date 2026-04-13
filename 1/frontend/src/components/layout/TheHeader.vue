<template>
  <div class="header-content">
    <h1>LLaMA-Factory Workstation</h1>
    <div class="header-actions">
      <el-button type="primary" size="small" @click="toggleSidebar">
        <el-icon>
          <Menu v-if="uiStore.isCollapsed" />
          <Close v-else />
        </el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useUIStore } from '../../store/ui'
import { Menu, Close } from '@element-plus/icons-vue'

const uiStore = useUIStore()

const toggleSidebar = () => {
  uiStore.toggleSidebar()
}
</script>

<style scoped>
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-content h1 {
  font-size: 20px;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>