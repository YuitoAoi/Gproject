<template>
  <div class="header">
    <div class="header-left">
      <h2>LLaMA-Factory Workstation</h2>
    </div>
    <div class="header-right">
      <el-button @click="toggleSidebar">
        <span v-if="isCollapsed">展开</span>
        <span v-else>收起</span>
      </el-button>
      <el-badge :value="status" :type="statusType" class="status-badge" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUIStore } from '@/store/ui'
import httpClient from '@/api/httpClient'

const uiStore = useUIStore()

const isCollapsed = computed(() => uiStore.isCollapsed)

const status = computed(() => uiStore.connected ? 'Connected' : 'Disconnected')
const statusType = computed(() => uiStore.connected ? 'success' : 'danger')

const toggleSidebar = () => {
  uiStore.toggleSidebar()
}

uiStore.checkBackendConnection()
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-left h2 {
  margin: 0;
  font-size: 18px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-badge {
  margin-left: 8px;
}
</style>
