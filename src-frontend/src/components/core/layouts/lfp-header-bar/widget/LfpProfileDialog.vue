<!-- 个人设置弹窗 -->
<template>
  <ElDialog
    v-model="visible"
    title="个人设置"
    width="420px"
    :close-on-click-modal="false"
    @closed="handleClosed"
  >
    <div class="profile-panel">
      <Transition :name="transitionName" mode="out-in">
        <!-- 信息展示面板 -->
        <div v-if="!editing" key="info" class="info-panel">
          <div class="info-item">
            <span class="info-label">用户名</span>
            <span class="info-value">{{ userStore.info.userName || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">邮箱</span>
            <span class="info-value">{{ userStore.info.email || '-' }}</span>
          </div>
          <div class="mt-6 flex justify-center">
            <ElButton type="primary" @click="editing = true">
              <LfpSvgIcon icon="ri:edit-line" class="mr-1.5" />
              修改信息
            </ElButton>
          </div>
        </div>

        <!-- 编辑表单面板 -->
        <div v-else key="edit" class="edit-panel">
          <ElForm ref="formRef" :model="formData" :rules="rules" label-width="70px">
            <ElFormItem label="用户名" prop="name">
              <ElInput v-model="formData.name" placeholder="请输入用户名" />
            </ElFormItem>
            <ElFormItem label="邮箱" prop="email">
              <ElInput v-model="formData.email" placeholder="请输入邮箱" />
            </ElFormItem>
            <ElFormItem label="原密码" prop="old_password">
              <ElInput
                v-model="formData.old_password"
                type="password"
                show-password
                placeholder="如需修改密码请填写"
              />
            </ElFormItem>
            <ElFormItem label="新密码" prop="password">
              <ElInput
                v-model="formData.password"
                type="password"
                show-password
                placeholder="请输入新密码"
              />
            </ElFormItem>
          </ElForm>
          <div class="flex justify-end gap-3 mt-2">
            <ElButton @click="editing = false">取消</ElButton>
            <ElButton type="primary" :loading="submitting" @click="handleSubmit">确定</ElButton>
          </div>
        </div>
      </Transition>
    </div>
  </ElDialog>
</template>

<script setup lang="ts">
  import { ref, reactive, watch, computed } from 'vue'
  import type { FormInstance, FormRules } from 'element-plus'
  import { ElMessage } from 'element-plus'
  import { useUserStore } from '@/store/modules/user'
  import { fetchGetUserInfo } from '@/api/auth'
  import request from '@/utils/http'

  defineOptions({ name: 'LfpProfileDialog' })

  const visible = defineModel<boolean>('visible', { default: false })
  const userStore = useUserStore()
  const formRef = ref<FormInstance>()
  const submitting = ref(false)
  const editing = ref(false)
  const transitionName = computed(() => (editing.value ? 'slide-left' : 'slide-right'))

  const formData = reactive({
    name: '',
    email: '',
    old_password: '',
    password: ''
  })

  const rules: FormRules = {
    name: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    email: [
      { required: true, message: '请输入邮箱', trigger: 'blur' },
      { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
    ],
    password: [{ min: 8, message: '密码长度不少于8位', trigger: 'blur' }]
  }

  watch(visible, (val) => {
    if (val) {
      editing.value = false
      formData.name = (userStore.info.userName as string) || ''
      formData.email = (userStore.info.email as string) || ''
      formData.old_password = ''
      formData.password = ''
    }
  })

  const handleSubmit = async () => {
    if (!formRef.value) return
    const valid = await formRef.value.validate().catch(() => false)
    if (!valid) return

    submitting.value = true
    try {
      const updateData: Record<string, string> = {}
      if (formData.name !== userStore.info.userName) updateData.name = formData.name
      if (formData.email !== userStore.info.email) updateData.email = formData.email
      if (formData.old_password && formData.password) {
        updateData.old_password = formData.old_password
        updateData.password = formData.password
      }

      if (Object.keys(updateData).length === 0) {
        ElMessage.info('未修改任何信息')
        return
      }

      const res = await request.patch<{ success: boolean; error?: string }>({
        url: '/user',
        data: updateData
      })
      if (!res.success) {
        ElMessage.error(res.error || '更新失败')
        return
      }

      const userInfo = await fetchGetUserInfo()
      userStore.setUserInfo({
        userId: userInfo.id,
        userName: userInfo.name,
        email: userInfo.email,
        roles: userInfo.roles
      })

      ElMessage.success('修改成功')
      editing.value = false
    } catch (error: any) {
      ElMessage.error(error?.message || '操作失败')
    } finally {
      submitting.value = false
    }
  }

  const handleClosed = () => {
    formRef.value?.resetFields()
    editing.value = false
  }
</script>

<style scoped>
  @reference '@styles/core/tailwind.css';

  .profile-panel {
    @apply py-1 overflow-hidden;
  }

  .info-panel .info-item {
    @apply flex items-center justify-between py-3 border-b border-g-100;
  }

  .info-panel .info-label {
    @apply text-sm text-g-500;
  }

  .info-panel .info-value {
    @apply text-sm font-medium text-g-800;
  }

  .edit-panel {
    @apply pt-1;
  }

  /* 点击"修改信息"：信息面板向左滑出，编辑面板从右侧滑入 */
  .slide-left-enter-active,
  .slide-left-leave-active {
    transition: all 0.25s ease-in-out;
  }
  .slide-left-enter-from {
    transform: translateX(100%);
    opacity: 0;
  }
  .slide-left-leave-to {
    transform: translateX(-100%);
    opacity: 0;
  }

  /* 点击"取消"：编辑面板向右滑出，信息面板从左侧滑入 */
  .slide-right-enter-active,
  .slide-right-leave-active {
    transition: all 0.25s ease-in-out;
  }
  .slide-right-enter-from {
    transform: translateX(-100%);
    opacity: 0;
  }
  .slide-right-leave-to {
    transform: translateX(100%);
    opacity: 0;
  }
</style>
