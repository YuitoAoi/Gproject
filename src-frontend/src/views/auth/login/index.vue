<!-- 登录页面 -->
<template>
  <div class="flex w-full h-screen">
    <LoginLeftView />

    <div class="relative flex-1">
      <AuthTopBar />

      <div class="auth-right-wrap">
        <div class="form">
          <h3 class="title">登录</h3>
          <p class="sub-title">欢迎回来，请输入您的账号信息</p>
          <ElForm
            ref="formRef"
            :model="formData"
            :rules="rules"
            @keyup.enter="handleSubmit"
            style="margin-top: 25px"
          >
            <ElFormItem prop="email">
              <ElInput
                class="custom-height"
                placeholder="请输入邮箱"
                v-model.trim="formData.email"
              />
            </ElFormItem>
            <ElFormItem prop="password">
              <ElInput
                class="custom-height"
                placeholder="请输入密码"
                v-model.trim="formData.password"
                type="password"
                autocomplete="off"
                show-password
              />
            </ElFormItem>

            <div class="flex-cb mt-2 text-sm">
              <ElCheckbox v-model="formData.rememberPassword">记住密码</ElCheckbox>
              <RouterLink class="text-theme" :to="{ name: 'ForgetPassword' }">忘记密码？</RouterLink>
            </div>

            <div style="margin-top: 30px">
              <ElButton
                class="w-full custom-height"
                type="primary"
                @click="handleSubmit"
                :loading="loading"
                v-ripple
              >
                登录
              </ElButton>
            </div>

            <div class="mt-5 text-sm text-gray-600">
              <span>还没有账号？</span>
              <RouterLink class="text-theme" :to="{ name: 'Register' }">立即注册</RouterLink>
            </div>
          </ElForm>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { useUserStore } from '@/store/modules/user'
  import { fetchLogin, fetchGetUserInfo } from '@/api/auth'
  import { ElNotification, type FormInstance, type FormRules } from 'element-plus'

  defineOptions({ name: 'Login' })

  const userStore = useUserStore()
  const router = useRouter()
  const route = useRoute()

  const formRef = ref<FormInstance>()

  const formData = reactive({
    email: '',
    password: '',
    rememberPassword: true
  })

  const rules: FormRules = {
    email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
    password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
  }

  const loading = ref(false)

  const handleSubmit = async () => {
    if (!formRef.value) return

    try {
      const valid = await formRef.value.validate()
      if (!valid) return

      loading.value = true

      const { email, password } = formData

      const response = await fetchLogin({ email, password })

      if (!response.success) {
        throw new Error(response.error || '登录失败')
      }

      const { access_token, refresh_token } = response
      userStore.setToken(access_token, refresh_token)
      userStore.setLoginStatus(true)

      // 获取用户信息
      try {
        const userInfo = await fetchGetUserInfo()
        userStore.setUserInfo({
          userId: userInfo.id,
          userName: userInfo.name,
          email: userInfo.email,
          roles: userInfo.is_admin ? ['R_ADMIN', 'R_USER'] : ['R_USER'],
          avatar: ''
        })
      } catch (e) {
        console.warn('[Login] 获取用户信息失败，使用基本信息', e)
      }

      ElNotification({
        title: '登录成功',
        type: 'success',
        duration: 2500,
        message: '欢迎回来！'
      })

      const redirect = route.query.redirect as string
      router.push(redirect || '/workbench/dashboard')
    } catch (error) {
      console.error('[Login] error:', error)
    } finally {
      loading.value = false
    }
  }
</script>

<style scoped>
  @import './style.css';
</style>
