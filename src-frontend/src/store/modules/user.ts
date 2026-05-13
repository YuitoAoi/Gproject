/**
 * 用户状态管理
 *
 * 管理用户登录状态、令牌、基本信息
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { router } from '@/router'

export interface UserInfo {
  userId: number | string
  userName: string
  email: string
  roles: string[]
  avatar: string
}

export const useUserStore = defineStore(
  'user',
  () => {
    /** 登录状态 */
    const isLogin = ref(false)
    /** 访问令牌 */
    const accessToken = ref('')
    /** 刷新令牌 */
    const refreshToken = ref('')
    /** 用户信息 */
    const info = ref<Partial<UserInfo>>({})
    /** 搜索历史 */
    const searchHistory = ref<any[]>([])
    /** 获取用户角色 */
    const roles = computed(() => info.value.roles || [])

    /** 是否为管理员 */
    const isAdmin = computed(() => roles.value.includes('R_ADMIN'))

    /**
     * 设置令牌
     */
    const setToken = (newAccessToken: string, newRefreshToken?: string) => {
      accessToken.value = newAccessToken
      if (newRefreshToken) {
        refreshToken.value = newRefreshToken
      }
    }

    /**
     * 设置登录状态
     */
    const setLoginStatus = (status: boolean) => {
      isLogin.value = status
    }

    /**
     * 设置用户信息
     */
    const setUserInfo = (newInfo: UserInfo) => {
      info.value = newInfo
    }

    /**
     * 设置搜索历史
     */
    const setSearchHistory = (list: any[]) => {
      searchHistory.value = list
    }

    /**
     * 退出登录
     */
    const logOut = () => {
      info.value = {}
      isLogin.value = false
      accessToken.value = ''
      refreshToken.value = ''

      const currentPath = router.currentRoute.value.fullPath
      const redirect = currentPath !== '/auth/login' ? currentPath : undefined
      router.push({
        path: '/auth/login',
        query: redirect ? { redirect } : undefined
      })
    }

    return {
      isLogin,
      accessToken,
      refreshToken,
      info,
      roles,
      isAdmin,
      searchHistory,
      setToken,
      setLoginStatus,
      setUserInfo,
      setSearchHistory,
      logOut
    }
  },
  {
    persist: {
      key: 'user',
      storage: localStorage
    }
  }
)
