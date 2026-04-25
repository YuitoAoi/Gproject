<template>
  <el-container class="main-layout">
    <el-header height="60px">
      <TheHeader />
    </el-header>
    <el-container>
      <el-aside width="200px">
        <TheSidebar />
      </el-aside>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import TheHeader from '@/components/layout/TheHeader.vue'
import TheSidebar from '@/components/layout/TheSidebar.vue'
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.el-header {
  background-color: #545c64;
  color: #fff;
  display: flex;
  align-items: center;
}

.el-aside {
  background-color: #f2f2f2;
}

.el-main {
  background-color: #fff;
  padding: 20px;
}
</style>
