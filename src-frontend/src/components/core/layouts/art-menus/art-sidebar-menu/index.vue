<!-- 左侧菜单 -->
<template>
  <div class="layout-sidebar" v-if="menuList.length > 0">
    <div
      class="menu-left"
      :class="`menu-left-${menuTheme} menu-left-${!sidebarOpen ? 'close' : 'open'}`"
      :style="{ background: menuBackground }"
    >
      <!-- Logo、系统名称 -->
      <div class="header" @click="navigateToHome" :style="{ background: menuBackground }">
        <ArtLogo class="logo" />
        <p :style="{ opacity: !sidebarOpen ? 0 : 1 }">
          LLaMA-Factory Workstation
        </p>
      </div>

      <ElScrollbar style="height: calc(100% - 60px)">
        <ElMenu
          :class="'el-menu-' + menuTheme"
          :collapse="!sidebarOpen"
          :default-active="currentPath"
          :unique-opened="true"
          :background-color="menuBackground"
          :text-color="menuTextColor"
        >
          <template v-for="menu in visibleMenus" :key="menu.path">
            <!-- 有子菜单 -->
            <ElSubMenu v-if="menu.children?.length" :index="menu.path">
              <template #title>
                <div class="menu-icon flex-cc">
                  <ArtSvgIcon :icon="menu.icon" />
                </div>
                <span class="menu-name">{{ menu.title }}</span>
              </template>
              <ElMenuItem
                v-for="child in menu.children"
                :key="child.path"
                :index="child.path"
                @click="navigateTo(child.path)"
              >
                <div class="menu-icon flex-cc">
                  <ArtSvgIcon :icon="child.icon" />
                </div>
                <template #title>
                  <span class="menu-name">{{ child.title }}</span>
                </template>
              </ElMenuItem>
            </ElSubMenu>

            <!-- 无子菜单 -->
            <ElMenuItem v-else :index="menu.path" @click="navigateTo(menu.path)">
              <div class="menu-icon flex-cc">
                <ArtSvgIcon :icon="menu.icon" />
              </div>
              <template #title>
                <span class="menu-name">{{ menu.title }}</span>
              </template>
            </ElMenuItem>
          </template>
        </ElMenu>
      </ElScrollbar>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { useAppStore, type MenuItem } from '@/store/modules/app'
  import { useUserStore } from '@/store/modules/user'

  defineOptions({ name: 'ArtSidebarMenu' })

  const route = useRoute()
  const router = useRouter()
  const appStore = useAppStore()
  const userStore = useUserStore()

  const sidebarOpen = computed(() => appStore.sidebarOpen)
  const menuList = computed(() => appStore.menuList)
  const currentPath = computed(() => route.path)

  // 菜单主题（跟随暗色模式）
  const menuTheme = computed(() => (appStore.isDark ? 'dark' : 'design'))
  const menuBackground = computed(() => (appStore.isDark ? 'var(--default-box-color)' : '#FFFFFF'))
  const menuTextColor = computed(() => (appStore.isDark ? '#BABBBD' : '#29343D'))

  // 根据用户角色过滤菜单
  const visibleMenus = computed(() => {
    const roles = userStore.roles
    return filterMenuByRoles(menuList.value, roles)
  })

  /** 根据角色过滤菜单 */
  function filterMenuByRoles(menus: MenuItem[], roles: string[]): MenuItem[] {
    return menus
      .filter((menu) => {
        if (!menu.roles || menu.roles.length === 0) return true
        return menu.roles.some((role) => roles.includes(role))
      })
      .map((menu) => ({
        ...menu,
        children: menu.children
          ? filterMenuByRoles(menu.children, roles)
          : undefined
      }))
  }

  /** 导航到首页 */
  const navigateToHome = () => {
    router.push('/workbench/dashboard')
  }

  /** 导航到指定路径 */
  const navigateTo = (path: string) => {
    router.push(path)
  }
</script>

<style lang="scss" scoped>
  @use './style';
</style>

<style lang="scss">
  @use './theme';

  .layout-sidebar {
    .el-menu:not(.el-menu--collapse) {
      width: v-bind('appStore.sidebarWidthPx');
    }
    .el-menu--collapse {
      width: 64px;
    }
  }
</style>
