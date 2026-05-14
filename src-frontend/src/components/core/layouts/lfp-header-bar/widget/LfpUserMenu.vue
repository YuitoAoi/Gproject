<!-- 用户中心按钮 + 下拉菜单 -->
<template>
  <ElPopover
    ref="userMenuPopover"
    placement="bottom-end"
    :width="180"
    :hide-after="0"
    :offset="8"
    trigger="click"
    :show-arrow="false"
    popper-style="padding: 6px;"
  >
    <template #reference>
      <button class="user-center-btn">
        <LfpSvgIcon icon="ri:user-3-line" class="mr-1.5 text-sm" />
        用户中心
      </button>
    </template>
    <template #default>
      <div class="flex flex-col gap-1">
        <div class="menu-item" @click="openProfile">
          <LfpSvgIcon icon="ri:settings-3-line" class="mr-2 text-base" />
          个人设置
        </div>
        <div class="menu-item menu-item--danger" @click="loginOut">
          <LfpSvgIcon icon="ri:logout-box-r-line" class="mr-2 text-base" />
          退出登录
        </div>
      </div>
    </template>
  </ElPopover>

  <!-- 个人设置弹窗 -->
  <LfpProfileDialog v-model:visible="profileVisible" />
</template>

<script setup lang="ts">
  import { ref } from 'vue'
  import { ElMessageBox } from 'element-plus'
  import { useUserStore } from '@/store/modules/user'
  import LfpProfileDialog from './LfpProfileDialog.vue'

  defineOptions({ name: 'LfpUserMenu' })

  const userStore = useUserStore()
  const userMenuPopover = ref()
  const profileVisible = ref(false)

  const openProfile = () => {
    userMenuPopover.value?.hide()
    profileVisible.value = true
  }

  const loginOut = (): void => {
    userMenuPopover.value?.hide()
    setTimeout(() => {
      ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        customClass: 'login-out-dialog'
      }).then(() => {
        userStore.logOut()
      })
    }, 150)
  }
</script>

<style scoped>
  @reference '@styles/core/tailwind.css';

  .user-center-btn {
    @apply flex items-center px-3 py-1.5 mr-4 text-sm text-g-700 bg-g-100 rounded-lg
      border border-g-200 cursor-pointer transition-all duration-150
      hover:bg-g-200 hover:border-g-300 active:scale-95;
  }

  .menu-item {
    @apply flex items-center py-2 px-3 text-sm text-g-700 rounded-md cursor-pointer
      transition-colors duration-150 hover:bg-g-100;
  }

  .menu-item--danger {
    @apply text-red-500 hover:bg-red-50;
  }
</style>
