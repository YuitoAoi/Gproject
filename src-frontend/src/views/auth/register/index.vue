<!-- 注册页面 -->
<template>
  <div class="flex w-full h-screen">
    <LoginLeftView />

    <div class="relative flex-1">
      <AuthTopBar />

      <div class="auth-right-wrap">
        <div class="form">
          <h3 class="title">注册</h3>
          <p class="sub-title">创建您的账号</p>
          <ElForm
            class="mt-7.5"
            ref="formRef"
            :model="formData"
            :rules="rules"
            label-position="top"
          >
            <ElFormItem prop="name">
              <ElInput
                class="custom-height"
                v-model.trim="formData.name"
                placeholder="请输入用户名"
              />
            </ElFormItem>

            <ElFormItem prop="email">
              <ElInput
                class="custom-height"
                v-model.trim="formData.email"
                placeholder="请输入邮箱"
              />
            </ElFormItem>

            <ElFormItem prop="password">
              <ElInput
                class="custom-height"
                v-model.trim="formData.password"
                placeholder="请输入密码"
                type="password"
                autocomplete="off"
                show-password
              />
            </ElFormItem>

            <ElFormItem prop="confirmPassword">
              <ElInput
                class="custom-height"
                v-model.trim="formData.confirmPassword"
                placeholder="请确认密码"
                type="password"
                autocomplete="off"
                @keyup.enter="register"
                show-password
              />
            </ElFormItem>

            <div style="margin-top: 15px">
              <ElButton
                class="w-full custom-height"
                type="primary"
                @click="register"
                :loading="loading"
                v-ripple
              >
                注册
              </ElButton>
            </div>

            <div class="mt-5 text-sm text-g-600">
              <span>已有账号？</span>
              <RouterLink class="text-theme" :to="{ name: 'Login' }">去登录</RouterLink>
            </div>
          </ElForm>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ElMessage } from 'element-plus'
  import type { FormInstance, FormRules } from 'element-plus'
  import { fetchRegister } from '@/api/auth'
  import { useRouter } from 'vue-router'

  defineOptions({ name: 'Register' })

  interface RegisterForm {
    name: string
    email: string
    password: string
    confirmPassword: string
  }

  const USERNAME_MIN_LENGTH = 3
  const USERNAME_MAX_LENGTH = 50
  const PASSWORD_MIN_LENGTH = 8
  const REDIRECT_DELAY = 1000

  const router = useRouter()
  const formRef = ref<FormInstance>()

  const loading = ref(false)

  const formData = reactive<RegisterForm>({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  })

  /**
   * 验证用户名
   */
  const validateName = (_rule: any, value: string, callback: (error?: Error) => void) => {
    if (!value) {
      callback(new Error('请输入用户名'))
      return
    }
    if (value.length < USERNAME_MIN_LENGTH || value.length > USERNAME_MAX_LENGTH) {
      callback(new Error('用户名长度需在3-50个字符之间'))
      return
    }
    callback()
  }

  /**
   * 验证邮箱
   */
  const validateEmail = (_rule: any, value: string, callback: (error?: Error) => void) => {
    if (!value) {
      callback(new Error('请输入邮箱'))
      return
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(value)) {
      callback(new Error('邮箱格式不正确'))
      return
    }
    callback()
  }

  /**
   * 验证密码强度
   * >=8 位，至少包含大小写/数字/特殊字符中的 2 类
   */
  const validatePassword = (_rule: any, value: string, callback: (error?: Error) => void) => {
    if (!value) {
      callback(new Error('请输入密码'))
      return
    }
    if (value.length < 8) {
      callback(new Error('密码长度不能少于8位'))
      return
    }
    let count = 0
    if (/[a-z]/.test(value)) count++
    if (/[A-Z]/.test(value)) count++
    if (/\d/.test(value)) count++
    if (/[^a-zA-Z0-9]/.test(value)) count++
    if (count < 2) {
      callback(new Error('密码强度不够，需包含大小写字母、数字或特殊字符中的至少2类'))
      return
    }

    if (formData.confirmPassword) {
      formRef.value?.validateField('confirmPassword')
    }

    callback()
  }

  /**
   * 验证确认密码
   * 检查确认密码是否与密码一致
   */
  const validateConfirmPassword = (
    _rule: any,
    value: string,
    callback: (error?: Error) => void
  ) => {
    if (!value) {
      callback(new Error('请确认密码'))
      return
    }

    if (value !== formData.password) {
      callback(new Error('两次输入的密码不一致'))
      return
    }

    callback()
  }

  const rules = computed<FormRules<RegisterForm>>(() => ({
    name: [{ required: true, validator: validateName, trigger: 'blur' }],
    email: [{ required: true, validator: validateEmail, trigger: 'blur' }],
    password: [{ required: true, validator: validatePassword, trigger: 'blur' }],
    confirmPassword: [{ required: true, validator: validateConfirmPassword, trigger: 'blur' }]
  }))

  /**
   * 注册用户
   * 验证表单后提交注册请求
   */
  const register = async () => {
    if (!formRef.value) return

    try {
      await formRef.value.validate()
      loading.value = true

      const response = await fetchRegister({
        name: formData.name.trim(),
        email: formData.email,
        password: formData.password
      })

      if (response.success) {
        ElMessage.success('注册成功')
        toLogin()
      } else {
        ElMessage.error(response.error || '注册失败')
      }
    } catch (error) {
      console.error('[Register] error:', error)
      ElMessage.error('注册失败')
    } finally {
      loading.value = false
    }
  }

  /**
   * 跳转到登录页面
   */
  const toLogin = () => {
    setTimeout(() => {
      router.push({ name: 'Login' })
    }, REDIRECT_DELAY)
  }
</script>

<style scoped>
  @import '../login/style.css';
</style>
