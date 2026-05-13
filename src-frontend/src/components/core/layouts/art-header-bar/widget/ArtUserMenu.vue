<!-- 用户菜单 -->
<template>
  <ElPopover
    ref="userMenuPopover"
    placement="bottom-end"
    :width="240"
    :hide-after="0"
    :offset="10"
    trigger="hover"
    :show-arrow="false"
    popper-class="user-menu-popover"
    popper-style="padding: 5px 16px;"
  >
    <template #reference>
      <img
        class="size-8.5 mr-5 c-p rounded-full max-sm:w-6.5 max-sm:h-6.5 max-sm:mr-[16px]"
        src="@imgs/user/avatar.webp"
        alt="avatar"
      />
    </template>
    <template #default>
      <div class="pt-3">
        <div class="flex-c pb-1 px-0">
          <img
            class="w-10 h-10 mr-3 ml-0 overflow-hidden rounded-full float-left"
            src="@imgs/user/avatar.webp"
          />
          <div class="w-[calc(100%-60px)] h-full">
            <span class="block text-sm font-medium text-g-800 truncate">{{
              userStore.info.userName || '用户'
            }}</span>
            <span class="block mt-0.5 text-xs text-g-500 truncate">{{ userStore.info.email }}</span>
          </div>
        </div>
        <ul class="py-4 mt-3 border-t border-g-300/80">
          <div class="w-full h-px my-2 bg-g-300/80"></div>
          <div class="log-out c-p" @click="loginOut">
            退出登录
          </div>
        </ul>
      </div>
    </template>
  </ElPopover>
</template>

<script setup lang="ts">
  import { ElMessageBox } from 'element-plus'
  import { useUserStore } from '@/store/modules/user'

  defineOptions({ name: 'ArtUserMenu' })

  const userStore = useUserStore()
  const userMenuPopover = ref()

  const loginOut = (): void => {
    setTimeout(() => {
      userMenuPopover.value?.hide()
    }, 100)
    setTimeout(() => {
      ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        customClass: 'login-out-dialog'
      }).then(() => {
        userStore.logOut()
      })
    }, 200)
  }
</script>

<style scoped>
  @reference '@styles/core/tailwind.css';

  .log-out {
    @apply py-1.5
    mt-5
    text-xs
    text-center
    border
    border-g-400
    rounded-md
    transition-all
    duration-200
    hover:shadow-xl;
    cursor: pointer;
  }
</style>
